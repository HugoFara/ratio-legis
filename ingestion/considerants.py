#!/usr/bin/env python3
"""Neuvième tranche : les considérants des actes de l'Union.

La huitième tranche a rattaché 284 actes de l'Union aux articles du code, mais
par leur seul identifiant : le graphe savait *qu'*un règlement commande un
article, jamais *pourquoi il a été écrit*. Or le droit de l'Union motive
systématiquement ce qu'il édicte, en tête de son propre texte, et le publie.

C'est la meilleure source de motivation que ce projet ait rencontrée. À comparer
au corpus français, mesuré en phase 0 : l'exposé des motifs ne nomme l'article
que dans 6,4 % des cas, l'étude d'impact dans 24,8 %. Un acte de l'Union, lui,
porte toujours ses considérants.

**La segmentation n'est pas à faire.** EUR-Lex publie les actes récents en HTML
structuré selon ELI : chaque considérant porte `id="rct_N"`, chaque article
`id="art_N"`, et N est le numéro imprimé. C'est une structure déclarée, pas une
heuristique — l'inverse exact du découpage des rapports parlementaires, qui avait
coûté quatre défauts silencieux (`docs/07` § 4).

**Mais elle ne couvre que la moitié du fonds.** Les actes convertis avant ELI
n'ont ni ancre d'article ni considérant numéroté ; leurs considérants sont des
paragraphes commençant par « considérant que », et ils ne portent **aucun numéro,
ni dans le HTML ni dans le Journal officiel de l'époque**. Le rang de lecture est
alors enregistré, et `numero` reste nul : inventer une numérotation absente de
l'original serait exactement ce que le § 5.1 interdit.

Usage :
    considerants.py <base.sqlite> <data/raw/eurlex/>
"""

from __future__ import annotations

import html
import re
import sqlite3
import sys
from pathlib import Path

# Structure ELI, déclarée par EUR-Lex.
CONSIDERANT = re.compile(r'id="rct_(\d+)"')
ARTICLE = re.compile(r'id="art_(\d+)"')
INTITULE = re.compile(r'<p[^>]*class="oj-sti-art"[^>]*>(.*?)</p>', re.S)
FIN_CONSIDERANTS = re.compile(r'id="enc_\d+"|ONT? ADOPTÉ|A ADOPTÉ')
# Formes héritées : le paragraphe est déclaré par le balisage, le numéro n'existe
# pas. « considérant que … ; qu'il convient … » est un seul considérant. EUR-Lex
# a converti ces actes selon trois générations de gabarit — `id="rct_N"`,
# `<p class="normal">`, et `<p>` sans classe aucune. La troisième couvrait à elle
# seule 95 actes que la première version rendait « sans aucun considérant ».
PARAGRAPHE = re.compile(r'<p(?:\s[^>]*)?>(.*?)</p>', re.S)
# Les actes des années 1990 numérotent déjà, mais dans le corps du paragraphe et
# avant le mot : « (1) considérant que … », parfois « 1. considérant que … ». Ce
# numéro-là est imprimé : il est repris, non recalculé.
DEBUT_HERITE = re.compile(r"^(?:\(?(\d{1,3})\)?\s*[.)]?\s*)?(consid[ée]rant\b.*)$",
                          re.I | re.S)

ANCRE_CONSIDERANT = ("https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                     "?uri=CELEX:{}#rct_{}")
ANCRE_ARTICLE = ("https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                 "?uri=CELEX:{}#art_{}")
SANS_ANCRE = "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:{}"


def en_texte(fragment: str) -> str:
    # Une balise ouverte que le fragment ne referme pas n'est pas une balise pour
    # `<[^>]+>` : elle traverse le filtre et se retrouve dans le texte cité. Elle
    # est donc retirée d'abord, aux deux bouts — c'est une coupe de fragment,
    # jamais du contenu, puisqu'un « < » de contenu est échappé en `&lt;` dans le
    # HTML d'EUR-Lex.
    fragment = re.sub(r"<[^>]*$", " ", re.sub(r"^[^<]*?>", " ", fragment, count=1))
    texte = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", texte).strip()


def debut_de_balise(brut: str, position: int) -> int:
    """Le « < » qui ouvre la balise contenant `position`, ou `position` à défaut."""
    ouvrant = brut.rfind("<", max(0, position - 400), position)
    return ouvrant if ouvrant != -1 else position


def considerants(celex: str, brut: str) -> list[tuple]:
    """(rang, numero, texte, url) pour chaque considérant de l'acte.

    `numero` est le numéro imprimé, ou None quand l'acte n'en porte pas.
    """
    ancres = list(CONSIDERANT.finditer(brut))
    if ancres:
        fin = FIN_CONSIDERANTS.search(brut, ancres[-1].end())
        limite = fin.start() if fin else len(brut)
        releves = []
        for rang, ancre in enumerate(ancres, 1):
            # La borne est le **début de la balise** qui porte l'ancre suivante,
            # non l'ancre elle-même : `id="rct_2"` est un attribut, et couper là
            # laissait `<div class="eli-subdivision"` en queue du considérant
            # précédent. 7 111 des 7 674 considérants en portaient la trace.
            borne = (debut_de_balise(brut, ancres[rang].start())
                     if rang < len(ancres) else limite)
            # `ancre.end()` tombe **dans** la balise ouvrante : le `>` qui la
            # ferme se retrouve en tête du texte si on ne le saute pas.
            ouverture = brut.find(">", ancre.end())
            texte = en_texte(brut[ouverture + 1:borne])
            # Le numéro imprimé ouvre le bloc : « (12) » puis le corps.
            texte = re.sub(r"^\(\s*\d+\s*\)\s*", "", texte)
            if texte:
                releves.append((rang, int(ancre.group(1)), texte,
                                ANCRE_CONSIDERANT.format(celex, ancre.group(1))))
        return releves

    releves, rang = [], 0
    for paragraphe in PARAGRAPHE.finditer(brut):
        texte = en_texte(paragraphe.group(1))
        trouve = DEBUT_HERITE.match(texte)
        if trouve:
            rang += 1
            numero = int(trouve.group(1)) if trouve.group(1) else None
            releves.append((rang, numero, trouve.group(2),
                            SANS_ANCRE.format(celex)))
    return releves


def articles(celex: str, brut: str) -> list[tuple]:
    """(numero, intitulé, url) pour chaque article déclaré par la structure ELI."""
    releves = []
    for ancre in ARTICLE.finditer(brut):
        numero = ancre.group(1)
        suite = brut[ancre.end():ancre.end() + 1500]
        trouve = INTITULE.search(suite)
        releves.append((numero, en_texte(trouve.group(1)) if trouve else None,
                        ANCRE_ARTICLE.format(celex, numero)))
    return releves


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    miroir = Path(sys.argv[2])
    schema = Path(__file__).resolve().parent.parent / "schema" / "005-considerants.sql"
    base.executescript(schema.read_text(encoding="utf-8"))

    connus = [c for (c,) in base.execute("SELECT celex FROM acte_ue ORDER BY celex")]
    absents, sans_considerant = [], []
    lignes_c, lignes_a, numerotes, herites = [], [], 0, 0

    for celex in connus:
        fichier = miroir / f"{celex}.html"
        if not fichier.exists():
            absents.append(celex)
            continue
        brut = fichier.read_text(encoding="utf-8", errors="replace")
        releves = considerants(celex, brut)
        if not releves:
            sans_considerant.append(celex)
        for rang, numero, texte, url in releves:
            lignes_c.append((celex, rang, numero, texte, url))
            numerotes += numero is not None
            herites += numero is None
        for numero, intitule, url in articles(celex, brut):
            lignes_a.append((celex, numero, intitule, url))

    base.executemany("INSERT OR IGNORE INTO considerant "
                     "(celex, rang, numero, texte, url) VALUES (?, ?, ?, ?, ?)",
                     lignes_c)
    base.executemany("INSERT OR IGNORE INTO article_acte_ue "
                     "(celex, numero, intitule, url) VALUES (?, ?, ?, ?)", lignes_a)

    # Un numéro d'article que l'acte ne déclare pas ne doit pas produire de lien
    # profond. Il n'est effacé que si l'acte déclare bien ses articles : sur un
    # acte sans structure ELI, l'absence ne prouve rien.
    efface = base.execute("""
        UPDATE cite_acte_ue SET article_cite = NULL
        WHERE article_cite IS NOT NULL
          AND celex IN (SELECT celex FROM article_acte_ue)
          AND NOT EXISTS (SELECT 1 FROM article_acte_ue a
                          WHERE a.celex = cite_acte_ue.celex
                            AND a.numero = cite_acte_ue.article_cite)""").rowcount
    base.commit()

    violations = base.execute("PRAGMA foreign_key_check").fetchall()
    resolus, total_cite = base.execute(
        "SELECT count(*) FILTER (WHERE article_cite IS NOT NULL), count(*) "
        "FROM cite_acte_ue").fetchone()
    articles_touches = base.execute(
        "SELECT count(DISTINCT article) FROM motivation_europeenne").fetchone()[0]

    print(f"actes en base              : {len(connus)}")
    print(f"  absents du miroir        : {len(absents)}")
    print(f"  sans aucun considérant   : {len(sans_considerant)}")
    print(f"considérants chargés       : {len(lignes_c)}")
    print(f"  au numéro imprimé        : {numerotes}")
    print(f"  sans numéro dans l'original : {herites}")
    print(f"articles d'actes déclarés  : {len(lignes_a)}")
    print(f"  citations résolues à l'article : {resolus} sur {total_cite}")
    print(f"  attributions effacées faute d'article correspondant : {efface}")
    print(f"\narticles en vigueur atteignant un considérant : {articles_touches}")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
