#!/usr/bin/env python3
"""Relève dans DOLE les études d'impact et avis du Conseil d'État du périmètre.

Ce sont les deux dernières colonnes vides du § 4.3 : ce que le Gouvernement a
**chiffré** avant de déposer, et ce que le Conseil d'État a **objecté** avant que
le texte parte au Parlement. Un article adopté malgré une objection du Conseil
d'État est un fait qui n'existe nulle part ailleurs.

Contrairement à l'exposé des motifs, ces documents ne sont pas dans le XML : DOLE
n'en porte que le lien, dans `<ARBORESCENCE>`, sous forme de PDF servis depuis le
chemin média de Légifrance — lequel, contrairement au site de consultation, n'est
pas derrière un défi JavaScript (`docs/01` § 2.6).

**Le libellé s'écrit avec et sans accent.** « Etude d'impact » et « Étude
d'impact » coexistent dans le même fonds, 18 contre 6 ; « Avis du Conseil d'Etat »
et « Avis du Conseil d'État », 10 contre 5. Filtrer sur la forme accentuée
perdrait les trois quarts des études et les deux tiers des avis. Le rapprochement
se fait donc sans accents.

Le plan produit est versionné : le pipeline doit pouvoir retélécharger sans
retraverser l'archive DOLE.

Usage :
    plan_impacts.py <miroir_dila/> <perimetre.csv> <plan-impacts.tsv>
"""

from __future__ import annotations

import csv
import html
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

LIEN = re.compile(r"<LIEN\b([^>]*?)/?>", re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')
TYPES = {"etude d'impact": "etude_impact",
         "avis du conseil d'etat": "avis_conseil_etat"}


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte)
                   if unicodedata.category(c) != "Mn").lower().strip()


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

    lignes, compte = [], {"etude_impact": 0, "avis_conseil_etat": 0}
    with tempfile.TemporaryDirectory() as tmp:
        extraire(archives[-1], [f"*{d}.xml" for d in dossiers], tmp)
        for dossier in dossiers:
            for fichier in Path(tmp).rglob(f"{dossier}.xml"):
                brut = fichier.read_text(encoding="utf-8", errors="replace")
                rang = {}
                for trouve in LIEN.finditer(brut):
                    attributs = dict(ATTR.findall(trouve.group(1)))
                    type_document = TYPES.get(
                        sans_accents(html.unescape(attributs.get("libelle", ""))))
                    url = html.unescape(attributs.get("lien", ""))
                    if not type_document or not url.lower().endswith(".pdf"):
                        continue
                    rang[type_document] = rang.get(type_document, 0) + 1
                    lignes.append((dossier, type_document, rang[type_document], url))
                    compte[type_document] += 1
                break

    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.writer(flux, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["dossier", "type", "rang", "url"])
        ecrivain.writerows(sorted(set(lignes)))

    print(f"dossiers du périmètre  : {len(dossiers)}")
    print(f"  études d'impact      : {compte['etude_impact']}")
    print(f"  avis du Conseil d'État : {compte['avis_conseil_etat']}")
    print(f"  dossiers couverts    : {len({l[0] for l in lignes})}")
    print(f"→ {sortie}")


if __name__ == "__main__":
    main()
