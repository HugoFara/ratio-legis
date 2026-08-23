#!/usr/bin/env python3
"""Télécharge les textes en discussion relevés par `plan_textes.py`.

Les deux chambres servent ces pages sans authentification, mais pas dans le même
encodage : l'Assemblée publie en latin-1, le Sénat en UTF-8. Le fichier est stocké
tel qu'il est servi, sans transcodage — c'est au chargement de le lire, en suivant
le `charset` déclaré dans la page.

Un `User-Agent` descriptif est posé : plusieurs services publics refusent par 403
les requêtes qui n'en portent aucun, et `Python-urllib` n'en pose pas (`docs/15`
§ 4). Il annonce le projet, il n'imite pas un navigateur.

Usage :
    telecharger_textes.py <plan-textes.tsv> <corpus/textes/>
"""

from __future__ import annotations

import csv
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AGENT = "ratio-legis/1.0 (graphe de provenance normative)"
PAUSE = 0.4
MINIMUM = 3000        # une page plus courte que cela est une erreur, pas un texte
# L'Assemblée sert désormais ses textes récents par une application JavaScript :
# 200, 77 ko, et pas une ligne du texte. Mais la coquille **déclare** où est le
# document, dans un lien vers sa version PDF. On suit cette déclaration ; on ne
# devine pas l'URL, qui diffère selon le stade (`_texte-adopte-commission`,
# `_texte-adopte-seance`) et ne se déduit pas de celle de la page.
LIEN_PDF = re.compile(rb'href="([^"]+\.pdf)"')


def obtenir(url: str) -> bytes | None:
    try:
        requete = urllib.request.Request(url, headers={"User-Agent": AGENT})
        with urllib.request.urlopen(requete, timeout=180) as reponse:
            return reponse.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return None


def exploitable(corps: bytes | None) -> bool:
    """Le contenu décide, pas le code de retour : une coquille répond 200."""
    return corps is not None and len(corps) >= MINIMUM and (
        corps.startswith(b"%PDF") or b"rticle" in corps)


def telecharger(url: str, cible: Path) -> bool:
    corps = obtenir(url)
    if not exploitable(corps):
        if corps is None:
            return False
        trouve = LIEN_PDF.search(corps)
        if not trouve:
            return False
        chemin = trouve.group(1).decode("utf-8", "replace")
        if chemin.startswith("/"):
            chemin = re.sub(r"(https?://[^/]+).*", r"\1", url) + chemin
        corps = obtenir(chemin)
        if not exploitable(corps):
            return False
    cible.write_bytes(corps)
    return True


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    plan, corpus = (Path(a) for a in sys.argv[1:])
    corpus.mkdir(parents=True, exist_ok=True)

    repris = telecharges = 0
    echecs = []
    for ligne in csv.DictReader(plan.open(encoding="utf-8"), delimiter="\t"):
        cible = corpus / f"{ligne['dossier']}__{ligne['fichier']}"
        if cible.exists() and cible.stat().st_size >= MINIMUM:
            repris += 1
            continue
        if telecharger(ligne["url"], cible):
            telecharges += 1
        else:
            echecs.append(ligne["url"])
        time.sleep(PAUSE)

    print(f"textes au plan   : {repris + telecharges + len(echecs)}")
    print(f"  déjà présents  : {repris}")
    print(f"  téléchargés    : {telecharges}")
    print(f"  en échec       : {len(echecs)}")
    for url in echecs[:10]:
        print(f"    {url}")


if __name__ == "__main__":
    main()
