#!/usr/bin/env python3
"""Télécharge les études d'impact et avis du Conseil d'État, et en extrait le texte.

Ce sont les seuls documents du corpus qui n'existent qu'en PDF. Ils portent une
couche de texte — aucune OCR n'est nécessaire, vérifié sur l'étude d'impact du
projet de loi consommation : 195 pages, 554 000 caractères, 466 numéros d'articles
de code cités.

Le PDF est conservé à côté du texte extrait : c'est lui la source, et le § 5.2
veut qu'elle reste telle quelle. Le texte, lui, est écrit dans le corpus des
rapports, d'où le chargement des documents le reprend avec les autres.

Usage :
    telecharger_impacts.py <plan-impacts.tsv> <corpus/impacts/> <corpus/rapports/>
"""

from __future__ import annotations

import csv
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import fitz          # pymupdf

PAUSE = 0.5
MINIMUM = 1000       # un PDF plus court que cela n'est pas un document
# Légifrance refuse par 403 les requêtes sans `User-Agent`, et `Python-urllib`
# n'en pose aucun : les 40 documents avaient été comptés « en échec » alors que
# `curl` les servait sans difficulté depuis la même machine. L'agent annonce le
# projet plutôt que d'imiter un navigateur — un agent descriptif est accepté.
AGENT = "ratio-legis/1.0 (graphe de provenance normative)"
NOM = {"etude_impact": "etude-impact", "avis_conseil_etat": "avis-ce"}


def telecharger(url: str, cible: Path) -> bool:
    try:
        requete = urllib.request.Request(
            url, headers={"User-Agent": AGENT, "Accept": "application/pdf"})
        with urllib.request.urlopen(requete, timeout=300) as reponse:
            corps = reponse.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return False
    if len(corps) < MINIMUM or not corps.startswith(b"%PDF"):
        return False
    cible.write_bytes(corps)
    return True


def en_texte(pdf: Path) -> str:
    """Texte du PDF, pages concaténées dans l'ordre.

    Aucun marqueur de page n'est inséré : il deviendrait du contenu, et fausserait
    les offsets de toute citation ultérieure.
    """
    with fitz.open(pdf) as document:
        pages = [page.get_text() for page in document]
    brut = "\n".join(pages)
    return re.sub(r"\n{3,}", "\n\n",
                  "\n".join(l.rstrip() for l in brut.split("\n"))).strip()


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    plan, depot, corpus = (Path(a) for a in sys.argv[1:])
    depot.mkdir(parents=True, exist_ok=True)
    corpus.mkdir(parents=True, exist_ok=True)

    repris = telecharges = 0
    echecs, vides = [], []
    for ligne in csv.DictReader(plan.open(encoding="utf-8"), delimiter="\t"):
        base = f"{ligne['dossier']}__{NOM[ligne['type']]}-{ligne['rang']}"
        pdf = depot / f"{base}.pdf"
        if pdf.exists() and pdf.stat().st_size >= MINIMUM:
            repris += 1
        elif telecharger(ligne["url"], pdf):
            telecharges += 1
            time.sleep(PAUSE)
        else:
            echecs.append(ligne["url"].rsplit("/", 1)[-1])
            continue
        texte = en_texte(pdf)
        if len(texte) < 500:
            vides.append(base)      # PDF image : il faudrait une OCR, hors périmètre
            continue
        (corpus / f"{base}.txt").write_text(texte + "\n", encoding="utf-8")

    print(f"documents au plan     : {repris + telecharges + len(echecs)}")
    print(f"  déjà présents       : {repris}")
    print(f"  téléchargés         : {telecharges}")
    print(f"  en échec            : {len(echecs)}"
          + (f" — {', '.join(echecs[:5])}" if echecs else ""))
    print(f"  sans couche de texte : {len(vides)}"
          + (f" — {', '.join(vides[:5])}" if vides else ""))


if __name__ == "__main__":
    main()
