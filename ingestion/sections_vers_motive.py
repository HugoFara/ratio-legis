#!/usr/bin/env python3
"""Douzième tranche : convertir le gisement de sections écartées.

Onze tranches, et les deux arêtes qui répondent à « pourquoi cet article dit
*ceci* » couvraient moins de 5 % du code : `motive` 65 articles en vigueur,
`resulte_de` 41. Tout le reste répondait à « pourquoi ce texte existe ».

La cause n'était pas le manque de matière. Un rapport de commission commente
article par article, et le corpus en porte **6 427 sections** dont l'en-tête ne
déclare aucun article du code. Elles étaient jetées, faute de savoir de quel
article du code elles parlaient. La onzième tranche l'a appris : `porte_sur`
relie l'article du texte en discussion à l'article du code.

**Le piège est la renumérotation entre lectures**, et il est mesurable. Sur 240
couples (dossier, article du texte) présents dans plusieurs états du texte, **40
ont une intersection vide** : le même numéro d'article y désigne des articles du
code entièrement différents. C'est ce qui avait fait retirer le contrôle de
cohérence structurelle (`docs/11`), et c'est ici visible dans la donnée.

D'où la règle : **l'intersection sur au moins deux états**. Un couple présent
dans un seul état ne fournit aucun recoupement et n'est pas retenu — 173 couples
écartés à ce titre. Un couple dont les états se contredisent entièrement est
écarté aussi. Restent 200 couples, dont la cible est ce sur quoi tous les états
s'accordent.

Deux gardes indépendantes s'ajoutent : LEGI doit rattacher l'article au dossier,
et la section ne doit pas déjà porter une déclaration en en-tête — celle-là est
plus sûre, elle est traitée par `rapports_vers_motive.py`.

L'arête est posée sur l'article **tel que le texte le nomme**, jamais sur son
descendant : c'est la restitution qui remonte la chaîne de renumérotation, comme
pour toutes les autres. 137 articles historiques atteignent ainsi 436 articles en
vigueur.

Usage :
    sections_vers_motive.py <corpus/rapports/> <perimetre.csv> <plan.tsv>
                            <base.sqlite> [plan-impacts.tsv]
"""

from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "prototype"))
from commentaires_rapports import commentaires  # noqa: E402
from rapports_vers_motive import (  # noqa: E402
    fenetre_preuve, rattachements_legi, url_dossier, url_rapport_pr,
    urls_des_impacts, urls_du_plan)

ETATS_MINIMUM = 2        # sans recoupement entre deux états, aucune garantie


def cle_article(numero: str) -> str:
    """Forme canonique d'un numéro d'article de texte, pour le rapprochement.

    Les deux côtés écrivent le même article différemment — « 1 er », « 1er »,
    « 10 bis A », « 10 bis a ». Espaces retirés et casse abaissée, la clef est
    stable ; l'affichage garde la forme lue.
    """
    return re.sub(r"\s+", "", numero).lower()

# Précision mesurée à la main sur 20 arêtes tirées au sort : voir
# `docs/17-sections-appariees.md` § 4. Borne inférieure de Wilson à 95 %.
CONFIANCE = 0.8389


def cibles_par_article_du_texte(base: sqlite3.Connection) -> dict[tuple, set[int]]:
    """(dossier, article du texte) → articles du code sur lesquels les états s'accordent.

    L'intersection est la seule protection disponible contre la renumérotation
    entre lectures : elle ne retient que ce que tous les états du texte disent du
    même numéro d'article.
    """
    par_etat: dict[tuple, set[int]] = defaultdict(set)
    for dossier, article_du_texte, texte_id, article_id in base.execute(
            "SELECT t.dossier_id, p.article_du_texte, p.texte_id, p.article_id "
            "FROM porte_sur p JOIN texte_discute t ON t.id = p.texte_id "
            "WHERE p.portee = 'interne'"):
        par_etat[(dossier, cle_article(article_du_texte),
                  texte_id)].add(article_id)
    par_couple: dict[tuple, list[set[int]]] = defaultdict(list)
    for (dossier, article_du_texte, _), cibles in par_etat.items():
        par_couple[(dossier, article_du_texte)].append(cibles)

    retenues, compte = {}, defaultdict(int)
    for couple, etats in par_couple.items():
        if len(etats) < ETATS_MINIMUM:
            compte["un_seul_etat"] += 1
            continue
        commun = set.intersection(*etats)
        if not commun:
            compte["contradiction"] += 1
            continue
        compte["retenus"] += 1
        retenues[couple] = commun
    return retenues, compte


def main() -> None:
    if not 5 <= len(sys.argv) <= 6:
        sys.exit(__doc__)
    corpus, perimetre, plan, chemin_base = (Path(a) for a in sys.argv[1:5])
    plan_impacts = Path(sys.argv[5]) if len(sys.argv) == 6 else None
    base = sqlite3.connect(chemin_base)

    # Idempotence : la tranche ne possède que les arêtes dont la preuve porte sa
    # méthode. Les preuves sont effacées après les arêtes, sinon la clef
    # étrangère refuse — et elle a raison.
    base.execute("DELETE FROM motive WHERE preuve_id IN "
                 "(SELECT id FROM preuve WHERE methode = 'section_appariee')")
    base.execute("DELETE FROM preuve WHERE methode = 'section_appariee'")

    cibles, compte = cibles_par_article_du_texte(base)
    legi, titres, _ = rattachements_legi(perimetre)
    numeros = {i: n for n, i in base.execute("SELECT numero, id FROM article")}
    liens = urls_du_plan(plan) | urls_des_impacts(plan_impacts)
    documents = {url: (i, texte) for i, url, texte in base.execute(
        "SELECT id, url, texte FROM document WHERE type = 'rapport_commission'")}
    deja = {(d, a) for d, a in base.execute(
        "SELECT document_id, article_id FROM motive WHERE article_id IS NOT NULL")}

    suivant = (base.execute("SELECT COALESCE(MAX(id), 0) FROM preuve").fetchone()[0]) + 1
    aretes, preuves = [], []
    vus, examinees, sans_preuve = set(), 0, 0

    for fichier in sorted(corpus.iterdir()):
        if "__" not in fichier.name:
            continue
        if (fichier.parent / f"{fichier.stem}_mono.html").exists():
            continue          # page d'index paginée du Sénat : le sommaire, pas le texte
        url = (liens.get(fichier.name) or url_rapport_pr(fichier.name)
               or url_dossier(fichier.name))
        if url not in documents:
            continue
        document_id, texte = documents[url]
        dossier = fichier.name.split("__", 1)[0]
        try:
            sections = commentaires(fichier)
        except Exception:
            continue
        for section in sections:
            article_du_texte = section["article_du_texte"]
            if not article_du_texte or section["articles_declares"]:
                continue      # déclaré en en-tête : plus sûr, traité ailleurs
            examinees += 1
            commun = cibles.get((dossier, cle_article(str(article_du_texte))))
            if not commun:
                continue
            for article_id in sorted(commun):
                if dossier not in legi.get(numeros[article_id], ()):
                    compte["non_corrobore"] += 1
                    continue
                if (document_id, article_id) in deja | vus:
                    compte["deja_connu"] += 1
                    continue
                debut, fin = section["offset_debut"], section["offset_fin"]
                extrait = fenetre_preuve(texte, debut, min(fin, debut + 400))
                if extrait is None:
                    sans_preuve += 1
                    continue
                vus.add((document_id, article_id))
                preuves.append((suivant, "section_appariee", extrait, debut, None))
                aretes.append((document_id, article_id, str(article_du_texte),
                               debut, fin, "derivee", CONFIANCE, suivant))
                suivant += 1

    base.executemany(
        "INSERT INTO preuve (id, methode, fenetre, source_offset, cible_offset) "
        "VALUES (?, ?, ?, ?, ?)", preuves)
    base.executemany(
        "INSERT INTO motive (document_id, article_id, article_du_texte, "
        "offset_debut, offset_fin, methode, confiance, preuve_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", aretes)
    base.commit()

    violations = base.execute("PRAGMA foreign_key_check").fetchall()
    couverts = base.execute("""
        WITH RECURSIVE descendance(origine, courant) AS (
            SELECT id, id FROM article
            UNION SELECT d.origine, r.article_id
            FROM renumerote_de r JOIN descendance d ON r.ancien_id = d.courant)
        SELECT count(DISTINCT a.numero) FROM motive m
        JOIN descendance d ON d.origine = m.article_id
        JOIN article a ON a.id = d.courant
        JOIN version_article v ON v.article_id = a.id AND v.etat = 'VIGUEUR'
        """).fetchone()[0]

    print(f"couples (dossier, article du texte) exploitables : {compte['retenus']}")
    print(f"  écartés faute d'un second état : {compte['un_seul_etat']}")
    print(f"  écartés pour contradiction entre états : {compte['contradiction']}")
    print(f"\nsections sans déclaration examinées : {examinees}")
    print(f"arêtes motive ajoutées              : {len(aretes)}")
    print(f"  écartées, non corroborées par LEGI : {compte['non_corrobore']}")
    print(f"  déjà connues par la déclaration en en-tête : {compte['deja_connu']}")
    print(f"  écartées faute de preuve          : {sans_preuve}")
    print(f"\narticles en vigueur atteints par motive, chaîne comprise : {couverts}")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
