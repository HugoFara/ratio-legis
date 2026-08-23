#!/usr/bin/env python3
"""Extrait du miroir JORF les rapports au Président de la République.

Une ordonnance n'a ni exposé des motifs, ni rapport de commission, ni débat : sa
**seule** motivation publiée est le rapport au Président de la République. Le
périmètre compte 40 dossiers d'ordonnance, dont trois recodifications qui portent
l'essentiel du code de la consommation actuel.

Ces rapports avaient été récupérés à la main en phase 0, sans plan versionné, et
ont disparu avec le répertoire de travail. Ils sont publiés au Journal officiel :
ce script les reprend du miroir DILA, sans aucun accès réseau.

Le chemin est en trois temps, et aucune étape n'est devinable depuis la
précédente :

    DOLE <dossier>  --ID_TEXTE_2-->  JORFTEXT du rapport
    JORFTEXT        --texte/struct-->  identifiants JORFARTI
    JORFARTI        --BLOC_TEXTUEL-->  le texte lui-même

La version d'un texte JORF ne contient que des métadonnées — 1,5 ko pour un
rapport de plusieurs pages. Le corps est dans ses articles, référencés par le
fichier de structure. Chercher le texte dans le fichier `version`, comme le fait
l'intuition, ne rend rien et ne lève aucune erreur.

Usage :
    rapports_president.py <miroir_dila/> <perimetre.csv> <destination/>
"""

from __future__ import annotations

import csv
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ID_TEXTE_2 = re.compile(r"<ID_TEXTE_2>(JORFTEXT\d+)</ID_TEXTE_2>")
ARTICLE = re.compile(r"(JORFARTI\d+)")
BLOC = re.compile(r"<BLOC_TEXTUEL>(.*?)</BLOC_TEXTUEL>", re.S)
TITRE = re.compile(r"<TITREFULL>(.*?)</TITREFULL>", re.S)


def sans_balises(fragment: str) -> str:
    texte = re.sub(r"<br\s*/?>|</p\s*>", "\n", fragment, flags=re.I)
    texte = html.unescape(re.sub(r"<[^>]+>", " ", texte))
    return re.sub(r"\n{3,}", "\n\n",
                  "\n".join(re.sub(r"[ \t]+", " ", l).strip() for l in texte.split("\n")))


def extraire(archive: Path, motifs: list[str], destination: str) -> None:
    """Une seule passe de tar par lot : l'archive JORF fait 1,6 Go."""
    for depart in range(0, len(motifs), 400):     # limite de longueur de commande
        subprocess.run(["tar", "xzf", str(archive), "-C", destination, "--wildcards"]
                       + motifs[depart:depart + 400],
                       stderr=subprocess.DEVNULL, check=False)


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    miroir, perimetre, destination = (Path(a) for a in sys.argv[1:])
    destination.mkdir(parents=True, exist_ok=True)

    dossiers = sorted({l["id_dole_origine"] for l in
                       csv.DictReader(perimetre.open(encoding="utf-8"))
                       if l["id_dole_origine"] and l["nature_origine"] == "ORDONNANCE"})
    dole = sorted(miroir.glob("DOLE/Freemium_dole_global_*.tar.gz"))
    jorf = sorted(miroir.glob("JORF/Freemium_jorf_global_*.tar.gz"))
    if not dole or not jorf:
        sys.exit("archives globales DOLE ou JORF absentes du miroir")

    with tempfile.TemporaryDirectory() as tmp:
        extraire(dole[-1], [f"*{d}.xml" for d in dossiers], tmp)
        rapports: dict[str, str] = {}          # JORFTEXT -> dossier
        for dossier in dossiers:
            for fichier in Path(tmp).rglob(f"{dossier}.xml"):
                trouve = ID_TEXTE_2.search(fichier.read_text(encoding="utf-8",
                                                             errors="replace"))
                if trouve:
                    rapports[trouve.group(1)] = dossier

        extraire(jorf[-1], [f"*/{t}.xml" for t in rapports], tmp)
        articles: dict[str, list[str]] = {}
        for texte in rapports:
            struct = [p for p in Path(tmp).rglob(f"{texte}.xml") if "struct" in str(p)]
            if struct:
                articles[texte] = sorted(set(ARTICLE.findall(
                    struct[0].read_text(encoding="utf-8", errors="replace"))))

        besoins = [f"*/{a}.xml" for ids in articles.values() for a in ids]
        extraire(jorf[-1], besoins, tmp)

        ecrits, vides, hors_rapport = 0, [], []
        for texte, dossier in sorted(rapports.items()):
            version = [p for p in Path(tmp).rglob(f"{texte}.xml") if "version" in str(p)]
            titre = ""
            if version:
                brut = version[0].read_text(encoding="utf-8", errors="replace")
                t = TITRE.search(brut)
                titre = sans_balises(t.group(1)).strip() if t else ""
            # Le rapport est identifié par son titre, non par ID_TEXTE_2 seul :
            # certains dossiers y placent l'ordonnance elle-même.
            if "rapport au président" not in titre.lower():
                hors_rapport.append((dossier, texte, titre[:60]))
                continue
            corps = []
            for identifiant in articles.get(texte, []):
                for fichier in Path(tmp).rglob(f"{identifiant}.xml"):
                    for bloc in BLOC.findall(fichier.read_text(encoding="utf-8",
                                                               errors="replace")):
                        corps.append(sans_balises(bloc))
            contenu = (titre + "\n\n" + "\n\n".join(corps)).strip()
            if len(contenu) < 400:
                vides.append((dossier, texte))
                continue
            (destination / f"{dossier}__rapport-pr-{texte}.txt").write_text(
                contenu + "\n", encoding="utf-8")
            ecrits += 1

    print(f"dossiers d'ordonnance du périmètre : {len(dossiers)}")
    print(f"  avec un ID_TEXTE_2               : {len(rapports)}")
    print(f"  dont le titre n'est pas un rapport : {len(hors_rapport)}")
    print(f"  sans corps exploitable           : {len(vides)}")
    print(f"rapports écrits                    : {ecrits} → {destination}")


if __name__ == "__main__":
    main()
