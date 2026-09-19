#!/usr/bin/env python3
"""Treizième tranche : rendre le verdict, y compris quand il est négatif.

Le § 4.3 de la feuille de route donne au produit un verdict explicite —
**`raison non documentée`** — et en fait « un résultat de premier ordre, pas un
échec ». Douze tranches plus tard, il n'était rendu nulle part. La restitution
affichait ce qu'elle savait et se taisait sur le reste, ce qui n'est pas la même
chose que le dire : un lecteur ne peut pas distinguer « nous n'avons pas cherché »
de « nous avons cherché partout et il n'y a rien ».

Le verdict retient le grain le plus fin disponible. Chaque voie est calculée sur
la chaîne qui lui est propre, et c'est ce qui fait la difficulté : un article en
vigueur n'est presque jamais rattaché sous son numéro d'aujourd'hui.

  `motive`      remonte les **ancêtres** de l'article (`renumerote_de`) : un
                rapport de 2013 nomme L. 121-105, jamais L. 224-65.
  `resulte_de`  remonte les **segments** dont l'alinéa est repris (`repris_de`) :
                l'amendement a écrit un alinéa d'une version antérieure.
  `porte_sur`   descend vers les **descendants** de l'article visé : le texte de
                2014 vise L. 121-42, devenu L. 224-43.

Trois directions différentes sur le même graphe. Les confondre — ou en oublier
une — donne un taux de silence faux, et ce taux est précisément ce que la tranche
publie.

Usage :
    verdict.py <base.sqlite>
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

# Les articles D et R n'ont ni exposé des motifs, ni débat, ni amendement. Leur
# silence est structurel ; celui d'un article L ne l'est pas.
PARTIES = ("L", "R", "D")
# Vingt et un articles en vigueur ne commencent pas par L, R ou D : vingt annexes
# — « Annexe à l'article R. 312-14 », qui relèvent de la partie de leur article
# d'accueil — et l'article liminaire, qui ouvre la partie législative. Une
# première version les écartait en silence ; ils sont rattachés.
ANNEXE = re.compile(r"^Annexe à l'article\s+([LRD])", re.I)


def partie_de(numero: str) -> str | None:
    if numero[:1] in PARTIES:
        return numero[:1]
    trouve = ANNEXE.match(numero)
    if trouve:
        return trouve.group(1).upper()
    return "L" if numero.strip().lower() == "liminaire" else None

VOIES = {
    # Un passage qui explique cet article : commentaire de rapport qui le nomme.
    "a_passage_motivant": """
        WITH RECURSIVE ascendance(cible, ancetre) AS (
            SELECT id, id FROM article
            UNION SELECT a.cible, r.ancien_id
            FROM renumerote_de r JOIN ascendance a ON r.article_id = a.ancetre)
        SELECT DISTINCT a.cible FROM ascendance a
        JOIN motive m ON m.article_id = a.ancetre""",
    # L'amendement qui a écrit l'alinéa, retrouvé par la continuité des segments.
    "a_amendement": """
        WITH RECURSIVE suite(origine, courant) AS (
            SELECT id, id FROM segment
            UNION SELECT s.origine, r.segment_source_id
            FROM repris_de r JOIN suite s ON r.segment_id = s.courant)
        SELECT DISTINCT v.article_id FROM version_article v
        JOIN segment g ON g.version_id = v.id_legi
        JOIN suite s ON s.origine = g.id
        JOIN resulte_de rd ON rd.segment_id = s.courant""",
    # Sous quel article de quel texte il a été discuté.
    "a_article_du_texte": """
        SELECT DISTINCT a.id FROM articles_du_texte x
        JOIN article_courant a ON a.numero = x.article""",
    # Un document qui motive le texte entier : exposé, étude d'impact, avis,
    # rapport au Président. Mais le texte doit avoir **écrit** le dispositif —
    # créé l'article à la racine de sa chaîne de renumérotation, ou modifié une
    # de ses versions — et non l'avoir seulement recodifié : la création d'un
    # numéro nouveau pour un article qui a des ancêtres est une renumérotation,
    # et son rapport au Président motive la refonte, pas ce que l'article dit.
    # Sans cette réserve, tout article de 1993 était « motivé » par le rapport de
    # la recodification de 2016, et « raison non documentée » n'avait plus de
    # sens (docs/39 § 3). Le verdict suit la définition que les annotateurs
    # appliquent.
    "a_document_du_texte": """
        WITH RECURSIVE ascendance(cible, ancetre) AS (
            SELECT id, id FROM article
            UNION SELECT a.cible, r.ancien_id
            FROM renumerote_de r JOIN ascendance a ON r.article_id = a.ancetre)
        SELECT DISTINCT a.cible FROM ascendance a
        JOIN version_article v ON v.article_id = a.ancetre
        JOIN produite_par p ON p.version_id = v.id_legi
        JOIN issu_de i ON i.texte_id = p.texte_id
        JOIN document d ON d.dossier_id = i.dossier_id
        WHERE p.type_lien IN ('MODIFIE', 'MODIFICATION', 'RECTIFICATION')
           OR (p.type_lien IN ('CREE', 'CREATION')
               AND NOT EXISTS (SELECT 1 FROM renumerote_de r WHERE r.article_id = a.ancetre))""",
    # Un acte de l'Union cité par l'article, ou transposé par son texte.
    "a_acte_ue": """
        SELECT DISTINCT a.id FROM union_par_article u
        JOIN article_courant a ON a.numero = u.article
        UNION
        SELECT DISTINCT v.article_id FROM version_article v
        JOIN produite_par p ON p.version_id = v.id_legi
        JOIN transpose t ON t.texte_id = p.texte_id""",
}


def classer(voies: dict[str, bool]) -> str:
    if voies["a_passage_motivant"] or voies["a_amendement"]:
        return "passage_motivant"
    if voies["a_article_du_texte"]:
        return "origine_situee"
    if voies["a_document_du_texte"] or voies["a_acte_ue"]:
        return "motivation_du_texte"
    return "raison_non_documentee"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    schema = Path(__file__).resolve().parent.parent / "schema" / "007-verdict.sql"
    base.executescript(schema.read_text(encoding="utf-8"))

    en_vigueur = {i: n for i, n in base.execute(
        "SELECT DISTINCT a.id, a.numero FROM article a "
        "JOIN version_en_vigueur v ON v.article_id = a.id")}
    atteints = {voie: {i for (i,) in base.execute(requete)}
                for voie, requete in VOIES.items()}

    lignes, hors_partie = [], 0
    for article_id, numero in en_vigueur.items():
        partie = partie_de(numero)
        if partie is None:
            hors_partie += 1
            continue
        voies = {voie: article_id in atteints[voie] for voie in VOIES}
        lignes.append((article_id, partie, classer(voies),
                       *(int(voies[voie]) for voie in VOIES)))

    base.executemany(
        "INSERT INTO verdict (article_id, partie, verdict, a_passage_motivant, "
        "a_amendement, a_article_du_texte, a_document_du_texte, a_acte_ue) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", lignes)
    base.commit()

    violations = base.execute("PRAGMA foreign_key_check").fetchall()
    print(f"articles en vigueur classés : {len(lignes)}"
          + (f"   ⚠ {hors_partie} non rattachés à une partie" if hors_partie else ""))
    print()
    print(f"{'partie':7}{'articles':>9}{'motivés':>9}{'situés':>8}"
          f"{'texte':>8}{'MUETS':>8}{'part muette':>13}")
    for partie, articles, motives, situes, texte, muets, part in base.execute(
            "SELECT * FROM hygiene_par_partie"):
        print(f"{partie:7}{articles:9}{motives:9}{situes:8}{texte:8}{muets:8}"
              f"{part:12.1f} %")
    total = base.execute(
        "SELECT count(*), sum(verdict = 'raison_non_documentee') FROM verdict").fetchone()
    print(f"{'total':7}{total[0]:9}{'':9}{'':8}{'':8}{total[1]:8}"
          f"{100 * total[1] / total[0]:12.1f} %")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
