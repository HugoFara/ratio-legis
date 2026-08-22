#!/usr/bin/env python3
"""Généralisation des mesures du pilote à tout le périmètre.

Le prototype (`docs/03-prototype-resolveur.md`) ne portait que sur la loi
2014-344, soit 307 des 832 articles éligibles. Trois chiffres structurants en
dépendaient : la part d'articles issus du texte initial du Gouvernement, la
couverture C1, et le taux d'ancrage par les rapports de commission. Ce script les
recalcule dossier par dossier sur les 48 dossiers du périmètre.

Une précaution de méthode, apprise à ses dépens : **l'appariement d'un amendement
est restreint aux articles imputables à son propre dossier**. Sans cette
restriction, un amendement au projet de loi consommation se rattache à un article
issu d'une tout autre loi au seul motif qu'un passage de 60 caractères se retrouve
dans les deux. C'est l'erreur qui avait produit 9 faux rattachements sur 10 dans
la première version du golden set.

Usage :
    generalisation.py <perimetre.csv> <articles_code.json> <corpus/> <sortie.csv>

Le corpus attend trois sous-répertoires, tous nommés `<ID_DOLE>__<fichier>` :
`rapports/`, `initiaux/`, `ameli/`.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commentaires_rapports import commentaires, numeros_cites  # noqa: E402
from resolveur import (FENETRE, fenetres, lire_ameli, normalise,  # noqa: E402
                       passages_cites, texte_html)


def fenetres_de(texte: str, pas: int = 10) -> set[str]:
    """Fenêtres d'un texte, à pas fixe."""
    return {texte[d:d + FENETRE]
            for d in range(0, max(1, len(texte) - FENETRE + 1), pas)}


def fenetres_retrouvees(grand: str, index: dict[str, set[str]]) -> dict[str, set[str]]:
    """Pour chaque numéro, les fenêtres de son texte retrouvées dans `grand`.

    Le balayage se fait au pas de 1 sur le grand texte, l'index étant construit au
    pas de 10 sur les petits. Indexer les deux côtés à pas fixe ne marche pas : les
    grilles d'offsets ne coïncident jamais et l'appariement rend zéro là où une
    recherche de sous-chaîne trouve.

    On rend les fenêtres et non un booléen, parce qu'une seule fenêtre commune ne
    dit rien : elle peut signaler un article repris intégralement du texte déposé
    comme un article réécrit dont une phrase a survécu. C'est la part de l'article
    couverte qui informe, pas le fait qu'il le soit.
    """
    trouves: dict[str, set[str]] = defaultdict(set)
    for depart in range(0, max(1, len(grand) - FENETRE + 1)):
        fenetre = grand[depart:depart + FENETRE]
        for numero in index.get(fenetre, ()):
            trouves[numero].add(fenetre)
    return trouves


def par_dossier(repertoire: Path) -> dict[str, list[Path]]:
    groupes: dict[str, list[Path]] = defaultdict(list)
    if repertoire.is_dir():
        for fichier in sorted(repertoire.iterdir()):
            if "__" in fichier.name:
                groupes[fichier.name.split("__", 1)[0]].append(fichier)
    return groupes


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    perimetre, fichier_articles, corpus, sortie = (Path(a) for a in sys.argv[1:])

    articles = json.loads(fichier_articles.read_text(encoding="utf-8"))
    versions_par_numero: dict[str, list[str]] = defaultdict(list)
    for a in articles:
        if a["texte"]:
            versions_par_numero[a["num"]].append(normalise(a["texte"]))
    en_vigueur = {a["num"]: normalise(a["texte"]) for a in articles
                  if a["etat"] == "VIGUEUR" and a["texte"]}

    rapports = par_dossier(corpus / "rapports")
    initiaux = par_dossier(corpus / "initiaux")
    amendements = par_dossier(corpus / "ameli")

    perim = list(csv.DictReader(perimetre.open(encoding="utf-8")))
    eligibles = [a for a in perim if a["eligible_resulte_de"] == "1"]
    par_dole: dict[str, list[dict]] = defaultdict(list)
    for a in eligibles:
        par_dole[a["id_dole_origine"]].append(a)

    def cles(article: dict) -> list[str]:
        return [c for c in (article["num_article"].replace(" ", ""),
                            article["article_predecesseur"].replace(" ", "")) if c]

    lignes = []
    for dossier, groupe in sorted(par_dole.items(), key=lambda kv: -len(kv[1])):
        numeros = {c for a in groupe for c in cles(a)}

        # A / B : la rédaction figure-t-elle déjà dans le texte déposé ?
        # Le texte initial d'un gros dossier fait plusieurs mégaoctets ; chercher
        # chaque fenêtre par balayage y coûte des heures. On indexe une fois.
        initial = " ".join(texte_html(f) for f in initiaux.get(dossier, []))
        index: dict[str, set[str]] = defaultdict(set)
        total_fenetres: dict[str, int] = defaultdict(int)
        for article in groupe:
            for cle in cles(article):
                for texte in versions_par_numero.get(cle, ()):
                    if len(texte) < FENETRE:
                        continue
                    fen = fenetres_de(texte)
                    total_fenetres[article["num_article"]] = max(
                        total_fenetres[article["num_article"]], len(fen))
                    for fenetre in fen:
                        index[fenetre].add(article["num_article"])

        couverture: dict[str, float] = {}
        if initial:
            retrouvees = fenetres_retrouvees(initial, index)
            for numero, fen in retrouvees.items():
                if total_fenetres.get(numero):
                    couverture[numero] = len(fen) / total_fenetres[numero]
        # Seuil de reprise : un article dont plus de la moitié du texte figure au
        # texte déposé est motivé par l'exposé des motifs. En deçà, la rédaction a
        # été retravaillée et l'amendement redevient nécessaire.
        gouvernement = {n for n, part in couverture.items() if part >= 0.5}

        # Ancrage : un commentaire de rapport nomme-t-il l'article ?
        declares: set[str] = set()
        cites: set[str] = set()
        for fichier in rapports.get(dossier, []):
            try:
                sections = commentaires(fichier)
            except Exception:
                continue
            for section in sections:
                declares |= set(section["articles_declares"])
                cites |= set(section["articles_cites"])
        ancres = {a["num_article"] for a in groupe if any(c in cites for c in cles(a))}
        ancres_fort = {a["num_article"] for a in groupe if any(c in declares for c in cles(a))}

        # C1 : rattachement à un amendement du Sénat, restreint à ce dossier.
        # Même index, balayage au pas de 1 sur le dispositif de l'amendement.
        rattaches: set[str] = set()
        survivants: set[str] = set()
        adoptes = 0
        for fichier in amendements.get(dossier, []):
            try:
                jeu = [a for a in lire_ameli(fichier) if a.get("Sort") == "Adopté"]
            except Exception:
                continue
            adoptes += len(jeu)
            for amendement in jeu:
                for passage in passages_cites(amendement.get("Dispositif", "")):
                    for depart in range(0, max(1, len(passage) - FENETRE + 1)):
                        fenetre = passage[depart:depart + FENETRE]
                        touches = index.get(fenetre)
                        if not touches or len(touches) > 2:
                            continue
                        rattaches |= touches
                        for numero in touches:
                            if fenetre in en_vigueur.get(numero, ""):
                                survivants.add(numero)
        survivants &= (rattaches - gouvernement)

        navette = [a for a in groupe if a["num_article"] not in gouvernement]
        # C1 ne se mesure que sur la population qui a besoin de l'arête : un
        # article dont la rédaction vient du texte déposé est motivé par l'exposé
        # des motifs, et l'amendement qui l'a effleuré ne l'explique pas.
        rattaches_navette = rattaches - gouvernement
        lignes.append({
            "id_dole": dossier,
            "articles_eligibles": len(groupe),
            "texte_initial_disponible": int(bool(initial)),
            "issus_du_texte_initial": len(gouvernement),
            "repris_a_plus_de_90pc": sum(1 for p in couverture.values() if p >= 0.9),
            "repris_de_10_a_90pc": sum(1 for p in couverture.values() if 0.1 <= p < 0.9),
            "repris_a_moins_de_10pc": sum(1 for p in couverture.values() if p < 0.1),
            "issus_de_la_navette": len(navette),
            "rapports_exploites": len(rapports.get(dossier, [])),
            "ancres_par_un_rapport": len(ancres),
            "ancres_declares_en_entete": len(ancres_fort),
            "jeux_amendements": len(amendements.get(dossier, [])),
            "amendements_adoptes": adoptes,
            "rattaches_a_un_amendement": len(rattaches),
            "rattaches_parmi_la_navette": len(rattaches_navette),
            "rattachement_survivant_en_vigueur": len(survivants),
        })

    with sortie.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(lignes[0]))
        writer.writeheader()
        writer.writerows(lignes)

    total = sum(l["articles_eligibles"] for l in lignes)
    avec_initial = [l for l in lignes if l["texte_initial_disponible"]]
    n_initial = sum(l["articles_eligibles"] for l in avec_initial)
    gouv = sum(l["issus_du_texte_initial"] for l in avec_initial)
    navette = n_initial - gouv
    rattaches = sum(l["rattaches_parmi_la_navette"] for l in avec_initial)
    ancres = sum(l["ancres_par_un_rapport"] for l in lignes)

    print(f"dossiers                            : {len(lignes)}")
    print(f"articles éligibles                  : {total}")
    print(f"\nancrés par un commentaire de rapport : {ancres} ({100 * ancres / total:.1f} %)")
    print(f"  dont déclarés en en-tête           : {sum(l['ancres_declares_en_entete'] for l in lignes)}")
    print(f"\npartition, sur les {n_initial} articles dont le texte initial est disponible :")
    print(f"  issus du texte initial            : {gouv} ({100 * gouv / n_initial:.1f} %)")
    print(f"  issus de la navette               : {navette} ({100 * navette / n_initial:.1f} %)")
    if navette:
        print(f"\nC1 — rattachés à un amendement du Sénat : {rattaches} / {navette} "
              f"({100 * rattaches / navette:.1f} %)")
    print(f"  dont le texte subsiste en vigueur : "
          f"{sum(l['rattachement_survivant_en_vigueur'] for l in avec_initial)}")


if __name__ == "__main__":
    main()
