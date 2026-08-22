#!/usr/bin/env python3
"""Phase 0 — rattachement amendement → article du code, sur les jeux Améli du Sénat.

Mesure le rendement et la fiabilité des deux méthodes comparées dans
`docs/02-golden-set.md` § 4.

Les CSV Améli sont en latin-1, séparés par tabulation, précédés d'une ligne
parasite `sep=`, et leurs champs longs contiennent du HTML échappé.

    https://www.senat.fr/amendements/{session}/{texte}/jeu_complet_{session}_{texte}.csv

Usage : amendements_senat.py <fichier.csv> [<fichier.csv> ...]
"""

from __future__ import annotations

import csv
import html
import io
import re
import sys
from collections import defaultdict
from pathlib import Path

ARTICLE = r"L\.?\s?\d{3}-\d{1,3}(?:-\d{1,3})?"

# Formules par lesquelles un amendement désigne l'article qu'il modifie. Une simple
# occurrence d'un numéro d'article ne suffit pas : elle confond la cible avec les
# renvois. Mesuré à ~90 % de faux rattachements.
FORMULES = [
    re.compile(rf"article\s+({ARTICLE})\s+(?:du code de la consommation\s+)?est\s+(?:ainsi\s+)?"
               r"(?:modifié|rédigé|remplacé|abrogé|complété|rétabli)", re.I),
    re.compile(rf"alin[ée]as?\s+de\s+l[’']article\s+({ARTICLE})\s+(?:est|sont)\s+(?:ainsi\s+)?"
               r"(?:modifié|rédigé|remplacé|abrogé|complété|supprimé)", re.I),
    re.compile(rf"(?:Après|Avant)\s+l[’']article\s+({ARTICLE})\s*,\s*il\s+est\s+ins[ée]r[ée]", re.I),
    re.compile(rf"[ÀA]\s+l[’']article\s+({ARTICLE})\s*,\s*les\s+mots", re.I),
]


def texte_brut(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", html.unescape(fragment))).strip()


def lire(chemin: Path) -> list[dict]:
    brut = chemin.read_bytes().decode("latin-1")
    corps = "\n".join(brut.split("\n")[1:])  # ligne « sep= »
    lignes = csv.DictReader(io.StringIO(corps), delimiter="\t")
    return [{(k or "").strip(): (v or "") for k, v in ligne.items()} for ligne in lignes]


def cibles(dispositif: str) -> set[str]:
    texte = texte_brut(dispositif)
    trouve = set()
    for formule in FORMULES:
        for m in formule.finditer(texte):
            trouve.add("L" + re.sub(r"^L\.?\s?", "", m.group(1)).strip())
    return trouve


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    amendements = [a for chemin in sys.argv[1:] for a in lire(Path(chemin))]
    adoptes = [a for a in amendements if a.get("Sort") == "Adopté"]

    naif = {re.sub(r"^L\.?\s?", "L", m)
            for a in adoptes for m in re.findall(ARTICLE, texte_brut(a["Dispositif"]))}
    index: dict[str, list] = defaultdict(list)
    for a in adoptes:
        for c in cibles(a["Dispositif"]):
            index[c].append(a.get("Numéro"))

    print(f"amendements déposés           : {len(amendements)}")
    print(f"  adoptés                     : {len(adoptes)}")
    print(f"  citant un numéro d'article  : {len(naif)} articles (rattachement non fiable)")
    print(f"  avec cible modificative     : {len(index)} articles, "
          f"{sum(1 for a in adoptes if cibles(a['Dispositif']))} amendements")


if __name__ == "__main__":
    main()
