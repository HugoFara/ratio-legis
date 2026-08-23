#!/usr/bin/env python3
"""Relève dans DOLE les rapports de commission des dossiers du périmètre.

`data/corpus/plan-rapports.tsv` était un artefact de phase 0 : 221 lignes
versionnées, sans le code qui les avait produites. La conséquence ne s'est vue
qu'en élargissant le périmètre aux parties R et D — deux dossiers législatifs
nouveaux, et **aucun moyen d'en obtenir les rapports**, puisque le plan ne
pouvait pas suivre. Un corpus qui ne suit pas son périmètre fait passer une
limite d'outillage pour un silence du fonds documentaire, ce qui est exactement
l'erreur que ce projet dit ne pas vouloir commettre.

La donnée était là. DOLE énumère sous `<ARBORESCENCE>` tous les documents d'un
dossier, chacun avec son libellé et son lien : textes en discussion, comptes
rendus, études d'impact — et rapports. `plan_textes.py` retient les libellés qui
commencent par « projet de loi », « proposition de loi » ou « texte » ; celui-ci
retient ceux qui commencent par « rapport ». C'est la même source, le même
mécanisme, et la seule distinction est le premier mot du libellé.

Sont écartés, et comptés :

  - les rapports d'information et les avis, qui ne commentent pas le texte
    article par article — c'est ce commentaire qui porte l'arête `motive` ;
  - les liens hors des deux chambres, dont le corpus ne sait rien.

Usage :
    plan_rapports.py <miroir_dila/> <perimetre.csv> <plan-rapports.tsv>
"""

from __future__ import annotations

import csv
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

LIEN = re.compile(r"<LIEN\b([^>]*?)/?>", re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')
RAPPORT = re.compile(r"^rapport\b", re.I)
# Un rapport d'information n'est pas un rapport de commission sur un texte : il
# ne suit pas le texte article par article, et c'est ce suivi que l'ingestion
# découpe. Un avis de commission saisie pour avis non plus.
ECARTES = re.compile(r"^rapport\s+d'information\b", re.I)
CHAMBRES = ("www.assemblee-nationale.fr", "www.senat.fr")


def extraire(archive: Path, motifs: list[str], destination: str) -> None:
    for depart in range(0, len(motifs), 200):
        subprocess.run(["tar", "xzf", str(archive), "-C", destination,
                        "--wildcards"] + motifs[depart:depart + 200],
                       stderr=subprocess.DEVNULL, check=False)


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    miroir, perimetre, sortie = (Path(a) for a in sys.argv[1:])
    dossiers = sorted({l["id_dole_origine"] for l in
                       csv.DictReader(perimetre.open(encoding="utf-8"))
                       if l["id_dole_origine"]})
    archives = sorted(miroir.glob("DOLE/Freemium_dole_global_*.tar.gz"))
    if not archives:
        sys.exit("archive globale DOLE absente du miroir")

    lignes, information, hors_chambre = [], 0, 0
    with tempfile.TemporaryDirectory() as tmp:
        extraire(archives[-1], [f"*{d}.xml" for d in dossiers], tmp)
        for dossier in dossiers:
            for fichier in Path(tmp).rglob(f"{dossier}.xml"):
                brut = fichier.read_text(encoding="utf-8", errors="replace")
                for trouve in LIEN.finditer(brut):
                    attributs = dict(ATTR.findall(trouve.group(1)))
                    libelle = html.unescape(attributs.get("libelle", "")).strip()
                    url = html.unescape(attributs.get("lien", "")).strip()
                    if not RAPPORT.match(libelle) or not url:
                        continue
                    if ECARTES.match(libelle):
                        information += 1
                        continue
                    hote = re.sub(r"https?://([^/]+)/.*", r"\1", url)
                    if hote not in CHAMBRES:
                        hors_chambre += 1
                        continue
                    lignes.append((dossier, url))
                break

    lignes = sorted(set(lignes))
    with sortie.open("w", encoding="utf-8", newline="") as flux:
        csv.writer(flux, delimiter="\t", lineterminator="\n").writerows(lignes)

    print(f"dossiers du périmètre : {len(dossiers)}")
    print(f"rapports relevés      : {len(lignes)}")
    print(f"  dossiers couverts   : {len({l[0] for l in lignes})}")
    print(f"  rapports d'information écartés : {information}")
    print(f"  hors des deux chambres, écartés : {hors_chambre}")
    print(f"→ {sortie}")


if __name__ == "__main__":
    main()
