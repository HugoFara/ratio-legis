#!/usr/bin/env python3
"""Relève dans DOLE les textes en discussion, à chaque stade de la navette.

C'est le chaînon manquant du projet, et il manque à trois chantiers à la fois.

Le graphe sait ce qu'un **article du code** est devenu, et ce qu'un **article du
texte en discussion** a suscité — un amendement s'y dépose, un rapport le
commente, une étude d'impact le chiffre. Ce qu'il ne sait pas, c'est relier les
deux : quel article du code l'article 5 du projet de loi touche. Ce lien n'est
écrit qu'à un seul endroit, le texte lui-même : « L'article L. 121-1 du code de la
consommation est ainsi modifié ».

Sans lui :
- l'étude d'impact et l'exposé des motifs restent au grain du texte entier
  (`docs/15` § 5) ;
- un amendement qui insère un alinéa sans nommer de code reste non rattaché,
  dernier mode d'échec de `resulte_de` (`docs/09`) ;
- les tableaux de concordance des directives n'ont pas d'ancrage français.

DOLE porte ces textes dans `<ARBORESCENCE>`, à tous les stades — dépôt, texte de
commission, adoption en première lecture, nouvelle lecture, lecture définitive.
229 liens sur le périmètre, vers l'Assemblée (116) et le Sénat (101 plus 8 sur
Améli). Ce sont des pages HTML, pas des PDF.

Usage :
    plan_textes.py <miroir_dila/> <dossiers-du-perimetre.tsv> <plan-textes.tsv>
"""

from __future__ import annotations

import csv
import html
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dossiers_du_perimetre import lire  # noqa: E402
from fonds import deployer  # noqa: E402

LIEN = re.compile(r"<LIEN\b([^>]*?)/?>", re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')
# Un libellé qui commence par « Dossier » désigne le dossier, pas le texte : c'est
# la seule distinction à faire, et elle est portée par le premier mot.
TEXTE = re.compile(r"^(projet de loi|proposition de loi|texte\b)", re.I)
CHAMBRE = {"www.assemblee-nationale.fr": "assemblee",
           "www.senat.fr": "senat", "ameli.senat.fr": "senat"}


def nom_local(url: str) -> str:
    """Nom de fichier stable, dérivé de l'URL, sans perdre la législature.

    `13/ta/ta0037.asp` et `14/ta/ta0037.asp` sont deux textes différents : ne
    garder que le dernier segment les confondrait.
    """
    chemin = re.sub(r"^https?://[^/]+/", "", url)
    return re.sub(r"[^A-Za-z0-9._-]+", "-", chemin)


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    miroir, liste, sortie = (Path(a) for a in sys.argv[1:])
    dossiers = sorted({l["id_dole"] for l in lire(liste)})
    lignes, hors_chambre = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        deployer(miroir, "dole", Path(tmp), [f"*{d}.xml" for d in dossiers])
        for dossier in dossiers:
            for fichier in Path(tmp).rglob(f"{dossier}.xml"):
                brut = fichier.read_text(encoding="utf-8", errors="replace")
                for trouve in LIEN.finditer(brut):
                    attributs = dict(ATTR.findall(trouve.group(1)))
                    libelle = html.unescape(attributs.get("libelle", "")).strip()
                    url = html.unescape(attributs.get("lien", "")).strip()
                    if not TEXTE.match(libelle) or not url:
                        continue
                    hote = re.sub(r"https?://([^/]+)/.*", r"\1", url)
                    if hote not in CHAMBRE:
                        hors_chambre += 1
                        continue
                    lignes.append((dossier, CHAMBRE[hote],
                                   re.sub(r"\s+", " ", libelle), nom_local(url), url))
                break

    # DOLE liste parfois la même page sous deux libellés — « Proposition de loi
    # … » et « Texte adopté en 1ère lecture … » pour une seule URL. Un texte, un
    # fichier, une ligne : l'identifiant en base est le fichier, et deux lignes
    # y entraient en collision.
    vus: set[tuple[str, str]] = set()
    lignes = [l for l in sorted(set(lignes))
              if (l[0], l[3]) not in vus and not vus.add((l[0], l[3]))]
    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.writer(flux, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["dossier", "chambre", "stade", "fichier", "url"])
        ecrivain.writerows(lignes)

    print(f"dossiers du périmètre : {len(dossiers)}")
    print(f"textes relevés        : {len(lignes)}")
    for chambre in ("assemblee", "senat"):
        print(f"  {chambre:10s}          : {sum(1 for l in lignes if l[1] == chambre)}")
    print(f"  hors des deux chambres, écartés : {hors_chambre}")
    print(f"  dossiers couverts   : {len({l[0] for l in lignes})}")
    print(f"→ {sortie}")


if __name__ == "__main__":
    main()
