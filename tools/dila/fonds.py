#!/usr/bin/env python3
"""L'état courant d'un fonds DILA : l'archive globale, puis ses incréments.

Six lecteurs de DOLE et deux de JORF n'ouvraient que l'archive **globale**, datée
du 13 juillet 2025, alors que le miroir reçoit un incrément par jour ouvré. Tout
dossier ouvert depuis leur était invisible : huit lois et ordonnances de 2026,
entrées dans la base par les incréments LEGI, restaient sans `issu_de` — non parce
que DOLE ne les liste pas, mais parce qu'on ne lisait pas les incréments qui les
listent. `increments.py` avait réglé la question pour LEGI seul.

Le geste est le même que pour LEGI : déployer le global, puis chaque incrément
postérieur au socle, dans l'ordre — **recouvrir, puis supprimer** ce que
`liste_suppression_<fonds>.dat` énumère. Un incrément est une arborescence
identique au global, précédée d'un répertoire horodaté ; on retire ce préfixe
pour que les appelants retrouvent le même arbre qu'avant, et leurs `rglob`
n'ont pas à changer.

    global      dole/global/JORF/DOLE/…              → tel quel
    incrément   20260819-222711/dole/global/…        → strip 1

Les incréments antérieurs au socle sont déjà dans le global : on les saute.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

HORODATAGE = re.compile(r"(\d{8}-\d{6})\.tar\.gz$")


def archives(miroir: Path, fonds: str) -> tuple[Path, list[Path]]:
    """Le global le plus récent et les incréments qui lui sont postérieurs."""
    repertoire = miroir / fonds.upper()
    globaux = sorted(repertoire.glob(f"Freemium_{fonds.lower()}_global_*.tar.gz"))
    if not globaux:
        raise SystemExit(f"archive globale {fonds.upper()} absente du miroir")
    socle = HORODATAGE.search(globaux[-1].name).group(1)
    increments = sorted(
        (a for a in repertoire.glob(f"{fonds.upper()}_*.tar.gz")
         if (h := HORODATAGE.search(a.name)) and h.group(1) > socle),
        key=lambda a: HORODATAGE.search(a.name).group(1))
    return globaux[-1], increments


def _tar(archive: Path, destination: Path, motifs: list[str] | None,
         retrait: int) -> None:
    commande = ["tar", "xzf", str(archive), "-C", str(destination),
                f"--strip-components={retrait}"]
    if motifs is None:
        subprocess.run(commande, stderr=subprocess.DEVNULL, check=False)
        return
    # Par lots : la liste de motifs dépasse sinon la longueur d'une commande.
    for depart in range(0, len(motifs), 400):
        subprocess.run(commande + ["--wildcards"] + motifs[depart:depart + 400],
                       stderr=subprocess.DEVNULL, check=False)


def _suppressions(archive: Path, fonds: str) -> list[str]:
    lecture = subprocess.run(
        ["tar", "xzf", str(archive), "-O", "--wildcards",
         f"*/liste_suppression_{fonds.lower()}.dat"],
        capture_output=True, text=True, check=False)
    return [l.strip() for l in lecture.stdout.splitlines() if l.strip()]


def deployer(miroir: Path, fonds: str, destination: Path,
             motifs: list[str] | None = None) -> int:
    """Déploie l'état courant du fonds dans `destination`. Rend le nombre
    d'incréments appliqués. `motifs` restreint l'extraction (`--wildcards`)."""
    destination = Path(destination)
    socle, increments = archives(miroir, fonds)
    _tar(socle, destination, motifs, 0)
    for increment in increments:
        _tar(increment, destination, motifs, 1)
        for chemin in _suppressions(increment, fonds):
            cible = destination / f"{chemin}.xml"
            if cible.exists():
                cible.unlink()
    return len(increments)
