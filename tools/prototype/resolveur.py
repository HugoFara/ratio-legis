#!/usr/bin/env python3
"""Prototype du résolveur amendement → article du code.

Jalon go/no-go décidé en fin de phase 0, avant d'engager la phase 1
(`docs/00-note-de-cadrage.md` § 3). Mesuré sur la loi n° 2014-344 du 17 mars 2014,
qui produit 307 des 832 articles éligibles du périmètre.

Le maillon manquant n'est pas celui qu'anticipait la feuille de route. Le § 3
suppose qu'il faut résoudre « article du projet de loi → article du code » en
parsant le langage modificatif ; c'est inutile, LEGI déclare déjà quels articles
du code chaque article de la loi promulguée a modifiés. Ce qui manque est le
rattachement de l'amendement lui-même.

Méthode : **appariement textuel exact sur les passages cités**. Le langage
législatif français cite entre guillemets le texte qu'il insère. Si un passage
cité par un amendement adopté se retrouve mot pour mot dans une version d'article
du code, l'amendement a produit ce passage. Déterministe et vérifiable — aucun
vecteur, aucun LLM dans la décision (règles § 5.5 et § 5.6).

Deux garde-fous de précision, tous deux mesurés :

1. **Discriminance.** Une fenêtre retrouvée dans plus de deux numéros d'articles
   est du texte type et ne prouve rien. Le seuil de deux n'est pas un compromis :
   84 % des fenêtres à deux numéros désignent le même article sous ses
   numérotations d'avant et d'après la recodification de 2016.
2. **Partition gouvernement / navette.** Un article dont la rédaction figure déjà
   dans le texte initial du projet de loi n'a besoin d'aucune arête `resulte_de` :
   sa motivation est l'exposé des motifs. Mélanger les deux populations gonfle
   artificiellement le dénominateur.

L'arête produite relie une **version historique** de l'article. Le script vérifie
séparément si le texte de l'amendement subsiste dans la version en vigueur, seul
cas où la chaîne va de l'article d'aujourd'hui jusqu'à l'amendement.

Sources :
  - versions d'articles du code : sortie de `tools/phase0/legi_scan.py` ;
  - texte initial du projet de loi : page HTML de l'Assemblée nationale ;
  - amendements : jeux Améli du Sénat.

Usage :
    resolveur.py <articles_code.json> <projet_initial.html> <perimetre.csv> \\
                 <loi_origine> <amendements.csv...>

    resolveur.py conso_articles.json pl1015.html data/perimetre-v1.csv \\
                 2014-344 hamon_810.csv hamon_283.csv
"""

from __future__ import annotations

import csv
import html
import io
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

# Longueur de la fenêtre d'appariement. Plus court — « du présent code » — un
# fragment apparaît partout et ne prouve rien ; à 60 caractères, la coïncidence
# est invraisemblable dans un corpus de cette taille.
FENETRE = 60

# Au-delà de deux numéros d'articles, une fenêtre est du texte type.
DISCRIMINANCE = 2


def sans_balises(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(fragment))).strip()


def normalise(texte: str) -> str:
    """Forme comparable : casse, apostrophes et guillemets typographiques, espaces.

    Le Sénat et le Journal officiel ne composent pas le même passage de la même
    façon ; sans cette normalisation l'appariement exact ne trouve rien.
    """
    t = unicodedata.normalize("NFKC", texte).lower()
    t = t.replace("’", "'").replace("‘", "'")
    t = re.sub(r"[«»\"“”]", " ", t)
    t = t.replace("­", "").replace("–", "-").replace("—", "-")
    return re.sub(r"[\s ]+", " ", t).strip()


def fenetres(passage: str, pas: int = 20):
    """Fenêtres glissantes.

    Un amendement adopté au Sénat est souvent réécrit ensuite, en deuxième lecture
    ou en commission mixte paritaire. Exiger la correspondance du passage entier
    ferait manquer les cas — majoritaires — où seule une partie survit.
    """
    for debut in range(0, max(1, len(passage) - FENETRE + 1), pas):
        yield passage[debut:debut + FENETRE]


def passages_cites(dispositif: str) -> list[str]:
    """Passages entre guillemets, seuls porteurs du texte que l'amendement insère."""
    texte = sans_balises(dispositif)
    return [norme for citation in re.findall(r"«(.+?)»", texte, re.S)
            if len(norme := normalise(citation)) >= FENETRE]


def lire_ameli(chemin: Path) -> list[dict]:
    """Jeu Améli : latin-1, tabulations, ligne « sep= » en tête, HTML dans les champs."""
    brut = chemin.read_bytes().decode("latin-1")
    corps = "\n".join(brut.split("\n")[1:])
    return [{(k or "").strip(): (v or "") for k, v in ligne.items()}
            for ligne in csv.DictReader(io.StringIO(corps), delimiter="\t")]


def texte_html(chemin: Path) -> str:
    brut = chemin.read_bytes()
    encodage = "latin-1" if b"charset=iso" in brut[:3000].lower() else "utf-8"
    page = brut.decode(encodage, errors="replace")
    page = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    return normalise(re.sub(r"<[^>]+>", " ", html.unescape(page)))


def rattacher(amendements: list[dict], versions: list[tuple[str, str]]) -> dict[str, dict]:
    """Amendement adopté → numéros d'articles du code, par appariement exact."""
    par_article: dict[str, dict] = defaultdict(lambda: {"amendements": set(), "fenetres": set()})
    for amendement in amendements:
        for passage in passages_cites(amendement.get("Dispositif", "")):
            for fenetre in fenetres(passage):
                numeros = {num for num, texte in versions if fenetre in texte}
                if not 1 <= len(numeros) <= DISCRIMINANCE:
                    continue
                for num in numeros:
                    par_article[num]["amendements"].add(amendement["Numéro"])
                    par_article[num]["fenetres"].add(fenetre)
    return par_article


def main() -> None:
    if len(sys.argv) < 6:
        sys.exit(__doc__)
    fichier_articles, projet_initial, perimetre = (Path(a) for a in sys.argv[1:4])
    loi_origine = sys.argv[4]
    fichiers_amendements = [Path(a) for a in sys.argv[5:]]

    articles = json.loads(fichier_articles.read_text(encoding="utf-8"))
    versions = [(a["num"], normalise(a["texte"])) for a in articles if a["texte"]]
    par_numero: dict[str, list[str]] = defaultdict(list)
    for a in articles:
        if a["texte"]:
            par_numero[a["num"]].append(normalise(a["texte"]))
    en_vigueur = {a["num"]: normalise(a["texte"]) for a in articles
                  if a["etat"] == "VIGUEUR" and a["texte"]}

    initial = texte_html(projet_initial)
    adoptes = [a for f in fichiers_amendements for a in lire_ameli(f)
               if a.get("Sort") == "Adopté"]
    rattachements = rattacher(adoptes, versions)

    perim = list(csv.DictReader(perimetre.open(encoding="utf-8")))
    imputables = [a for a in perim if a["eligible_resulte_de"] == "1"
                  and loi_origine in (a["texte_origine"] or "")]

    def cles(article: dict) -> list[str]:
        return [c for c in (article["num_article"].replace(" ", ""),
                            article["article_predecesseur"].replace(" ", "")) if c]

    def issu_du_texte_initial(article: dict) -> bool:
        for cle in cles(article):
            for texte in par_numero.get(cle, ()):
                if len(texte) >= FENETRE and any(f in initial for f in fenetres(texte, pas=40)):
                    return True
        return False

    gouvernement, navette = [], []
    for article in imputables:
        (gouvernement if issu_du_texte_initial(article) else navette).append(article)

    def rattache(article: dict) -> set[str]:
        trouve: set[str] = set()
        for cle in cles(article):
            trouve |= rattachements.get(cle, {}).get("amendements", set())
        return trouve

    chaines = []
    for article in navette:
        amdts = rattache(article)
        if not amdts:
            continue
        fen = {f for cle in cles(article) for f in rattachements.get(cle, {}).get("fenetres", set())}
        courant = en_vigueur.get(article["num_article"], "")
        chaines.append({
            "article": article["num_article"],
            "article_predecesseur": article["article_predecesseur"],
            "id_legi": article["id_legi"],
            "amendements_senat": sorted(amdts),
            "texte_subsiste_dans_la_version_en_vigueur": any(f in courant for f in fen),
        })

    survivants = [c for c in chaines if c["texte_subsiste_dans_la_version_en_vigueur"]]
    Path("chaines-resulte-de.json").write_text(
        json.dumps(chaines, ensure_ascii=False, indent=1), encoding="utf-8")

    n = len(imputables)
    print(f"articles imputables à la loi {loi_origine} : {n}\n")
    print(f"  A. rédaction issue du texte initial du Gouvernement : {len(gouvernement)} "
          f"({100 * len(gouvernement) / n:.0f} %)")
    print("     motivés par l'exposé des motifs et l'étude d'impact ; "
          "aucune arête resulte_de requise\n")
    print(f"  B. rédaction issue de la navette : {len(navette)} ({100 * len(navette) / n:.0f} %)")
    print(f"     rattachés à un amendement du Sénat : {len(chaines)} "
          f"({100 * len(chaines) / len(navette):.1f} %)")
    print(f"     non rattachés : {len(navette) - len(chaines)}\n")
    print(f"  C1 = {len(chaines)} / {len(navette)} = "
          f"{100 * len(chaines) / len(navette):.1f} %")
    print(f"  chaînes complètes jusqu'à la version en vigueur : {len(survivants)}")
    print(f"  couverture de la motivation, toutes voies : {len(gouvernement) + len(chaines)} / {n} "
          f"= {100 * (len(gouvernement) + len(chaines)) / n:.1f} %")


if __name__ == "__main__":
    main()
