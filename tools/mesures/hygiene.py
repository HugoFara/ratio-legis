#!/usr/bin/env python3
"""Métriques d'hygiène législative, calculées sur le graphe.

Le § 7 de la feuille de route les annonce comme « le meilleur produit d'appel
médiatique du projet ». Elles ne demandent aucune source nouvelle : le graphe les
porte, il ne les comptait pas.

Trois précautions, sans lesquelles chacun de ces chiffres ment.

**Le silence de la partie réglementaire n'est pas celui de la partie
législative.** Un décret n'a ni exposé des motifs, ni débat, ni amendement : son
silence est structurel. Fondre les deux dans un taux unique donne 35 % de code
« non documenté », chiffre qui ne décrit rien. Séparés, ils disent deux choses
vraies et différentes.

**Un amendement sans objet publié n'est pas un amendement sans justification.**
Le taux brut est de 11,5 % au Sénat. Mais 1 515 des 2 338 objets manquants sont
ceux d'amendements « retirés avant séance » et 804 d'amendements irrecevables au
titre de l'article 40 : Améli ne publie pas l'objet de ce qui n'a pas été
défendu. Rapporté aux seuls amendements **adoptés**, le taux tombe à 0,3 %.

**L'origine apparente n'est pas l'origine réelle.** La recodification de 2016 fait
apparaître 78 % du code comme issu d'ordonnances. Remonter la chaîne de
renumérotation rétablit la loi dans l'ascendance de 84 % des articles. C'est la
thèse du projet, et c'est le seul chiffre de cette liste qui ait demandé onze
tranches de travail pour être calculable.

Usage :
    hygiene.py <base.sqlite> <perimetre.csv> <mesures.tsv>
"""

from __future__ import annotations

import csv
import datetime
import re
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "ingestion"))
from textes_des_amendements import ARTICLE_ADDITIONNEL  # noqa: E402

MOIS = {m: i + 1 for i, m in enumerate(
    "janvier février mars avril mai juin juillet août septembre octobre "
    "novembre décembre".split())}
DATE = re.compile(r"(\d{1,2})\s+(" + "|".join(MOIS) + r")\s+(\d{4})", re.I)


def mesures(base: sqlite3.Connection, perimetre: Path) -> list[tuple]:
    un = lambda s, *a: base.execute(s, a).fetchone()   # noqa: E731
    lignes: list[tuple] = []

    def ajouter(famille: str, mesure: str, valeur, sur=None, note=""):
        part = f"{100 * valeur / sur:.1f}" if sur else ""
        lignes.append((famille, mesure, valeur, sur or "", part, note))

    # 1. Le verdict, par partie du code.
    for partie, articles, motives, situes, texte, muets, part in base.execute(
            "SELECT * FROM hygiene_par_partie"):
        ajouter("verdict", f"partie {partie} — articles en vigueur", articles)
        ajouter("verdict", f"partie {partie} — un passage les motive", motives, articles)
        ajouter("verdict", f"partie {partie} — origine située seulement", situes, articles)
        ajouter("verdict", f"partie {partie} — motivation du texte seule", texte, articles)
        ajouter("verdict", f"partie {partie} — RAISON NON DOCUMENTÉE", muets, articles)

    # 2. Origine apparente et origine réelle.
    # `version_en_vigueur`, et non `version_article` : la mesure porte sur le
    # droit en vigueur, et son libellé le dit. Sur toutes les versions jamais
    # écrites, elle rendait 1 822 articles L d'origine ordonnantielle pour un
    # dénominateur de 1 293 — 140,9 %, ce qui aurait dû suffire à la faire
    # relire. Les deux natures se recouvrent encore un peu : treize versions en
    # vigueur portent deux textes producteurs de natures différentes, et un
    # article compté deux fois vaut mieux qu'un article attribué à tort.
    apparente = dict(base.execute(
        "SELECT t.nature, count(DISTINCT a.id) FROM version_en_vigueur v "
        "JOIN article a ON a.id = v.article_id AND a.numero LIKE 'L%' "
        "JOIN produite_par p ON p.version_id = v.id_legi "
        "JOIN texte_normatif t ON t.id_jorf = p.texte_id "
        "GROUP BY 1"))
    articles_l = un("SELECT count(*) FROM verdict WHERE partie = 'L'")[0]
    reelle = un("""
        WITH RECURSIVE ascendance(cible, ancetre) AS (
            SELECT a.id, a.id FROM article a
            JOIN version_en_vigueur v ON v.article_id = a.id
            UNION SELECT x.cible, r.ancien_id
            FROM renumerote_de r JOIN ascendance x ON r.article_id = x.ancetre)
        SELECT count(DISTINCT x.cible) FROM ascendance x
        JOIN version_article v ON v.article_id = x.ancetre
        JOIN produite_par p ON p.version_id = v.id_legi
        JOIN texte_normatif t ON t.id_jorf = p.texte_id
        JOIN article c ON c.id = x.cible
        WHERE c.numero LIKE 'L%' AND t.nature = 'loi'""")[0]
    ajouter("origine", "articles L dont la version en vigueur vient d'une ordonnance",
            apparente.get("ordonnance", 0), articles_l, "origine apparente")
    ajouter("origine", "articles L dont la version en vigueur vient d'une loi",
            apparente.get("loi", 0), articles_l, "origine apparente")
    ajouter("origine", "articles L ayant une loi dans leur ascendance",
            reelle, articles_l, "origine réelle, chaîne de renumérotation remontée")

    # 3. Amendements.
    for chambre, total, adoptes, sans_objet, adoptes_sans_objet in base.execute(
            "SELECT chambre, count(*), sum(sort = 'Adopté'), "
            "sum(objet IS NULL OR trim(objet) = ''), "
            "sum(sort = 'Adopté' AND (objet IS NULL OR trim(objet) = '')) "
            "FROM amendement GROUP BY chambre"):
        ajouter("amendements", f"{chambre} — déposés", total)
        ajouter("amendements", f"{chambre} — adoptés", adoptes, total)
        ajouter("amendements", f"{chambre} — sans objet publié", sans_objet, total,
                "surtout des amendements retirés avant séance ou irrecevables")
        ajouter("amendements", f"{chambre} — adoptés sans objet publié",
                adoptes_sans_objet, adoptes,
                "dispositif adopté sans justification publiée")

    # 3 bis. Le sort, famille par famille. Le décompte des irrecevabilités est le
    # seul motif d'échec dont la cause soit publiée : l'article 40 dit que
    # l'amendement coûtait de l'argent et n'a jamais été discuté, l'article 45
    # qu'il était hors sujet. Ce sont des chiffres d'hygiène au sens du § 7.
    for chambre, famille, nombre, via_etat in base.execute(
            "SELECT * FROM sort_par_chambre"):
        depose = un("SELECT count(*) FROM amendement WHERE chambre = ?", chambre)[0]
        ajouter("sort", f"{chambre} — {famille}", nombre, depose,
                "sort lu dans l'état procédural, la chambre n'en publie pas"
                if via_etat == nombre else "")
    for motif, nombre in base.execute(
            "SELECT coalesce(motif, '(non précisé)'), count(*) FROM sort_amendement "
            "WHERE famille = 'irrecevable' GROUP BY 1 ORDER BY 2 DESC"):
        ajouter("irrecevabilite", f"fondement — {motif}", nombre,
                un("SELECT count(*) FROM sort_amendement "
                   "WHERE famille = 'irrecevable'")[0])

    # 3 ter. Ce que le fonds sait dire d'un article quand on lui demande ce qui a
    # été tenté sur lui — et non plus seulement ce qui a abouti.
    tentatives, disputes = un(
        "SELECT count(*), count(DISTINCT t.article) FROM tentative_sur_article t "
        "JOIN article a ON a.numero = t.article "
        "JOIN version_en_vigueur v ON v.article_id = a.id")
    en_vigueur = un("SELECT count(*) FROM version_en_vigueur")[0]
    # La restitution réunit deux voies : la cible déclarée par le dispositif
    # (`vise`, ci-dessus) et l'alinéa effectivement écrit (`resulte_de`, remonté
    # par `repris_de`). Ne publier que la première ferait dire à la mesure autre
    # chose qu'à l'écran — voir `restitution/tentatives.py` et `docs/30` § 6.
    ecrits = un("""
        WITH RECURSIVE remonte(depart, courant) AS (
            SELECT s.id, s.id FROM segment s
            JOIN version_en_vigueur v ON v.id_legi = s.version_id
            UNION
            SELECT remonte.depart, r.segment_source_id FROM repris_de r
            JOIN remonte ON r.segment_id = remonte.courant)
        SELECT count(DISTINCT a.numero) FROM remonte
        JOIN resulte_de rd ON rd.segment_id = remonte.courant
        JOIN segment s ON s.id = remonte.depart
        JOIN version_article v ON v.id_legi = s.version_id
        JOIN article a ON a.id = v.article_id""")[0]
    reunis = un("""
        WITH RECURSIVE remonte(depart, courant) AS (
            SELECT s.id, s.id FROM segment s
            JOIN version_en_vigueur v ON v.id_legi = s.version_id
            UNION
            SELECT remonte.depart, r.segment_source_id FROM repris_de r
            JOIN remonte ON r.segment_id = remonte.courant)
        SELECT count(*) FROM (
            SELECT t.article AS numero FROM tentative_sur_article t
            JOIN article a ON a.numero = t.article
            JOIN version_en_vigueur v ON v.article_id = a.id
            UNION
            SELECT a.numero FROM remonte
            JOIN resulte_de rd ON rd.segment_id = remonte.courant
            JOIN segment s ON s.id = remonte.depart
            JOIN version_article v ON v.id_legi = s.version_id
            JOIN article a ON a.id = v.article_id
            UNION
            SELECT a.numero FROM depose_sur d
            JOIN article a ON a.id = d.article_id
            JOIN version_en_vigueur v ON v.article_id = a.id)""")[0]
    deposes = un("SELECT count(DISTINCT d.article_id) FROM depose_sur d "
                 "JOIN version_en_vigueur v ON v.article_id = d.article_id")[0]
    ajouter("tentatives", "articles en vigueur portant une tentative, les trois voies",
            reunis, en_vigueur, "cible déclarée, alinéa écrit ou subdivision déposée")
    ajouter("tentatives", "dont par la cible déclarée du dispositif", disputes, reunis)
    ajouter("tentatives", "dont par un alinéa écrit qui subsiste", ecrits, reunis)
    ajouter("tentatives", "dont par la subdivision déposée", deposes, reunis)
    ajouter("tentatives", "tentatives déclarées sur un article en vigueur", tentatives,
            note="voie de la cible déclarée seule ; le détail par sort suit")

    # 3 quater. La troisième voie : la correspondance des identifiants de texte.
    # Son résultat principal est négatif, et il se compte — voir `docs/31`.
    depots, arts_depot = un(
        "SELECT count(*), count(DISTINCT d.article_id) FROM depose_sur d "
        "JOIN version_en_vigueur v ON v.article_id = d.article_id")
    ajouter("depot", "amendements positionnés sur un article en vigueur", depots)
    ajouter("depot", "articles en vigueur atteints", arts_depot, en_vigueur)
    for chambre, jeux, total_jeux in base.execute(
        "SELECT t.chambre, count(*), (SELECT count(DISTINCT texte_discute) "
        "FROM amendement WHERE chambre = t.chambre) FROM texte_des_amendements t "
        "GROUP BY 1"):
        ajouter("depot", f"{chambre} — jeux d'amendements appariés à leur texte",
                jeux, total_jeux)
    plage, subdivisions = un(
        "SELECT sum(dans_la_plage), sum(subdivisions) FROM texte_des_amendements")
    ajouter("depot", "subdivisions tombant dans la plage d'articles du texte",
            plage, subdivisions, "contrôle de l'appariement ; un texte faux s'y "
            "verrait en premier")
    # La règle qui reconnaît un article additionnel est celle de l'ingestion, et
    # non une approximation en SQL : deux définitions du même fait donneraient
    # deux chiffres, et c'est celui-ci que `docs/31` § 5 publie.
    additionnels = sum(
        1 for (sub,) in base.execute(
            "SELECT a.subdivision FROM amendement a "
            "JOIN texte_des_amendements t ON t.chambre = a.chambre "
            "AND t.texte_corpus = a.texte_discute")
        if ARTICLE_ADDITIONNEL.search(sub or ""))
    ajouter("depot", "amendements portant sur un article additionnel", additionnels,
            note="ils ne visent aucun article existant du code : c'est le "
                 "plafond de la voie du dépôt")
    for famille, nombre in base.execute(
            "SELECT s.famille, count(*) FROM tentative_sur_article t "
            "JOIN sort_amendement s ON s.amendement_id = t.amendement_id "
            "JOIN article a ON a.numero = t.article "
            "JOIN version_en_vigueur v ON v.article_id = a.id "
            "GROUP BY 1 ORDER BY 2 DESC"):
        ajouter("tentatives", f"dont {famille}", nombre, tentatives)

    # 4. Durée de la navette, mesurée sur les dates des états du texte.
    par_dossier: dict[str, list[datetime.date]] = defaultdict(list)
    for dossier, stade in base.execute("SELECT dossier_id, stade FROM texte_discute"):
        trouve = DATE.search(stade)
        if trouve:
            par_dossier[dossier].append(datetime.date(
                int(trouve.group(3)), MOIS[trouve.group(2).lower()],
                int(trouve.group(1))))
    durees = [(max(d) - min(d)).days for d in par_dossier.values() if len(d) > 1]
    if durees:
        ajouter("navette", "dossiers ayant au moins deux états datés", len(durees))
        ajouter("navette", "durée médiane, en jours", round(statistics.median(durees)))
        ajouter("navette", "durée la plus courte, en jours", min(durees))
        ajouter("navette", "durée la plus longue, en jours", max(durees))

    # 5. Part de chaque chambre dans ce qui est traçable jusqu'à un amendement.
    traces = un("SELECT count(DISTINCT v.article_id) FROM version_article v "
                "JOIN segment s ON s.version_id = v.id_legi "
                "JOIN resulte_de r ON r.segment_id = s.id")[0]
    for chambre, n in base.execute(
            "SELECT am.chambre, count(DISTINCT rd.segment_id) FROM resulte_de rd "
            "JOIN amendement am ON am.id = rd.amendement_id GROUP BY 1"):
        ajouter("chambres", f"segments écrits par un amendement — {chambre}", n,
                note="dénominateur faible : voir docs/09")
    ajouter("chambres", "articles dont un alinéa est tracé jusqu'à un amendement",
            traces, note="sans remonter la chaîne des segments")

    # 6. Ce que le fonds documentaire contient.
    for type_document, n in base.execute(
            "SELECT type, count(*) FROM document GROUP BY 1 ORDER BY 1"):
        ajouter("sources", f"documents — {type_document}", n)
    ajouter("sources", "actes de l'Union", un("SELECT count(*) FROM acte_ue")[0])
    ajouter("sources", "considérants", un("SELECT count(*) FROM considerant")[0])
    ajouter("sources", "textes en discussion",
            un("SELECT count(*) FROM texte_discute")[0])

    # 7. Points de rupture : ce qu'une réforme déplace.
    for numero, n in base.execute(
            "SELECT article_cite, count(DISTINCT article_citant) c "
            "FROM renvois_entrants GROUP BY 1 ORDER BY c DESC LIMIT 5"):
        ajouter("renvois", f"articles citant {numero}", n)

    eligibles = sum(1 for l in csv.DictReader(perimetre.open(encoding="utf-8"))
                    if l["eligible_resulte_de"] == "1")
    ajouter("perimetre", "articles éligibles à resulte_de", eligibles)
    return lignes


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    chemin_base, perimetre, sortie = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(f"file:{chemin_base}?mode=ro", uri=True)
    if not base.execute("SELECT count(*) FROM sqlite_master "
                        "WHERE name = 'verdict'").fetchone()[0]:
        sys.exit("table `verdict` absente : lancer ingestion/verdict.py")
    lignes = mesures(base, perimetre)
    base.close()

    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.writer(flux, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["famille", "mesure", "valeur", "sur", "part_pourcent",
                           "note"])
        ecrivain.writerows(lignes)

    famille = None
    for f, mesure, valeur, sur, part, note in lignes:
        if f != famille:
            famille = f
            print(f"\n\033[1m{f.upper()}\033[0m")
        part = f"{part:>6} %" if part else " " * 8
        print(f"  {mesure:58s} {valeur:>7} {part}"
              + (f"   {note}" if note else ""))
    print(f"\n→ {sortie}")


if __name__ == "__main__":
    main()
