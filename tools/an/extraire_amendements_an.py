#!/usr/bin/env python3
"""Extraction des amendements de l'Assemblée nationale pour les dossiers du périmètre.

**Le dépôt existe, contrairement à ce que ce projet a d'abord conclu.** Le chemin
publié sur la page d'archives de la XIVe législature pointe vers un hôte
`data-preprod` qui ne résout pas, et le chemin voisin `amendements_legis/` rend
404. Le bon chemin est `amendements_legis_XIV/`, et il est servi en clair :

    /static/openData/repository/14/loi/amendements_legis_XIV/Amendements_XIV.csv.zip

Il a été retrouvé par l'index CDX de la Wayback Machine, qui archive l'arborescence
du dépôt. La leçon est générale : un 404 sur une URL recopiée d'une page
institutionnelle prouve que l'URL est fausse, pas que la donnée est absente.

Le CSV fait 420 Mo pour 624 colonnes — un XML aplati. Il est lu en flux depuis
l'archive, sans décompression sur disque.

Deux formats de référence de texte coexistent et les confondre fait perdre la
moitié du corpus : `…L14B1015` désigne le texte déposé, `…L14BTC2442` le texte
issu des travaux de commission.

Usage :
    extraire_amendements_an.py <Amendements_XIV.csv.zip> <plan-textes.tsv> <sortie.csv>

Le plan associe un identifiant DOLE à un numéro de texte de l'Assemblée, une
ligne par couple.
"""

from __future__ import annotations

import collections
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

csv.field_size_limit(10 ** 9)

# Le marqueur `B` ou `BTC` est capturé, pas seulement toléré : le même numéro
# d'amendement désigne deux amendements différents selon qu'il porte sur le texte
# déposé (`B2736`) ou sur le texte issu de la commission (`BTC2736`). Les
# confondre en écrase 2 032.
REFERENCE = re.compile(r"L\d\d(B(?:TC)?)(\d+)")

# Colonnes utiles du fichier aplati, par position : les intitulés sont des chemins
# XML (« identifiant[1]/saisine[1]/refTexteLegislatif[1] ») et changent de forme
# d'une législature à l'autre, mais les positions de tête sont stables.
# Le sort n'est pas dans la colonne `sort[1]`, qui est vide sur toute la
# législature, mais dans `sort[1]/sortEnSeance[1]`. `etat[1]` ne dit que l'état
# procédural — « Discuté », « Irrecevable » — et le prendre pour le sort ferait
# disparaître 3 280 rejets derrière un « Discuté » uniforme.
#
# L'auteur n'est pas nommé non plus : les colonnes portent des références
# (`PA…` pour l'acteur, `PO…` pour l'organe), résolues par le jeu Acteurs de
# l'Assemblée. Elles sont conservées telles quelles, à charger séparément.
# `organeExamen` est indispensable à l'identité : le même numéro d'amendement
# désigne deux amendements différents sur le même texte selon qu'il est examiné en
# commission ou en séance — 2 098 couples (texte, numéro) en double, aux
# dispositifs et aux sorts distincts. Sans lui, 2 116 amendements disparaissent
# silencieusement à l'insertion.
COLONNES = {
    "numero": 4, "ref_texte": 7, "organe_examen": 9, "etat": 16, "type_auteur": 19,
    "acteur_ref": 20, "organe_ref": 21, "groupe_ref": 22,
    "division": 35, "dispositif": 47, "expose": 48, "sort": 70,
}


def plan(chemin: Path) -> dict[str, set[str]]:
    """Numéro de texte de l'Assemblée → identifiants DOLE."""
    textes: dict[str, set[str]] = collections.defaultdict(set)
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if "\t" in ligne:
            dossier, numero = ligne.split("\t", 1)
            textes[numero.strip().lstrip("0")].add(dossier.strip())
    return textes


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    archive, fichier_plan, sortie = (Path(a) for a in sys.argv[1:])
    textes = plan(fichier_plan)

    z = zipfile.ZipFile(archive)
    membre = max(z.namelist(), key=lambda n: z.getinfo(n).file_size)
    retenus, par_texte, lues = [], collections.Counter(), 0
    with z.open(membre) as flux:
        lecteur = csv.reader(io.TextIOWrapper(flux, encoding="utf-8", errors="replace"),
                             delimiter=";")
        next(lecteur)
        for ligne in lecteur:
            lues += 1
            if len(ligne) <= max(COLONNES.values()):
                continue
            trouve = REFERENCE.search(ligne[COLONNES["ref_texte"]] or "")
            if not trouve:
                continue
            numero = trouve.group(2).lstrip("0")
            if numero not in textes:
                continue
            par_texte[numero] += 1
            retenus.append([sorted(textes[numero])[0], numero, trouve.group(1)]
                           + [ligne[i] for i in COLONNES.values()])

    with sortie.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(["dossier", "texte", "stade"] + list(COLONNES))
        ecrivain.writerows(retenus)

    sorts = collections.Counter(l[3 + list(COLONNES).index("sort")] or "(vide)"
                                for l in retenus)
    print(f"lignes lues        : {lues}")
    print(f"amendements retenus : {len(retenus)} sur {len(par_texte)} textes")
    for numero, n in par_texte.most_common(10):
        print(f"   texte {numero:>6s} : {n}")
    print("\npar sort :")
    for sort, n in sorts.most_common(6):
        print(f"   {sort:24s} {n}")


if __name__ == "__main__":
    main()
