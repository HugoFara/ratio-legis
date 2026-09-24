#!/usr/bin/env python3
"""Les tableaux de concordance des études d'impact : l'article de la directive,
l'article du code qui le transpose.

**Le seul chemin connu vers l'Union au grain de l'article.** `transpose` relie
un texte à la directive qu'il déclare transposer ; `cite_acte_ue` relève l'acte
qu'un article nomme lui-même, ce que fait une minorité d'articles. Ce que la loi
consommation a fait de l'article 6 de la directive 2011/83/UE — c'est L. 121-17 —
n'est écrit ni dans la loi ni dans le code. Il l'est dans l'annexe 4 de son
étude d'impact, que le Gouvernement dresse en tableau : une ligne par
disposition de la directive, en face l'article du code.

**Lire le tableau, non le texte.** L'extraction du PDF en texte aplatit les
colonnes : les articles de la directive, puis ceux du code, sans les lignes qui
les appariaient. On relit donc la page avec la position de chaque bloc. Une
ligne du tableau commence à l'ancre d'un article de l'acte (« Art.2-7) »,
« Article 2 §1 ») dans la colonne de l'acte, et court jusqu'à l'ancre suivante ;
les articles du code écrits **en tête** d'une cellule de cette ligne sont ceux
que le tableau met en face. Les numéros cités dans le corps des cellules — une
citation du droit existant, un commentaire — ne le sont pas.

Deux mises en page cohabitent : le tableau tourné d'un quart de tour (2013),
où la ligne se lit en abscisse, et le tableau droit (2024), où elle se lit en
ordonnée. Le sens des lignes de texte, que le PDF porte, dit lequel.

**Notre code, et lui seul.** Un tableau de transposition mêle les codes : la
directive 2020/1828 est transposée dans le code de la consommation, le code de
justice administrative et le code de la santé publique. Un numéro est retenu
quand sa cellule nomme le code de la consommation, ou quand l'en-tête de la
colonne le nomme et que la cellule n'en nomme pas un autre.

**Les numéros sont ceux du projet de loi**, et l'étude d'impact de la loi
consommation le dit en note : ils se résolvent à la date du dossier
(`lignees.Resolveur`), non dans le code d'aujourd'hui.

Usage :
    concordances.py <corpus/impacts/> <plan-impacts.tsv> <base.sqlite>
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lignees import Resolveur  # noqa: E402
from rapports_vers_motive import urls_des_impacts  # noqa: E402

# Mesurée sur la population entière, 33 arêtes, deux juges Sonnet 5 qui ont
# relu chaque ligne sur la page : 33 sur 33, Wilson 0,8957 (docs/54 § 3).
CONFIANCE = 0.8957

TITRE = re.compile(r"tableau\s+de\s+(?:concordance|transposition)", re.I)
ACTE = re.compile(r"(directive|règlement)\s+(?:\(UE\)\s*)?(?:n°\s*)?"
                  r"(?:(\d{4})/(\d{1,4})|(\d{1,4})/(\d{4}))", re.I)
ANNEXE = re.compile(r"^\s*(?:\d+\s+)?ANNEXE\b", re.I | re.M)
# L'article de l'acte en tête de sa cellule : « Art.2-7) », « Article 2 §1 »,
# « Article 5 (1) », « Art. 9 ». Pas de lettre avant le nombre — ce serait un
# article de code.
ART_ACTE = re.compile(r"^\s*(?:\s*)?Art(?:icle)?\.?\s*(\d{1,3})"
                      r"(?:\s*(?:[-§(.]|point)\s*(\d{1,3}))?(?![\d-])", re.I | re.M)
ART_CODE = re.compile(r"\b([LRD])\.?\s?(\d{3})[-‑–](\d{1,3})(?:[-‑–](\d{1,3}))?"
                      r"(?:[-‑–](\d{1,3}))?(?![\d‑–-])")
# La tête d'une cellule qui ouvre sur un article du code : « • Art. L. 121-16 1° »,
# « Articles L. 623-1 et L.621-7 du code de la consommation ». Une citation
# (« « Art. L. 321-13. – … ») n'en est pas une.
TETE = re.compile(r"^[^\w«“\"]*(?:Art(?:icles?|\.)?\s*)?[LRD]\.?\s?\d{3}[-‑–]\d", re.I)
CONSO = re.compile(r"code\s+de\s+la\s+consommation|C\.\s?conso", re.I)
AUTRE_CODE = re.compile(
    r"\bcode\s+(?!de\s+la\s+consommation)(?:de|des|du|d['’]|g[ée]n[ée]ral|mon[ée]taire"
    r"|rural|civil|p[ée]nal)|\b(?:CJA|CSP|CMF|CGI|CPC)\b", re.I)
MEME_LIGNE = 8        # tolérance, en points, entre une ancre et le haut de sa ligne
MEME_COLONNE = 30     # tolérance, en points, pour dire deux blocs dans la même colonne


def numero(m: re.Match) -> str:
    return f"{m.group(1)}{m.group(2)}-{m.group(3)}" + "".join(
        f"-{g}" for g in m.groups()[3:5] if g)


def blocs(page: fitz.Page) -> list[tuple[float, float, str]]:
    """(ligne, colonne, texte) de chaque bloc, dans le repère du tableau : la
    ligne est l'ordonnée d'un texte droit, l'abscisse d'un texte tourné."""
    sortie = []
    for bloc in page.get_text("dict")["blocks"]:
        if bloc.get("type") != 0 or not bloc["lines"]:
            continue
        dx, dy = bloc["lines"][0]["dir"]
        x0, y0, _, y1 = bloc["bbox"]
        texte = "\n".join("".join(s["text"] for s in l["spans"]) for l in bloc["lines"])
        sortie.append((y0, x0, texte) if abs(dx) >= abs(dy) else (x0, -y1, texte))
    return sorted(sortie)


def celex(m: re.Match) -> str:
    annee, rang = (m.group(2), m.group(3)) if m.group(2) else (m.group(5), m.group(4))
    return f"3{annee}{'L' if m.group(1).lower().startswith('directive') else 'R'}{int(rang):04d}"


def lignes_du_tableau(chemin: Path, actes: set[str]):
    """(page, celex, article, paragraphe, numéro écrit, ligne de preuve) pour
    chaque article de notre code qu'un tableau met en face d'un article d'acte."""
    document = fitz.open(chemin)
    en_cours, entete_conso = None, False
    for rang in range(len(document)):
        page = document[rang]
        haut = page.get_text()[:500]
        titre = TITRE.search(haut)
        if not titre and ANNEXE.search(haut):
            en_cours = None                    # l'annexe suivante n'est pas un tableau
        if titre:
            acte = ACTE.search(haut[max(0, titre.start() - 250):titre.end() + 250])
            if acte:
                en_cours, entete_conso = celex(acte), False
        if en_cours not in actes:
            continue
        contenu = blocs(page)
        # L'en-tête de colonne qui nomme notre code vaut pour tout le tableau.
        entete_conso = entete_conso or any(CONSO.search(t) and len(t) < 120
                                           for _, _, t in contenu[:15])
        ancres = [(l, c, m) for l, c, t in contenu for m in [ART_ACTE.search(t)]
                  if m and not ART_CODE.search(t[:m.end() + 3])]
        if not ancres:
            continue
        colonne_acte = min(c for _, c, _ in ancres)
        ancres = [(l, m) for l, c, m in ancres if abs(c - colonne_acte) < MEME_COLONNE]
        for i, (debut, ancre) in enumerate(ancres):
            fin = ancres[i + 1][0] if i + 1 < len(ancres) else float("inf")
            for l, c, texte in contenu:
                if not (debut - MEME_LIGNE <= l < fin - MEME_LIGNE) \
                        or abs(c - colonne_acte) < MEME_COLONNE or not TETE.match(texte):
                    continue
                # La puce « • » occupe parfois sa propre ligne : la tête est la
                # première ligne qui porte un mot.
                lignes = texte.split("\n")
                while lignes and not re.search(r"\w", lignes[0]):
                    lignes.pop(0)
                tete = lignes[0] if lignes else ""
                cellule = texte[:texte.find(tete) + len(tete) + 120]
                if not (CONSO.search(cellule)
                        or (entete_conso and not AUTRE_CODE.search(cellule))):
                    continue
                for m in ART_CODE.finditer(tete):
                    yield (rang + 1, en_cours, ancre.group(1), ancre.group(2) or "",
                           numero(m), " ".join(f"{ancre.group(0)} — {tete}".split()))


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    corpus, plan, chemin_base = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(chemin_base)
    schema = Path(__file__).resolve().parent.parent / "schema" / "012-concordances.sql"
    base.executescript(schema.read_text(encoding="utf-8"))
    anciennes = [i for (i,) in base.execute(
        "SELECT preuve_id FROM transpose_article WHERE preuve_id IS NOT NULL")]
    base.execute("DELETE FROM transpose_article")
    base.executemany("DELETE FROM preuve WHERE id = ?", [(i,) for i in anciennes])

    actes = {c for (c,) in base.execute("SELECT celex FROM acte_ue")}
    # L'article de l'acte doit exister dans l'acte : « Article 3 1) » lu « 31 »
    # dans un tableau de la directive 2020/1828, qui en compte 26.
    articles_actes = set(base.execute("SELECT celex, numero FROM article_acte_ue"))
    denomination = dict(base.execute("SELECT celex, denomination FROM acte_ue"))
    documents = dict(base.execute("SELECT url, id FROM document WHERE type = 'etude_impact'"))
    liens = urls_des_impacts(plan)
    resolveur = Resolveur(base)
    compte = {"lignes": 0, "article_d_acte_inconnu": 0, "non_resolues": 0,
              "document_absent": 0, "aretes": 0}
    for fichier in sorted(corpus.glob("*__etude-impact-*.pdf")):
        dossier = fichier.name.split("__")[0]
        document_id = documents.get(liens.get(fichier.with_suffix(".txt").name, ""))
        for page, acte, article, paragraphe, ecrit, ligne in lignes_du_tableau(fichier, actes):
            compte["lignes"] += 1
            if (acte, article) not in articles_actes:
                compte["article_d_acte_inconnu"] += 1
                continue
            if document_id is None:
                compte["document_absent"] += 1
                continue
            article_id = resolveur.du_dossier(ecrit, dossier)
            if article_id is None:
                compte["non_resolues"] += 1
                continue
            fenetre = (f"Tableau de concordance de l'étude d'impact, page {page} : "
                       f"{denomination[acte]}, {ligne}")
            preuve = base.execute(
                "INSERT INTO preuve (methode, fenetre, source_offset) VALUES "
                "('tableau_de_concordance', ?, ?)", (fenetre, page)).lastrowid
            avant = base.total_changes
            base.execute(
                "INSERT OR IGNORE INTO transpose_article (article_id, celex, article_acte,"
                " paragraphe, document_id, page, numero_ecrit, confiance, preuve_id)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (article_id, acte, article, paragraphe, document_id, page, ecrit,
                 CONFIANCE, preuve))
            if base.total_changes > avant:
                compte["aretes"] += 1
            else:
                base.execute("DELETE FROM preuve WHERE id = ?", (preuve,))
    base.commit()
    print(f"lignes de tableau lues        : {compte['lignes']}")
    print(f"  article de l'acte inconnu    : {compte['article_d_acte_inconnu']}")
    print(f"  numéro non résolu au dossier : {compte['non_resolues']}")
    print(f"  étude d'impact absente       : {compte['document_absent']}")
    print(f"arêtes transpose_article      : {compte['aretes']}")
    for acte, n, articles in base.execute(
            "SELECT celex, count(*), count(DISTINCT article_id) FROM transpose_article "
            "GROUP BY 1"):
        print(f"  {denomination[acte]:40s} {n:4d} arêtes, {articles} articles du code")


if __name__ == "__main__":
    main()
