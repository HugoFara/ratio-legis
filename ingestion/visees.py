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
from textes_des_amendements import (ALINEA, ARTICLE_ENTIER, Textes,  # noqa: E402
                                    alineas_nommes, correspondances,
                                    numero_de_subdivision)
from textes_deposes import (contenu_corrobore, mots,  # noqa: E402
                            resolu_par_le_contenu, trigrammes)
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
# Ce qui suit le numéro dans l'en-tête d'un article écrit — « Art. L. 423-17.
# – » —, avant le premier alinéa.
TETE = re.compile(r"\s*(?:\((?:nouveau|non modifié)\))?\s*[.\s]*[–‑-]?\s*", re.I)
# Un amendement qui écrit une division entière — « Section 14 « Appellation
# « artisan restaurateur » « Art. L. 121-97 … » — numérote ses articles
# lui-même, comme celui qui réécrit tout l'article du texte : le numéro n'est
# que le sien. L'amendement 17406 de 2013 met sous « Art. L. 121-99 » la
# recherche des infractions à son appellation ; la loi y a mis les métaux
# précieux, par une autre section adoptée le même jour. Jugée fausse en
# arbitrage (docs/49 § 8).
DIVISION_ECRITE = re.compile(r"«\s*(?:section|sous-section|chapitre|titre)\s+\d", re.I)
# « Rédiger ainsi le premier alinéa : « I. – L'article L. 115-16 est ainsi
# modifié : » » — un chapeau réécrit pour y mettre « I. – », et rien après le
# deux-points. La formule y est, la modification non : deux juges l'ont dite
# fausse (docs/49 § 8). La formule suivie du deux-points et de la fin du
# dispositif n'est pas une cible.
# Le point final après le guillemet (« … est ainsi modifié : ». ) est encore un
# chapeau vide : la garde l'ignorait, et 020e9a44 de `docs/50` est passée.
CHAPEAU_VIDE = re.compile(r"\s*:\s*[»\"]?\s*\.?\s*$")
DEVIENT = re.compile(r"devient\s+l['’]article\s*$", re.I)
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
# La date d'un texte en discussion, telle que son stade l'écrit : « Texte de
# la commission déposé le 28 octobre 2015 ». Un projet déposé n'en porte pas.
MOIS = {m: i + 1 for i, m in enumerate(
    "janvier février mars avril mai juin juillet août septembre octobre "
    "novembre décembre".split())}
DATE = re.compile(r"(\d{1,2})(?:er)?\s+(" + "|".join(MOIS) + r")\s+(\d{4})", re.I)


def dates_des_textes(base: sqlite3.Connection) -> tuple[dict[str, str], dict[str, str]]:
    """Par texte discuté, sa date ; par dossier, la plus ancienne de ses textes.

    C'est à cette date qu'un amendement nomme un article, et non à celle de la
    loi promulguée, des mois après — le temps d'une recodification (`lignees`).
    """
    par_texte, par_dossier = {}, {}
    for texte_id, dossier, stade in base.execute(
            "SELECT id, dossier_id, stade FROM texte_discute"):
        trouve = DATE.search(stade)
        if not trouve:
            continue
        date = f"{trouve.group(3)}-{MOIS[trouve.group(2).lower()]:02d}-{int(trouve.group(1)):02d}"
        par_texte[texte_id] = date
        if date < par_dossier.get(dossier, "9999"):
            par_dossier[dossier] = date
    return par_texte, par_dossier


def bornes(texte: str, debut: int, fin: int) -> tuple[int, int]:
    """La clause qui contient la référence : d'une borne à la suivante."""
    gauche = max((m.end() for m in BORNE.finditer(texte, 0, debut)), default=0)
    droite = BORNE.search(texte, fin)
    return gauche, droite.start() if droite else len(texte)


class Instruction:
    """Les noms de code d'un dispositif, avec le bloc guillemeté qui les porte.

    Ce qu'un dispositif met entre « » est le texte qu'il insère ; un code nommé
    là ne qualifie pas un numéro écrit hors de ce bloc. « Après le deuxième
    alinéa de l'article L. 411-1 du code de la mutualité, sont insérés deux
    alinéas : « … régis par le présent code. » » se rattachait à notre L. 411-1
    par ce « présent code », qui est celui de la mutualité ; « Le code des
    assurances est ainsi modifié : … « p) … L. 531-1 du code de la
    consommation ; » 3° L'article L. 512-1 est ainsi rédigé » rattachait
    L. 512-1 à notre code par la liste citée au p). Deux arêtes jugées fausses
    (`docs/48` § 3), une seule cause.

    Mais le bloc n'est pas un masque : un amendement de l'Assemblée qui
    complète un article du projet de loi met **tout** entre guillemets —
    « V. – Le livre Ier du code de la consommation est ainsi modifié : « 2°
    L'article L. 113-9 est abrogé » — et le code nommé en tête du bloc
    gouverne les numéros du même bloc. La règle est donc : un nom de code
    vaut pour un numéro si le bloc qui contient le nom contient aussi le
    numéro, ou si le nom n'est dans aucun bloc.

    Les blocs suivent la convention de légistique : chaque alinéa inséré
    ouvre un guillemet, seul le dernier le ferme. Un « qui suit un point ou
    un point-virgule, à l'intérieur d'un bloc, continue ce bloc ; tout autre
    « en ouvre un, imbriqué ; un » ferme le plus récent. Un bloc jamais fermé
    court jusqu'à la fin.
    """

    def __init__(self, texte: str) -> None:
        blocs: list[list[int]] = []          # [ouverture, fermeture]
        pile: list[list[int]] = []
        for i, c in enumerate(texte):
            if c == "«":
                j = i - 1
                while j >= 0 and texte[j].isspace():
                    j -= 1
                if pile and j >= 0 and texte[j] in ".;":
                    continue
                bloc = [i, len(texte)]
                blocs.append(bloc)
                pile.append(bloc)
            elif c == "»" and pile:
                pile.pop()[1] = i
        # (début, fin, nom, bloc englobant le plus étroit)
        self.noms: list[tuple[int, int, str, tuple[int, int] | None]] = []
        for m in CODE_NOMME.finditer(texte):
            dedans = [b for b in blocs if b[0] < m.start() < b[1]]
            bloc = max(dedans, key=lambda b: b[0]) if dedans else None
            self.noms.append((m.start(), m.end(), m.group(0).lower(),
                              tuple(bloc) if bloc else None))

    def visibles(self, position: int, gauche: int = 0, droite: int | None = None
                 ) -> list[tuple[int, str]]:
        """Les noms entre `gauche` et `droite` qui valent pour `position`."""
        return [(d, nom) for d, f, nom, bloc in self.noms
                if d >= gauche and (droite is None or f <= droite)
                and (bloc is None or bloc[0] < position < bloc[1])]


# « Le présent code », « ce code », « le même code » ne nomment pas un code :
# ils renvoient à celui qui les gouverne.
ANAPHORE = re.compile(r"^(?:\S+\s+)?(?:(?:présent|même)\s+)?code$", re.I)


def vise_un_autre_code(texte: str, debut: int, fin: int, instruction: Instruction) -> bool:
    """Vrai si la clause nomme un code, et que ce n'est pas celui-ci."""
    noms = [nom for _, nom in instruction.visibles(debut, *bornes(texte, debut, fin))]
    if not noms:
        # Le code est souvent nommé une seule fois, en tête du bloc modificateur :
        # « Le code de l'énergie est ainsi modifié : 1° … "Art. L. 241-2-…" ». La
        # clause ne le contient pas, mais il gouverne tout ce qui suit. Même
        # convention que « du même code » dans la tranche des renvois.
        #
        # Le dernier **nom** de code, non la dernière anaphore : l'amendement
        # 47111 modifie « le code de l'action sociale », et le « du présent
        # code » écrit dans l'alinéa qu'il y insère faisait passer ses L. 314-7
        # et L. 315-14 pour les nôtres (`docs/50` § 7). Faute de nom, l'anaphore
        # garde son sens d'avant.
        amont = instruction.visibles(debut, 0, debut)
        if not amont:
            return False
        nommes = [nom for _, nom in amont if not ANAPHORE.match(nom.strip())]
        noms = [(nommes or [amont[-1][1]])[-1]]
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
# Le 21 septembre 2026 (docs/49), le bloc guillemeté, la date du texte et le
# contenu de l'article écrit retirent 86 arêtes et en ajoutent 13. Re-mesurée
# le même jour sur la population d'aujourd'hui, deux juges Sonnet 5 par fiche
# et un arbitre : un tirage disjoint de 20, les 11 nouvelles, puis un second
# tirage disjoint de 20 après les corrections que les deux premiers ont
# dictées (lignée mort-née, division écrite, chapeau vide) — **47 justes sur
# 50**, réunis et dédoublonnés, Wilson 0,8378. Les trois fausses sont chacune
# la cause d'une garde ; la population d'après n'a pas de tirage à elle.
# Le 24 septembre 2026 (docs/50), 164 arêtes nouvelles — législatures XVI et
# XVII, loi Hamon complète, onze dossiers de plus. Vingt d'entre elles, deux
# juges Sonnet 5 d'accord partout : **17 sur 20**. Les trois fausses ont dicté
# deux gardes : le chapeau vide suivi d'un point, et l'anaphore — « du présent
# code » écrit dans l'alinéa inséré au code de l'action sociale n'est pas le
# nôtre. Réunies aux 50 d'avant : **64 sur 70**, Wilson 0,8253.
CONFIANCE = 0.8253
# L'article que le contenu désigne quand le numéro écrit n'est pas le bon
# (`docs/50`). Mesurée à part, sur cette seule population, le 24 septembre
# 2026 : les treize arêtes d'avant la garde des articles créés, deux juges
# Sonnet 5 et un arbitre Opus 5 sur l'unique désaccord — 10 justes sur 13,
# et les trois fausses sont les seules à viser un article que la loi n'a pas
# créé. Après la garde, 10 sur 10 : Wilson 0,7225. La garde est choisie sur
# l'échantillon qui la mesure ; la population n'a pas d'autre membre à tirer.
CONFIANCE_CONTENU = 0.7225
MOTS_MINI_RESOLUTION = 20


def code_nomme(texte: str, debut: int, fin: int, instruction: Instruction) -> bool:
    """Le dispositif nomme-t-il un code — le nôtre — pour cette référence ?"""
    return bool(instruction.visibles(debut, *bornes(texte, debut, fin))
                or instruction.visibles(debut, 0, debut))


def alinea_ecrit(texte: str, position: int, en_tete: int) -> tuple[list[str], str]:
    """Les mots du premier alinéa qu'un amendement écrit sous l'en-tête dont
    le numéro finit à `position` : jusqu'au guillemet suivant, qui ouvre
    l'alinéa d'après ou ferme le bloc. Avec la fenêtre du dispositif, depuis
    l'en-tête, qui sert de preuve quand le contenu désigne l'article."""
    debut = TETE.match(texte, position).end()
    fin = min((i for i in (texte.find("«", debut), texte.find("»", debut)) if i >= 0),
              default=len(texte))
    return mots(texte[debut:fin]), texte[en_tete:fin].strip()


def cibles(dispositif: str
           ) -> list[tuple[str, tuple[str, bool, tuple[list[str], str] | None]]]:
    """Articles visés par une formule de modification :
    (numéro, (formule, code nommé, alinéa écrit)).

    `code nommé` dit si le dispositif désigne lui-même le code de la
    consommation. Sans cela, « L. 122-3 » d'un amendement au code forestier se
    rattachait à notre L. 122-3 : le dispositif ne nomme pas son code quand
    l'article du texte le dit pour lui. Neuf arêtes sur vingt du premier
    tirage (docs/43) : c'est la voie non nommée qui les portait toutes.

    `alinéa écrit` n'est là que pour l'article que le dispositif rédige sous
    un numéro — « Art. L. 121-104. – Lorsque… » — : ce qu'il met sous ce
    numéro, pour le comparer à ce que la loi y a mis.
    """
    # Tirets insécables et espaces fines des sites des chambres : « L. 223‑1 »
    # n'était pas lu.
    texte = sans_balises(dispositif).translate(TIRETS)
    instruction = Instruction(texte)
    trouves: dict[str, tuple[str, bool, tuple[list[str], str] | None]] = {}
    for m in ARTICLE.finditer(texte):
        cle = f"{m.group(1)}{m.group(2)}-{m.group(3)}" + (f"-{m.group(4)}" if m.group(4) else "")
        if vise_un_autre_code(texte, m.start(), m.end(), instruction):
            continue
        if ANCRE.search(texte[max(0, m.start() - 40):m.start()]):
            continue
        nomme = code_nomme(texte, m.start(), m.end(), instruction)
        suite = APRES.match(texte[m.end():m.end() + 80])
        if suite:
            # Le chapeau qui renumérote n'est pas vide pour le numéro qu'il donne :
            # « L'article L. 121-20-13 […] devient l'article L. 121-30 et le I est
            # ainsi modifié : » vise L. 121-30, jugée juste (docs/46).
            if CHAPEAU_VIDE.match(texte, m.end() + suite.end()) \
                    and not DEVIENT.search(texte[max(0, m.start() - 30):m.start()]):
                continue
            trouves.setdefault(cle, (suite.group(1).lower(), nomme, None))
            continue
        amont = AVANT.search(texte[max(0, m.start() - 40):m.start()])
        if amont:
            trouves.setdefault(cle, (amont.group(1).lower(), nomme, None))
            continue
        if CREATION.search(texte[max(0, m.start() - 20):m.start()]):
            trouves.setdefault(cle, ("rédigé", nomme, alinea_ecrit(texte, m.end(), m.start())))
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
    # Le numéro que le texte écrit et que la loi n'a pas gardé (docs/47) : le
    # premier alinéa écrit sous « Art. L. 423-8 » est celui du L. 423-16
    # promulgué, `porte_sur` l'a vu au contenu — et l'a résolu quand une seule
    # version produite par la loi le contient, tenu pour non résolu sinon. Un
    # amendement qui rédige « Art. L. 423-8 » sur ce texte rédige le même
    # article mal numéroté : il vise L. 423-16, ou rien.
    glisses: dict[tuple[str, str, str], int | None] = {}
    for texte_id, article_du_texte, cle, article_id, portee in base.execute(
            "SELECT ps.texte_id, lower(ps.article_du_texte), ps.numero_cite, "
            "       ps.article_id, ps.portee "
            "FROM porte_sur ps JOIN preuve p ON p.id = ps.preuve_id "
            "WHERE p.methode = 'article_cree' "
            "  AND (ps.portee = 'non_resolue' OR ps.methode = 'inferee')"):
        glisses[(texte_id, article_du_texte, cle.replace(" ", ""))] = (
            article_id if portee == "interne" else None)
    textes = Textes(base, Path(__file__).resolve().parent.parent / "travail" / "corpus" / "textes")
    # **Ce que l'amendement écrit sous le numéro, comparé à ce que la loi y a
    # mis** — la corroboration par le contenu de `textes_deposes`, portée à
    # l'amendement lui-même (`docs/46` § 4 l'annonçait, `docs/49` le fait).
    # Trois familles, que la part des trigrammes de l'alinéa écrit sépare :
    #
    # - **le numéro a glissé** : l'amendement 4384 de 2013 rédige « Art.
    #   L. 121-109 », et la loi a mis ce texte sous L. 121-110 — à 1,0, et
    #   0,0 sous L. 121-109. Le contenu désigne un autre article de la même
    #   loi, seul au-dessus du seuil : le numéro ne vaut rien, l'arête n'est
    #   pas posée. Elle n'est pas non plus résolue vers l'article désigné —
    #   ce serait une population nouvelle, non mesurée ; elle est comptée ;
    # - **le plan propre** : l'amendement 4495 réécrit tout l'article 1er de
    #   2013 selon son propre plan, et met sous « Art. L. 423-17 » un texte
    #   que la loi n'a mis nulle part — 0,0 partout. Sous un article du
    #   texte réécrit en entier, le numéro n'est que celui de l'amendement ;
    #   il ne vaut que corroboré par le contenu. Onze arêtes sur quatorze
    #   jugées fausses pour cette cause (`docs/47` § 4) ; la garde d'alors
    #   n'attrapait que les numéros que `porte_sur` savait glissés, et
    #   L. 423-17 ← 4495, jugée fausse, revenait dès que le nom de code cité
    #   qui l'écartait par hasard cessait de compter ;
    # - **l'autre rédaction** : l'amendement 3146 rédige « Art. L. 121-104 »
    #   à sa façon, sous le plan du texte, et sa version ressemble à rien de
    #   promulgué — c'est un amendement rejeté, sa rédaction diffère par
    #   construction. Il vise bien L. 121-104 : le numéro tient.
    versions_produites: dict[tuple[str, int], str] = {}
    for dossier_id, article_id, texte_version in base.execute(
            "SELECT i.dossier_id, v.article_id, v.texte FROM issu_de i "
            "JOIN produite_par p ON p.texte_id = i.texte_id "
            "JOIN version_article v ON v.id_legi = p.version_id ORDER BY v.date_debut"):
        versions_produites.setdefault((dossier_id, article_id), texte_version)
    # Les lignées dont la première version vient d'un texte du dossier.
    crees_par_le_dossier: dict[str, set[int]] = defaultdict(set)
    for dossier_id, article_id in base.execute("""
            SELECT i.dossier_id, v.article_id FROM issu_de i
            JOIN produite_par p ON p.texte_id = i.texte_id
            JOIN version_article v ON v.id_legi = p.version_id
            WHERE v.date_debut = (SELECT min(date_debut) FROM version_article
                                  WHERE article_id = v.article_id)"""):
        crees_par_le_dossier[dossier_id].add(article_id)
    trigrammes_produits: dict[str, dict[int, set[tuple[str, ...]]]] = defaultdict(dict)
    for (dossier_id, article_id), texte_version in versions_produites.items():
        trigrammes_produits[dossier_id][article_id] = trigrammes(mots(texte_version))

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
    date_du_texte, date_du_dossier = dates_des_textes(base)
    # Un article que le dispositif **crée** sous un numéro (« Art. L. 121-105. – »)
    # n'est le nôtre que si la loi du dossier a bien écrit ce numéro : la
    # numérotation proposée par un projet glisse en navette (docs/41 § 2).
    aretes, sans_cible, hors_dossier, hote_etranger, numero_glisse = [], 0, 0, 0, 0
    resolues: list[tuple[int, int, str, str]] = []
    par_l_instruction, glisse_dans_le_texte, suivi_par_le_contenu = 0, 0, 0
    plan_propre, corrobore, glisse_par_le_contenu, plan_propre_non_corrobore = 0, 0, 0, 0
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
        for n, (formule, nomme, redaction) in cibles(dispositif):
            ecrit, fenetre = redaction if redaction else (None, "")
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
            # À la date du texte discuté ; à défaut, du plus ancien texte du
            # dossier ; à défaut, de la loi. Sans cela « L. 141-3 » de 2015
            # se résolvait vers la lignée de 2024 (`docs/48` § 3).
            article_id = resolveur.du_dossier(
                n, dossier, date_du_texte.get(texte_id or "") or date_du_dossier.get(dossier))
            if article_id is None:
                continue
            if formule == "rédigé" and article_id not in resolveur.ecrits.get(dossier, ()):
                numero_glisse += 1
                continue
            if formule == "rédigé" and texte_id and numero \
                    and (texte_id, numero, n) in glisses:
                # Suivre le glissement suppose que l'amendement numérote
                # comme le texte : vrai quand il réécrit un alinéa du texte
                # (« Rédiger ainsi l'alinéa 41 : « Art. L. 423-8. – … » »),
                # faux quand il réécrit tout l'article du texte selon son
                # propre plan — les amendements 3661 et 4495 de 2013 écrivent
                # L. 423-1 à L. 423-17 avec un autre contenu à chaque numéro.
                # Onze arêtes sur quatorze jugées fausses pour cette seule
                # cause (docs/47 § 4) : sous un article du texte dont la
                # numérotation a glissé, le plan propre ne se rattache pas.
                if ARTICLE_ENTIER.search(dispositif):
                    plan_propre += 1
                    continue
                article_id = glisses[(texte_id, numero, n)]
                if article_id is None:
                    glisse_dans_le_texte += 1
                    continue
                suivi_par_le_contenu += 1
            elif ecrit is not None:
                accord = contenu_corrobore(ecrit, versions_produites.get((dossier, article_id)))
                if accord:
                    corrobore += 1
                else:
                    autre = resolu_par_le_contenu(ecrit, trigrammes_produits[dossier])
                    if autre is not None and autre != article_id:
                        glisse_par_le_contenu += 1
                        # Le numéro ne vaut rien ; le contenu, seul au-dessus du
                        # seuil, désigne l'article. Posé en `inferee`, avec sa
                        # fenêtre et sa constante propre, à partir d'un alinéa
                        # assez long pour que la concordance ne soit pas celle
                        # d'une formule : 3532 (« Art. L. 121-104 », treize
                        # mots) tombait à 0,64 sur L121-87, qui n'a rien à voir.
                        #
                        # Et vers un article que la loi du dossier a **créé** :
                        # l'amendement qui écrit « Art. L. X. – … » crée un
                        # article, et si son alinéa se retrouve dans un article
                        # que la loi n'a fait que modifier, c'est une formule
                        # qu'il recopie — la définition du crédit renouvelable
                        # de L. 311-16 pour l'interdire, la sanction de L. 121-82
                        # pour la boulangerie appliquée à la pâtisserie, la
                        # reconduction tacite de L. 136-1 collée sous le gaz de
                        # pétrole liquéfié. Jugées fausses toutes trois, et les
                        # seules du tirage à viser un article préexistant.
                        if len(ecrit) >= MOTS_MINI_RESOLUTION and len(fenetre) >= 60 \
                                and autre in crees_par_le_dossier[dossier]:
                            resolues.append((amendement_id, autre, formule, fenetre))
                        continue
                    if ARTICLE_ENTIER.search(dispositif) or DIVISION_ECRITE.search(dispositif):
                        plan_propre_non_corrobore += 1
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
    # Une arête déclarée par le numéro prime : l'amendement qui vise déjà
    # l'article désigné par le contenu n'en reçoit pas une seconde.
    suivante = base.execute("SELECT coalesce(max(id), 0) + 1 FROM preuve").fetchone()[0]
    posees_par_le_contenu = 0
    for amendement_id, article_id, formule, fenetre in resolues:
        if base.execute("SELECT 1 FROM vise WHERE amendement_id = ? AND article_id = ?",
                        (amendement_id, article_id)).fetchone():
            continue
        base.execute("INSERT INTO preuve (id, methode, fenetre) VALUES (?, ?, ?)",
                     (suivante, "contenu_de_l_article_ecrit", fenetre))
        base.execute("INSERT INTO vise (amendement_id, article_id, formule, methode, "
                     "confiance, preuve_id) VALUES (?, ?, ?, 'inferee', ?, ?)",
                     (amendement_id, article_id, formule, CONFIANCE_CONTENU, suivante))
        suivante += 1
        posees_par_le_contenu += 1
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
    print(f"  article rédigé sous un numéro que le texte écrit et que la loi a "
          f"donné à un autre : {glisse_dans_le_texte} non résolus, "
          f"{suivi_par_le_contenu} suivis vers l'article que le contenu désigne, "
          f"{plan_propre} écartés — l'article du texte réécrit en entier, plan propre")
    print(f"  article rédigé sous un numéro que la loi a écrit : {corrobore} au contenu "
          f"de la loi ; {glisse_par_le_contenu} dont le contenu désigne un autre article "
          f"de la loi, {plan_propre_non_corrobore} sous un plan propre que rien ne "
          f"corrobore — non rattachés")
    print(f"  dont posés vers l'article que le contenu désigne (inferee) : "
          f"{posees_par_le_contenu}")
    print(f"articles du code visés     : {touches}")
    print(f"  dont en vigueur          : {en_vigueur}")
    print("\npar sort :")
    for sort, n in par_sort:
        print(f"  {sort or '(vide)':24s} {n}")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
