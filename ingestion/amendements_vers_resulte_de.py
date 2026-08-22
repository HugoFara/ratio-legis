#!/usr/bin/env python3
"""Quatrième tranche : les amendements, et l'arête `resulte_de`.

C'est l'arête critique du projet — celle qui relie un alinéa du code à
l'amendement qui l'a écrit, avec son auteur et son sort.

**Pourquoi elle devient possible seulement maintenant.** La phase 0 avait établi
qu'aucun des 307 articles issus de la loi de 2014 n'a plus cette loi comme texte
producteur de sa version en vigueur : attachée à l'article, l'arête est vide par
construction sur un corpus recodifié. La solution est le grain du segment. On
n'apparie pas l'amendement au texte d'aujourd'hui — on l'apparie au segment de la
**version que sa propre loi a produite**, et l'arête `repris_de` de la première
tranche porte le lien jusqu'à l'article en vigueur. La chaîne se lit :

    article en vigueur --repris_de*--> segment historique --resulte_de--> amendement

Cette restriction n'est pas qu'une commodité : elle supprime par construction la
confusion inter-dossiers qui avait produit 9 faux rattachements sur 10 dans la
première version du golden set. Un amendement ne peut plus s'accrocher à un
article d'une autre loi, puisque les candidats sont les segments des versions que
sa loi a produites.

Deux garde-fous conservés de la phase 0 :

- **discriminance** : une fenêtre retrouvée dans plusieurs numéros d'articles ne
  prouve rien — sauf si ces numéros désignent le même article de part et d'autre
  d'une renumérotation, ce que `renumerote_de` sait dire. La phase 0 tolérait deux
  numéros au motif que 84 % des cas à deux numéros étaient de cette nature ; la
  condition est ici vérifiée au lieu d'être supposée ;
- **balayage au pas de 1 d'un côté au moins** : indexer les deux côtés à pas fixe
  fait tomber le rattachement de 29 % à 5 % sans qu'aucune donnée ne change.

Seuls les amendements adoptés produisent une arête : un amendement rejeté n'a
écrit aucun texte. Il est chargé comme nœud et reste interrogeable — c'est même
le corpus le plus intéressant pour le législateur, mais ce n'est pas de la
provenance.

Usage :
    amendements_vers_resulte_de.py <corpus/ameli> <base.sqlite>
"""

from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "prototype"))
from resolveur import (FENETRE, fenetres, lire_ameli,  # noqa: E402
                       normalise, sans_balises)

# Un dispositif d'amendement cite entre guillemets deux choses opposées : le texte
# qu'il insère, et celui qu'il abroge ou remplace. `passages_cites` de la phase 0
# les confondait, ce qui rattachait l'amendement à la rédaction qu'il faisait
# disparaître — sur sept arêtes vérifiées à la main, deux faux et un douteux
# venaient de là. Le sens se lit dans ce qui suit le guillemet fermant, jamais
# dans ce qui le précède : « les mots : X sont remplacés par les mots : Y »
# introduit l'ancien et le nouveau de la même façon.
ARTICLE_CITE = re.compile(r"\b([LRD])\.?\s?(\d{3})-(\d{1,3})(?:-(\d{1,3}))?")

SORTANT = re.compile(
    r"\s*[,;]?\s*(?:sont|est|seront|sera)\s+(?:remplac|supprim|abrog|ins[ée]r)"
    r"|\s*[,;]\s*(?:il est|ins[ée]rer|ajouter|r[ée]diger)", re.I)


def passages_inseres(dispositif: str) -> list[str]:
    """Passages que l'amendement introduit, à l'exclusion de ceux qu'il retire.

    Un passage suivi de « sont remplacés », « est supprimé » ou « il est inséré »
    n'est pas du texte nouveau : c'est la rédaction visée, ou un simple repère de
    position dans l'article.
    """
    texte = sans_balises(dispositif)
    gardes = []
    for m in re.finditer(r"«(.+?)»", texte, re.S):
        if SORTANT.match(texte[m.end():m.end() + 60]):
            continue
        if len(norme := normalise(m.group(1))) >= FENETRE:
            gardes.append(norme)
    return gardes

# Précision mesurée à la main sur 26 arêtes tirées au sort — 14 au Sénat, 12 à
# l'Assemblée : 23/26. Borne
# inférieure de Wilson à 95 %. C'est la plus faible confiance du graphe, et elle
# doit le rester tant que l'échantillon est de cette taille — voir
# `docs/09-tranche-amendements.md` § 4.
CONFIANCE = 0.7102


def charger_amendements(base: sqlite3.Connection, racine: Path) -> dict:
    dossiers = {d for (d,) in base.execute("SELECT id_dole FROM dossier")}
    # Les identifiants sont attribués à la suite de ceux déjà en base : la tranche
    # Assemblée peut avoir été chargée avant celle-ci.
    suivant = base.execute("SELECT coalesce(max(id), 0) + 1 FROM acteur").fetchone()[0]
    acteurs: dict[tuple[str, str], int] = {
        (nom, groupe or ""): identifiant
        for identifiant, nom, groupe in base.execute("SELECT id, nom, groupe FROM acteur")}
    deja = set(acteurs.values())
    lignes, ignores = [], 0

    for fichier in sorted(racine.iterdir()):
        if "__" not in fichier.name:
            continue
        dossier, texte_discute = fichier.name.split("__", 1)
        if dossier not in dossiers:
            ignores += 1
            continue
        try:
            jeu = lire_ameli(fichier)
        except Exception:
            ignores += 1
            continue
        for a in jeu:
            nom = sans_balises(a.get("Auteur", "")) or "(inconnu)"
            groupe = sans_balises(a.get("Au nom de", "")) or None
            if (nom, groupe or "") not in acteurs:
                acteurs[(nom, groupe or "")] = suivant
                suivant += 1
            auteur = acteurs[(nom, groupe or "")]
            lignes.append((dossier, "senat", texte_discute, a.get("Numéro", ""),
                           auteur, a.get("Sort") or None,
                           sans_balises(a.get("Subdivision", "")) or None,
                           sans_balises(a.get("Objet", "")) or None,
                           sans_balises(a.get("Dispositif", "")) or None,
                           a.get("Url amendement") or None))

    base.executemany("INSERT INTO acteur (id, nom, groupe) VALUES (?, ?, ?)",
                     [(i, nom, groupe or None) for (nom, groupe), i in acteurs.items()
                      if i not in deja])
    base.executemany(
        "INSERT OR IGNORE INTO amendement (dossier_id, chambre, texte_discute, numero,"
        " auteur_id, sort, subdivision, objet, dispositif, url)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", lignes)
    return {"acteurs": len(acteurs), "amendements": len(lignes), "fichiers_ignores": ignores}


def articles_nommes(dispositif: str) -> set[str]:
    """Numéros d'articles que le dispositif désigne explicitement.

    Un dispositif d'amendement modifie souvent plusieurs articles dans le même
    texte, avec des rédactions voisines : « L'article L. 215-2-4 est ainsi rédigé :
    "Les agents mentionnés à l'article L. 215-1…" », suivi d'un paragraphe presque
    identique pour L. 215-2-2. L'appariement textuel seul confond les deux. Quand
    le rédacteur nomme sa cible, sa déclaration prime.
    """
    texte = sans_balises(dispositif)
    return {f"{m.group(1)}{m.group(2)}-{m.group(3)}"
            + (f"-{m.group(4)}" if m.group(4) else "")
            for m in ARTICLE_CITE.finditer(texte)}


def construire_resulte_de(base: sqlite3.Connection) -> dict:
    """Apparie chaque amendement adopté aux segments que sa propre loi a produits."""
    # Les arêtes sont reconstruites, non complétées : sans cet effacement, une
    # exécution ultérieure laisse en base des arêtes portant l'ancienne confiance,
    # que `INSERT OR IGNORE` refuse de remplacer. Le graphe affichait ainsi
    # 0,685 là où le code disait 0,710.
    base.execute("DELETE FROM preuve WHERE methode = 'appariement_exact' AND id IN "
                 "(SELECT preuve_id FROM resulte_de WHERE preuve_id IS NOT NULL)")
    base.execute("DELETE FROM resulte_de")
    prochaine_preuve = base.execute(
        "SELECT coalesce(max(id), 0) + 1 FROM preuve").fetchone()[0]

    # Segments candidats, par dossier : ceux des versions d'articles produites par
    # un texte lui-même issu de ce dossier.
    candidats: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for dossier, segment_id, numero, texte in base.execute("""
            SELECT i.dossier_id, s.id, a.numero, s.texte
            FROM issu_de i
            JOIN produite_par p ON p.texte_id = i.texte_id
            JOIN version_article v ON v.id_legi = p.version_id
            JOIN article a ON a.id = v.article_id
            JOIN segment s ON s.version_id = v.id_legi"""):
        candidats[dossier].append((segment_id, numero, texte))

    # Classes de renumérotation : deux numéros d'articles reliés par une
    # recodification désignent la même disposition, et une fenêtre commune aux
    # deux n'est pas ambiguë.
    racine: dict[str, str] = {}

    def chercher(n: str) -> str:
        while racine.get(n, n) != n:
            n = racine[n]
        return n

    for cible, ancien in base.execute("""
            SELECT c.numero, a.numero FROM renumerote_de r
            JOIN article c ON c.id = r.article_id JOIN article a ON a.id = r.ancien_id"""):
        rc, ra = chercher(cible), chercher(ancien)
        if rc != ra:
            racine[rc] = ra

    aretes, preuves = [], []
    compte: dict[str, int] = defaultdict(int)
    for dossier, segments in candidats.items():
        # Index construit au pas de 1 : c'est le côté dont les offsets doivent être
        # indépendants de ceux de l'autre.
        index: dict[str, set[str]] = defaultdict(set)
        numero_du_segment = {}
        for segment_id, numero, texte in segments:
            numero_du_segment[segment_id] = numero
            propre = normalise(texte)
            for depart in range(0, max(1, len(propre) - FENETRE + 1)):
                index[propre[depart:depart + FENETRE]].add(segment_id)

        connus = set(numero_du_segment.values())
        for amendement_id, dispositif in base.execute(
                "SELECT id, dispositif FROM amendement "
                "WHERE dossier_id = ? AND sort = 'Adopté' AND dispositif IS NOT NULL",
                (dossier,)):
            # Cibles déclarées, ramenées à leurs classes de renumérotation. Un
            # dispositif qui ne nomme aucun article de ce code — il crée alors des
            # articles dont le numéro n'est pas encore fixé — n'impose rien.
            nommes = {chercher(n) for n in articles_nommes(dispositif or "")
                      if n in connus}
            touches: dict[str, tuple[str, int]] = {}
            for passage in passages_inseres(dispositif or ""):
                for position, fenetre in enumerate(fenetres(passage, pas=10)):
                    vises = index.get(fenetre)
                    if not vises:
                        continue
                    # La discriminance se mesure sur les numéros d'articles, non
                    # sur les segments : un même alinéa figure dans plusieurs
                    # versions du même article, ce qui n'est pas de l'ambiguïté.
                    numeros = {numero_du_segment[s] for s in vises}
                    if len({chercher(n) for n in numeros}) > 1:
                        compte["fenetres_non_discriminantes"] += 1
                        continue
                    if nommes and chercher(next(iter(numeros))) not in nommes:
                        compte["cible_non_declaree"] += 1
                        continue
                    for segment_id in vises:
                        touches.setdefault(segment_id, (fenetre, position * 10))
            for segment_id, (fenetre, offset) in touches.items():
                preuves.append((prochaine_preuve, "appariement_exact", fenetre, offset))
                aretes.append((segment_id, amendement_id, "derivee", CONFIANCE,
                               prochaine_preuve))
                prochaine_preuve += 1

    base.executemany(
        "INSERT INTO preuve (id, methode, fenetre, source_offset) VALUES (?, ?, ?, ?)",
        preuves)
    base.executemany(
        "INSERT OR IGNORE INTO resulte_de (segment_id, amendement_id, methode,"
        " confiance, preuve_id) VALUES (?, ?, ?, ?, ?)", aretes)
    compte["aretes"] = len(aretes)
    return compte


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    racine, base = Path(sys.argv[1]), sqlite3.connect(Path(sys.argv[2]))
    base.execute("PRAGMA foreign_keys = ON")

    noeuds = charger_amendements(base, racine)
    aretes = construire_resulte_de(base)
    base.commit()

    sorts = base.execute(
        "SELECT sort, count(*) FROM amendement GROUP BY sort ORDER BY 2 DESC LIMIT 4"
    ).fetchall()
    segments, amendements = base.execute(
        "SELECT count(DISTINCT segment_id), count(DISTINCT amendement_id) "
        "FROM resulte_de").fetchone()
    atteints = base.execute("""
        WITH RECURSIVE remonte(depart, courant) AS (
            SELECT s.id, s.id FROM segment s
            JOIN version_article v ON v.id_legi = s.version_id WHERE v.etat = 'VIGUEUR'
            UNION
            SELECT remonte.depart, r.segment_source_id
            FROM repris_de r JOIN remonte ON r.segment_id = remonte.courant)
        SELECT count(DISTINCT a.numero)
        FROM remonte JOIN resulte_de rd ON rd.segment_id = remonte.courant
        JOIN segment s ON s.id = remonte.depart
        JOIN version_article v ON v.id_legi = s.version_id
        JOIN article a ON a.id = v.article_id""").fetchone()[0]
    violations = base.execute("PRAGMA foreign_key_check").fetchall()

    print(f"acteurs                    : {noeuds['acteurs']}")
    print(f"amendements chargés        : {noeuds['amendements']}")
    print(f"  jeux ignorés (hors périmètre) : {noeuds['fichiers_ignores']}")
    for sort, n in sorts:
        print(f"    {sort or '(vide)':22s} {n}")
    print(f"\narêtes resulte_de          : {aretes['aretes']}")
    print(f"  segments touchés         : {segments}")
    print(f"  amendements rattachés    : {amendements}")
    print(f"  fenêtres écartées, non discriminantes : "
          f"{aretes['fenetres_non_discriminantes']}")
    print(f"  fenêtres écartées, cible non déclarée  : "
          f"{aretes['cible_non_declaree']}")
    print(f"\narticles en vigueur remontant à un amendement : {atteints}")
    print(f"intégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
