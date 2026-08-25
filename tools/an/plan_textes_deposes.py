#!/usr/bin/env python3
"""Relève le numéro de dépôt des textes de l'Assemblée, que DOLE ne lie pas.

**Ce que DOLE ne donne pas.** Son `<ARBORESCENCE>` lie le rapport, le texte de la
commission et le texte adopté ; il ne lie pas le **texte déposé** d'un projet de
loi. `docs/15` § 5 le constatait sans en sortir : aucun des dossiers ayant une
étude d'impact n'a de texte déposé dans le corpus, parce que DOLE ne lie ce texte
que pour les propositions de loi, qui n'ont jamais d'étude d'impact.

C'est le chaînon qui manque à deux chantiers à la fois : l'étude d'impact chiffre
les articles du **texte déposé**, et les amendements de l'Assemblée se déposent
sur lui (`B1015`, par opposition au texte de commission `BTC2442`).

**Le numéro est déclaré à deux endroits, et n'est deviné à aucun.**

1. *Le rapport de commission.* Son titre et sa première page nomment le texte
   rapporté : « Rapport de Mme Sophie Errante sur le projet de loi, après
   engagement de la procédure accélérée, relatif à la simplification de la vie
   des entreprises **(n° 2060)** ». La convention est celle des deux séries —
   projet de loi et proposition de loi —, et elle décide aussi de la rubrique de
   l'URL : `/projets/pl…` ou `/propositions/pion…`.
2. *Le corpus d'amendements.* La référence d'un amendement de l'Assemblée nomme
   le document sur lequel il porte, et `amendement.texte_discute` en garde la
   forme `B1773` / `BTC1156`.

   **Ce n'est pas le texte déposé**, contrairement à ce qu'affirmait `docs/10`
   § 4 : `l14b1773_projet-loi` rend 404 quand
   `l14b1773_texte-adopte-commission` rend « Texte de la commission, n° 1773-A0 ».
   Les deux préfixes désignent des textes de commission, et la loi consommation le
   montre sans ambiguïté — ses amendements portent `B1773`, `BTC1156` et
   `BTC1574`, quand son texte déposé est le n° 1015. Cette source alimente donc
   les **textes de commission**, qui sont ce que ces amendements ont réellement
   amendé — et ce qui manquait aux 13 jeux non appariés de `docs/31` § 3.

La législature vient de `dossier.legislature`, renseignée pour les 199 dossiers du
périmètre.

**Le plan est une hypothèse ; le téléchargement est sa vérification.** Un couple
(législature, numéro) faux rend 404, et `telecharger_textes.py` le laisse en
échec plutôt que d'écrire un fichier. Une seconde vérification suit au chargement
— les subdivisions des amendements doivent tomber dans la plage d'articles du
texte (`docs/31` § 3). Rien n'est écrit sur la foi du seul numéro.

Le numéro est cadré sur quatre chiffres : `/17/projets/pl0529.asp` répond,
`pl529.asp` non ; `l14b0469_…` répond, `l14b469_…` non.

Usage :
    plan_textes_deposes.py <base.sqlite> <corpus/rapports/> <sortie.tsv>
"""

from __future__ import annotations

import csv
import html
import re
import sqlite3
import sys
from pathlib import Path

# « (n° 2060) », « (n° 2060 rectifié) », « (nos 2060, 2061) » quand le rapport
# porte sur plusieurs textes. Le numéro doit suivre la mention du texte rapporté,
# et dans une fenêtre courte : un rapport cite plus loin quantité d'autres
# numéros — lois, articles, amendements — qui ne sont pas le sien.
RAPPORTE = re.compile(
    r"(?:sur\s+(?:le|la|les)\s+)?(projet|proposition)s?\s+de\s+loi\b"
    r".{0,400}?\(\s*n[°os]{1,3}\s*([\d\s,et]+?)\s*\)", re.I | re.S)
PORTEE_TITRE = 6000
# `B1247/PO644420`, `BTC1156/PO644420` : la référence porte le numéro de document
# **et** l'organe qui l'examine. Ancrer la fin de chaîne ne reconnaissait rien du
# tout — et le relevé se taisait au lieu d'échouer, ce qui est le pire des deux.
# Les deux préfixes désignent des textes de commission et vont à la même URL.
AMENDEMENT_AN = re.compile(r"^B(?:TC)?(\d+)/")
RAPPORT = re.compile(r"__(?:r\d+\.asp|l\d+b\d+.*rapport)")

RUBRIQUE = {"projet": ("projets", "pl"), "proposition": ("propositions", "pion")}
BASE_AN = "https://www.assemblee-nationale.fr"
# Le numéro est cadré sur quatre chiffres des deux côtés : `pl0529.asp` répond,
# `pl529.asp` non ; `l14b0469_…` répond, `l14b469_…` non.
CADRE = "{:04d}"


def texte_brut(fichier: Path) -> str:
    brut = fichier.read_bytes()
    encodage = "latin-1" if b"charset=iso" in brut[:3000].lower() else "utf-8"
    page = re.sub(r"<script.*?</script>", " ", brut.decode(encodage, "replace"),
                  flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))


def numeros_du_rapport(fichier: Path) -> list[tuple[str, str]]:
    """(nature, numéro) déclarés par un rapport, sur sa première page."""
    trouve = RAPPORTE.search(texte_brut(fichier)[:PORTEE_TITRE])
    if not trouve:
        return []
    nature = trouve.group(1).lower()
    return [(nature, numero) for numero in re.findall(r"\d+", trouve.group(2))]


def deja_planifies(plan: Path) -> set[str]:
    """Les documents que `plan_textes.py` relève déjà depuis DOLE.

    `texte_discute.id` est une clef primaire : proposer deux fois le même
    document ferait échouer le chargement entier, et l'échec ne dirait pas
    lequel.
    """
    if not plan.exists():
        return set()
    return {ligne["fichier"] for ligne
            in csv.DictReader(plan.open(encoding="utf-8"), delimiter="\t")}


def relever(base: sqlite3.Connection, rapports: Path,
            connus: set[str]) -> tuple[list, dict]:
    legislature = dict(base.execute(
        "SELECT id_dole, legislature FROM dossier WHERE legislature IS NOT NULL"))
    compte = {"textes_de_commission": 0, "par_rapport": 0, "sans_legislature": 0,
              "rapports_muets": 0, "deja_dans_le_plan_dole": 0}
    # (dossier, nature, numéro) → la source la plus forte l'emporte pour la
    # rubrique de l'URL ; le corpus d'amendements ne dit pas la nature du texte,
    # et c'est le rapport qui la donne.
    natures: dict[tuple[str, str], str] = {}

    for fichier in sorted(rapports.iterdir()):
        if not RAPPORT.search(fichier.name):
            continue
        dossier = fichier.name.split("__")[0]
        trouves = numeros_du_rapport(fichier)
        if not trouves:
            compte["rapports_muets"] += 1
            continue
        for nature, numero in trouves:
            if (dossier, numero) not in natures:
                compte["par_rapport"] += 1
            natures[(dossier, numero)] = nature

    commissions: set[tuple[str, str]] = set()
    for dossier, corpus in base.execute(
            "SELECT DISTINCT dossier_id, texte_discute FROM amendement "
            "WHERE chambre = 'assemblee'"):
        trouve = AMENDEMENT_AN.match(corpus)
        if trouve:
            commissions.add((dossier, trouve.group(1)))
    compte["textes_de_commission"] = len(commissions)

    lignes = []
    for (dossier, numero), nature in sorted(natures.items()):
        if dossier not in legislature:
            compte["sans_legislature"] += 1
            continue
        rubrique, prefixe = RUBRIQUE[nature]
        chemin = (f"{legislature[dossier]}/{rubrique}/"
                  f"{prefixe}{CADRE.format(int(numero))}.asp")
        lignes.append((dossier, "assemblee",
                       f"{nature.capitalize()} de loi n° {numero} déposé à "
                       "l'Assemblée nationale",
                       chemin.replace("/", "-"), f"{BASE_AN}/{chemin}"))
    for dossier, numero in sorted(commissions):
        if dossier not in legislature:
            compte["sans_legislature"] += 1
            continue
        leg = legislature[dossier]
        # `/ta-commission/r{numéro}-a0.asp`, non la forme `dyn` : celle-ci répond
        # 200 pour la XIVe législature, mais sa page ne contient pas le texte et
        # ne déclare aucun PDF du document — seulement la déclaration
        # d'accessibilité. La forme historique rend le texte entier, et elle
        # redirige d'elle-même vers `dyn` là où c'est nécessaire. C'est aussi
        # celle que DOLE emploie pour les textes de commission qu'il lie.
        chemin = f"{leg}/ta-commission/r{CADRE.format(int(numero))}-a0.asp"
        lignes.append((dossier, "assemblee",
                       f"Texte de la commission n° {numero} de l'Assemblée "
                       "nationale",
                       re.sub(r"[^A-Za-z0-9._-]+", "-", chemin),
                       f"{BASE_AN}/{chemin}"))
    retenues = [l for l in lignes if l[3] not in connus]
    compte["deja_dans_le_plan_dole"] = len(lignes) - len(retenues)
    return retenues, compte


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    chemin_base, rapports, sortie = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(f"file:{chemin_base}?mode=ro", uri=True)
    connus = deja_planifies(sortie.parent / "plan-textes.tsv")
    lignes, compte = relever(base, rapports, connus)
    base.close()

    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.writer(flux, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["dossier", "chambre", "stade", "fichier", "url"])
        ecrivain.writerows(lignes)

    print(f"documents relevés          : {len(lignes)}")
    print(f"  textes déposés, déclarés par un rapport : {compte['par_rapport']}")
    print(f"  textes de commission, tirés du corpus d'amendements : "
          f"{compte['textes_de_commission']}")
    print(f"  rapports ne nommant aucun numéro : {compte['rapports_muets']}")
    print(f"  déjà relevés par le plan DOLE, écartés : "
          f"{compte['deja_dans_le_plan_dole']}")
    print(f"  dossiers sans législature, écartés : {compte['sans_legislature']}")
    print(f"  dossiers couverts        : {len({l[0] for l in lignes})}")
    print(f"→ {sortie}")


if __name__ == "__main__":
    main()
