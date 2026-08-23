#!/usr/bin/env python3
"""Extraction des commentaires d'article des rapports de commission.

Source d'annotation externe pour le golden set. Le rapport de commission est le
seul document du corpus qui commente **article par article** : chaque article du
texte y reçoit un en-tête, une parenthèse déclarant les dispositions visées, un
titre, puis un commentaire développé qui expose la raison du dispositif et
mentionne les amendements adoptés.

C'est ce qui manquait. Mesuré sur le périmètre :

    exposé des motifs      nomme l'article dans   6,4 % des cas
    étude d'impact                               24,8 %
    rapport de commission                        94,1 %   (loi 2014-344)

La parenthèse d'en-tête est une **déclaration éditoriale** du rapporteur reliant
l'article du texte aux articles du code. Elle est indépendante des liens LEGI et
sert donc de contrôle croisé, pas seulement de source.

Ce que l'extraction produit, par article du code : le rapport, l'article du texte
commenté, et les **offsets de caractères** du commentaire dans le document — c'est
la forme exigée par le contrat de génération du § 4.3 de la feuille de route, et
c'est ce que l'annotateur humain devait produire à la main.

Limite assumée : un commentaire porte sur l'article *du texte en discussion*, qui
peut créer ou modifier plusieurs articles du code. Le rattachement est donc au
bon grain pour dire « pourquoi ce dispositif », pas « pourquoi cet alinéa ».

Usage :
    commentaires_rapports.py <perimetre.csv> <loi_origine> <rapport.html...>
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# En-tête de commentaire : « Article 12 », « Article 1er », « Article 19 septies
# [nouveau] », « Article additionnel après l'article 19 ». Le suffixe ordinal peut
# être rejeté à la ligne suivante par la mise en forme d'origine.
#
# Le motif sert deux usages distincts : ouvrir une section, et **fermer la
# précédente**. Ne reconnaître que « Article N » nu, comme le faisait la première
# version, laisse une section déborder sur toutes celles dont l'en-tête porte un
# ordinal — la moitié du corpus. Le commentaire rendu porte alors les offsets
# d'un article et le texte de plusieurs, ce qu'un contrôle à la main de douze
# arêtes `motive` a fait apparaître sur deux cas. L'ouverture d'une section reste
# soumise au test de déclaration ou de titre : élargir le motif ne relâche donc
# pas le critère, cela découpe plus finement.
ORDINAL = r"(?:er|bis|ter|quater|quinquies|sexies|septies|octies|nonies|decies)"
# `^Article` sans tolérance d'indentation ne reconnaissait aucun en-tête des
# rapports du Sénat, qui préfixent la ligne d'une espace : 221 fichiers ne
# rendaient que 455 sections, contre 7 343 pour 82 fichiers de l'Assemblée. Le
# déséquilibre était trop grand pour une différence de convention rédactionnelle.
ENTETE = re.compile(
    # La capture couvre l'ordinal et la lettre, non le seul nombre : « Article 18
    # bis » rendait « 18 », donc le même identifiant que l'article 18. Tant que
    # `article_du_texte` n'était qu'une donnée d'affichage, la confusion restait
    # sans effet ; elle en a un dès qu'on s'en sert pour rattacher une section à
    # un article du code (`docs/17`), où elle attribuait à l'article 18 ce qui
    # commentait l'article 18 bis.
    r"^[ \t]*Article (?:additionnel[^\n]{0,90}|(\d+"
    r"(?:\s*" + ORDINAL + r")*(?:\s*[A-H]{1,2})?)"
    r"(?:\s*\[?\((?:nouveau|supprimé)\)\]?)?"
    # Le Sénat rend l'en-tête et sa parenthèse sur une seule ligne :
    # « Article 22 ter (article 22-2 de la loi n° 89-462) ». Sans cette
    # alternative, l'en-tête ne ferme pas la section précédente, qui a atteint
    # 553 330 caractères sur un rapport du périmètre. Le suffixe admis se limite
    # à une parenthèse ou à un tiret de titre : « Article 22 est ainsi modifié »
    # reste écarté, faute de quoi toute phrase ouvrirait une section.
    r"(?:[ \t]*(?:\([^\n]*|[-–—][ \t][^\n]*))?"
    r")"
    r"[ \t]*(?:\n[ \t]*" + ORDINAL + r")?[ \t]*$", re.M)

ARTICLE = re.compile(r"\bL\.?\s?(\d{3})-(\d{1,3})(?:-(\d{1,3}))?")
PLAGE = re.compile(r"L\.?\s?(\d{3})-(\d{1,3})\s+(?:à|au)\s+L\.?\s?(\d{3})-(\d{1,3})")


def texte_brut(chemin: Path) -> str:
    brut = chemin.read_bytes()
    encodage = "latin-1" if b"charset=iso" in brut[:3000].lower() else "utf-8"
    page = brut.decode(encodage, errors="replace")
    page = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    page = re.sub(r"<[^>]+>", "\n", page)
    page = html.unescape(page)
    return re.sub(r"\n+", "\n", re.sub(r"[ \t\xa0]+", " ", page))


def numeros_cites(fragment: str) -> set[str]:
    """Numéros d'articles du code, plages « L. 111-1 à L. 111-5 » comprises."""
    trouves = {f"L{a}-{b}" + (f"-{c}" if c else "")
               for a, b, c in ARTICLE.findall(fragment)}
    for livre_d, debut, livre_f, fin in PLAGE.findall(fragment):
        if livre_d == livre_f and int(fin) - int(debut) < 40:
            trouves |= {f"L{livre_d}-{n}" for n in range(int(debut), int(fin) + 1)}
    return trouves


def est_suivi_d_un_titre(section: str) -> bool:
    """Convention du Sénat : l'en-tête est suivi d'un titre, non d'une phrase.

    Un titre ne se termine pas par un point et ne commence pas en minuscule ;
    c'est ce qui le distingue d'un renvoi du type « … prévu à l'article 12 » pris
    au début d'une phrase.
    """
    lignes = [l.strip() for l in section.split("\n")[1:8] if l.strip()]
    if not lignes:
        return False
    titre = lignes[0]
    return (10 <= len(titre) <= 200 and not titre.endswith(".")
            and not titre[0].islower() and len(section) > 1200)


def commentaires(chemin: Path) -> list[dict]:
    """Sections de commentaire d'article, avec leurs offsets dans le document."""
    texte = texte_brut(chemin)

    # Une ordonnance n'a pas de rapport de commission : sa motivation est le
    # rapport au Président de la République, qui n'est pas découpé par article.
    # Le document entier fait alors une seule section — grain plus grossier,
    # signalé comme tel, mais c'est la seule motivation qui existe.
    if "rapport-pr" in chemin.name:
        return [{
            "rapport": chemin.name,
            "article_du_texte": "",
            "dispositions_visees": "rapport au Président de la République, non découpé par article",
            "offset_debut": 0,
            "offset_fin": len(texte),
            "articles_declares": [],
            "articles_cites": sorted(numeros_cites(texte)),
            "mentions_amendement": 0,
        }]

    depart = texte.find("EXAMEN DES ARTICLES", texte.find("EXAMEN DES ARTICLES") + 10)
    if depart < 0:
        depart = max(0, texte.find("EXAMEN DES ARTICLES"))
    corps = texte[depart:]

    # Le texte brut met chaque balise sur sa ligne : « Article 1<sup>er</sup> »
    # rend « 1\n \n er ». L'espacement est réduit pour que le numéro soit
    # comparable d'un rapport à l'autre.
    entetes = [(m.start(), re.sub(r"\s+", " ", m.group(1) or "").strip())
               for m in ENTETE.finditer(corps)]
    sections = []
    for rang, (debut, numero) in enumerate(entetes):
        fin = entetes[rang + 1][0] if rang + 1 < len(entetes) else len(corps)
        tete = re.sub(r"\s+", " ", corps[debut:debut + 260])
        # Deux conventions de rédaction coexistent. L'Assemblée annonce les
        # dispositions visées entre parenthèses ; le Sénat fait suivre l'en-tête
        # d'un simple titre. Sans l'un ou l'autre, « Article 12 » n'est qu'un
        # renvoi au fil du texte et ne doit pas ouvrir une section.
        declaration = re.search(r"\(([^)]{10,400})\)", tete)
        if not (declaration or est_suivi_d_un_titre(corps[debut:fin])):
            continue
        # Une ligne de sommaire a la même forme qu'un en-tête de commentaire : un
        # numéro d'article, une parenthèse déclarant les dispositions visées, un
        # titre — et rien après. Elle nomme les bons articles et n'explique rien.
        # La distribution des tailles est franchement bimodale : 112 sections sous
        # 400 caractères, trois entre 400 et 800, toutes des lignes de sommaire ;
        # le premier commentaire véritable apparaît à 926 caractères.
        if fin - debut < 800:
            continue
        sections.append({
            "rapport": chemin.name,
            "article_du_texte": numero,
            "dispositions_visees": (declaration.group(1).strip() if declaration
                                    else re.sub(r"\s+", " ", corps[debut:fin].split("\n", 1)[-1])[:200]),
            "offset_debut": depart + debut,
            "offset_fin": depart + fin,
            "articles_declares": sorted(numeros_cites(declaration.group(1))) if declaration else [],
            "articles_cites": sorted(numeros_cites(corps[debut:fin])),
            "mentions_amendement": len(re.findall(r"amendement", corps[debut:fin], re.I)),
        })
    return sections


def main() -> None:
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    perimetre, loi_origine = Path(sys.argv[1]), sys.argv[2]
    rapports = [Path(a) for a in sys.argv[3:]]

    sections = [s for rapport in rapports for s in commentaires(rapport)]

    declares: dict[str, list[dict]] = defaultdict(list)
    cites: dict[str, list[dict]] = defaultdict(list)
    for section in sections:
        for numero in section["articles_declares"]:
            declares[numero].append(section)
        for numero in section["articles_cites"]:
            cites[numero].append(section)

    articles = list(csv.DictReader(perimetre.open(encoding="utf-8")))
    imputables = [a for a in articles if a["eligible_resulte_de"] == "1"
                  and loi_origine in (a["texte_origine"] or "")]

    def cles(article: dict) -> list[str]:
        return [c for c in (article["num_article"].replace(" ", ""),
                            article["article_predecesseur"].replace(" ", "")) if c]

    annotations = []
    for article in imputables:
        retenues = [s for c in cles(article) for s in declares.get(c, [])] \
            or [s for c in cles(article) for s in cites.get(c, [])]
        if not retenues:
            continue
        section = min(retenues, key=lambda s: s["offset_fin"] - s["offset_debut"])
        annotations.append({
            "num_article": article["num_article"],
            "article_predecesseur": article["article_predecesseur"],
            "id_legi": article["id_legi"],
            "rapport": section["rapport"],
            "article_du_texte_commente": section["article_du_texte"],
            "dispositions_visees": section["dispositions_visees"],
            "offset_debut": section["offset_debut"],
            "offset_fin": section["offset_fin"],
            "declare_en_entete": any(c in declares for c in cles(article)),
            "mentions_amendement": section["mentions_amendement"],
        })

    Path("annotations-rapports.json").write_text(
        json.dumps(annotations, ensure_ascii=False, indent=1), encoding="utf-8")

    n = len(imputables)
    en_tete = sum(1 for a in annotations if a["declare_en_entete"])
    print(f"rapports dépouillés            : {len(rapports)}")
    print(f"commentaires d'article extraits : {len(sections)}")
    print(f"articles du code déclarés en en-tête : {len(declares)}")
    print(f"articles du code cités               : {len(cites)}")
    print(f"\narticles imputables à la loi {loi_origine} : {n}")
    print(f"  avec un commentaire d'article      : {len(annotations)} "
          f"({100 * len(annotations) / n:.1f} %)")
    print(f"  dont déclarés dans l'en-tête       : {en_tete} "
          f"({100 * en_tete / n:.1f} %)")


if __name__ == "__main__":
    main()
