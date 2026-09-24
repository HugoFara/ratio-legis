#!/usr/bin/env python3
"""La fiche des arêtes `transpose_article`, et son bilan.

L'arête affirme que **l'article A du code transpose la disposition de l'acte
de l'Union** que la ligne nomme — parce que le tableau de concordance de
l'étude d'impact les met en face. Deux choses peuvent la rendre fausse : une
lecture du tableau qui apparie deux cellules de lignes différentes, et une
résolution du numéro écrit vers un autre article que celui que le projet de
loi désignait. La fiche donne de quoi vérifier l'une et l'autre : la ligne
lue, la page du PDF, l'article du code dans la version que la loi du dossier a
écrite, l'intitulé de l'article de l'acte.

Population petite : tirée en entier, dans l'ordre d'une clef SHA-256.

Usage :
    precision_concordances.py <base.sqlite> <fiche.tsv> [effectif]
    precision_concordances.py --bilan <fiche.tsv>
"""

from __future__ import annotations

import csv
import hashlib
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precision_porte_sur import etat_pour_le_juge, wilson  # noqa: E402

COLONNES = ["verdict", "cle", "celex", "article_acte", "paragraphe", "intitule_acte",
            "article", "numero_ecrit", "dossier", "pdf", "page", "ligne",
            "article_du_fonds", "url_acte"]


def echantillon(base: sqlite3.Connection, effectif: int) -> list[dict]:
    lignes = []
    for (celex, article_acte, paragraphe, intitule, url_acte, article, article_id,
         ecrit, dossier, page, ligne) in base.execute("""
            SELECT t.celex, t.article_acte, t.paragraphe, u.intitule, u.url,
                   a.numero, t.article_id, t.numero_ecrit, d.dossier_id, t.page, p.fenetre
            FROM transpose_article t
            JOIN article a ON a.id = t.article_id
            JOIN document d ON d.id = t.document_id
            JOIN preuve p ON p.id = t.preuve_id
            LEFT JOIN article_acte_ue u ON u.celex = t.celex AND u.numero = t.article_acte"""):
        lignes.append({
            "verdict": "", "cle": hashlib.sha256(
                f"{celex}|{article_acte}|{paragraphe}|{article}".encode()).hexdigest()[:16],
            "celex": celex, "article_acte": article_acte, "paragraphe": paragraphe,
            "intitule_acte": intitule or "", "article": article, "numero_ecrit": ecrit,
            "dossier": dossier, "pdf": f"travail/corpus/impacts/{dossier}__etude-impact-1.pdf",
            "page": str(page), "ligne": ligne,
            "article_du_fonds": etat_pour_le_juge(base, article_id, dossier),
            "url_acte": url_acte or ""})
    lignes.sort(key=lambda l: l["cle"])
    return lignes[:effectif]


def bilan(fiche: Path) -> None:
    lignes = list(csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t"))
    examinees = [l for l in lignes if l["verdict"]]
    justes = sum(l["verdict"] == "juste" for l in examinees)
    print(f"arêtes examinées   : {len(examinees)}")
    print(f"  justes           : {justes}")
    print(f"  fausses          : {sum(l['verdict'] == 'faux' for l in examinees)}")
    print(f"  douteuses        : {sum(l['verdict'] == 'douteux' for l in examinees)}")
    if examinees:
        print(f"précision ponctuelle : {justes / len(examinees):.3f}")
        print(f"borne de Wilson 95 % : {wilson(justes, len(examinees)):.4f}")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--bilan":
        return bilan(Path(sys.argv[2]))
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    effectif = int(sys.argv[3]) if len(sys.argv) == 4 else 10_000
    lignes = echantillon(base, effectif)
    with Path(sys.argv[2]).open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.DictWriter(flux, fieldnames=COLONNES, delimiter="\t",
                                  lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    print(f"{len(lignes)} arêtes tirées → {sys.argv[2]}")


if __name__ == "__main__":
    main()
