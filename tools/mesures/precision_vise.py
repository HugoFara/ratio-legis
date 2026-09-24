#!/usr/bin/env python3
"""Tire un échantillon reproductible d'arêtes `vise`, et en fait le bilan.

`vise` lit le **dispositif** de l'amendement : « L'article L. 121-36 est ainsi
rédigé », « Après le mot…, la fin de l'article L. 223-1 est ainsi rédigée ».
Elle n'avait jamais été mesurée à part — sa confiance était celle de
`resulte_de` (`docs/09`) —, et deux corrections du 19 septembre 2026 ont
changé sa population : l'ancre d'insertion (« après l'article L. 312-9, il est
inséré… ») n'est plus une cible, et les tirets insécables des sites des
chambres sont lus, ce qui a fait passer l'arête de 318 à 1 019 (`docs/43`).
Une arête qui triple se mesure avant de se servir.

Ce que la fiche porte : le numéro visé et la formule relevée, le dispositif
entier, l'article du code (numéro, date de première version, texte) et l'URL.
La colonne `verdict` reste vide — `juste`, `faux`, `douteux`. Est juste une
arête dont le dispositif **modifie, crée, abroge ou réécrit** cet article-là
du code de la consommation ; est fausse celle qui le cite sans le toucher, le
nomme comme ancre, ou vise un homonyme d'un autre code.

Tirage reproductible, clef SHA-256 du couple (amendement, article) ; `--sauf`
écarte les arêtes d'une fiche déjà jugée.

`--methode inferee` restreint le tirage aux arêtes posées par le contenu de
l'article écrit (`docs/50`), qui ont leur constante à elles.

Usage :
    precision_vise.py <base.sqlite> <fiche.tsv> [effectif] [--sauf <fiche.tsv>]
                      [--methode declaree|inferee]
    precision_vise.py --bilan <fiche.tsv>
"""

from __future__ import annotations

import csv
import hashlib
import math
import re
import sqlite3
import sys
from pathlib import Path

EFFECTIF = 20
COLONNES = ["verdict", "cle", "chambre", "amendement", "sort", "auteur", "article",
            "formule", "dossier", "subdivision", "dispositif", "article_du_fonds", "url"]


def coupe(texte: str | None, longueur: int) -> str:
    texte = re.sub(r"\s+", " ", texte or "").strip()
    return texte if len(texte) <= longueur else texte[:longueur] + " […]"


def wilson(succes: int, total: int, z: float = 1.96) -> float:
    if total == 0:
        return 0.0
    p = succes / total
    denominateur = 1 + z * z / total
    centre = p + z * z / (2 * total)
    ecart = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return (centre - ecart) / denominateur


def echantillon(base: sqlite3.Connection, sauf: set[tuple[str, str]],
                effectif: int, methode: str | None = None) -> list[dict]:
    lignes = []
    for (amendement, numero, chambre, sort, auteur, article, formule, dossier,
         subdivision, dispositif, url, d0, texte_article) in base.execute("""
            SELECT v.amendement_id, am.numero, am.chambre, am.sort, ac.nom, a.numero,
                   v.formule, am.dossier_id, am.subdivision, am.dispositif, am.url,
                   (SELECT min(date_debut) FROM version_article WHERE article_id = a.id),
                   (SELECT texte FROM version_article WHERE article_id = a.id
                    ORDER BY date_debut LIMIT 1)
            FROM vise v
            JOIN amendement am ON am.id = v.amendement_id
            LEFT JOIN acteur ac ON ac.id = am.auteur_id
            JOIN article a ON a.id = v.article_id
            WHERE ? IS NULL OR v.methode = ?""", (methode, methode)):
        if (str(amendement), article) in sauf:
            continue
        lignes.append({
            "verdict": "", "cle": hashlib.sha256(
                f"{amendement}|{article}".encode()).hexdigest()[:16],
            "chambre": chambre, "amendement": str(amendement), "sort": sort or "",
            "auteur": auteur or "", "article": article, "formule": formule,
            "dossier": dossier, "subdivision": coupe(subdivision, 90),
            "dispositif": coupe(dispositif, 600),
            "article_du_fonds": f"{article} ({d0}) " + coupe(texte_article, 320),
            "url": url or ""})
    lignes.sort(key=lambda l: l["cle"])
    return lignes[:effectif]


def bilan(fiche: Path) -> None:
    lignes = list(csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t"))
    examinees = [l for l in lignes if l["verdict"]]
    justes = [l for l in examinees if l["verdict"] == "juste"]
    doutes = [l for l in examinees if l["verdict"] == "douteux"]
    print(f"arêtes examinées   : {len(examinees)}")
    print(f"  justes           : {len(justes)}")
    print(f"  douteuses        : {len(doutes)}")
    print(f"  fausses          : {len(examinees) - len(justes) - len(doutes)}")
    if examinees:
        print(f"précision ponctuelle : {len(justes) / len(examinees):.3f}")
        print(f"borne de Wilson 95 % : {wilson(len(justes), len(examinees)):.4f}")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--bilan":
        return bilan(Path(sys.argv[2]))
    arguments, sauf, methode = sys.argv[1:], set(), None
    if "--methode" in arguments:
        place = arguments.index("--methode")
        methode = arguments[place + 1]
        arguments = arguments[:place] + arguments[place + 2:]
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
    lignes = echantillon(sqlite3.connect(chemin_base), sauf, effectif, methode)
    with fiche.open("w", encoding="utf-8", newline="") as sortie:
        graveur = csv.DictWriter(sortie, COLONNES, delimiter="\t", lineterminator="\n")
        graveur.writeheader()
        graveur.writerows(lignes)
    print(f"{len(lignes)} arêtes tirées → {fiche}")


if __name__ == "__main__":
    main()
