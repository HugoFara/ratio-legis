#!/usr/bin/env python3
"""Prépare la base à être lue : index de restitution, puis ANALYZE.

Une interrogation du graphe coûtait de 0,6 à 4,2 secondes par article, ce qui
condamnait d'avance l'API de la phase 4. La cause n'était ni le volume — 240 Mo —
ni la forme des requêtes.

**Le planificateur travaillait à l'aveugle.** Sans statistiques, SQLite suppose
que toutes les tables se valent, et il choisissait de balayer les 6 131 versions
d'articles — chacune portant le texte intégral — *pour chaque* acte de l'Union,
deux fois par requête. Environ 1,7 million de lignes visitées pour répondre sur
un article.

La mesure sépare les deux remèdes, parce qu'ils ne pèsent pas pareil :

    base telle quelle          1,70 s pour quatre articles
    index seul                 0,41 s      (× 4)
    ANALYZE seul               0,047 s     (× 36)
    les deux                   0,037 s     (× 46)

C'est donc `ANALYZE` qui fait l'essentiel : le planificateur n'avait pas besoin
d'un chemin de plus, il avait besoin de savoir ce qu'il avait. L'index sur
`article (numero)` reste utile — la restitution part toujours du numéro, et
`article` n'était indexé que par le couple (code, numero), préfixe inutilisable
pour ce seul champ.

Après quoi le balayage des 2 139 articles en vigueur prend 28 secondes, soit une
médiane de 8 ms et un maximum de 154 ms.

Usage :
    index_de_lecture.py <base.sqlite> [schema/008-index-de-lecture.sql]
"""

from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "008-index-de-lecture.sql"


def main() -> None:
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    schema = Path(sys.argv[2]) if len(sys.argv) == 3 else SCHEMA

    base.executescript(schema.read_text(encoding="utf-8"))
    depart = time.perf_counter()
    base.execute("ANALYZE")
    base.commit()

    index = [n for (n,) in base.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL")]
    print(f"index de lecture en place : {len(index)}")
    print(f"statistiques du planificateur recalculées en {time.perf_counter()-depart:.1f} s")


if __name__ == "__main__":
    main()
