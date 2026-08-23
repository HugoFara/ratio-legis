#!/usr/bin/env python3
"""Reprend du miroir JORF l'intitulé complet des textes du périmètre.

LEGI ne porte que la forme courte du titre — « Ordonnance n°2016-301 du 14 mars
2016 ». Or c'est la forme longue, publiée au Journal officiel, qui dit ce que le
texte prétend faire : « … portant transposition de la directive 2011/83/UE
relative aux droits des consommateurs ». La mention de transposition est une
déclaration de l'auteur du texte, la seule que le corpus contienne sur le lien
entre droit français et droit de l'Union.

Elle est dans `<TITREFULL>` du fichier `version` du texte JORF — contrairement au
corps des articles, qui n'y est pas (voir `rapports_president.py`).

Usage :
    titres_jorf.py <miroir_dila/> <base.sqlite> <titres-jorf.tsv>
"""

from __future__ import annotations

import csv
import html
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

TITRE = re.compile(r"<TITREFULL>(.*?)</TITREFULL>", re.S)


def sans_balises(fragment: str) -> str:
    texte = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", texte).strip()


def extraire(archive: Path, motifs: list[str], destination: str) -> None:
    """Une seule passe de tar par lot : l'archive JORF fait 1,6 Go."""
    for depart in range(0, len(motifs), 200):     # limite de longueur de commande
        subprocess.run(["tar", "xzf", str(archive), "-C", destination,
                        "--wildcards"] + motifs[depart:depart + 200],
                       stderr=subprocess.DEVNULL, check=False)


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    miroir, chemin_base, sortie = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(f"file:{chemin_base}?mode=ro", uri=True)
    textes = [t for (t,) in base.execute("SELECT id_jorf FROM texte_normatif")]
    base.close()

    jorf = sorted(miroir.glob("JORF/Freemium_jorf_global_*.tar.gz"))
    if not jorf:
        sys.exit("archive globale JORF absente du miroir")

    titres: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        extraire(jorf[-1], [f"*/{t}.xml" for t in textes], tmp)
        for identifiant in textes:
            for fichier in Path(tmp).rglob(f"{identifiant}.xml"):
                if "version" not in str(fichier):
                    continue
                trouve = TITRE.search(fichier.read_text(encoding="utf-8",
                                                        errors="replace"))
                if trouve:
                    titres[identifiant] = sans_balises(trouve.group(1))
                break

    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.writer(flux, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["id_jorf", "titre"])
        for identifiant in sorted(titres):
            ecrivain.writerow([identifiant, titres[identifiant]])

    print(f"textes du périmètre     : {len(textes)}")
    print(f"  intitulé complet repris : {len(titres)}")
    print(f"  mentionnant une transposition : "
          f"{sum(1 for t in titres.values() if 'transpos' in t.lower())}")
    print(f"→ {sortie}")


if __name__ == "__main__":
    main()
