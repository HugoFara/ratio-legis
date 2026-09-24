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
import tarfile
import tempfile
from concurrent.futures import ProcessPoolExecutor
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
    # Lister, choisir par le nom de fichier, puis extraire la liste exacte.
    # `tar --wildcards` compare chaque motif à chaque membre : des milliers de
    # motifs contre les millions de fichiers de JORF, cinq minutes pour une
    # étape qui décompresse en vingt secondes. Deux passes, un ensemble.
    noms = {m.rsplit("/", 1)[-1].lstrip("*") for m in motifs}
    listing = subprocess.run(["tar", "tzf", str(archive)], capture_output=True,
                             text=True, check=False)
    voulus = [m for m in listing.stdout.splitlines() if m.rsplit("/", 1)[-1] in noms]
    if not voulus:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".liste", encoding="utf-8") as liste:
        liste.write("\n".join(voulus) + "\n")
        liste.flush()
        subprocess.run(commande + ["--no-wildcards", "--verbatim-files-from", "-T", liste.name],
                       stderr=subprocess.DEVNULL, check=False)


def _increment(archive: Path, destination: Path, noms: set[str] | None,
               fonds: str) -> list[str]:
    """Un incrément en une seule décompression : les membres voulus, écrits
    sous `destination`. Rend les chemins que l'incrément dit supprimer.

    Rejouer `tar --wildcards` par lot de motifs sur chacun des ~740 incréments
    JORF décompressait chacun des dizaines de fois : l'étape des rapports au
    Président, qui en demande des milliers, ne finissait plus. Ici chaque
    archive est lue une fois, et un membre est retenu par son nom de fichier."""
    suppression = f"liste_suppression_{fonds.lower()}.dat"
    supprimes: list[str] = []
    with tarfile.open(archive, "r:gz") as tar:
        for membre in tar:
            nom = membre.name.rsplit("/", 1)[-1]
            if nom == suppression:
                lu = tar.extractfile(membre)
                supprimes = lu.read().decode("utf-8", "replace").split() if lu else []
                continue
            if not membre.isfile() or (noms is not None and nom not in noms):
                continue
            relatif = membre.name.split("/", 1)[1] if "/" in membre.name else membre.name
            cible = destination / relatif
            cible.parent.mkdir(parents=True, exist_ok=True)
            lu = tar.extractfile(membre)
            if lu:
                cible.write_bytes(lu.read())
    return supprimes


def _appliquer(source: Path, destination: Path, supprimes: list[str]) -> None:
    """Recouvre `destination` par ce que l'incrément a extrait, puis supprime."""
    for fichier in sorted(p for p in source.rglob("*") if p.is_file()):
        cible = destination / fichier.relative_to(source)
        cible.parent.mkdir(parents=True, exist_ok=True)
        fichier.replace(cible)
    for chemin in supprimes:
        cible = destination / f"{chemin}.xml"
        if cible.exists():
            cible.unlink()


def deployer(miroir: Path, fonds: str, destination: Path,
             motifs: list[str] | None = None) -> int:
    """Déploie l'état courant du fonds dans `destination`. Rend le nombre
    d'incréments appliqués. `motifs` restreint l'extraction ; ils sont tous de
    la forme « *nom.xml » ou « */nom.xml », et c'est le nom qui compte."""
    destination = Path(destination)
    socle, increments = archives(miroir, fonds)
    _tar(socle, destination, motifs, 0)
    noms = None if motifs is None else {m.rsplit("/", 1)[-1].lstrip("*") for m in motifs}
    # La décompression, indépendante d'un incrément à l'autre, se fait en
    # parallèle, chacun dans son répertoire ; l'application, elle, suit l'ordre
    # des incréments, parce qu'un recouvrement ou une suppression plus récente
    # doit l'emporter.
    with tempfile.TemporaryDirectory(dir=destination) as tampon, \
            ProcessPoolExecutor() as pool:
        dossiers = [Path(tampon) / f"{rang:05d}" for rang in range(len(increments))]
        suppressions = pool.map(_increment, increments, dossiers,
                                [noms] * len(increments), [fonds] * len(increments))
        for dossier, supprimes in zip(dossiers, suppressions):
            _appliquer(dossier, destination, supprimes)
    return len(increments)
