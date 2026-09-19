#!/usr/bin/env python3
"""Relève les dossiers législatifs de tout l'historique des articles en vigueur.

Les quatre plans de récupération — rapports, textes en discussion, études
d'impact, exposés des motifs — et l'extraction des rapports au Président
partaient tous de la même colonne du périmètre : `id_dole_origine`, le dossier
du texte qui a **créé** le prédécesseur de l'article, un seul saut. C'est une
convention de la phase 0, faite pour trouver *une* origine par article. Elle
disait autre chose au corpus : que les textes qui ont **modifié** l'article
depuis n'ont pas de dossier à télécharger.

Mesuré sur la base du 19 septembre 2026 : 95 dossiers d'origine, **188** dans
l'historique complet des articles en vigueur, **94 absents du corpus** — 61 lois,
33 ordonnances — touchant 451 articles en vigueur. Un article créé en 2014 et
réécrit en 2020 n'avait que le rapport de 2014 : ses alinéas de 2020 étaient
sans raison documentée, et le corpus le faisait passer pour un silence du fonds.

La liste se déduit de ce que la base déclare déjà : `produite_par` dit quel texte
a produit chaque version, `issu_de` dit le dossier de chaque texte, et
`renumerote_de` remonte aux numéros d'avant 2016. Elle est écrite dans un
fichier versionné, comme le périmètre, pour que les plans se rejouent sans la
base et que le diff dise quand elle bouge.

Usage :
    dossiers_du_perimetre.py <base.sqlite> <sortie.tsv>
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

COLONNES = ["id_dole", "nature", "legislature", "articles_en_vigueur", "textes",
            "titre"]

REQUETE = """
    WITH RECURSIVE asc_a(art, anc) AS (
        SELECT v.article_id, v.article_id FROM version_en_vigueur v
        UNION SELECT a.art, r.ancien_id FROM renumerote_de r JOIN asc_a a
        ON r.article_id = a.anc)
    SELECT i.dossier_id, d.legislature, d.titre,
           group_concat(DISTINCT t.nature)   AS natures,
           count(DISTINCT a.art)             AS articles,
           group_concat(DISTINCT t.id_jorf)  AS textes
    FROM asc_a a
    JOIN version_article v ON v.article_id = a.anc
    JOIN produite_par p    ON p.version_id = v.id_legi
    JOIN texte_normatif t  ON t.id_jorf = p.texte_id
    JOIN issu_de i         ON i.texte_id = t.id_jorf
    JOIN dossier d         ON d.id_dole = i.dossier_id
    GROUP BY i.dossier_id ORDER BY i.dossier_id"""


def dossiers(base: sqlite3.Connection) -> list[dict]:
    lignes = []
    for id_dole, legislature, titre, natures, articles, textes in base.execute(REQUETE):
        # Un dossier porte une loi ou une ordonnance, et parfois les deux — la loi
        # de ratification et l'ordonnance ratifiée. La nature « ordonnance » prime
        # pour l'extraction du rapport au Président, qui n'existe que pour elle.
        nature = "ordonnance" if "ordonnance" in natures.split(",") else natures
        lignes.append({"id_dole": id_dole, "nature": nature,
                       "legislature": legislature if legislature is not None else "",
                       "articles_en_vigueur": articles, "textes": textes,
                       "titre": titre})
    return lignes


def lire(chemin: Path) -> list[dict]:
    """Ce que les plans lisent : le fichier écrit ici."""
    with chemin.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    chemin_base, sortie = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(f"file:{chemin_base}?mode=ro", uri=True)
    lignes = dossiers(base)
    with sortie.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES, delimiter="\t",
                                  lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    print(f"dossiers de l'historique : {len(lignes)}")
    print(f"  ordonnances            : {sum(l['nature'] == 'ordonnance' for l in lignes)}")
    print(f"  articles en vigueur couverts : "
          f"{base.execute('SELECT count(*) FROM version_en_vigueur').fetchone()[0]}"
          f" au fonds, {max((l['articles_en_vigueur'] for l in lignes), default=0)}"
          f" au plus gros dossier")
    print(f"→ {sortie}")


if __name__ == "__main__":
    main()
