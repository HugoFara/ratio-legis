#!/usr/bin/env python3
"""Rejoue les fiches jugées contre la base du jour : le harnais de régression.

Chaque fiche de `data/mesures/precision-*.tsv` porte des arêtes identifiées par
une clef — SHA-256 du couple qui les définit, écrite par le script de tirage —
et un verdict : `juste`, `faux`, `douteux`. Ces sept cents verdicts sont ce que
le projet sait de plus sûr sur ses arêtes, et ils ne servaient qu'une fois, le
jour du tirage. `depose_sur` est tombée de 15/15 à 3/15 sans que rien ne le
dise (`docs/35`), `vise` a été servie à 9/20 (`docs/43`) : chaque tranche
redécouvrait à la main ce que rejouer les fiches aurait montré.

Pour chaque fiche, les arêtes de la même famille sont relues dans la base avec
la même clef, et trois choses sont comptées :

- **revenue** — jugée fausse, et présente : une régression, ou une arête que
  la correction n'a pas atteinte ; c'est ce qui fait échouer le harnais ;
- **perdue** — jugée juste, et absente : du rappel qui s'en va, à expliquer
  (une garde nouvelle, un article scindé), pas forcément un défaut ;
- **déplacée** — jugée juste, présente, mais vers un autre article du fonds :
  `docs/47` en a fait neuf, toutes vers le numéro promulgué, et il faut le
  savoir.

Le harnais ne juge pas : il compare des verdicts écrits à la base. Une clef
que la base ne connaît plus et qu'aucun tirage n'expliquerait — une fiche
d'avant un changement de clef — apparaît comme perdue en bloc, et se lit
comme telle.

Usage :
    rejouer.py <base.sqlite> [data/mesures]        # code de sortie 1 si une fausse est revenue
"""

from __future__ import annotations

import csv
import hashlib
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


def cle(*parts) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()


def aretes_de(base: sqlite3.Connection) -> dict[str, dict[str, str]]:
    """Par famille, clef → article du fonds (numéro) tel que la base le porte aujourd'hui."""
    familles: dict[str, dict[str, str]] = defaultdict(dict)
    for amendement, article in base.execute(
            "SELECT v.amendement_id, a.numero FROM vise v JOIN article a ON a.id = v.article_id"):
        familles["vise"][cle(amendement, article)[:16]] = article
    for amendement, article in base.execute(
            "SELECT d.amendement_id, a.numero FROM depose_sur d JOIN article a ON a.id = d.article_id"):
        familles["depose-sur"][cle(amendement, article)[:16]] = article
    # porte_sur : la clef est la mention (texte, article du texte, numéro cité) ;
    # ce que la fiche juge est son rattachement interne, donc seules les arêtes
    # internes comptent, et l'article du fonds est ce vers quoi elle résout.
    for texte_id, article_du_texte, numero_cite, article in base.execute("""
            SELECT p.texte_id, p.article_du_texte, p.numero_cite, a.numero
            FROM porte_sur p JOIN article a ON a.id = p.article_id
            WHERE p.portee = 'interne'"""):
        familles["porte-sur"][cle(texte_id, article_du_texte, numero_cite)[:16]] = article
    for segment, amendement, article in base.execute("""
            SELECT r.segment_id, r.amendement_id, a.numero
            FROM resulte_de r JOIN segment s ON s.id = r.segment_id
            JOIN version_article v ON v.id_legi = s.version_id
            JOIN article a ON a.id = v.article_id"""):
        familles["resulte-de"][cle(segment, amendement)[:16]] = article
    return familles


def famille_de(fiche: Path) -> str | None:
    nom = fiche.name.removeprefix("precision-")
    for f in ("depose-sur", "porte-sur", "resulte-de", "vise"):
        if nom.startswith(f):
            return f
    return None


def numero_juge(ligne: dict[str, str]) -> str:
    # L'article du fonds tel que la fiche l'a montré au juge. Selon la famille
    # il est dans `article` ou en tête de `article_du_fonds` — « L423-16 (2014…) ».
    if ligne.get("article"):
        return ligne["article"]
    return (ligne.get("article_du_fonds") or "").split(" (")[0]


def main() -> None:
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    dossier = Path(sys.argv[2]) if len(sys.argv) == 3 else Path("data/mesures")
    familles = aretes_de(base)

    # Une même arête peut avoir été jugée deux fois — fausse avant une
    # correction, juste après (`docs/47` a rejugé par le contenu ce que
    # `docs/45` avait jugé par le numéro). Le dernier verdict tient : par date
    # de jugement, puis par nom de fiche, les tirages successifs étant numérotés.
    dernier: dict[tuple[str, str], tuple[str, str, str]] = {}
    for fiche in sorted(dossier.glob("precision-*.tsv")):
        famille = famille_de(fiche)
        if famille is None:
            continue
        for l in csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t"):
            if l.get("verdict") in ("juste", "faux"):
                marque = (l.get("date_jugement") or "", fiche.name)
                clef = (famille, l["cle"][:16])
                if clef not in dernier or marque > dernier[clef][:2]:
                    dernier[clef] = (*marque, l["verdict"])

    total = defaultdict(int)
    revenues = []
    for fiche in sorted(dossier.glob("precision-*.tsv")):
        famille = famille_de(fiche)
        if famille is None:
            continue
        presentes = familles[famille]
        lignes = [l for l in csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t")
                  if l.get("verdict") in ("juste", "faux")]
        bilan = defaultdict(int)
        detail = []
        for l in lignes:
            k = l["cle"][:16]
            if dernier[(famille, k)][1] != fiche.name:
                bilan["rejugée ailleurs"] += 1
                continue
            presente = k in presentes
            if l["verdict"] == "faux":
                if presente:
                    bilan["revenue"] += 1
                    detail.append(f"    revenue  {numero_juge(l)}  clé {k[:16]}")
                    revenues.append((fiche.name, k))
                else:
                    bilan["faux absente"] += 1
            else:
                if not presente:
                    bilan["perdue"] += 1
                    detail.append(f"    perdue   {numero_juge(l)}  clé {k[:16]}")
                elif famille != "porte-sur" and presentes[k] != numero_juge(l):
                    bilan["déplacée"] += 1
                    detail.append(f"    déplacée {numero_juge(l)} → {presentes[k]}  clé {k[:16]}")
                else:
                    bilan["juste tenue"] += 1
        for k2, v in bilan.items():
            total[k2] += v
        resume = ", ".join(f"{v} {k2}" for k2, v in sorted(bilan.items()))
        print(f"{fiche.name:52s} {len(lignes):3d} jugées : {resume}")
        for ligne in detail:
            print(ligne)

    print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(total.items())))
    if revenues:
        print(f"\nÉCHEC : {len(revenues)} arête(s) jugée(s) fausse(s) sont dans la base.")
        sys.exit(1)
    print("Aucune arête jugée fausse n'est dans la base.")


if __name__ == "__main__":
    main()
