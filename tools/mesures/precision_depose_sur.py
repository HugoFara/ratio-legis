#!/usr/bin/env python3
"""Tire un échantillon reproductible d'arêtes `depose_sur`, et en fait le bilan.

`depose_sur` compose deux liens : l'amendement fut déposé sur l'article X du texte
T, et l'article X de T réécrit l'article A du code. Elle n'a pas de preuve propre —
sa preuve est celle de `porte_sur`, plus la subdivision que l'amendement déclare —
et c'est justement pourquoi elle demande d'être mesurée à part : **une chaîne de
deux liens ne vaut pas son maillon le plus fort** (`docs/31` § 4).

Ce que la fiche porte, et qui permet de trancher :

- `subdivision` : ce que l'amendement déclare amender, tel qu'il l'écrit.
- `cibles_de_l_article` : combien d'articles du code l'article du texte réécrit.
  Au-delà de 1, l'arête ne devrait pas exister — la définition de `depose_sur` le
  dit —, et une arête qui existe quand même signale une liste de cibles
  incomplète, non une attribution établie.
- `vise` : l'amendement déclare-t-il lui-même modifier cet article, ou l'un de ses
  voisins de renumérotation ? Ce signal vient du **dispositif**, l'arête vient de
  la **composition** : ils peuvent se contredire, et c'est ce qui les rend
  informatifs l'un pour l'autre.
- `fenetre` : le passage du texte en discussion qui a fondé la cible.
- `dispositif` et `article_du_fonds` : de quoi lire ce que l'amendement fait, et
  ce que l'article dit.

Ces colonnes **n'établissent rien**, elles orientent l'examen. La colonne
`verdict` reste vide et se remplit à la main — `juste`, `faux` ou `douteux`.

**Un tirage reproductible, pas aléatoire** : clef de tri SHA-256 du couple
(amendement, article), comme pour `resulte_de` et `porte_sur`. `--sauf` écarte les
arêtes d'une fiche déjà examinée.

Usage :
    precision_depose_sur.py <base.sqlite> <fiche.tsv> [effectif] [--sauf <fiche.tsv>]
    precision_depose_sur.py --bilan <fiche.tsv>
"""

from __future__ import annotations

import csv
import hashlib
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precision_porte_sur import coupe, wilson      # noqa: E402

EFFECTIF = 15
COLONNES = ["verdict", "cle", "chambre", "amendement", "sort", "auteur",
            "article", "cibles_de_l_article", "vise", "texte", "article_du_texte",
            "subdivision", "fenetre", "dispositif", "article_du_fonds", "url"]


def echantillon(base: sqlite3.Connection, sauf: set[tuple[str, str]],
                effectif: int) -> list[dict]:
    base.executescript("""
        CREATE TEMP TABLE cibles AS
            SELECT texte_id, lower(article_du_texte) AS art,
                   count(DISTINCT article_id) AS combien
            FROM porte_sur WHERE portee = 'interne' GROUP BY 1, 2;
        CREATE TEMP TABLE chaine AS
            WITH RECURSIVE d(origine, courant) AS (
                SELECT id, id FROM article
                UNION SELECT d.origine, r.article_id
                  FROM renumerote_de r JOIN d ON r.ancien_id = d.courant
                UNION SELECT d.origine, r.ancien_id
                  FROM renumerote_de r JOIN d ON r.article_id = d.courant)
            SELECT origine, courant FROM d;""")
    lignes = []
    for (amendement, numero, chambre, sort, auteur, article, texte_id,
         article_du_texte, subdivision, dispositif, url, combien, texte_article,
         fenetre) in base.execute("""
            SELECT d.amendement_id, am.numero, am.chambre, am.sort, ac.nom,
                   a.numero, d.texte_id, d.article_du_texte, am.subdivision,
                   am.dispositif, am.url, c.combien, v.texte, pr.fenetre
            FROM depose_sur d
            JOIN amendement am ON am.id = d.amendement_id
            LEFT JOIN acteur ac ON ac.id = am.auteur_id
            JOIN article a ON a.id = d.article_id
            LEFT JOIN cibles c ON c.texte_id = d.texte_id
                              AND c.art = lower(d.article_du_texte)
            LEFT JOIN porte_sur p ON p.texte_id = d.texte_id
                              AND lower(p.article_du_texte) = lower(d.article_du_texte)
                              AND p.article_id = d.article_id
            LEFT JOIN preuve pr ON pr.id = p.preuve_id
            LEFT JOIN (SELECT article_id, min(date_debut) AS d0, texte FROM version_article
                       GROUP BY article_id) v ON v.article_id = d.article_id"""):
        accord = base.execute(
            "SELECT count(*), sum(v.article_id = ?), "
            "       sum(EXISTS(SELECT 1 FROM chaine c WHERE c.courant = v.article_id "
            "                  AND c.origine = ?)) "
            "FROM vise v WHERE v.amendement_id = ?",
            (article_id_de(base, article), article_id_de(base, article), amendement)
        ).fetchone()
        if not accord[0]:
            lu = "sans visée"
        elif accord[1]:
            lu = "oui"
        elif accord[2]:
            lu = "oui, par renumérotation"
        else:
            lu = "non"
        lignes.append({
            "verdict": "", "cle": hashlib.sha256(
                f"{amendement}|{article}".encode()).hexdigest()[:16],
            "chambre": chambre, "amendement": numero, "sort": sort or "",
            "auteur": auteur or "", "article": article,
            "cibles_de_l_article": str(combien or 0), "vise": lu,
            "texte": texte_id, "article_du_texte": article_du_texte,
            "subdivision": coupe(subdivision, 90), "fenetre": coupe(fenetre, 220),
            "dispositif": coupe(dispositif, 420),
            "article_du_fonds": coupe(texte_article, 320), "url": url or "",
        })
    lignes = [l for l in lignes if (l["amendement"], l["article"]) not in sauf]
    lignes.sort(key=lambda l: l["cle"])
    return lignes[:effectif]


def article_id_de(base: sqlite3.Connection, numero: str) -> int:
    return base.execute("SELECT id FROM article WHERE numero = ?",
                        (numero,)).fetchone()[0]


def bilan(fiche: Path) -> None:
    lignes = list(csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t"))
    examinees = [l for l in lignes if l["verdict"]]
    justes = [l for l in examinees if l["verdict"] == "juste"]
    doutes = [l for l in examinees if l["verdict"] == "douteux"]
    print(f"arêtes tirées      : {len(lignes)}")
    print(f"arêtes examinées   : {len(examinees)}")
    print(f"  justes           : {len(justes)}")
    print(f"  douteuses        : {len(doutes)}")
    print(f"  fausses          : {len(examinees) - len(justes) - len(doutes)}")
    if not examinees:
        return
    # Le douteux compte comme un échec : § 5.3, la précision prime le rappel.
    print(f"précision ponctuelle : {len(justes) / len(examinees):.3f}")
    print(f"borne de Wilson 95 % : {wilson(len(justes), len(examinees)):.4f}")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--bilan":
        return bilan(Path(sys.argv[2]))
    arguments, sauf = sys.argv[1:], set()
    if "--sauf" in arguments:
        place = arguments.index("--sauf")
        deja = Path(arguments[place + 1])
        sauf = {(l["amendement"], l["article"]) for l in
                csv.DictReader(deja.open(encoding="utf-8"), delimiter="\t")}
        arguments = arguments[:place] + arguments[place + 2:]
    if len(arguments) not in (2, 3):
        sys.exit(__doc__)
    chemin_base, fiche = Path(arguments[0]), Path(arguments[1])
    effectif = int(arguments[2]) if len(arguments) == 3 else EFFECTIF
    base = sqlite3.connect(chemin_base)
    lignes = echantillon(base, sauf, effectif)
    with fiche.open("w", encoding="utf-8", newline="") as sortie:
        graveur = csv.DictWriter(sortie, COLONNES, delimiter="\t",
                                 lineterminator="\n")
        graveur.writeheader()
        graveur.writerows(lignes)
    print(f"{len(lignes)} arêtes tirées → {fiche}")
    base.close()


if __name__ == "__main__":
    main()
