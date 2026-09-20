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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "prototype"))
from resolveur import sans_balises  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lignees import Resolveur  # noqa: E402
from textes_des_amendements import (ALINEA, Textes, alineas_nommes,  # noqa: E402
                                    correspondances, numero_de_subdivision)
from collections import defaultdict  # noqa: E402


def corpus_vers_texte(base: sqlite3.Connection) -> dict[tuple[str, str], str]:
    """(chambre, clef du corpus d'amendements) → texte en discussion apparié."""
    return {(chambre, corpus): texte_id for chambre, corpus, texte_id in correspondances(base)}

# La négation finale interdit de tronquer : « L. 111-6-1-3 » du code de la
# construction se lisait « L. 111-6-1 », qui existe au code de la consommation.
# Le suffixe en lettre appartient au numéro : « Art. L. 222-1 B » du code de
# l'environnement n'est pas L. 222-1 du code de la consommation. Le laisser tomber
# fabriquait une identité entre deux articles sans rapport.
# « L. 312-9-… » — l'article nouveau dont le numéro n'est pas fixé — n'est pas
# L. 312-9 : le tiret suivi de n'importe quoi d'autre qu'un blanc ferme la lecture.
ARTICLE = re.compile(
    r"\b([LRD])\.?\s?(\d{3,4})-(\d{1,3})(?:-(\d{1,3}))?(?!\s?-\s?\S)(?!\s[A-Z]\b)")

# Formules de modification de la légistique française. Relevées après le numéro,
# dans la fenêtre qui suit immédiatement : « L'article L. 121-36 est ainsi rédigé ».
APRES = re.compile(
    r"^[^.;«»]{0,60}?\b(?:est|sont)\s+(?:ainsi\s+)?"
    r"(r[ée]dig[ée]s?|modifi[ée]s?|compl[ée]t[ée]s?|abrog[ée]s?|remplac[ée]s?|ins[ée]r[ée]s?)",
    re.I)
# Formules qui précèdent le numéro : « Au début de l'article L. 121-36, … ».
# « Après l'article L. 121-36, il est inséré un article L. 121-36-1 » n'y est
# plus : L. 121-36 y est une **ancre**, pas une cible — l'amendement ne le
# modifie en rien, il place un article nouveau après lui. Trois juges l'ont dit
# sur trois arêtes (docs/42 § 3) ; `ANCRE` l'écarte.
AVANT = re.compile(
    r"\b(au d[ée]but de|à la fin de)\s+(?:le|la|l['’])?\s*article\s*$", re.I)
ANCRE = re.compile(r"\b(?:apr[èe]s|avant|à la suite de)\s+(?:le|la|l['’])?\s*article\s*$", re.I)
# Un amendement à un projet de loi de consommation ne nomme pas l'article du code
# comme cible : il le rédige. « Insérer trois alinéas ainsi rédigés : "Art.
# L. 121-104. – Lorsque le consommateur…" ». Sans cette forme, les amendements des
# dossiers les plus lourds du périmètre — ceux qui écrivent le code — étaient
# précisément ceux qu'on ne voyait pas.
CREATION = re.compile(r"[«\"]\s*(?:art|article)\.?\s*$", re.I)
TIRETS = str.maketrans({"\u2011": "-", "\u2010": "-", "\u00a0": " ", "\u202f": " "})

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


# Précision mesurée à la main sur 15 arêtes tirées au sort en août : 13/15
# (`docs/10` § 3). Re-mesurée le 19 septembre 2026 par deux juges indépendants
# (deepseek-v4p1-flash, glm-5p3-flash, qwen3p8-max en arbitrage) après les
# gardes du code hôte et du numéro glissé : **16 justes, 2 fausses, 2 douteuses
# sur 20** — Wilson 0,5840 (`precision-vise-2.tsv`, `docs/43`). Avant les
# gardes, 9 sur 20 : le tiret insécable avait triplé l'arête, et la moitié du
# gain était des homonymes d'autres codes. Troisième tirage, disjoint, après la
# règle « hôte inconnu = pas de rattachement » : **20 sur 20** (docs/44),
# Wilson 0,8389. Réunis, 36 justes sur 40 ; la constante prend le dernier
# tirage, comme pour toutes les arêtes dont la population a changé entre deux.
# Le 20 septembre 2026, le numéro nu sous un article multi-codes rattaché par
# l'instruction (docs/46) ajoute 40 arêtes sans en retirer : 20 d'entre
# elles jugées par deux agents Sonnet, **19 sur 20**, un arbitrage — la
# fausse est un numéro glissé que la garde ne voit pas (§ 4 de docs/46). Les
# deux tirages décrivent ensemble la population d'aujourd'hui : 39 sur 40.
CONFIANCE = 0.8712


def code_nomme(texte: str, debut: int, fin: int) -> bool:
    """Le dispositif nomme-t-il un code — le nôtre — pour cette référence ?"""
    if CODE_NOMME.search(clause(texte, debut, fin)):
        return True
    return bool(list(CODE_NOMME.finditer(texte, 0, debut)))


def cibles(dispositif: str) -> list[tuple[str, tuple[str, bool]]]:
    """Articles visés par une formule de modification : (numéro, (formule, code nommé)).

    `code nommé` dit si le dispositif désigne lui-même le code de la
    consommation. Sans cela, « L. 122-3 » d'un amendement au code forestier se
    rattachait à notre L. 122-3 : le dispositif ne nomme pas son code quand
    l'article du texte le dit pour lui. Neuf arêtes sur vingt du premier
    tirage (docs/43) : c'est la voie non nommée qui les portait toutes.
    """
    # Tirets insécables et espaces fines des sites des chambres : « L. 223‑1 »
    # n'était pas lu.
    texte = sans_balises(dispositif).translate(TIRETS)
    trouves: dict[str, tuple[str, bool]] = {}
    for m in ARTICLE.finditer(texte):
        cle = f"{m.group(1)}{m.group(2)}-{m.group(3)}" + (f"-{m.group(4)}" if m.group(4) else "")
        if vise_un_autre_code(texte, m.start(), m.end()):
            continue
        if ANCRE.search(texte[max(0, m.start() - 40):m.start()]):
            continue
        nomme = code_nomme(texte, m.start(), m.end())
        suite = APRES.match(texte[m.end():m.end() + 80])
        if suite:
            trouves.setdefault(cle, (suite.group(1).lower(), nomme))
            continue
        amont = AVANT.search(texte[max(0, m.start() - 40):m.start()])
        if amont:
            trouves.setdefault(cle, (amont.group(1).lower(), nomme))
            continue
        if CREATION.search(texte[max(0, m.start() - 20):m.start()]):
            trouves.setdefault(cle, ("rédigé", nomme))
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

    resolveur = Resolveur(base)   # le numéro visé se résout à la date du dossier
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
    # Le code hôte de l'article du texte sur lequel l'amendement est déposé :
    # `porte_sur` sait quels codes cet article modifie. Un dispositif qui ne
    # nomme pas son code hérite de celui-là ; s'il n'est pas le nôtre, ou si
    # l'article du texte en modifie plusieurs, le numéro nu ne se rattache pas.
    hote: dict[tuple[str, str], set[str]] = defaultdict(set)
    # Et, plus fin que l'article du texte, **l'instruction** (docs/45 § 6).
    # Sous un article de texte qui modifie le code de commerce au I et le
    # nôtre au II, « l'article L. 223-5 » sans code n'était pas rattaché :
    # l'hôte de l'article est double. Mais l'hôte de l'instruction ne l'est
    # pas, et deux choses le disent. Le numéro lui-même, quand `porte_sur` l'a
    # relevé dans cet article du texte comme une cible de notre code et de nul
    # autre : le texte modifie notre L. 223-5 là, l'amendement qui le nomme y
    # parle de lui. Sinon l'alinéa que le dispositif nomme, dont l'instruction
    # gouvernante est connue de `porte_sur` avec sa portée : « Après l'alinéa 8,
    # insérer : « …° À l'article L. 111-3, … » » sous une instruction sur
    # notre code s'y trouve, sous une instruction sur un autre code, non.
    mentions: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    mentions_id: dict[tuple[str, str], dict[str, int | None]] = defaultdict(dict)
    for texte_id, article_du_texte, portee, cle, article_id in base.execute(
            "SELECT texte_id, lower(article_du_texte), portee, numero_cite, article_id "
            "FROM porte_sur"):
        hote[(texte_id, article_du_texte)].add("interne" if portee == "interne" else "autre")
        mentions[(texte_id, article_du_texte)][cle.replace(" ", "")].add(portee)
        mentions_id[(texte_id, article_du_texte)][cle.replace(" ", "")] = (
            article_id if portee == "interne" else None)
    textes = Textes(base, Path(__file__).resolve().parent.parent / "travail" / "corpus" / "textes")

    def hote_de_l_instruction(texte_id: str, numero: str, n: str, dispositif: str) -> bool:
        """Le numéro nu `n` désigne-t-il notre code, à en juger par l'instruction
        du texte qui le porte ou qui gouverne l'alinéa nommé ?"""
        portees = mentions.get((texte_id, numero), {}).get(n)
        if portees:
            return portees == {"interne"}
        trouve = ALINEA.search(dispositif)
        if not trouve:
            return False
        cible = textes.gouvernant(texte_id, numero, alineas_nommes(trouve),
                                  mentions_id.get((texte_id, numero), {}))
        return isinstance(cible, list)
    textes_du_corpus = corpus_vers_texte(base)
    # Un article que le dispositif **crée** sous un numéro (« Art. L. 121-105. – »)
    # n'est le nôtre que si la loi du dossier a bien écrit ce numéro : la
    # numérotation proposée par un projet glisse en navette (docs/41 § 2).
    aretes, sans_cible, hors_dossier, hote_etranger, numero_glisse = [], 0, 0, 0, 0
    par_l_instruction = 0
    for amendement_id, dossier, dispositif, chambre, corpus, subdivision in base.execute(
            "SELECT id, dossier_id, dispositif, chambre, texte_discute, subdivision "
            "FROM amendement WHERE dispositif IS NOT NULL"):
        if dossier not in dossiers_du_code:
            hors_dossier += 1
            continue
        codes_de_l_hote = None
        texte_id = textes_du_corpus.get((chambre, corpus))
        numero = numero_de_subdivision(subdivision)
        if texte_id and numero:
            codes_de_l_hote = hote.get((texte_id, numero))
        retenues = []
        for n, (formule, nomme) in cibles(dispositif):
            # Sans code nommé, le numéro ne vaut que par son hôte ; hôte étranger,
            # hôte multi-codes, ou hôte inconnu — jeu d'amendements non apparié à
            # un texte — : on ne rattache pas. Dix amendements y perdent leur
            # arête, dont celui qui complétait « L. 131-4 » du code de
            # l'environnement (docs/43 § 2) ; c'est le prix de la règle § 5.3.
            if not nomme and codes_de_l_hote != {"interne"}:
                if codes_de_l_hote and "interne" in codes_de_l_hote and texte_id \
                        and hote_de_l_instruction(texte_id, numero, n, dispositif):
                    par_l_instruction += 1
                else:
                    hote_etranger += 1
                    continue
            article_id = resolveur.du_dossier(n, dossier)
            if article_id is None:
                continue
            if formule == "rédigé" and article_id not in resolveur.ecrits.get(dossier, ()):
                numero_glisse += 1
                continue
            retenues.append((article_id, formule))
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
    print(f"  numéro nu, article du texte hors de ce code ou multi-codes : {hote_etranger}")
    print(f"  numéro nu sous un article multi-codes, rattaché par l'instruction : "
          f"{par_l_instruction}")
    print(f"  article créé sous un numéro que la loi n'a pas écrit : {numero_glisse}")
    print(f"articles du code visés     : {touches}")
    print(f"  dont en vigueur          : {en_vigueur}")
    print("\npar sort :")
    for sort, n in par_sort:
        print(f"  {sort or '(vide)':24s} {n}")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
