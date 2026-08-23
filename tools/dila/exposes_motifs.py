#!/usr/bin/env python3
"""Reprend du miroir DOLE l'exposé des motifs des projets de loi du périmètre.

C'est la colonne « ce que le Gouvernement a déclaré vouloir » du § 4.3, et elle
était vide. Le graphe savait ce que le Parlement avait *fait* — amendements,
rapports de commission — et ce que l'Union avait *voulu* — considérants — mais
rien de ce que l'auteur du texte disait chercher en le déposant.

Contrairement aux études d'impact et aux avis du Conseil d'État, qui sont des PDF
liés depuis `<ARBORESCENCE>`, l'exposé des motifs est **dans le XML DOLE lui-même**,
sous `<EXPOSE_MOTIF>` : ni téléchargement, ni PDF, ni OCR, et des offsets fiables.

39 des 93 dossiers du périmètre en portent un exploitable, de 46 000 caractères en
médiane. Les 54 autres sont des ordonnances — qui n'ont qu'un rapport au Président
— ou des lois dont l'exposé n'est porté que par le dossier du *projet* de loi et
n'a pas été recopié sur celui de la loi promulguée.

L'URL du dossier ne pointe plus sur Légifrance : celui-ci redirige désormais les
dossiers législatifs vers vie-publique.fr, et c'est là que la citation résout.

Le périmètre suffit à savoir quels dossiers extraire : lire la base créerait une
dépendance circulaire, puisque c'est le chargement de ce corpus qui la peuple.

Usage :
    exposes_motifs.py <miroir_dila/> <perimetre.csv> <destination/>
"""

from __future__ import annotations

import csv
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXPOSE = re.compile(r"<EXPOSE_MOTIF>(.*?)</EXPOSE_MOTIF>", re.S)
MINIMUM = 200          # en deçà, la balise est présente mais vide


def sans_balises(fragment: str) -> str:
    texte = re.sub(r"<br\s*/?>|</p\s*>", "\n", fragment, flags=re.I)
    texte = html.unescape(re.sub(r"<[^>]+>", " ", texte))
    return re.sub(r"\n{3,}", "\n\n",
                  "\n".join(re.sub(r"[ \t]+", " ", l).strip()
                            for l in texte.split("\n"))).strip()


def extraire(archive: Path, motifs: list[str], destination: str) -> None:
    for depart in range(0, len(motifs), 200):     # limite de longueur de commande
        subprocess.run(["tar", "xzf", str(archive), "-C", destination,
                        "--wildcards"] + motifs[depart:depart + 200],
                       stderr=subprocess.DEVNULL, check=False)


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    miroir, perimetre, destination = (Path(a) for a in sys.argv[1:])
    destination.mkdir(parents=True, exist_ok=True)
    dossiers = sorted({l["id_dole_origine"] for l in
                       csv.DictReader(perimetre.open(encoding="utf-8"))
                       if l["id_dole_origine"]})

    archives = sorted(miroir.glob("DOLE/Freemium_dole_global_*.tar.gz"))
    if not archives:
        sys.exit("archive globale DOLE absente du miroir")

    ecrits, vides = 0, 0
    with tempfile.TemporaryDirectory() as tmp:
        extraire(archives[-1], [f"*{d}.xml" for d in dossiers], tmp)
        for dossier in dossiers:
            for fichier in Path(tmp).rglob(f"{dossier}.xml"):
                trouve = EXPOSE.search(fichier.read_text(encoding="utf-8",
                                                         errors="replace"))
                corps = sans_balises(trouve.group(1)) if trouve else ""
                if len(corps) < MINIMUM:
                    vides += 1
                    break
                (destination / f"{dossier}__expose-motifs.txt").write_text(
                    corps + "\n", encoding="utf-8")
                ecrits += 1
                break

    print(f"dossiers du périmètre        : {len(dossiers)}")
    print(f"  sans exposé exploitable    : {vides}")
    print(f"exposés des motifs écrits    : {ecrits} → {destination}")


if __name__ == "__main__":
    main()
