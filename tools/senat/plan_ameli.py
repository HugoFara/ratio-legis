#!/usr/bin/env python3
"""Dérive le plan de récupération des jeux d'amendements du Sénat depuis DOLE.

Ce plan n'était pas versionné : il vivait dans un répertoire temporaire, et sa
perte a rendu tout le corpus sénatorial irrécupérable jusqu'à ce que ce script
existe. Il est reconstruit à partir du seul miroir DILA, donc sans dépendre
d'aucune donnée dérivée.

La clef d'une URL Améli est le couple (session parlementaire, numéro de texte).
DOLE ne l'expose pas directement, mais il publie pour chaque dossier des liens
« petite loi » qui le portent :

    http://www.senat.fr/petite-loi-ameli/2013-2014/283.html
                                         ^^^^^^^^^ ^^^
    https://www.senat.fr/amendements/2013-2014/283/jeu_complet_2013-2014_283.csv

Usage :
    plan_ameli.py <miroir_dila/> <dossiers-du-perimetre.tsv> <sortie.tsv>
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dila"))
from dossiers_du_perimetre import lire  # noqa: E402
from fonds import deployer  # noqa: E402

PETITE_LOI = re.compile(r"petite-loi-ameli/(\d{4}-\d{4})/(\d+)\.html")
# Deuxième forme, plus fréquente : les liens vers le texte lui-même. Le préfixe
# porte l'année de session sur deux chiffres — `pjl12-810` est le texte 810 de la
# session 2012-2013. S'en tenir à la première forme laissait 68 dossiers sur 93
# sans plan, alors que le corpus d'origine en couvrait 36.
TEXTE = re.compile(r"senat\.fr/(?:leg|rap|dossier-legislatif)/[a-z]*?(\d{2})-(\d+)")


def couples_du_texte(texte: str) -> set[tuple[str, str]]:
    trouves = {(session, numero) for session, numero in PETITE_LOI.findall(texte)}
    for annee, numero in TEXTE.findall(texte):
        debut = 2000 + int(annee)
        trouves.add((f"{debut}-{debut + 1}", numero))
    return trouves


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    miroir, liste, sortie = (Path(a) for a in sys.argv[1:])

    dossiers = sorted({l["id_dole"] for l in lire(liste)})
    with tempfile.TemporaryDirectory() as tmp:
        # Une seule passe sur l'archive : elle fait plusieurs centaines de Mo et
        # la parcourir une fois par dossier coûterait des heures.
        deployer(miroir, "dole", Path(tmp), [f"*{d}.xml" for d in dossiers])
        lignes, sans_ameli = [], []
        for dossier in dossiers:
            trouves = list(Path(tmp).rglob(f"{dossier}.xml"))
            if not trouves:
                sans_ameli.append(dossier)
                continue
            texte = trouves[0].read_text(encoding="utf-8", errors="replace")
            couples = sorted(couples_du_texte(texte))
            if not couples:
                sans_ameli.append(dossier)
            lignes += [(dossier, session, numero) for session, numero in couples]

    sortie.write_text("".join(f"{d}\t{s}\t{n}\n" for d, s, n in lignes), encoding="utf-8")
    print(f"dossiers du périmètre       : {len(dossiers)}")
    print(f"couples (session, texte)    : {len(lignes)}")
    print(f"dossiers sans lien Améli    : {len(sans_ameli)}")
    print(f"écrit : {sortie}")


if __name__ == "__main__":
    main()
