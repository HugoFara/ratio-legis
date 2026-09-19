#!/usr/bin/env python3
"""Tire un échantillon reproductible d'arêtes `resulte_de`, et en fait le bilan.

`resulte_de` est l'arête critique du § 3, et la feuille de route lui impose le
seuil le plus haut du projet : **précision > 95 %**, « cette métrique prime sur
toutes les autres ». Elle a longtemps été mesurée sur 26 arêtes examinées à la
main — 23 justes, borne inférieure de Wilson à 0,7102. Vingt-six arêtes ne
permettent pas de distinguer 88 % de 96 % : l'écart entre la mesure et le seuil
n'était pas un écart de qualité, c'était un manque d'échantillon.

**Un tirage reproductible, pas aléatoire.** Chaque arête reçoit une clef de tri
issue du SHA-256 de son couple (segment, amendement). L'ordre qui en résulte est
sans rapport avec la structure du corpus — numéro d'article, dossier, chambre —
et il est le même à chaque exécution, sans graine à transmettre. Un échantillon
qu'on ne peut pas retirer à l'identique n'est pas une mesure.

**Ce que la fiche porte, et ce qu'elle ne porte pas.** Chaque ligne donne de quoi
trancher : la fenêtre commune qui a fondé l'arête, le dispositif de l'amendement,
le segment retrouvé, et deux corroborations calculées séparément —

- `vise` : l'amendement déclare-t-il modifier cet article, ou l'un de ses
  ancêtres de renumérotation ? Ce signal vient du **dispositif déclaré**, l'arête
  vient du **recouvrement textuel** : ils peuvent se contredire, et c'est
  précisément ce qui rend le rapprochement informatif.
- `nb_segments_fenetre` : combien de segments du même dossier portent cette
  fenêtre. Au-delà de 1 hors renumérotation, la fenêtre ne discrimine pas.

Ces colonnes **n'établissent rien** : elles orientent l'examen. La colonne
`verdict` reste vide et se remplit à la main — `juste`, `faux` ou `douteux`.

Un correctif tiré d'un échantillon ne peut pas être mesuré sur ce même
échantillon : l'option `--sauf` écarte du tirage les arêtes d'une fiche déjà
examinée, et rend ainsi une mesure sur pièces neuves.

Usage :
    precision_resulte_de.py <base.sqlite> <fiche.tsv> [effectif] [--sauf <fiche.tsv>]
    precision_resulte_de.py --bilan <fiche.tsv>
"""

from __future__ import annotations

import csv
import hashlib
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

EFFECTIF = 120
COLONNES = ["verdict", "cle", "chambre", "amendement", "sort", "auteur", "dossier",
            "article", "segment", "longueur_fenetre", "vise", "nb_segments_fenetre",
            "fenetre", "dispositif", "segment_texte", "url"]


def wilson(succes: int, total: int, z: float = 1.96) -> float:
    """Borne inférieure de Wilson à 95 %, la convention de confiance du § 5.4."""
    if total == 0:
        return 0.0
    p = succes / total
    denominateur = 1 + z * z / total
    centre = p + z * z / (2 * total)
    ecart = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return (centre - ecart) / denominateur


def coupe(texte: str, limite: int = 400) -> str:
    texte = " ".join((texte or "").split())
    return texte if len(texte) <= limite else texte[:limite] + " […]"


def classes_de_renumerotation(base: sqlite3.Connection) -> dict[str, str]:
    """Chaque numéro d'article vers la racine de sa chaîne de renumérotation."""
    racine: dict[str, str] = {}

    def chercher(numero: str) -> str:
        while racine.get(numero, numero) != numero:
            numero = racine[numero]
        return numero

    for cible, ancien in base.execute("""
            SELECT c.numero, a.numero FROM renumerote_de r
            JOIN article c ON c.id = r.article_id
            JOIN article a ON a.id = r.ancien_id"""):
        gauche, droite = chercher(cible), chercher(ancien)
        if gauche != droite:
            racine[gauche] = droite
    return {n: chercher(n) for n in
            {n for (n,) in base.execute("SELECT numero FROM article")}}


def tirer(base: sqlite3.Connection, effectif: int,
          sauf: set[tuple[str, str]] = frozenset()) -> list[dict[str, str]]:
    aretes = base.execute("""
        SELECT r.segment_id, r.amendement_id, p.fenetre,
               am.chambre, am.numero, am.sort, am.dispositif, am.url, am.dossier_id,
               coalesce(ac.nom, ''), a.numero, s.texte
        FROM resulte_de r
        JOIN preuve p ON p.id = r.preuve_id
        JOIN amendement am ON am.id = r.amendement_id
        LEFT JOIN acteur ac ON ac.id = am.auteur_id
        JOIN segment s ON s.id = r.segment_id
        JOIN version_article v ON v.id_legi = s.version_id
        JOIN article_courant a ON a.id = v.article_id""").fetchall()

    vise: dict[int, set[str]] = defaultdict(set)
    for amendement, numero in base.execute("""
            SELECT v.amendement_id, a.numero FROM vise v
            JOIN article_courant a ON a.id = v.article_id"""):
        vise[amendement].add(numero)
    racines = classes_de_renumerotation(base)

    # Combien de segments du même dossier portent la même fenêtre : la mesure de
    # discriminance, recalculée ici pour ne pas croire sur parole celle de
    # l'ingestion.
    portees: dict[tuple[str, str], set[str]] = defaultdict(set)
    for dossier, segment, fenetre in base.execute("""
            SELECT am.dossier_id, r.segment_id, p.fenetre
            FROM resulte_de r JOIN preuve p ON p.id = r.preuve_id
            JOIN amendement am ON am.id = r.amendement_id"""):
        portees[(dossier, fenetre)].add(segment)

    lignes = []
    for (segment, amendement, fenetre, chambre, numero, sort, dispositif, url,
         dossier, auteur, article, texte) in aretes:
        cle = hashlib.sha256(f"{segment}|{amendement}".encode()).hexdigest()
        cibles = vise.get(amendement, set())
        if not cibles:
            accord = "sans visée"
        elif article in cibles:
            accord = "oui"
        elif racines.get(article) in {racines.get(c) for c in cibles}:
            accord = "oui, par renumérotation"
        else:
            accord = "non : " + ", ".join(sorted(cibles)[:3])
        lignes.append({
            "verdict": "", "cle": cle[:16], "chambre": chambre,
            "amendement": numero, "sort": sort or "", "auteur": auteur,
            "dossier": dossier, "article": article, "segment": segment,
            "longueur_fenetre": str(len(fenetre)), "vise": accord,
            "nb_segments_fenetre": str(len(portees[(dossier, fenetre)])),
            "fenetre": coupe(fenetre, 200), "dispositif": coupe(dispositif),
            "segment_texte": coupe(texte), "url": url or "",
        })
    lignes = [l for l in lignes if (l["segment"], l["amendement"]) not in sauf]
    lignes.sort(key=lambda l: l["cle"])
    return lignes[:effectif]


def bilan(fiche: Path) -> None:
    lignes = list(csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t"))
    examinees = [l for l in lignes if l["verdict"]]
    justes = [l for l in examinees if l["verdict"] == "juste"]
    doutes = [l for l in examinees if l["verdict"] == "douteux"]
    print(f"arêtes tirées      : {len(lignes)}")
    print(f"arêtes examinées   : {len(examinees)}")
    print(f"  justes           : {len(justes)}")
    print(f"  douteuses        : {len(doutes)}")
    print(f"  fausses          : {len(examinees) - len(justes) - len(doutes)}")
    if not examinees:
        return
    # Le douteux compte comme un échec : le § 5.3 met la précision au-dessus du
    # rappel, une arête dont on n'est pas sûr n'est pas une arête juste.
    print(f"précision ponctuelle : {len(justes) / len(examinees):.3f}")
    print(f"borne de Wilson 95 % : {wilson(len(justes), len(examinees)):.4f}")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--bilan":
        return bilan(Path(sys.argv[2]))
    arguments = sys.argv[1:]
    sauf: set[tuple[str, str]] = set()
    if "--sauf" in arguments:
        place = arguments.index("--sauf")
        deja = Path(arguments[place + 1])
        sauf = {(l["segment"], l["amendement"]) for l in
                csv.DictReader(deja.open(encoding="utf-8"), delimiter="\t")}
        arguments = arguments[:place] + arguments[place + 2:]
    if len(arguments) not in (2, 3):
        sys.exit(__doc__)
    chemin_base, fiche = Path(arguments[0]), Path(arguments[1])
    effectif = int(arguments[2]) if len(arguments) == 3 else EFFECTIF

    base = sqlite3.connect(chemin_base)
    base.execute("PRAGMA foreign_keys = ON")
    lignes = tirer(base, effectif, sauf)
    total = base.execute("SELECT COUNT(*) FROM resulte_de").fetchone()[0]

    fiche.parent.mkdir(parents=True, exist_ok=True)
    with fiche.open("w", encoding="utf-8", newline="") as sortie:
        graveur = csv.DictWriter(sortie, COLONNES, delimiter="\t",
                                 quoting=csv.QUOTE_MINIMAL)
        graveur.writeheader()
        graveur.writerows(lignes)
    print(f"arêtes resulte_de en base : {total}")
    print(f"échantillon tiré          : {len(lignes)} → {fiche}")
    accord = sum(1 for l in lignes if l["vise"].startswith("oui"))
    sans = sum(1 for l in lignes if l["vise"] == "sans visée")
    print(f"  corroborées par `vise`  : {accord}")
    print(f"  contredites par `vise`  : {len(lignes) - accord - sans}")
    print(f"  amendement sans visée   : {sans}")
    peu = sum(1 for l in lignes if int(l["nb_segments_fenetre"]) > 1)
    print(f"  fenêtre portée par plusieurs segments : {peu}")


if __name__ == "__main__":
    main()
