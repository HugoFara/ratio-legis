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

Le harnais ne juge pas : il compare des verdicts écrits à la base.

**La clef d'une arête d'amendement ne peut pas être son identifiant.**
`amendement.id` est attribué à l'insertion, dans l'ordre des fichiers du
corpus ; quand le corpus grossit (`docs/37`), les identifiants glissent, et
une fiche jugée avant apparaissait « perdue en bloc » — 143 arêtes
`resulte_de` présentes et jugées passaient pour perdues (`docs/49` § 8).
L'arête est donc reconnue aussi par ce qui ne bouge pas : pour `resulte_de`
(segment, chambre, dossier, numéro de l'amendement), pour `depose_sur`
(chambre, texte discuté, numéro, article). La clef SHA reste ce que la fiche
porte ; la clef stable est calculée des deux côtés.

**Une arête `depose_sur` est jugée par sa voie.** `juger.py` le dit : la voie
— `visee`, `alinea`, `article_entier` — fixe ce que le juge vérifie, et un
« faux » sur la voie `article_entier` (« N réécrit aussi d'autres articles »)
ne dit rien de la même arête établie par l'alinéa que le dispositif nomme.
L'amendement 342 de 2013 sur L121-79-4 a été jugé faux quand `porte_sur` ne
connaissait qu'une cible à l'article 64 et que la voie par défaut lui donnait
tout l'article ; elle est aujourd'hui posée par ses alinéas 6 et 7, sous
l'instruction qui réécrit L. 121-79-4 — ce que le second juge disait déjà.
Quand la base porte une arête jugée fausse **par une autre voie** que celle
jugée, elle est comptée à part, non jugée. Une arête jugée juste reste juste
tenue quelle que soit la voie : c'est l'affirmation qui a été validée, et
elle ne dépend pas de la façon de l'établir. Les fiches d'avant la colonne
`voie` la donnent par `vise` : « visée » est la voie `visee`, « sans visée »
la voie `article_entier`.

**Un numéro n'est pas un article** (`docs/38`) : la clef d'une arête `vise` ou
`porte_sur` est prise sur le numéro, et deux lignées peuvent le porter. Le
juge a vu la lignée, par la date de sa première version — « L141-3
(2024-11-15) » — et c'est celle-là qu'il a jugée. Quand la base porte
aujourd'hui l'arête vers l'autre lignée, ce n'est ni la fausse revenue ni la
juste tenue : c'est une autre arête, **vers une autre lignée**, comptée à
part et non jugée.

Usage :
    rejouer.py <base.sqlite> [data/mesures]        # code de sortie 1 si une fausse est revenue
"""

from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precision_vise import coupe  # noqa: E402


def cle(*parts) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()


def aretes_de(base: sqlite3.Connection) -> dict[str, dict[str, tuple[str, str]]]:
    """Par famille, clef → (numéro, date de la première version de la lignée)
    tel que la base le porte aujourd'hui. Les arêtes d'amendement y sont aussi
    sous leur clef stable, préfixée « stable: »."""
    familles: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
    debut = dict(base.execute(
        "SELECT article_id, min(date_debut) FROM version_article GROUP BY article_id"))
    for amendement, article_id, article, chambre, dossier, dispositif in base.execute(
            "SELECT v.amendement_id, a.id, a.numero, am.chambre, am.dossier_id, "
            "am.dispositif FROM vise v JOIN article a ON a.id = v.article_id "
            "JOIN amendement am ON am.id = v.amendement_id"):
        valeur = (article, debut.get(article_id, ""))
        familles["vise"][cle(amendement, article)[:16]] = valeur
        familles["vise"]["stable:" + cle(chambre, dossier, coupe(dispositif, 600),
                                         article)] = valeur
    for amendement, article_id, article, voie, chambre, texte, numero in base.execute(
            "SELECT d.amendement_id, a.id, a.numero, d.voie, am.chambre, d.texte_id, "
            "am.numero FROM depose_sur d JOIN article a ON a.id = d.article_id "
            "JOIN amendement am ON am.id = d.amendement_id"):
        valeur = (article, debut.get(article_id, ""), voie)
        familles["depose-sur"][cle(amendement, article)[:16]] = valeur
        familles["depose-sur"]["stable:" + cle(chambre, texte, numero, article)] = valeur
    # porte_sur : la clef est la mention (texte, article du texte, numéro cité) ;
    # ce que la fiche juge est son rattachement interne, donc seules les arêtes
    # internes comptent, et l'article du fonds est ce vers quoi elle résout.
    for texte_id, article_du_texte, numero_cite, article_id, article in base.execute("""
            SELECT p.texte_id, p.article_du_texte, p.numero_cite, a.id, a.numero
            FROM porte_sur p JOIN article a ON a.id = p.article_id
            WHERE p.portee = 'interne'"""):
        familles["porte-sur"][cle(texte_id, article_du_texte, numero_cite)[:16]] = (
            article, debut.get(article_id, ""))
    for segment, amendement, article_id, article, chambre, dossier, numero in base.execute("""
            SELECT r.segment_id, r.amendement_id, a.id, a.numero, am.chambre, am.dossier_id,
                   am.numero
            FROM resulte_de r JOIN segment s ON s.id = r.segment_id
            JOIN version_article v ON v.id_legi = s.version_id
            JOIN article a ON a.id = v.article_id
            JOIN amendement am ON am.id = r.amendement_id"""):
        valeur = (article, debut.get(article_id, ""))
        familles["resulte-de"][cle(segment, amendement)[:16]] = valeur
        familles["resulte-de"]["stable:" + cle(segment, chambre, dossier, numero)] = valeur
    # transpose_article : la ligne du tableau de concordance (docs/54). Toutes
    # ses composantes sont des numéros publiés, la clef ne glisse pas.
    if base.execute("SELECT 1 FROM sqlite_master WHERE name = 'transpose_article'").fetchone():
        for celex, article_acte, paragraphe, article_id, article in base.execute(
                "SELECT t.celex, t.article_acte, t.paragraphe, a.id, a.numero "
                "FROM transpose_article t JOIN article a ON a.id = t.article_id"):
            familles["concordances"][cle(celex, article_acte, paragraphe, article)[:16]] = (
                article, debut.get(article_id, ""))
    return familles


def famille_de(fiche: Path) -> str | None:
    nom = fiche.name.removeprefix("precision-")
    for f in ("depose-sur", "porte-sur", "resulte-de", "vise", "concordances"):
        if nom.startswith(f):
            return f
    return None


LIGNEE = re.compile(r"^\S+ \((\d{4}-\d{2}-\d{2})\)")


def cle_stable(famille: str, ligne: dict[str, str]) -> str | None:
    if famille == "resulte-de" and ligne.get("segment"):
        return "stable:" + cle(ligne["segment"], ligne["chambre"], ligne["dossier"],
                               ligne["amendement"])
    # Les fiches `vise` ne portent que l'identifiant interne de l'amendement,
    # qui glisse dès qu'un chargement en insère d'autres avant lui : l'ajout
    # des législatures XV à XVII les a tous décalés. Ce que le juge a lu — le
    # dispositif, tel que la fiche l'a coupé — et le dossier font la clef.
    if famille == "vise" and ligne.get("dispositif"):
        return "stable:" + cle(ligne["chambre"], ligne["dossier"], ligne["dispositif"],
                               ligne["article"])
    if famille == "depose-sur" and ligne.get("texte"):
        return "stable:" + cle(ligne["chambre"], ligne["texte"], ligne["amendement"],
                               ligne["article"])
    return None


def numero_juge(ligne: dict[str, str]) -> str:
    # L'article du fonds tel que la fiche l'a montré au juge. Selon la famille
    # il est dans `article` ou en tête de `article_du_fonds` — « L423-16 (2014…) ».
    if ligne.get("article"):
        return ligne["article"]
    return (ligne.get("article_du_fonds") or "").split(" (")[0]


def voie_jugee(ligne: dict[str, str]) -> str | None:
    """La voie sous laquelle une arête `depose_sur` a été jugée, ou None."""
    if ligne.get("voie"):
        return ligne["voie"]
    if ligne.get("vise") == "sans visée":
        return "article_entier"
    if ligne.get("vise") in ("visée", "oui", "vise"):
        return "visee"
    return None


def lignee_jugee(ligne: dict[str, str]) -> str | None:
    """La date de première version de la lignée montrée au juge, quand la
    fiche l'écrit — « L141-3 (2024-11-15) … » ; None sinon."""
    trouve = LIGNEE.match(ligne.get("article_du_fonds") or "")
    return trouve.group(1) if trouve else None


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
            if k not in presentes and cle_stable(famille, l) in presentes:
                k = cle_stable(famille, l)          # l'identifiant a glissé
            presente = k in presentes
            lignee = lignee_jugee(l)
            voie = voie_jugee(l) if famille == "depose-sur" else None
            if presente and lignee is not None and presentes[k][1] != lignee:
                bilan["vers une autre lignée"] += 1
                detail.append(f"    {l['verdict']:5s} {numero_juge(l)} ({lignee}) → "
                              f"lignée de {presentes[k][1]}, non jugée  clé {k[:16]}")
            elif (presente and l["verdict"] == "faux" and voie is not None
                    and presentes[k][2] != voie):
                bilan["par une autre voie"] += 1
                detail.append(f"    {l['verdict']:5s} {numero_juge(l)} voie {voie} → "
                              f"voie {presentes[k][2]}, non jugée  clé {k[:16]}")
            elif l["verdict"] == "faux":
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
                elif famille != "porte-sur" and presentes[k][0] != numero_juge(l):
                    bilan["déplacée"] += 1
                    detail.append(f"    déplacée {numero_juge(l)} → {presentes[k][0]}  clé {k[:16]}")
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
