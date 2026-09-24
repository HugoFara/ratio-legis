#!/usr/bin/env python3
"""Extraction des amendements de l'Assemblée nationale pour les dossiers du périmètre.

**Le dépôt existe, contrairement à ce que ce projet a d'abord conclu.** Le chemin
publié sur la page d'archives de la XIVe législature pointe vers un hôte
`data-preprod` qui ne résout pas, et le chemin voisin `amendements_legis/` rend
404. Le bon chemin est `amendements_legis_XIV/`, et il est servi en clair :

    /static/openData/repository/14/loi/amendements_legis_XIV/Amendements_XIV.csv.zip

Il a été retrouvé par l'index CDX de la Wayback Machine, qui archive l'arborescence
du dépôt. La leçon est générale : un 404 sur une URL recopiée d'une page
institutionnelle prouve que l'URL est fausse, pas que la donnée est absente.

Le CSV fait 420 Mo pour 624 colonnes — un XML aplati. Il est lu en flux depuis
l'archive, sans décompression sur disque.

Deux formats de référence de texte coexistent et les confondre fait perdre la
moitié du corpus : `…L14B1015` désigne le texte déposé, `…L14BTC2442` le texte
issu des travaux de commission.

Depuis la XVe législature, l'Assemblée ne publie plus de CSV mais une fiche JSON
par amendement (`Amendements_XV.json.zip`, puis `amendements_div_legis/
Amendements.json.zip`) ; `lire_json` en tire les mêmes colonnes.

Usage :
    extraire_amendements_an.py <Amendements_XIV.csv.zip | Amendements_*.json.zip>
                               <plan-textes.tsv> <sortie.csv>

Le plan associe un identifiant DOLE à un numéro de texte de l'Assemblée, une
ligne par couple.
"""

from __future__ import annotations

import collections
import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path

csv.field_size_limit(10 ** 9)

# Le marqueur `B` ou `BTC` est capturé, pas seulement toléré : il dit sur quel
# texte l'amendement est déposé, le texte déposé (`B2736`) ou le texte issu de la
# commission (`BTC2736`). Les confondre en écrasait 2 032 — mais 2 030 d'entre eux
# n'étaient qu'un même amendement publié sous les deux stades, que
# `dedoublonner` fond désormais ; ce ne sont pas des amendements distincts.
REFERENCE = re.compile(r"L\d\d(B(?:TC)?)(\d+)")

# Colonnes utiles du fichier aplati, par position : les intitulés sont des chemins
# XML (« identifiant[1]/saisine[1]/refTexteLegislatif[1] ») et changent de forme
# d'une législature à l'autre, mais les positions de tête sont stables.
# Le sort n'est pas dans la colonne `sort[1]`, qui est vide sur toute la
# législature, mais dans `sort[1]/sortEnSeance[1]`. `etat[1]` ne dit que l'état
# procédural — « Discuté », « Irrecevable » — et le prendre pour le sort ferait
# disparaître 3 280 rejets derrière un « Discuté » uniforme.
#
# L'auteur n'est pas nommé non plus : les colonnes portent des références
# (`PA…` pour l'acteur, `PO…` pour l'organe), résolues par le jeu Acteurs de
# l'Assemblée. Elles sont conservées telles quelles, à charger séparément.
# `organeExamen` est indispensable à l'identité : le même numéro d'amendement
# désigne deux amendements différents sur le même texte selon qu'il est examiné en
# commission ou en séance — 2 098 couples (texte, numéro) en double, aux
# dispositifs et aux sorts distincts. Sans lui, 2 116 amendements disparaissent
# silencieusement à l'insertion.
COLONNES = {
    "numero": 4, "ref_texte": 7, "organe_examen": 9, "etat": 16, "type_auteur": 19,
    "acteur_ref": 20, "organe_ref": 21, "groupe_ref": 22,
    "division": 35, "dispositif": 47, "expose": 48, "sort": 70,
}
ORGANE_EXAMEN = re.compile(r"L\d+(PO\d+)")
LIGNE_DU_PLAN = re.compile(r"(JORFDOLE\d+)\t(\d+)")

# Lues pour reconnaître un doublon, non écrites : le document publié de
# l'amendement, l'horodatage de son sort, et son identifiant, qui dit s'il est
# examiné en séance (`…SEA…`) ou en commission.
DOCUMENT, DATE_SORT, UID = 65, 69, 1


def dedoublonner(retenus: list[list[str]],
                 meta: list[tuple[str, str, str]]) -> tuple[list[list[str]], int]:
    """Fond les copies B / BTC d'un même amendement. Rend (lignes, copies retirées).

    **Le même amendement est publié deux fois**, sous le texte déposé (`B2736`) et
    sous le texte de commission (`BTC2736`) : même numéro, même organe, même
    document PDF, même dispositif, même sort, à la seconde près. Sur toute la
    XIVe législature, 11 945 couples (numéro, organe) existent sous les deux
    stades ; 11 934 sont ce doublon, 11 seulement sont deux amendements distincts
    — ceux que le commentaire de `REFERENCE` a raison de ne pas confondre. Les
    garder tous deux donnait deux arêtes pour une (798 sur le texte 2736).

    L'identité est le document publié, non le numéro : deux amendements distincts
    n'ont pas le même PDF, et le dispositif doit concorder en plus.

    **Le stade retenu** est celui que portent les autres amendements, non
    doublés, du même texte devant le même organe : c'est le texte que cet organe
    examinait, et c'est lui dont l'alinéa nommé par l'amendement est numéroté. À
    défaut, l'usage de la législature : BTC en séance (67 631 amendements seuls
    contre 19 718), B en commission (50 117 contre 214).

    **Le sort vient de la copie la plus récente.** Dans 28 couples, l'une des deux
    est restée « A discuter », sans sort, quand l'autre dit « Rejeté » ou
    « Adopté » avec son horodatage.
    """
    i_numero, i_organe = 3 + list(COLONNES).index("numero"), 3 + list(COLONNES).index("organe_examen")
    i_disp = 3 + list(COLONNES).index("dispositif")
    groupes: dict[tuple[str, ...], list[int]] = collections.defaultdict(list)
    for rang, (ligne, (document, _, _)) in enumerate(zip(retenus, meta)):
        if document:
            groupes[(ligne[1], ligne[i_numero], ligne[i_organe], document)].append(rang)
    doublons = [r for r in groupes.values()
                if len(r) == 2 and {retenus[i][2] for i in r} == {"B", "BTC"}
                and retenus[r[0]][i_disp] == retenus[r[1]][i_disp]]
    doubles = {i for r in doublons for i in r}
    usage: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter)
    for rang, ligne in enumerate(retenus):
        if rang not in doubles:
            usage[(ligne[1], ligne[i_organe])][ligne[2]] += 1

    i_sort, i_etat = 3 + list(COLONNES).index("sort"), 3 + list(COLONNES).index("etat")
    retires: set[int] = set()
    for paire in doublons:
        a, b = paire
        texte, organe = retenus[a][1], retenus[a][i_organe]
        compte = usage[(texte, organe)]
        if compte["B"] != compte["BTC"]:
            stade = "B" if compte["B"] > compte["BTC"] else "BTC"
        else:
            stade = "BTC" if "SEA" in meta[a][2] else "B"
        garde, retire = (a, b) if retenus[a][2] == stade else (b, a)
        # `max` sur l'horodatage ISO : une copie sans sort a une date vide.
        recente = max(paire, key=lambda i: meta[i][1])
        retenus[garde][i_sort] = retenus[recente][i_sort]
        retenus[garde][i_etat] = retenus[recente][i_etat]
        retires.add(retire)
    return [l for i, l in enumerate(retenus) if i not in retires], len(retires)


def plan(chemin: Path) -> dict[str, set[str]]:
    """Numéro de texte de l'Assemblée → identifiants DOLE."""
    textes: dict[str, set[str]] = collections.defaultdict(set)
    for rang, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
        if not ligne.strip():
            continue
        # Une ligne mal formée arrête tout : le plan de la XIVe a perdu un saut
        # de ligne, et « 4378JORFDOLE…\t1015 » a fait disparaître en silence le
        # projet de loi Hamon et ses amendements.
        trouve = LIGNE_DU_PLAN.fullmatch(ligne.strip())
        if not trouve:
            sys.exit(f"{chemin}:{rang} : ligne de plan illisible : {ligne!r}")
        textes[trouve.group(2).lstrip("0")].add(trouve.group(1))
    return textes


def _valeur(noeud, *chemin: str) -> str:
    """Suit un chemin dans le JSON de l'Assemblée. Un champ absent ou nul
    (`{"@xsi:nil": "true"}`) rend la chaîne vide, comme une cellule vide du CSV."""
    for cle in chemin:
        if not isinstance(noeud, dict):
            return ""
        noeud = noeud.get(cle)
    return noeud if isinstance(noeud, str) else ""


def _amendements(objet):
    """Les fiches `amendement` d'un document, où qu'elles soient : une par fichier
    dans les archives récentes, regroupées par texte dans d'autres."""
    if isinstance(objet, dict):
        fiche = objet.get("amendement")
        if isinstance(fiche, dict) and "uid" in fiche:
            yield fiche
        elif isinstance(fiche, list):
            yield from (f for f in fiche if isinstance(f, dict) and "uid" in f)
        for cle, enfant in objet.items():
            if cle != "amendement":
                yield from _amendements(enfant)
    elif isinstance(objet, list):
        for enfant in objet:
            yield from _amendements(enfant)


def lire_csv(z: zipfile.ZipFile):
    """XIVe législature : un CSV de 624 colonnes, un XML aplati."""
    membre = max(z.namelist(), key=lambda n: z.getinfo(n).file_size)
    with z.open(membre) as flux:
        lecteur = csv.reader(io.TextIOWrapper(flux, encoding="utf-8", errors="replace"),
                             delimiter=";")
        next(lecteur)
        for ligne in lecteur:
            if len(ligne) <= max(COLONNES.values()):
                continue
            yield ({nom: ligne[i] for nom, i in COLONNES.items()},
                   (ligne[DOCUMENT], ligne[DATE_SORT], ligne[UID]))


def lire_json(z: zipfile.ZipFile):
    """Depuis la XVe législature : une fiche JSON par amendement, et plus de CSV.

    Les champs sont les mêmes que les colonnes du CSV de la XIVe, sous leur nom
    XML. Deux écarts. L'organe d'examen n'a plus de champ propre : il est dans
    `examenRef` (`EXANR5L17PO59046BTC1376P0D1`). Et le numéro est
    `numeroOrdreDepot` — `numeroLong` y ajoute le préfixe de la commission
    (« AE12 »), que la XIVe ne portait pas.
    """
    for membre in z.namelist():
        if not membre.endswith(".json"):
            continue
        for a in _amendements(json.loads(z.read(membre))):
            examen = ORGANE_EXAMEN.search(_valeur(a, "examenRef"))
            auteur = a.get("signataires", {}).get("auteur", {})
            cycle = a.get("cycleDeVie", {})
            champs = {
                "numero": _valeur(a, "identification", "numeroOrdreDepot"),
                "ref_texte": _valeur(a, "texteLegislatifRef"),
                "organe_examen": examen.group(1) if examen else "",
                "etat": _valeur(cycle, "etatDesTraitements", "etat", "libelle"),
                "type_auteur": _valeur(auteur, "typeAuteur"),
                "acteur_ref": _valeur(auteur, "acteurRef"),
                "organe_ref": _valeur(auteur, "auteurRapporteurOrganeRef"),
                "groupe_ref": _valeur(auteur, "groupePolitiqueRef"),
                "division": _valeur(a, "pointeurFragmentTexte", "division",
                                    "articleDesignationCourte"),
                "dispositif": _valeur(a, "corps", "contenuAuteur", "dispositif"),
                "expose": _valeur(a, "corps", "contenuAuteur", "exposeSommaire"),
                "sort": _valeur(cycle, "sort"),
            }
            document = _valeur(a, "representations", "representation", "contenu",
                               "documentURI")
            yield champs, (document, _valeur(cycle, "dateSort"), _valeur(a, "uid"))


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    archive, fichier_plan, sortie = (Path(a) for a in sys.argv[1:])
    textes = plan(fichier_plan)

    z = zipfile.ZipFile(archive)
    lecture = lire_json(z) if archive.name.endswith(".json.zip") else lire_csv(z)
    retenus, meta, par_texte, lues = [], [], collections.Counter(), 0
    for champs, marques in lecture:
        lues += 1
        trouve = REFERENCE.search(champs["ref_texte"] or "")
        if not trouve:
            continue
        numero = trouve.group(2).lstrip("0")
        if numero not in textes:
            continue
        par_texte[numero] += 1
        retenus.append([sorted(textes[numero])[0], numero, trouve.group(1)]
                       + [champs[nom] for nom in COLONNES])
        meta.append(marques)

    retenus, fondus = dedoublonner(retenus, meta)

    with sortie.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(["dossier", "texte", "stade"] + list(COLONNES))
        ecrivain.writerows(retenus)

    sorts = collections.Counter(l[3 + list(COLONNES).index("sort")] or "(vide)"
                                for l in retenus)
    print(f"lignes lues        : {lues}")
    print(f"amendements retenus : {len(retenus)} sur {len(par_texte)} textes")
    print(f"  copies B / BTC fondues : {fondus}")
    for numero, n in par_texte.most_common(10):
        print(f"   texte {numero:>6s} : {n}")
    print("\npar sort :")
    for sort, n in sorts.most_common(6):
        print(f"   {sort:24s} {n}")


if __name__ == "__main__":
    main()
