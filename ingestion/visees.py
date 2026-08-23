#!/usr/bin/env python3
"""Cinquième tranche : ce qu'un amendement visait, qu'il ait abouti ou non.

`resulte_de` ne relie que les amendements dont le texte a survécu — 79 sur 19 078.
Elle ne dit rien des 5 913 rejetés, 3 638 retirés, 795 irrecevables au titre de
l'article 40 et 597 au titre de l'article 45. Or c'est ce corpus qui répond à la
question du législateur : qu'a-t-on déjà tenté sur cet article, et qu'est-ce qui
l'a fait échouer ?

**La cible est déclarée, pas inférée.** Aucun appariement textuel n'intervient :
le dispositif nomme l'article et la formule qui le modifie. C'est ce qui rend
l'arête possible pour un amendement qui n'a jamais produit une ligne de droit.

**Seule la cible d'une formule de modification compte.** C'est la leçon la plus
chère de la phase 0 : relever tout numéro d'article cité dans un dispositif avait
produit neuf faux rattachements sur dix, parce qu'un dispositif cite abondamment
le droit existant sans le modifier. « L'article L. 121-36 est ainsi rédigé » vise
L. 121-36 ; « dans les conditions prévues à l'article L. 121-36 » ne le vise pas.

Usage :
    visees.py <base.sqlite> [schema/003-visee.sql]
"""

from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "prototype"))
from resolveur import sans_balises  # noqa: E402

# La négation finale interdit de tronquer : « L. 111-6-1-3 » du code de la
# construction se lisait « L. 111-6-1 », qui existe au code de la consommation.
# Le suffixe en lettre appartient au numéro : « Art. L. 222-1 B » du code de
# l'environnement n'est pas L. 222-1 du code de la consommation. Le laisser tomber
# fabriquait une identité entre deux articles sans rapport.
ARTICLE = re.compile(
    r"\b([LRD])\.?\s?(\d{3})-(\d{1,3})(?:-(\d{1,3}))?(?!\s?-\s?\d)(?!\s[A-Z]\b)")

# Formules de modification de la légistique française. Relevées après le numéro,
# dans la fenêtre qui suit immédiatement : « L'article L. 121-36 est ainsi rédigé ».
APRES = re.compile(
    r"^[^.;«»]{0,60}?\b(?:est|sont)\s+(?:ainsi\s+)?"
    r"(r[ée]dig[ée]s?|modifi[ée]s?|compl[ée]t[ée]s?|abrog[ée]s?|remplac[ée]s?|ins[ée]r[ée]s?)",
    re.I)
# Formules qui précèdent le numéro : « Après l'article L. 121-36, il est inséré ».
AVANT = re.compile(
    r"\b(apr[èe]s|avant|au d[ée]but de|à la fin de)\s+(?:le|la|l')?\s*article\s*$", re.I)
# Un amendement à un projet de loi de consommation ne nomme pas l'article du code
# comme cible : il le rédige. « Insérer trois alinéas ainsi rédigés : "Art.
# L. 121-104. – Lorsque le consommateur…" ». Sans cette forme, les amendements des
# dossiers les plus lourds du périmètre — ceux qui écrivent le code — étaient
# précisément ceux qu'on ne voyait pas.
CREATION = re.compile(r"[«\"]\s*(?:art|article)\.?\s*$", re.I)

# Le numéro seul ne dit pas le code : L. 152-1 existe au code de l'environnement,
# L. 121-1 au code de l'urbanisme, et les deux au code de la consommation. Un
# dispositif qui modifie un autre code se rattacherait sinon à un article
# homonyme du nôtre — c'est la confusion de cible de la phase 0, sous une autre
# forme. La clause est bornée comme dans la tranche des renvois, en excluant le
# point de « L. 152-1 » des fins de phrase.
BORNE = re.compile(r"(?<![LRD])(?<!art)(?<!n°)[.;]")
# « Le code de l'énergie est ainsi modifié : 1° L'article L. 241-2… » : le code
# est nommé en tête du bloc, pas après le numéro, et l'article défini y est
# « le », non « du ». N'accepter que « du code » laissait passer les
# modifications d'autres codes dont un numéro existe aussi dans le nôtre.
CODE_NOMME = re.compile(
    r"\b(?:du|le|la|au|dans le|de ce|ce|même)\s+(?:présent\s+)?code(?:\s+[^,;.:)]{3,45})?", re.I)


def clause(texte: str, debut: int, fin: int) -> str:
    gauche = max((m.end() for m in BORNE.finditer(texte, 0, debut)), default=0)
    droite = BORNE.search(texte, fin)
    return texte[gauche:droite.start() if droite else len(texte)]


def vise_un_autre_code(texte: str, debut: int, fin: int) -> bool:
    """Vrai si la clause nomme un code, et que ce n'est pas celui-ci."""
    noms = [m.group(0).lower() for m in CODE_NOMME.finditer(clause(texte, debut, fin))]
    if not noms:
        # Le code est souvent nommé une seule fois, en tête du bloc modificateur :
        # « Le code de l'énergie est ainsi modifié : 1° … "Art. L. 241-2-…" ». La
        # clause ne le contient pas, mais il gouverne tout ce qui suit. Même
        # convention que « du même code » dans la tranche des renvois.
        amont = list(CODE_NOMME.finditer(texte, 0, debut))
        if not amont:
            return False
        noms = [amont[-1].group(0).lower()]
    return not any("consommation" in n or "présent code" in n for n in noms)


# Précision mesurée à la main sur 15 arêtes tirées au sort : 13/15. Borne
# inférieure de Wilson à 95 %. Voir `docs/10-amendements-non-adoptes.md` § 3.
CONFIANCE = 0.6212


def cibles(dispositif: str) -> list[tuple[str, str]]:
    """Articles visés par une formule de modification, avec la formule relevée."""
    texte = sans_balises(dispositif)
    trouves: dict[str, str] = {}
    for m in ARTICLE.finditer(texte):
        cle = f"{m.group(1)}{m.group(2)}-{m.group(3)}" + (f"-{m.group(4)}" if m.group(4) else "")
        if vise_un_autre_code(texte, m.start(), m.end()):
            continue
        suite = APRES.match(texte[m.end():m.end() + 80])
        if suite:
            trouves.setdefault(cle, suite.group(1).lower())
            continue
        amont = AVANT.search(texte[max(0, m.start() - 40):m.start()])
        if amont:
            trouves.setdefault(cle, amont.group(1).lower())
            continue
        if CREATION.search(texte[max(0, m.start() - 20):m.start()]):
            trouves.setdefault(cle, "rédigé")
    return list(trouves.items())


def main() -> None:
    if not 2 <= len(sys.argv) <= 3:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    schema = Path(sys.argv[2]) if len(sys.argv) == 3 else \
        Path(__file__).resolve().parent.parent / "schema" / "003-visee.sql"
    base.execute("PRAGMA foreign_keys = ON")
    base.executescript("DROP VIEW IF EXISTS historique_article; DROP TABLE IF EXISTS vise;")
    base.executescript(schema.read_text(encoding="utf-8"))

    articles = {n: i for i, n in base.execute("SELECT id, numero FROM article")}
    # Un amendement à un projet de loi qui n'a produit aucun article de ce code ne
    # peut pas en viser un. La restriction écarte les dossiers d'environnement,
    # d'urbanisme ou de propriété intellectuelle dont les numéros d'articles
    # coïncident avec les nôtres — dernier reliquat de la confusion de cible, quand
    # le dispositif ne nomme son code nulle part.
    #
    # Le prix est connu et il est réel : un amendement « cavalier » qui tentait
    # d'ajouter une disposition de consommation à un texte étranger disparaît, alors
    # que c'est un cas intéressant. Il est préféré au faux rattachement (§ 5.3).
    dossiers_du_code = {d for (d,) in base.execute(
        "SELECT DISTINCT i.dossier_id FROM issu_de i "
        "JOIN produite_par p ON p.texte_id = i.texte_id")}
    aretes, sans_cible, hors_dossier = [], 0, 0
    for amendement_id, dossier, dispositif in base.execute(
            "SELECT id, dossier_id, dispositif FROM amendement WHERE dispositif IS NOT NULL"):
        if dossier not in dossiers_du_code:
            hors_dossier += 1
            continue
        retenues = [(articles[n], f) for n, f in cibles(dispositif) if n in articles]
        if not retenues:
            sans_cible += 1
            continue
        for article_id, formule in retenues:
            aretes.append((amendement_id, article_id, formule, CONFIANCE))

    base.executemany(
        "INSERT OR IGNORE INTO vise (amendement_id, article_id, formule, confiance)"
        " VALUES (?, ?, ?, ?)", aretes)
    base.commit()

    total = base.execute("SELECT count(*) FROM amendement").fetchone()[0]
    vises, touches = base.execute(
        "SELECT count(DISTINCT amendement_id), count(DISTINCT article_id) FROM vise"
    ).fetchone()
    par_sort = base.execute("""
        SELECT am.sort, count(DISTINCT am.id) FROM vise v
        JOIN amendement am ON am.id = v.amendement_id
        GROUP BY am.sort ORDER BY 2 DESC LIMIT 6""").fetchall()
    en_vigueur = base.execute("""
        SELECT count(DISTINCT a.id) FROM vise v JOIN article a ON a.id = v.article_id
        JOIN version_en_vigueur ver ON ver.article_id = a.id
    """).fetchone()[0]
    violations = base.execute("PRAGMA foreign_key_check").fetchall()

    print(f"amendements en base        : {total}")
    print(f"  avec une cible déclarée  : {vises} ({100 * vises / total:.1f} %)")
    print(f"  sans cible dans ce code  : {sans_cible}")
    print(f"  dossiers ne touchant pas ce code : {hors_dossier}")
    print(f"articles du code visés     : {touches}")
    print(f"  dont en vigueur          : {en_vigueur}")
    print("\npar sort :")
    for sort, n in par_sort:
        print(f"  {sort or '(vide)':24s} {n}")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
