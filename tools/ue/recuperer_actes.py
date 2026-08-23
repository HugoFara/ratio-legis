#!/usr/bin/env python3
"""Miroite le texte français des actes de l'Union cités par le code.

La huitième tranche a rattaché 284 actes de l'Union aux articles du code, mais
seulement par leur identifiant : le graphe savait *qu'*une directive commande un
article, jamais *ce qu'elle dit ni pourquoi*. Or le « pourquoi » du droit de
l'Union est écrit, numéroté et publié — ce sont les considérants, l'exposé des
motifs que le droit français n'a pas.

EUR-Lex publie chaque acte en HTML structuré selon ELI, et cette structure est
**déclarée**, non devinée : chaque considérant porte `id="rct_N"`, chaque article
`id="art_N"`, et N est le numéro imprimé. Rien n'est à segmenter à la main.

Le brut est stocké tel quel (§ 5.2), avec un manifeste horodaté portant taille et
SHA-256 par fichier — même convention que le miroir DILA, dont seuls les
manifestes sont versionnés.

Usage :
    recuperer_actes.py <base.sqlite> <data/raw/eurlex/>
"""

from __future__ import annotations

import hashlib
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:{}"
PAUSE = 0.5          # service public et gratuit : on ne le martèle pas
ESSAIS = 4
# Un 200 n'est pas une preuve qu'on tient le document. À cadence soutenue,
# EUR-Lex rend une page de défi anti-robot d'AWS — 2 035 octets, code 200 — et
# parfois la coquille JavaScript de son interface, 82 ko sans une ligne de
# l'acte. La première version les avait stockées comme des actes : 37 fichiers
# sur 284, dont le règlement 1008/2008 qui avait pourtant servi à valider la
# méthode. Le contrôle porte donc sur le contenu, jamais sur le code de retour
# ni sur la taille.
DEFI = b"awsWafCookieDomainList"
MARQUEURS = (b"consid\xc3\xa9rant", b'id="rct_', b"ADOPT\xc3\x89", b"ARR\xc3\x8aT\xc3\x89")


def acte_reel(corps: bytes) -> bool:
    """Un acte porte forcément soit des considérants, soit sa formule d'adoption."""
    return DEFI not in corps and any(m in corps for m in MARQUEURS)


def recuperer(celex: str) -> bytes | None:
    """Rend le corps de l'acte, ou None après ESSAIS tentatives espacées.

    La pause croît à chaque échec : un défi anti-robot ne se lève pas en
    réessayant tout de suite.
    """
    requete = urllib.request.Request(
        SOURCE.format(celex), headers={"Accept": "text/html"})
    for essai in range(ESSAIS):
        try:
            with urllib.request.urlopen(requete, timeout=120) as reponse:
                corps = reponse.read()
            if acte_reel(corps):
                return corps
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError):
            pass
        time.sleep(2 ** essai * 5)
    return None


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    destination = Path(sys.argv[2])
    destination.mkdir(parents=True, exist_ok=True)

    actes = [c for (c,) in base.execute("SELECT celex FROM acte_ue ORDER BY celex")]
    base.close()
    if not actes:
        sys.exit("aucun acte en base : lancer ingestion/union_europeenne.py")

    horodatage = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifeste = destination / f"manifeste-{horodatage}.tsv"
    lignes, repris, echecs = [], 0, []

    for rang, celex in enumerate(actes, 1):
        fichier = destination / f"{celex}.html"
        if fichier.exists() and acte_reel(fichier.read_bytes()):
            repris += 1
        else:
            corps = recuperer(celex)
            time.sleep(PAUSE)
            if corps is None:
                echecs.append(celex)
                continue
            fichier.write_bytes(corps)
            if rang % 25 == 0:
                print(f"  {rang}/{len(actes)}")
        octets = fichier.read_bytes()
        lignes.append((celex, fichier.name, len(octets),
                       hashlib.sha256(octets).hexdigest(),
                       datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))

    with manifeste.open("w", encoding="utf-8") as flux:
        flux.write("celex\tfichier\toctets\tsha256\trecupere_le\n")
        for ligne in lignes:
            flux.write("\t".join(str(v) for v in ligne) + "\n")

    total = sum(l[2] for l in lignes)
    print(f"actes en base            : {len(actes)}")
    print(f"  déjà présents          : {repris}")
    print(f"  sans réponse d'EUR-Lex : {len(echecs)}"
          + (f" — {', '.join(echecs[:8])}" if echecs else ""))
    print(f"miroir                   : {len(lignes)} fichiers, {total // 1048576} Mo")
    print(f"manifeste                : {manifeste}")


if __name__ == "__main__":
    main()
