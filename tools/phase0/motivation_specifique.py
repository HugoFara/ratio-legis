#!/usr/bin/env python3
"""Phase 0 — le document de motivation atteint nomme-t-il l'article ?

Répond à la question que « chaîne aboutissant à un dossier » ne pose pas :
l'exposé des motifs ou l'étude d'impact du texte d'origine contiennent-ils une
mention de *cet* article. Produit les chiffres du § 3 de la note de cadrage.

C'est une borne. Un passage peut motiver une disposition sans la nommer, mais un
tel passage n'est pas ancrable automatiquement — et le § 4.3 de la feuille de
route interdit toute phrase sans citation résoluble.

Prérequis : études d'impact converties en texte, une par dossier :
    pdftotext -layout <dossier>.pdf <dossier>.txt

Usage : motivation_specifique.py <perimetre.csv> <dole_texte.json> <repertoire_ei>
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path


def motif_article(numero: str) -> re.Pattern | None:
    """Motif tolérant aux variantes typographiques : « L. 121-17 », « L.121-17 »…

    Le garde-fou final évite que « L. 121-17 » attrape « L. 121-17-1 ».
    """
    m = re.match(r"([LRD])(\d+)-(\d+)(?:-(\d+))?", (numero or "").replace(" ", ""))
    if not m:
        return None
    partie, livre, article, sous = m.groups()
    queue = rf"\s*-\s*{sous}" if sous else r"(?!\s*-\s*\d)"
    return re.compile(rf"{partie}\.?\s*{livre}\s*-\s*{article}" + queue)


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    perimetre, index_dole, repertoire_ei = (Path(a) for a in sys.argv[1:])

    articles = list(csv.DictReader(perimetre.open(encoding="utf-8")))
    dossiers = {v["dole"]: v for v in json.loads(index_dole.read_text(encoding="utf-8")).values()}
    etudes = {f.stem: f.read_text(encoding="utf-8", errors="replace")
              for f in repertoire_ei.glob("*.txt")}

    eligibles = [a for a in articles if a["eligible_resulte_de"] == "1"]
    compte = Counter()
    complets = Counter()

    for a in eligibles:
        dossier = a["id_dole_origine"]
        motifs = [m for m in (motif_article(n) for n in
                              (a["num_article"], a["article_predecesseur"])) if m]
        expose = dossiers.get(dossier, {}).get("expose", "")
        etude = etudes.get(dossier, "")

        dans_expose = bool(expose) and any(m.search(expose) for m in motifs)
        dans_etude = bool(etude) and any(m.search(etude) for m in motifs)

        compte["expose_nomme"] += dans_expose
        compte["etude_nomme"] += dans_etude
        if expose and etude:
            complets["total"] += 1
            complets["nomme"] += dans_expose or dans_etude

    n = len(eligibles)
    print(f"articles éligibles                    : {n}")
    print(f"  nommés dans l'exposé des motifs     : {compte['expose_nomme']} ({100 * compte['expose_nomme'] / n:.1f} %)")
    print(f"  nommés dans l'étude d'impact        : {compte['etude_nomme']} ({100 * compte['etude_nomme'] / n:.1f} %)")
    if complets["total"]:
        print(f"  documentation complète            : {complets['total']}")
        print(f"    dont nommés dans l'un ou l'autre : {complets['nomme']} "
              f"({100 * complets['nomme'] / complets['total']:.1f} %)")


if __name__ == "__main__":
    main()
