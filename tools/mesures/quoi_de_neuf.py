#!/usr/bin/env python3
"""Dit ce qui a changé depuis la veille, et l'inscrit au journal.

Une reconstruction quotidienne muette ne vaut rien : elle coûte des minutes et ne
rend aucun compte. Ce script compare l'état du fonds à celui de la course
précédente et énonce la différence — articles entrés en vigueur, articles sortis,
verdicts qui basculent.

C'est le seul endroit du projet où l'on regarde le graphe **dans le temps**. Un
article qui passe de « raison non documentée » à « un passage l'explique » n'est
pas un détail d'exécution : c'est le produit qui progresse, ou une source qui
s'ouvre. L'inverse est un signal d'alerte.

L'état précédent est versionné (`data/mesures/etat-du-fonds.json`). Son historique
git est, littéralement, la chronique du corpus.

Usage :
    quoi_de_neuf.py <base.sqlite> [journal.tsv] [course]
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("data/mesures/etat-du-fonds.json")
TABLES = ["article", "version_article", "segment", "texte_normatif", "document",
          "amendement", "motive", "resulte_de", "porte_sur", "repris_de",
          "renumerote_de", "acte_ue", "considerant", "verdict"]


def releve(base: sqlite3.Connection) -> dict:
    return {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "compte": {t: base.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                   for t in TABLES},
        "verdicts": {n: v for n, v in base.execute(
            "SELECT a.numero, d.verdict FROM verdict d "
            "JOIN article a ON a.id = d.article_id")},
    }


def comparer(avant: dict, apres: dict) -> list[tuple[str, str]]:
    lignes = []
    va, vb = avant.get("verdicts", {}), apres["verdicts"]
    entres = sorted(set(vb) - set(va))
    sortis = sorted(set(va) - set(vb))
    bascules = sorted(n for n in set(va) & set(vb) if va[n] != vb[n])
    if entres:
        lignes.append(("articles_entres", f"{len(entres)} : "
                                          + ", ".join(entres[:8])))
    if sortis:
        lignes.append(("articles_sortis", f"{len(sortis)} : "
                                          + ", ".join(sortis[:8])))
    for numero in bascules[:20]:
        lignes.append(("verdict_change", f"{numero} : {va[numero]} → {vb[numero]}"))
    if len(bascules) > 20:
        lignes.append(("verdict_change", f"… et {len(bascules) - 20} autres"))
    for table, valeur in apres["compte"].items():
        ancien = avant.get("compte", {}).get(table)
        if ancien is not None and ancien != valeur:
            lignes.append((f"compte_{table}", f"{ancien} → {valeur} "
                                              f"({valeur - ancien:+d})"))
    return lignes


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    journal = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    course = sys.argv[3] if len(sys.argv) > 3 else datetime.now(
        timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    avant = json.loads(ETAT.read_text(encoding="utf-8")) if ETAT.exists() else {}
    apres = releve(base)
    base.close()
    differences = comparer(avant, apres)

    ETAT.parent.mkdir(parents=True, exist_ok=True)
    ETAT.write_text(json.dumps(apres, ensure_ascii=False, indent=1,
                               sort_keys=True) + "\n", encoding="utf-8")

    if not avant:
        print("premier relevé : aucune comparaison possible")
    elif not differences:
        print(f"aucun changement depuis {avant['date']}")
    else:
        print(f"changements depuis {avant['date']} :")
        for quoi, detail in differences:
            print(f"  {quoi:22} {detail}")

    if journal:
        with journal.open("a", encoding="utf-8") as sortie:
            for quoi, detail in differences or [("aucun_changement", "")]:
                sortie.write(f"{course}\t{quoi}\tINFO\t0\t{detail}\n")
    print(f"état écrit : {ETAT}")


if __name__ == "__main__":
    main()
