#!/usr/bin/env python3
"""Sixième tranche : les amendements de l'Assemblée nationale entrent en base.

Le corpus n'était jusqu'ici que sénatorial, alors que l'Assemblée est la chambre
de dépôt de la plupart des textes du périmètre. Cette tranche charge les 11 117
amendements de la XIVe législature extraits par `tools/an/extraire_amendements_an.py`,
d'où proviennent 513 des 832 articles éligibles.

**Les signataires ne sont pas nommés dans le fichier des amendements.** Il ne
porte que des références — `PA267551` pour l'acteur, `PO…` pour le groupe — qui se
résolvent par le jeu Acteurs historique de l'Assemblée. Sans ce second fichier,
les amendements auraient un sort mais pas d'auteur, ce qui vide de sens la moitié
de la promesse produit.

**Aucune URL n'est fabriquée.** Les anciennes adresses des amendements
(`/14/amendements/1015/AN/…asp`) rendent aujourd'hui 404 et le schéma `/dyn/` ne
les sert pas. Écrire une URL plausible mais morte contreviendrait au § 4.3, qui
exige une citation résoluble : le champ reste vide, et l'amendement est cité par
son numéro et son texte. La XIIIe législature fait exception : ses pages sont
celles-là mêmes que `tools/an/moissonner_amendements_13.py` a lues, et elles
répondent ; leur adresse est gardée.

**Les deux colonnes de sort sont chargées, pas une.** `sort[1]/sortEnSeance[1]`
est le sort, et c'est bien lui qu'il faut lire — `etat[1]` vaut « Discuté » sur
les 9 966 amendements qui en ont un. Mais l'inverse n'est pas vrai : sur les
1 149 amendements sans sort publié, `etat` dit « Retiré » 694 fois et
« Irrecevable » 447 fois. N'en garder qu'une faisait afficher zéro irrecevabilité
à l'Assemblée. La colonne `etat` est donc en base à côté de `sort`, et
`ingestion/sort_des_amendements.py` est seul à décider laquelle prime.

Usage :
    an_vers_amendements.py <amendements_extraits.csv> <acteurs_historique.json.zip> <base.sqlite>
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "prototype"))
from resolveur import sans_balises  # noqa: E402

csv.field_size_limit(10 ** 9)


def repertoire_acteurs(archive: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Références `PA…` → nom, et `PO…` → libellé de groupe politique."""
    z = zipfile.ZipFile(archive)
    acteurs: dict[str, str] = {}
    groupes: dict[str, str] = {}
    for nom in z.namelist():
        if "/acteur/" in nom:
            fiche = json.loads(z.read(nom)).get("acteur", {})
            ident = fiche.get("etatCivil", {}).get("ident", {})
            uid = fiche.get("uid", {})
            cle = uid.get("#text") if isinstance(uid, dict) else uid
            if cle and ident.get("nom"):
                acteurs[cle] = " ".join(
                    x for x in (ident.get("civ"), ident.get("prenom"), ident.get("nom")) if x)
        elif "/organe/" in nom:
            fiche = json.loads(z.read(nom)).get("organe", {})
            uid = fiche.get("uid")
            if uid and fiche.get("codeType") == "GP":
                groupes[uid] = fiche.get("libelleAbrege") or fiche.get("libelle") or ""
    return acteurs, groupes


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    extrait, archive_acteurs, chemin = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(chemin)
    base.execute("PRAGMA foreign_keys = ON")

    noms, groupes = repertoire_acteurs(archive_acteurs)
    dossiers = {d for (d,) in base.execute("SELECT id_dole FROM dossier")}
    # Les identifiants d'acteurs sont attribués à la suite de ceux déjà en base :
    # le chargement sénatorial en a posé 933 et ils ne doivent pas entrer en
    # collision.
    suivant = base.execute("SELECT coalesce(max(id), 0) + 1 FROM acteur").fetchone()[0]

    connus: dict[tuple[str, str], int] = {}
    for identifiant, nom, groupe in base.execute("SELECT id, nom, groupe FROM acteur"):
        connus[(nom, groupe or "")] = identifiant

    lignes, nouveaux, hors_dossier, sans_nom = [], [], 0, 0
    for a in csv.DictReader(extrait.open(encoding="utf-8")):
        if a["dossier"] not in dossiers:
            hors_dossier += 1
            continue
        if a["type_auteur"] == "Gouvernement":
            nom = "LE GOUVERNEMENT"
        else:
            nom = noms.get(a["acteur_ref"] or "", "")
        if not nom:
            sans_nom += 1
            nom = "(non résolu)"
        groupe = groupes.get(a["groupe_ref"] or "") or None
        cle = (nom, groupe or "")
        if cle not in connus:
            connus[cle] = suivant
            nouveaux.append((suivant, nom, groupe))
            suivant += 1
        # Le texte discuté porte le stade — texte déposé `B` ou texte de commission
        # `BTC` — et l'organe d'examen : le même numéro désigne des amendements
        # distincts selon l'un et l'autre.
        texte = f'{a["stade"]}{a["texte"]}/{a["organe_examen"] or "?"}'
        lignes.append((a["dossier"], "assemblee", texte, a["numero"], connus[cle],
                       a["sort"] or None, a["etat"] or None,
                       sans_balises(a["division"]) or None,
                       sans_balises(a["expose"]) or None,
                       sans_balises(a["dispositif"]) or None, a.get("url") or None))

    base.executemany("INSERT INTO acteur (id, nom, groupe) VALUES (?, ?, ?)", nouveaux)
    base.executemany(
        "INSERT OR IGNORE INTO amendement (dossier_id, chambre, texte_discute, numero,"
        " auteur_id, sort, etat, subdivision, objet, dispositif, url)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", lignes)
    base.commit()

    par_chambre = base.execute(
        "SELECT chambre, count(*) FROM amendement GROUP BY chambre").fetchall()
    par_sort = base.execute(
        "SELECT sort, count(*) FROM amendement WHERE chambre = 'assemblee'"
        " GROUP BY sort ORDER BY 2 DESC LIMIT 5").fetchall()
    violations = base.execute("PRAGMA foreign_key_check").fetchall()

    print(f"acteurs du répertoire      : {len(noms)} personnes, {len(groupes)} groupes")
    print(f"amendements AN présentés   : {len(lignes)}")
    print(f"  écartés, dossier hors périmètre : {hors_dossier}")
    print(f"  signataire non résolu    : {sans_nom}")
    print(f"acteurs créés              : {len(nouveaux)}")
    print("\namendements en base :")
    for chambre, n in par_chambre:
        print(f"  {chambre:12s} {n}")
    print("\nsorts, Assemblée :")
    for sort, n in par_sort:
        print(f"  {sort or '(vide)':16s} {n}")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
