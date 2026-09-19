#!/usr/bin/env python3
"""Étend le périmètre aux parties R et D, sans toucher aux lignes de la partie L.

`docs/00` § 1 a figé le périmètre sur la **partie législative seule**, et en a
donné la raison : « Aucun dossier législatif : rattachement à DOLE mesuré à 0 % ».
Cette raison est fausse, et la base le montre. Sur les 811 articles R et D en
vigueur, **64 ont une loi portant un dossier législatif dans leur ascendance** —
7,9 %, pas 0 %. La mesure de phase 0 avait été faite sur le rattachement
**direct** d'un décret à DOLE, qui est bien nul, et la conclusion avait été tirée
sans remonter la chaîne de renumérotation, c'est-à-dire sans faire ce que le
projet fait.

`docs/00` § 5 exige qu'un élargissement passe par une note de cadrage : c'est
`docs/27`, et ce fichier en est l'outil.

**Ce que ce script recalcule, et ce qu'il ne recalcule pas.**

Il n'y touche pas aux 1 280 lignes de la partie L. Elles ont été produites en
phase 0 par une procédure dont le code n'a pas été conservé, et leur colonne
`texte_origine` porte la thèse du projet — « la loi rétablie dans l'ascendance ».
Trois définitions candidates ont été confrontées à ces lignes ici même : la
meilleure en retrouve 670 sur 1 279. Redéfinir en silence la colonne qui porte la
thèse, pour gagner un format uniforme, coûterait plus que la non-uniformité.
Les lignes L sont donc **reprises telles quelles**, et les lignes R et D sont
ajoutées avec une définition écrite, celle qui suit.

**La définition des lignes nouvelles.** Pour chaque article R ou D en vigueur :

  - `texte_producteur_version` : le texte qui a produit la version en vigueur,
    liens d'abrogation exclus — un texte qui abroge n'écrit pas ;
  - `article_predecesseur` : l'ancêtre atteint par `renumerote_de` dont la plus
    ancienne version est la plus ancienne de l'ascendance, ou l'article lui-même ;
  - `texte_origine` : la **loi** la plus récente de toute l'ascendance, celle qui
    porte un dossier étant préférée ; à défaut de loi, le texte le plus récent,
    quelle que soit sa nature. C'est la seule colonne dont la définition diffère
    de celle des lignes L, et la seule qui ne soit pas reproductible depuis elles ;
  - `eligible_resulte_de` : 1 si l'origine est une loi, porte un dossier DOLE et
    relève d'une législature ≥ 13 — le seuil sous lequel aucun corpus
    d'amendements exploitable n'existe (`docs/00` § 3).

`livre` reste vide : le titre de section n'est pas dans le graphe, et l'inventer
depuis le numéro serait une donnée fabriquée. Aucun consommateur ne le lit.

Usage :
    perimetre.py <base.sqlite> <perimetre-v1.csv> <sortie.csv>
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

COLONNES = ["num_article", "id_legi", "date_debut", "livre",
            "texte_producteur_version", "nature_producteur", "article_predecesseur",
            "texte_origine", "nature_origine", "id_dole_origine",
            "legislature_origine", "eligible_resulte_de"]
NATURE = {"loi": "LOI", "ordonnance": "ORDONNANCE", "decret": "DECRET",
          "arrete": "ARRETE"}
LEGISLATURE_MINIMALE = 13
PARTIES_NOUVELLES = ("R", "D")

# `partie_de` d'`ingestion/verdict.py`, à l'identique : une annexe relève de la
# partie de son article d'accueil. Les deux listes doivent rester d'accord, sinon
# le périmètre et le verdict comptent deux populations différentes.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "ingestion"))
from verdict import partie_de  # noqa: E402


def ascendance(base: sqlite3.Connection) -> dict[str, list[dict]]:
    """Pour chaque article en vigueur, tout ce que son ascendance a produit.

    La récursion ne porte **que** l'identifiant de l'ancêtre : y ajouter une
    profondeur ferait boucler `UNION` sur les cycles de renumérotation, que le
    fonds contient.
    """
    base.row_factory = sqlite3.Row
    lignes = base.execute("""
        WITH RECURSIVE asc_a(cible, anc) AS (
            SELECT a.id, a.id FROM article a
            JOIN version_en_vigueur ve ON ve.article_id = a.id
            UNION SELECT x.cible, r.ancien_id
            FROM renumerote_de r JOIN asc_a x ON r.article_id = x.anc)
        SELECT c.numero AS cible, an.numero AS ancetre,
               v.id_legi, v.date_debut, p.type_lien,
               t.titre, t.nature, t.date_texte, i.dossier_id, d.legislature
        FROM asc_a x
        JOIN article c            ON c.id = x.cible
        JOIN article an           ON an.id = x.anc
        JOIN version_article v    ON v.article_id = x.anc
        LEFT JOIN produite_par p  ON p.version_id = v.id_legi
                                 AND p.type_lien NOT IN ('ABROGE', 'ABROGATION')
        LEFT JOIN texte_normatif t ON t.id_jorf = p.texte_id
        LEFT JOIN issu_de i        ON i.texte_id = t.id_jorf
        LEFT JOIN dossier d        ON d.id_dole = i.dossier_id""")
    par_article: dict[str, list[dict]] = defaultdict(list)
    for ligne in lignes:
        par_article[ligne["cible"]].append(dict(ligne))
    return par_article


def origine(chaine: list[dict]) -> dict:
    """La loi la plus récente de l'ascendance, celle qui a un dossier d'abord."""
    textes = [x for x in chaine if x["titre"]]
    if not textes:
        return {}
    lois = [x for x in textes if x["nature"] == "loi"]
    candidats = [x for x in lois if x["dossier_id"]] or lois or textes
    return max(candidats, key=lambda x: (x["date_texte"], x["titre"]))


def predecesseur(chaine: list[dict], numero: str) -> str:
    """L'ancêtre dont la plus ancienne version ouvre l'ascendance."""
    premieres: dict[str, str] = {}
    for x in chaine:
        d = premieres.get(x["ancetre"])
        if d is None or x["date_debut"] < d:
            premieres[x["ancetre"]] = x["date_debut"]
    if not premieres:
        return numero
    return min(premieres, key=lambda n: (premieres[n], n))


def lignes_nouvelles(base: sqlite3.Connection, deja: set[str]) -> list[dict]:
    base.row_factory = sqlite3.Row
    chaines = ascendance(base)
    versions = {r["numero"]: dict(r) for r in base.execute("""
        SELECT a.numero, v.id_legi, v.date_debut
        FROM version_en_vigueur v JOIN article_courant a ON a.id = v.article_id""")}

    nouvelles = []
    for numero, version in sorted(versions.items()):
        if numero in deja or partie_de(numero) not in PARTIES_NOUVELLES:
            continue
        chaine = chaines.get(numero, [])
        producteurs = [x for x in chaine
                       if x["id_legi"] == version["id_legi"] and x["titre"]]
        producteur = (max(producteurs, key=lambda x: (x["date_texte"], x["titre"]))
                      if producteurs else {})
        source = origine(chaine)
        legislature = source.get("legislature")
        eligible = int(source.get("nature") == "loi"
                       and bool(source.get("dossier_id"))
                       and (legislature or 0) >= LEGISLATURE_MINIMALE)
        nouvelles.append({
            "num_article": numero,
            "id_legi": version["id_legi"],
            "date_debut": version["date_debut"],
            "livre": "",
            "texte_producteur_version": producteur.get("titre", ""),
            "nature_producteur": NATURE.get(producteur.get("nature"), ""),
            "article_predecesseur": predecesseur(chaine, numero),
            "texte_origine": source.get("titre", ""),
            "nature_origine": NATURE.get(source.get("nature"), ""),
            "id_dole_origine": source.get("dossier_id") or "",
            "legislature_origine": legislature if legislature is not None else "",
            "eligible_resulte_de": eligible,
        })
    return nouvelles


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    chemin_base, ancien, sortie = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(f"file:{chemin_base}?mode=ro", uri=True)

    lues = list(csv.DictReader(ancien.open(encoding="utf-8")))
    deja = {l["num_article"] for l in lues}
    nouvelles = lignes_nouvelles(base, deja)

    with sortie.open("w", encoding="utf-8", newline="") as f:
        graveur = csv.DictWriter(f, fieldnames=COLONNES)
        graveur.writeheader()
        for ligne in lues:
            graveur.writerow({c: ligne.get(c, "") for c in COLONNES})
        graveur.writerows(nouvelles)

    par_partie: dict[str, int] = defaultdict(int)
    avec_dossier = eligibles = 0
    for ligne in nouvelles:
        par_partie[partie_de(ligne["num_article"])] += 1
        avec_dossier += bool(ligne["id_dole_origine"])
        eligibles += ligne["eligible_resulte_de"]

    print(f"lignes reprises de {ancien.name} : {len(lues)}")
    print(f"lignes ajoutées                  : {len(nouvelles)}")
    for partie in sorted(par_partie):
        print(f"  partie {partie} : {par_partie[partie]}")
    print(f"  dont un dossier DOLE dans l'ascendance : {avec_dossier}")
    print(f"  dont éligibles à resulte_de            : {eligibles}")
    print(f"écrit : {sortie} ({len(lues) + len(nouvelles)} lignes)")
    base.close()


if __name__ == "__main__":
    main()
