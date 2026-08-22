#!/usr/bin/env python3
"""Phase 0 — mesures de périmètre et construction du golden set.

Reproduit les chiffres des notes `docs/00-note-de-cadrage.md` et
`docs/02-golden-set.md`. N'appartient à aucun pipeline.

Prérequis :
    tar xzf Freemium_legi_global_<date>.tar.gz -C <legi> --wildcards '*LEGITEXT000006069565*'
    tar xzf Freemium_dole_global_<date>.tar.gz -C <dole>
    python legi_scan.py <legi> conso_articles.json

Trois pièges de la donnée LEGI sont traités ici et documentés dans
`docs/01-rapport-verification-sources.md` § 2.3 bis :
  - l'attribut `sens` n'est pas fiable, on filtre sur `typelien` + `naturetexte` ;
  - le graphe de concordance diverge, la remontée est bornée à un saut ;
  - deux vocabulaires de liens coexistent (CREE/CREATION, MODIFIE/MODIFICATION).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

CREATION = {"CREE", "CREATION"}
MODIFICATION = {"MODIFIE", "MODIFICATION", "RECTIFICATION"}
TEXTES = {"LOI", "ORDONNANCE", "DECRET", "ARRETE"}
RENUMEROTATION = {"CONCORDANCE", "CONCORDE", "TRANSFERE", "TRANSFERT", "DEPLACE"}

MOIS = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


def date_du_libelle(libelle: str) -> tuple | None:
    """Date du texte, lue dans le libellé du lien (« du 14 mars 2016 »)."""
    m = re.search(r"(\d{1,2})(?:er)?\s+(\w+)\s+(\d{4})", libelle)
    if m and m.group(2).lower() in MOIS:
        return int(m.group(3)), MOIS[m.group(2).lower()], int(m.group(1))
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", libelle)
    return tuple(int(x) for x in m.groups()) if m else None


def liens_producteurs(article: dict) -> list[tuple]:
    """Liens vers le texte qui a créé ou modifié cette version.

    `sens` est délibérément ignoré : les vocabulaires ancien et récent lui donnent
    des valeurs opposées pour la même relation.
    """
    out = []
    for l in article["liens"]:
        if l["typelien"] in CREATION | MODIFICATION and l["naturetexte"] in TEXTES:
            d = date_du_libelle(l["libelle"])
            if d:
                out.append((d, l["typelien"], l["cidtexte"], l["naturetexte"],
                            l["libelle"].split(" - art")[0].strip()))
    return out


def liens_renumerotation(article: dict, index: dict) -> list[dict]:
    return [l for l in article["liens"]
            if l["typelien"] in RENUMEROTATION
            and l["naturetexte"] == "CODE"
            and l["id"] in index]


def origine(article: dict, index: dict) -> dict:
    """Texte producteur de la version actuelle, et texte à l'origine de la disposition.

    La remontée de renumérotation est bornée à UN saut : celui de la recodification.
    La fermeture transitive diverge (jusqu'à 266 articles pour L311-1).
    """
    producteurs = liens_producteurs(article)
    version = sorted(producteurs)[-1] if producteurs else None

    subst = None
    predecesseurs = liens_renumerotation(article, index)
    if predecesseurs:
        pred = index[predecesseurs[0]["id"]]
        p = liens_producteurs(pred)
        creations = sorted(t for t in p if t[1] in CREATION)
        subst = creations[0] if creations else (sorted(p)[0] if p else None)

    return {
        "predecesseur": index[predecesseurs[0]["id"]]["num"] if predecesseurs else None,
        "nb_liens_renumerotation": len(predecesseurs),
        "texte_version": version,
        "texte_origine": subst,
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    articles = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    index = {a["id"]: a for a in articles}
    legislatifs = [a for a in articles if a["etat"] == "VIGUEUR" and a["num"].startswith("L")]

    resultats = {a["num"]: origine(a, index) for a in legislatifs}
    n = len(legislatifs)
    avec_producteur = sum(1 for r in resultats.values() if r["texte_version"])
    renumerotes = sum(1 for r in resultats.values() if r["nb_liens_renumerotation"])
    natures = Counter(
        (r["texte_origine"] or r["texte_version"])[3]
        for r in resultats.values() if r["texte_origine"] or r["texte_version"]
    )

    print(f"articles L en vigueur          : {n}")
    print(f"  arête produite_par déclarée  : {avec_producteur} ({100 * avec_producteur / n:.1f} %)")
    print(f"  arête renumerote_de déclarée : {renumerotes} ({100 * renumerotes / n:.1f} %)")
    print(f"  nature du texte d'origine    : {natures.most_common()}")


if __name__ == "__main__":
    main()
