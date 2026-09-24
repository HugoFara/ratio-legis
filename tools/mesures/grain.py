#!/usr/bin/env python3
"""Les deux tableaux du README, « au grain de l'article » et « au grain du texte ».

Ils étaient recopiés à la main dans le README depuis `docs/37`, et leurs
requêtes n'étaient écrites nulle part : quand `docs/50` a voulu les remettre à
jour, celle qu'on a reconstituée ne redonnait pas les chiffres publiés, et le
README a dû avouer des chiffres datés. Un chiffre qu'on ne sait plus recalculer
n'est plus une mesure.

**Les définitions sont celles du verdict.** Chaque ligne reprend la requête de
`ingestion/verdict.py` (`VOIES`) qui décide du verdict de l'article, et les
quatre premières lisent directement la table `verdict` : « un passage le
motive » veut dire ici exactement ce qu'il veut dire dans le verdict par
partie. Les lignes qui n'ont pas de voie dans le verdict — l'acte de l'Union
seulement cité, le considérant, la transposition, le renvoi entrant, le type
de document — ont leur requête ici, écrite une fois.

Le dénominateur est l'ensemble des articles en vigueur, c'est-à-dire des
articles qui ont un verdict.

Usage :
    grain.py <base.sqlite> <sortie.tsv>
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ingestion"))
from verdict import VOIES  # noqa: E402

# Le document qui motive le texte, par type : la requête du verdict, restreinte
# à un type par la jointure. « Rapport de commission » n'y est pas : il motive
# le texte au même titre, mais le README ne détaille que les quatre types qui
# viennent de l'auteur du texte ou du Conseil d'État.
TYPES = (
    ("par un rapport au Président", "rapport_president_republique"),
    ("par un exposé des motifs", "expose_des_motifs"),
    ("par une étude d'impact", "etude_impact"),
    ("par un avis du Conseil d'État", "avis_conseil_etat"),
)
PAR_TYPE = VOIES["a_document_du_texte"].replace(
    "JOIN document d ON d.dossier_id = i.dossier_id",
    "JOIN document d ON d.dossier_id = i.dossier_id AND d.type = ?")
assert PAR_TYPE != VOIES["a_document_du_texte"], "la requête du verdict a changé"

REQUETES = {
    # Un acte de l'Union que l'article en vigueur cite lui-même — non la
    # transposition, qui est au grain du texte.
    "acte_cite": "SELECT DISTINCT a.id FROM union_par_article u "
                 "JOIN article_courant a ON a.numero = u.article",
    # Un considérant de l'acte cité : le motif que l'Union écrit elle-même.
    "considerant": "SELECT DISTINCT a.id FROM motivation_europeenne m "
                   "JOIN article_courant a ON a.numero = m.article",
    # Une version de l'article produite par un texte qui déclare transposer.
    "transposition": "SELECT DISTINCT v.article_id FROM version_article v "
                     "JOIN produite_par p ON p.version_id = v.id_legi "
                     "JOIN transpose t ON t.texte_id = p.texte_id",
    # Rattaché à un article d'acte de l'Union par un tableau de concordance
    # (docs/54) : le numéro est celui du projet de loi, suivi par la chaîne de
    # renumérotation jusqu'à l'article d'aujourd'hui.
    "concordance": "WITH RECURSIVE s(id) AS (SELECT article_id FROM transpose_article "
                   "UNION SELECT r.article_id FROM renumerote_de r JOIN s ON r.ancien_id = s.id) "
                   "SELECT id FROM s",
    # Cité par un autre article en vigueur ; un article qui se cite lui-même
    # ne compte pas.
    "cite": "SELECT DISTINCT r.article_id FROM renvoie_a r "
            "JOIN segment s ON s.id = r.segment_id "
            "JOIN version_en_vigueur v ON v.id_legi = s.version_id "
            "WHERE v.article_id <> r.article_id",
}


def mesurer(base: sqlite3.Connection) -> list[tuple[str, str, int, int | None]]:
    """(tableau, ligne, nombre, dénominateur)."""
    en_vigueur = {a for (a,) in base.execute("SELECT article_id FROM verdict")}
    total = len(en_vigueur)

    def compte(requete: str, *parametres) -> int:
        return len(en_vigueur & {a for (a,) in base.execute(requete, parametres)})

    def colonne(nom: str) -> int:
        return base.execute(f"SELECT sum({nom}) FROM verdict").fetchone()[0]

    lignes = [
        ("article", "articles en vigueur", total, None),
        ("article", "remontant à un passage qui les motive",
         colonne("a_passage_motivant"), total),
        ("article", "reliés à un article de texte en discussion",
         colonne("a_article_du_texte"), total),
        ("article", "nommant un acte de l'Union", compte(REQUETES["acte_cite"]), total),
        ("article", "reliés à un article d'acte de l'Union par un tableau de concordance",
         compte(REQUETES["concordance"]), total),
        ("article", "remontant à un amendement identifié", colonne("a_amendement"), total),
        ("article", "cités par un autre article du fonds", compte(REQUETES["cite"]), total),
        ("texte", "atteignant un document motivant le texte",
         colonne("a_document_du_texte"), total),
    ]
    motives = colonne("a_document_du_texte")
    for libelle, type_document in TYPES:
        lignes.append(("texte", f"dont {libelle}", compte(PAR_TYPE, type_document), motives))
    lignes += [
        ("texte", "atteignant un considérant européen", compte(REQUETES["considerant"]), total),
        ("texte", "atteignant une transposition déclarée",
         compte(REQUETES["transposition"]), total),
    ]
    return lignes


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    chemin_base, sortie = Path(sys.argv[1]), Path(sys.argv[2])
    base = sqlite3.connect(f"file:{chemin_base}?mode=ro", uri=True)
    lignes = mesurer(base)
    base.close()

    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.writer(flux, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["grain", "mesure", "nombre", "sur", "pourcent"])
        for grain, mesure, nombre, sur in lignes:
            pourcent = f"{100 * nombre / sur:.1f}" if sur else ""
            ecrivain.writerow([grain, mesure, nombre, sur or "", pourcent])

    for grain, mesure, nombre, sur in lignes:
        part = f"  ({100 * nombre / sur:.1f} %)" if sur else ""
        print(f"{grain:8s} {mesure:48s} {nombre:6d}{part}")
    print(f"→ {sortie}")


if __name__ == "__main__":
    main()
