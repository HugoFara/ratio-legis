#!/usr/bin/env python3
"""Applique les incréments quotidiens LEGI au fonds extrait.

Le pipeline n'extrayait le code que de l'archive **globale**. Celle du miroir
date du 13 juillet 2025, et la DILA publie un incrément par jour ouvré : la base
de travail avait donc **un an de retard** sur le miroir, sans que rien ne le
signale. Vingt-cinq des quarante derniers incréments touchent le code de la
consommation.

**Ce qu'est un incrément.** La même arborescence que le global, précédée d'un
répertoire horodaté, plus un fichier `liste_suppression_legi.dat` qui énumère les
chemins à supprimer. Appliquer un incrément, c'est donc recouvrir puis supprimer,
dans cet ordre.

    global      legi/global/…/LEGI/TEXT/00/00/06/06/95/LEGITEXT…/…   → strip 9
    incrément   20260819-222711/legi/global/…                        → strip 10

**Le journal fait partie du livrable.** Sans lui, on ne peut pas dire de quand
date le fonds, ni rejouer la même séquence : chaque incrément appliqué est
enregistré avec son empreinte. Le § 5.2 demande un pipeline rejouable, pas
seulement rejouable une fois.

Usage :
    increments.py <miroir_dila/> <destination/> <LEGITEXT…> [--liste] [--jusqu-a AAAAMMJJ]
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

JOURNAL = Path("data/corpus/increments-appliques.tsv")
COLONNES = ["increment", "horodatage", "sha256", "entrees", "suppressions", "applique_le"]
HORODATAGE = re.compile(r"LEGI_(\d{8}-\d{6})\.tar\.gz$")
GLOBAL = re.compile(r"Freemium_legi_global_(\d{8}-\d{6})\.tar\.gz$")


def empreinte(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def journal_lu(chemin: Path) -> dict[str, dict[str, str]]:
    if not chemin.exists():
        return {}
    with chemin.open(encoding="utf-8") as source:
        return {l["increment"]: l for l in csv.DictReader(source, delimiter="\t")}


def journal_ecrit(chemin: Path, lignes: list[dict[str, str]]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="") as sortie:
        graveur = csv.DictWriter(sortie, COLONNES, delimiter="\t", lineterminator="\n")
        graveur.writeheader()
        graveur.writerows(sorted(lignes, key=lambda l: l["horodatage"]))


def suppressions(archive: Path, code: str) -> list[str]:
    """Chemins à supprimer, ramenés à la forme de l'arbre extrait."""
    lecture = subprocess.run(
        ["tar", "xzf", str(archive), "-O", "--wildcards", "*/liste_suppression_legi.dat"],
        capture_output=True, text=True, check=False)
    cibles = []
    for ligne in lecture.stdout.splitlines():
        ligne = ligne.strip()
        if code not in ligne:
            continue
        morceaux = ligne.split("/")
        if len(morceaux) > 9:
            cibles.append("/".join(morceaux[9:]) + ".xml")
    return cibles


def appliquer(archive: Path, destination: Path, code: str) -> tuple[int, int]:
    """Recouvre puis supprime. Rend (entrées écrites, fichiers supprimés)."""
    avant = {p: p.stat().st_mtime_ns for p in destination.rglob("*.xml")}
    subprocess.run(["tar", "xzf", str(archive), "-C", str(destination),
                    "--strip-components=10", "--wildcards", f"*/{code}/*"],
                   stderr=subprocess.DEVNULL, check=False)
    apres = {p: p.stat().st_mtime_ns for p in destination.rglob("*.xml")}
    ecrites = sum(1 for p, t in apres.items() if avant.get(p) != t)

    retires = 0
    for relatif in suppressions(archive, code):
        cible = destination / relatif
        if cible.exists():
            cible.unlink()
            retires += 1
    return ecrites, retires


def main() -> None:
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(arguments) != 3:
        sys.exit(__doc__)
    miroir, destination, code = Path(arguments[0]), Path(arguments[1]), arguments[2]
    liste_seule = "--liste" in sys.argv
    jusqu_a = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jusqu-a=")),
                   None)

    globaux = sorted(miroir.glob("LEGI/Freemium_legi_global_*.tar.gz"))
    if not globaux:
        sys.exit("archive globale LEGI absente du miroir")
    socle = GLOBAL.search(globaux[-1].name).group(1)

    journal = journal_lu(JOURNAL)
    candidats = []
    for archive in sorted(miroir.glob("LEGI/LEGI_*.tar.gz")):
        trouve = HORODATAGE.search(archive.name)
        if not trouve or trouve.group(1) <= socle:
            continue          # antérieur au socle : déjà dans le global
        if jusqu_a and trouve.group(1)[:8] > jusqu_a:
            continue
        if archive.name in journal:
            continue
        candidats.append((trouve.group(1), archive))

    print(f"socle global               : {socle}")
    print(f"incréments déjà appliqués  : {len(journal)}")
    print(f"incréments à appliquer     : {len(candidats)}")
    if liste_seule or not candidats:
        for h, a in candidats[:10]:
            print(f"   {a.name}")
        if len(candidats) > 10:
            print(f"   … et {len(candidats) - 10} autres")
        return

    destination.mkdir(parents=True, exist_ok=True)
    lignes = list(journal.values())
    ecrites_totales = retires_totaux = 0
    touchants = 0
    for horodatage, archive in candidats:
        ecrites, retires = appliquer(archive, destination, code)
        ecrites_totales += ecrites
        retires_totaux += retires
        touchants += 1 if (ecrites or retires) else 0
        lignes.append({"increment": archive.name, "horodatage": horodatage,
                       "sha256": empreinte(archive), "entrees": str(ecrites),
                       "suppressions": str(retires),
                       "applique_le": datetime.now(timezone.utc)
                       .isoformat(timespec="seconds")})
    journal_ecrit(JOURNAL, lignes)

    print(f"  dont touchant ce code    : {touchants}")
    print(f"  fichiers écrits          : {ecrites_totales}")
    print(f"  fichiers supprimés       : {retires_totaux}")
    print(f"fonds à jour au {candidats[-1][0]} — journal : {JOURNAL}")


if __name__ == "__main__":
    main()
