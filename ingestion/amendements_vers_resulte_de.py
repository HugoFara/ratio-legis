#!/usr/bin/env python3
"""Quatrième tranche : les amendements, et l'arête `resulte_de`.

C'est l'arête critique du projet — celle qui relie un alinéa du code à
l'amendement qui l'a écrit, avec son auteur et son sort.

**Pourquoi elle devient possible seulement maintenant.** La phase 0 avait établi
qu'aucun des 307 articles issus de la loi de 2014 n'a plus cette loi comme texte
producteur de sa version en vigueur : attachée à l'article, l'arête est vide par
construction sur un corpus recodifié. La solution est le grain du segment. On
n'apparie pas l'amendement au texte d'aujourd'hui — on l'apparie au segment de la
**version que sa propre loi a produite**, et l'arête `repris_de` de la première
tranche porte le lien jusqu'à l'article en vigueur. La chaîne se lit :

    article en vigueur --repris_de*--> segment historique --resulte_de--> amendement

Cette restriction n'est pas qu'une commodité : elle supprime par construction la
confusion inter-dossiers qui avait produit 9 faux rattachements sur 10 dans la
première version du golden set. Un amendement ne peut plus s'accrocher à un
article d'une autre loi, puisque les candidats sont les segments des versions que
sa loi a produites.

Deux garde-fous conservés de la phase 0 :

- **discriminance** : une fenêtre retrouvée dans plusieurs numéros d'articles ne
  prouve rien — sauf si ces numéros désignent le même article de part et d'autre
  d'une renumérotation, ce que `renumerote_de` sait dire. La phase 0 tolérait deux
  numéros au motif que 84 % des cas à deux numéros étaient de cette nature ; la
  condition est ici vérifiée au lieu d'être supposée ;
- **balayage au pas de 1 d'un côté au moins** : indexer les deux côtés à pas fixe
  fait tomber le rattachement de 29 % à 5 % sans qu'aucune donnée ne change.

Seuls les amendements adoptés produisent une arête : un amendement rejeté n'a
écrit aucun texte. Il est chargé comme nœud et reste interrogeable — c'est même
le corpus le plus intéressant pour le législateur, mais ce n'est pas de la
provenance. Ce qu'il visait est porté par l'arête `vise` (`ingestion/visees.py`)
et son sort par `ingestion/sort_des_amendements.py`, d'où vient ici le seul
prédicat « cet amendement a-t-il été adopté ».

**L'hôte de l'alinéa.** Un amendement de l'Assemblée ne nomme pas le code :
il dit « Substituer à l'alinéa 11 les deux alinéas suivants », et l'alinéa 11
de l'article 24 du texte est sous une instruction qui modifie un autre code.
Le passage inséré va là, et sa formule de sanction — la même que la nôtre,
mot pour mot — ne prouve rien sur L. 121-49 (`docs/48` § 3). Ce que
l'instruction du texte gouverne, `porte_sur` le sait et
`textes_des_amendements` le lit (`docs/45` § 6) ; les arêtes se construisent
donc après eux, et le script a deux temps :

    amendements_vers_resulte_de.py <corpus/ameli> <base.sqlite> --noeuds   # charger
    amendements_vers_resulte_de.py <corpus/ameli> <base.sqlite> --aretes   # apparier

Sans indication, les deux à la suite — sans l'hôte de l'alinéa si
`porte_sur` n'est pas encore là.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "prototype"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolveur import (FENETRE, fenetres, lire_ameli,  # noqa: E402
                       normalise, sans_balises)
from sort_des_amendements import est_adopte  # noqa: E402
from textes_des_amendements import (ALINEA, Textes, alineas_nommes,  # noqa: E402
                                    correspondances, numero_de_subdivision)

# Un dispositif d'amendement cite entre guillemets deux choses opposées : le texte
# qu'il insère, et celui qu'il abroge ou remplace. `passages_cites` de la phase 0
# les confondait, ce qui rattachait l'amendement à la rédaction qu'il faisait
# disparaître — sur sept arêtes vérifiées à la main, deux faux et un douteux
# venaient de là. Le sens se lit dans ce qui suit le guillemet fermant, jamais
# dans ce qui le précède : « les mots : X sont remplacés par les mots : Y »
# introduit l'ancien et le nouveau de la même façon.
ARTICLE_CITE = re.compile(r"\b([LRD])\.?\s?(\d{3})-(\d{1,3})(?:-(\d{1,3}))?(?:-(\d{1,3}))?(?!\d)")
# Les dispositifs de l'Assemblée écrivent « L. 116‑1 » avec le trait d'union
# insécable : sans cette table, aucun numéro n'y était lu, et `articles_nommes`
# rendait vide — donc sans contrainte — sur tout amendement de l'Assemblée.
TRAITS = str.maketrans({"\u2011": "-", "\u2010": "-", "\u00a0": " ", "\u202f": " "})

# Intitulé d'un texte cité. `règlement` en est volontairement absent : un article
# qui reprend mot pour mot la référence à un règlement de l'Union le fait parce
# que l'amendement l'y a écrite, et l'échantillon en donne un cas juste.
CITATION = re.compile(r"\b(?:loi|ordonnance|d[ée]cret)\s+n[°º]\s*\d")
PORTEE_TITRE = 80

SORTANT = re.compile(
    r"\s*[,;]?\s*(?:sont|est|seront|sera)\s+(?:remplac|supprim|abrog|ins[ée]r)"
    r"|\s*[,;]\s*(?:il est|ins[ée]rer|ajouter|r[ée]diger)", re.I)

# La convention du Sénat inverse l'ordre : « substituer aux mots : X les mots : Y »
# met le texte sortant AVANT sa marque, là où la rédaction ordinaire le met après.
# `SORTANT`, qui ne lit que l'aval du guillemet fermant, prenait donc la rédaction
# supprimée pour une insertion. Une arête vérifiée sur 120 venait de là.
AVANT_SORTANT = re.compile(
    r"(?:substituer\s+aux?\s+mots|remplacer\s+les\s+mots"
    r"|supprimer\s+les\s+mots)\s*:\s*$", re.I)

# Le texte que l'amendement modifie n'est pas toujours ce code. Un amendement au
# projet de loi consommation insère aussi dans le code de commerce, le code
# monétaire et financier, le code de l'environnement ou une loi non codifiée — et
# les formules de sanction ou de renvoi y sont les mêmes mot pour mot. Huit des
# dix-neuf arêtes fausses de l'échantillon venaient de cette confusion : la
# fenêtre était bien du texte inséré par l'amendement, mais dans un autre texte
# que celui du segment. On retient la dernière mention de texte hôte qui précède
# le guillemet ; l'absence de mention vaut « le même code », par convention
# légistique.
# Les tirets des numéros de loi ne sont pas tous des `-` : les dispositifs du
# Sénat emploient le trait d'union insécable U+2011. « loi n° 78‑17 » échappait
# ainsi à la reconnaissance de l'hôte, et un amendement à la loi Informatique et
# Libertés se rattachait à L. 218-1 du code de la consommation.
TIRETS = "\\u002d\\u2010-\\u2015"
HOTE = re.compile(r"code\s+(?:de\s+la\s+|de\s+l'|du\s+|des\s+|d')?[a-zà-ÿ'’\s]{3,45}"
                  r"|loi\s+n[°º]\s*[\d\s" + TIRETS + r"]{4,12}"
                  r"|ordonnance\s+n[°º]\s*[\d\s" + TIRETS + r"]{4,12}", re.I)

# Un dispositif peut placer la mention de l'hôte **dans** le passage cité, quand
# il ouvre un guillemet sur un paragraphe entier : « III. – L'article L. 44 du
# code des postes … est ainsi modifié : « … ». Regarder ce qui précède le
# guillemet ne suffit alors pas. La marque décisive n'est pas la mention seule —
# un texte inséré cite couramment un autre code sans le modifier — mais la
# mention **suivie d'une formule modificative**.
# « est complété par », « sont insérés » y manquaient : « III. – L'article
# L. 221-10 du code de la mutualité est complété par trois alinéas » passait
# pour du texte du nôtre, et son alinéa — le même que celui que l'amendement
# 526 de 2013 écrit aussi à L. 312-9 — portait l'arête (docs/49 § 8).
MODIFICATIF = re.compile(r"\b(?:est|sont)\s+(?:ainsi\s+)?(?:modifi|r[ée]dig|complét|rétabli"
                         r"|abrog|supprim|remplac|ins[ée]r|ajout)", re.I)
# « dans sa rédaction issue de la loi n° 2013-672 » cite une loi, elle n'en
# fait pas l'hôte : sans cela, le passage suivant — inséré dans notre code —
# passait pour inséré dans cette loi.
LOI_CITEE = re.compile(r"(?:r[ée]daction\s+(?:issue|r[ée]sultant)\s+d[eu]\s+la|modifi[ée]e?\s+par\s+la"
                       r"|pr[ée]vu[es]?\s+par\s+la|au\s+sens\s+de\s+la)\s*$", re.I)

# **La destination d'un passage** : l'article sous lequel l'amendement l'écrit.
# Elle se lit en tête du passage — « Art. L. 116-1. – … » — ou dans
# l'instruction qui l'introduit, à la dernière référence suivie d'une formule
# modificative : « L'article L. 121-79-4 est ainsi rédigé : « … ». Un passage
# destiné à L. 116-1 ne peut pas avoir écrit un alinéa de L. 115-16, même
# s'il le recopie mot pour mot — c'est l'adaptation à Wallis-et-Futuna de
# l'amendement 993 —, ni celui de L. 136-1-1 un alinéa de L. 136-2, ni celui
# de L. 731-3 d'un autre code un alinéa de L. 121-49. Quatre arêtes jugées
# fausses à la main (`docs/21`), que le harnais nommait à chaque passage
# (`docs/48` § 3) ; `articles_nommes` ne les tenait pas, qui relève tout
# numéro cité — L. 115-16 l'est, comme article adapté. La destination est
# une déclaration du rédacteur ; elle prime l'appariement.
TETE_DU_PASSAGE = re.compile(
    r"^\s*(?:[^«»]{0,160}«\s*)?art\.?\s*([LRD])\.?\s?(\d{3})-(\d{1,3})(?:-(\d{1,3}))?(?:-(\d{1,3}))?(?!\d)", re.I)
# Le verbe de l'instruction, quelque part après la référence : « À la dernière
# phrase du premier alinéa de l'article L. 330-1, après le mot : « principale »
# sont insérés les mots : « … » » — la formule ne suit pas le numéro, elle suit
# le repère. Et « Après l'article L. 121-41, il est inséré une section 7 » :
# L. 121-41 est une ancre, jamais une destination (`visees.ANCRE`).
VERBE_MODIFICATIF = re.compile(
    r"\b(?:est|sont)\s+(?:ainsi\s+)?(?:r[ée]dig|modifi|complét|rétabli|ins[ée]r|remplac"
    r"|supprim|abrog|ajout)|\bainsi\s+r[ée]dig", re.I)
FORMULE_DESTINATION = re.compile(
    r"\s*(?:(?:est|sont)\s+(?:ainsi\s+)?(?:r[ée]dig|modifi|complét|rétabli|ins[ée]r|remplac)"
    r"|ainsi\s+r[ée]dig)", re.I)
ANCRE = re.compile(r"\b(?:apr[èe]s|avant|à la suite de)\s+(?:le|la|l['’])?\s*article\s*$", re.I)
PORTEE_DESTINATION = 250


def numero_de(m: re.Match) -> str:
    return f"{m.group(1).upper()}{m.group(2)}-{m.group(3)}" + "".join(f"-{g}" for g in m.groups()[3:5] if g)


def destination_d_instruction(instruction: str) -> str | None:
    """La dernière référence de l'instruction, hors guillemets, qui n'est pas
    une ancre et qu'un verbe modificatif suit."""
    instruction = instruction[max((m.end() for m in re.finditer(
        r"(?<![LRD])(?<!art)(?<!n°)[.;]", instruction)), default=0):]
    instruction = re.sub(r"«[^»]*»", lambda m: " " * len(m.group(0)), instruction)
    trouvee = None
    for ref in ARTICLE_CITE.finditer(instruction):
        if ANCRE.search(instruction[max(0, ref.start() - 30):ref.start()]):
            continue
        if VERBE_MODIFICATIF.search(instruction, ref.end()):
            trouvee = numero_de(ref)
    return trouvee


def destination(texte: str, debut: int, cite: str) -> tuple[str | None, str | None]:
    """(numéro, 'instruction' | 'tete') — ou (None, None).

    Une destination lue dans une **instruction** est une déclaration ; lue en
    **tête** du passage — « Art. L. 121-47. – » —, c'est le numéro que
    l'amendement s'est donné, et la navette le change : l'appariement le
    corrige, l'instruction non. L'instruction peut être dans le guillemet
    lui-même, quand l'amendement cite tout son paragraphe : « I. – L'article
    L. 312-9 du code de la consommation … est ainsi rédigé : « Art. L. 312-9.
    – … » » — elle est alors lue avant le premier guillemet intérieur.
    """
    interieur = cite.find("«")
    if interieur > 0:
        lue = destination_d_instruction(cite[:interieur])
        if lue:
            return lue, "instruction"
    tete = TETE_DU_PASSAGE.match(cite)
    if tete:
        return numero_de(tete), "tete"
    lue = destination_d_instruction(texte[max(0, debut - PORTEE_DESTINATION):debut])
    return (lue, "instruction") if lue else (None, None)


# « Le 14° de l'article 28 de la même loi est ainsi rédigé » : l'hôte est une
# loi nommée plus haut dans le texte, pas dans le dispositif — `HOTE` ne le
# voyait pas, et « la même loi » valait « le même code ». Un amendement de
# 2007 à la loi sur l'audiovisuel se rattachait à L. 121-83 par « l'article
# L. 32 du code des postes » (docs/49 § 8). Le verbe modificatif est exigé,
# pour ne pas prendre « la présente loi » d'un texte inséré pour un hôte.
LOI_IMPLICITE = re.compile(
    r"\b(?:même|présente|ladite)\s+loi\b[^«»]{0,80}?\b(?:est|sont)\s+(?:ainsi\s+)?"
    r"(?:r[ée]dig|modifi|complét|abrog|remplac|ins[ée]r|supprim)", re.I)


def passages_inseres(dispositif: str) -> list[tuple[tuple[str | None, str | None], str]]:
    """Passages que l'amendement introduit, à l'exclusion de ceux qu'il retire,
    chacun avec sa destination quand le rédacteur la dit.

    Un passage suivi de « sont remplacés », « est supprimé » ou « il est inséré »
    n'est pas du texte nouveau : c'est la rédaction visée, ou un simple repère de
    position dans l'article. Un passage précédé de « substituer aux mots : » ne
    l'est pas davantage, et un passage inséré dans un autre texte que ce code ne
    peut pas expliquer un segment de ce code.
    """
    texte = sans_balises(dispositif).translate(TRAITS)
    hotes = [(m.start(), normalise(m.group(0))) for m in HOTE.finditer(texte)
             if not LOI_CITEE.search(texte[max(0, m.start() - 40):m.start()])]
    gardes = []
    for m in re.finditer(r"«(.+?)»", texte, re.S):
        if SORTANT.match(texte[m.end():m.end() + 60]):
            continue
        if AVANT_SORTANT.search(texte[max(0, m.start() - 40):m.start()]):
            continue
        precedents = [nom for depart, nom in hotes if depart < m.start()]
        if precedents and "consommation" not in precedents[-1]:
            continue
        derniere_loi = max((h.start() for h in LOI_IMPLICITE.finditer(texte, 0, m.start())),
                           default=-1)
        if derniere_loi >= 0 and all(depart < derniere_loi for depart, _ in hotes
                                     if depart < m.start()):
            continue
        cite = m.group(1)
        if any("consommation" not in normalise(interne.group(0))
               and MODIFICATIF.search(cite[interne.end():interne.end() + 60])
               for interne in HOTE.finditer(cite)):
            continue
        if len(norme := normalise(m.group(1))) >= FENETRE:
            gardes.append((destination(texte, m.start(), cite), norme))
    return gardes

# Les 277 arêtes du graphe ont été examinées une à une, en trois tirages
# reproductibles et disjoints (`data/mesures/precision-resulte-de*.tsv`). Le
# premier, sur le code d'avant les gardes de docs/21, a servi à les concevoir ;
# les deux suivants les mesuraient sur pièces neuves : 168 justes sur 179, soit
# 93,9 %, Wilson 0,8933 (`docs/21` § 6 bis).
#
# Le 21 septembre 2026 (docs/49), la destination du passage, l'hôte de
# l'alinéa et la garde temporelle changent la population, et les arêtes qui
# avaient servi à les concevoir ne la mesurent plus. Re-mesurée le même jour,
# deux juges Sonnet 5 par fiche et un arbitre : un tirage disjoint de 20, les
# 11 nouvelles, puis les 14 dernières jamais jugées, après les corrections
# que les deux premiers ont dictées — **35 justes sur 37**, réunis et
# dédoublonnés, Wilson 0,8230. Les deux fausses — des fenêtres de citation
# partagée, « l'article L. 32 du code des postes », « la loi n° 78-17 » — sont
# chacune la cause d'une garde. Le seuil de 95 % du § 4.2 n'est pas atteint.
#
# Le 24 septembre 2026 (docs/50), les législatures XVI et XVII, la loi Hamon
# enfin complète et onze dossiers nouveaux ajoutent 163 arêtes aux 284 d'avant,
# qui restent toutes. Vingt des 163, deux juges Sonnet 5 d'accord partout :
# **17 sur 20**. Deux fausses sont une formule administrative partagée par un
# passage destiné à un autre texte — la suspension d'un agrément du code de
# l'énergie, le plafond en chiffre d'affaires mondial d'une sanction de
# l'Arcom —, la troisième une rédaction dont le barème n'a pas été retenu.
# Aucune garde n'en sort ici. Réunis : **52 sur 57**, Wilson 0,8105.
#
# Le même jour (docs/53), 20 arêtes parmi les 120 qu'aucune fiche n'avait
# jugées : **18 sur 20**, un arbitre Opus 5 sur deux désaccords. Les deux
# fausses : un alinéa attribué à l'amendement 405, écrit par le 269 du même
# dossier ; et la formule d'injonction administrative, partagée par un VII
# de L. 141-1 et un alinéa de L. 218-5-5. Réunis : **70 sur 77**, Wilson 0,8240.
#
# Le même jour (docs/55 § 3), l'une des fausses de docs/50 est arbitrée juste :
# l'agrément « Mon Accompagnateur Rénov' » est celui de l'article L. 232-3 du
# code de l'énergie, et l'alinéa descend du paragraphe que l'amendement 18 a
# inséré, retouché par le Sénat. Réunis : **71 sur 77**, Wilson 0,8402.
CONFIANCE = 0.8402


def charger_amendements(base: sqlite3.Connection, racine: Path) -> dict:
    dossiers = {d for (d,) in base.execute("SELECT id_dole FROM dossier")}
    # Les identifiants sont attribués à la suite de ceux déjà en base : la tranche
    # Assemblée peut avoir été chargée avant celle-ci.
    suivant = base.execute("SELECT coalesce(max(id), 0) + 1 FROM acteur").fetchone()[0]
    acteurs: dict[tuple[str, str], int] = {
        (nom, groupe or ""): identifiant
        for identifiant, nom, groupe in base.execute("SELECT id, nom, groupe FROM acteur")}
    deja = set(acteurs.values())
    lignes, ignores = [], 0

    for fichier in sorted(racine.iterdir()):
        if "__" not in fichier.name:
            continue
        dossier, texte_discute = fichier.name.split("__", 1)
        if dossier not in dossiers:
            ignores += 1
            continue
        try:
            jeu = lire_ameli(fichier)
        except Exception:
            ignores += 1
            continue
        for a in jeu:
            nom = sans_balises(a.get("Auteur", "")) or "(inconnu)"
            groupe = sans_balises(a.get("Au nom de", "")) or None
            if (nom, groupe or "") not in acteurs:
                acteurs[(nom, groupe or "")] = suivant
                suivant += 1
            auteur = acteurs[(nom, groupe or "")]
            lignes.append((dossier, "senat", texte_discute, a.get("Numéro", ""),
                           auteur, a.get("Sort") or None,
                           sans_balises(a.get("Subdivision", "")) or None,
                           sans_balises(a.get("Objet", "")) or None,
                           sans_balises(a.get("Dispositif", "")) or None,
                           a.get("Url amendement") or None))

    base.executemany("INSERT INTO acteur (id, nom, groupe) VALUES (?, ?, ?)",
                     [(i, nom, groupe or None) for (nom, groupe), i in acteurs.items()
                      if i not in deja])
    base.executemany(
        "INSERT OR IGNORE INTO amendement (dossier_id, chambre, texte_discute, numero,"
        " auteur_id, sort, subdivision, objet, dispositif, url)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", lignes)
    return {"acteurs": len(acteurs), "amendements": len(lignes), "fichiers_ignores": ignores}


def articles_nommes(dispositif: str) -> set[str]:
    """Numéros d'articles que le dispositif désigne comme cibles d'une instruction.

    Un dispositif d'amendement modifie souvent plusieurs articles dans le même
    texte, avec des rédactions voisines : « L'article L. 215-2-4 est ainsi rédigé :
    "Les agents mentionnés à l'article L. 215-1…" », suivi d'un paragraphe presque
    identique pour L. 215-2-2. L'appariement textuel seul confond les deux. Quand
    le rédacteur nomme sa cible, sa déclaration prime.

    Nommer sa cible, c'est la faire suivre d'une formule modificative. Un
    numéro seulement cité — « dans les conditions prévues à l'article
    L. 141-1 » — ou écrit en tête d'un article créé — « Art. L. 121-42. – »,
    dont la navette change le numéro — n'est pas une déclaration : relever
    tout numéro cité, comme la première rédaction, tenait pour non déclarée
    la cible d'un amendement qui crée une section entière, et ne s'était pas
    vu sur les amendements de l'Assemblée, dont aucun numéro n'était lu.
    """
    texte = sans_balises(dispositif).translate(TRAITS)
    return {numero_de(m) for m in ARTICLE_CITE.finditer(texte)
            if FORMULE_DESTINATION.match(texte, m.end())}


def hotes_des_alineas(base: sqlite3.Connection):
    """Une fonction qui dit, pour un amendement, si l'alinéa du texte qu'il
    nomme est sous une instruction portant sur un autre code — None quand
    `porte_sur` n'est pas construite, ou que rien ne se lit."""
    tables = base.execute(
        "SELECT count(*) FROM sqlite_master WHERE name IN ('porte_sur', 'texte_discute')"
    ).fetchone()[0]
    if tables < 2:
        return lambda *_: None
    mentions_id: dict[tuple[str, str], dict[str, int | None]] = defaultdict(dict)
    for texte_id, article_du_texte, cle, article_id, portee in base.execute(
            "SELECT texte_id, lower(article_du_texte), numero_cite, article_id, portee "
            "FROM porte_sur"):
        # `visees` tient une mention non résolue pour « hors du code », parce
        # qu'elle ne peut pas y poser d'arête ; ici la question est inverse —
        # l'alinéa est-il sous un autre code ? — et un numéro du nôtre que la
        # navette a changé n'est pas un autre code. Sentinelle -1 : notre code,
        # article inconnu.
        mentions_id[(texte_id, article_du_texte)][cle.replace(" ", "")] = (
            None if portee == "externe" else (article_id if portee == "interne" else -1))
    textes_du_corpus = {(chambre, corpus): texte_id
                        for chambre, corpus, texte_id in correspondances(base)}
    textes = Textes(base, Path(__file__).resolve().parent.parent / "travail" / "corpus" / "textes")

    def etranger(chambre: str, corpus: str, subdivision: str | None, dispositif: str) -> bool | None:
        texte_id = textes_du_corpus.get((chambre, corpus))
        numero = numero_de_subdivision(subdivision)
        trouve = ALINEA.search(sans_balises(dispositif))
        if not texte_id or not numero or not trouve:
            return None
        cible = textes.gouvernant(texte_id, numero, alineas_nommes(trouve),
                                  mentions_id.get((texte_id, numero), {}))
        if cible == "illisible":
            return None
        return cible is None

    return etranger


def construire_resulte_de(base: sqlite3.Connection) -> dict:
    """Apparie chaque amendement adopté aux segments que sa propre loi a produits."""
    etranger = hotes_des_alineas(base)
    # Les arêtes sont reconstruites, non complétées : sans cet effacement, une
    # exécution ultérieure laisse en base des arêtes portant l'ancienne confiance,
    # que `INSERT OR IGNORE` refuse de remplacer. Le graphe affichait ainsi
    # 0,685 là où le code disait 0,710.
    # L'ordre compte : la preuve est référencée par l'arête. L'effacer d'abord
    # fait échouer la clef étrangère, ce que la première rédaction ne voyait pas
    # parce qu'elle n'avait jamais tourné deux fois sur la même base.
    anciennes = [i for (i,) in base.execute(
        "SELECT preuve_id FROM resulte_de WHERE preuve_id IS NOT NULL")]
    base.execute("DELETE FROM resulte_de")
    base.executemany("DELETE FROM preuve WHERE id = ? AND methode = 'appariement_exact'",
                     [(i,) for i in anciennes])
    prochaine_preuve = base.execute(
        "SELECT coalesce(max(id), 0) + 1 FROM preuve").fetchone()[0]

    # Segments candidats, par dossier : ceux des versions d'articles produites par
    # un texte lui-même issu de ce dossier.
    compte: dict[str, int] = defaultdict(int)
    candidats: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    version_du_segment: dict[str, str] = {}
    for dossier, segment_id, numero, texte, version_id in base.execute("""
            SELECT i.dossier_id, s.id, a.numero, s.texte, v.id_legi
            FROM issu_de i
            JOIN produite_par p ON p.texte_id = i.texte_id
            JOIN version_article v ON v.id_legi = p.version_id
            JOIN article a ON a.id = v.article_id
            JOIN segment s ON s.version_id = v.id_legi
            -- Un amendement à un projet de loi n'écrit pas un article
            -- réglementaire : le pouvoir réglementaire ne se discute pas au
            -- Parlement. La partie R du code porte pourtant les mêmes formules de
            -- sanction et de renvoi que la partie L, et une arête de
            -- l'échantillon rattachait ainsi R311-5 à un amendement.
            WHERE a.numero GLOB 'L*' OR a.numero GLOB 'Annexe*L*'
               OR a.numero = 'liminaire'"""):
        candidats[dossier].append((segment_id, numero, texte))
        version_du_segment[segment_id] = version_id

    # **Ce que le fonds portait avant la loi, l'amendement ne l'a pas écrit.**
    # L'appariement lisait tous les alinéas d'une version produite par la loi
    # comme écrits par elle ; la plupart sont repris de la version d'avant, et
    # `repris_de` ne le dit pas, qui ne suit que les prédécesseurs
    # renumérotés. « L'article L. 136-1 est reproduit intégralement dans les
    # contrats de prestation de services auxquels il s'applique » est dans
    # L. 136-2 depuis 2008 ; l'amendement 624 de 2013 écrit la même phrase sous
    # un autre article, et la fenêtre les joignait. Le 7° de L. 115-16, que
    # l'amendement 993 recopie dans l'adaptation à Wallis-et-Futuna, est de
    # 1993. Et « sont recherchés et constatés dans les conditions prévues au »,
    # que l'amendement 377 écrivait dans un autre code, se lit dans des
    # dizaines d'articles du nôtre depuis toujours : la discriminance,
    # mesurée parmi les seules versions que la loi a produites, ne le voyait
    # pas. Quatre fausses que le harnais nommait (`docs/48` § 3).
    #
    # La règle est temporelle, et c'est ce qui la rend sûre : une fenêtre
    # présente dans une version du fonds — de cet article ou d'un autre, R et D
    # compris — **antérieure à la version appariée et que la loi n'a pas
    # produite** existait avant l'amendement. Ni la version précédente du même
    # article quand la loi l'a produite aussi (le texte y a été écrit, puis
    # repris), ni les copies que la recodification de 2016 a faites sous
    # d'autres numéros ne comptent : une première rédaction qui les prenait
    # pour de la non-discriminance perdait vingt arêtes jugées justes pour
    # trois fausses.
    produites_par: dict[str, set[str]] = defaultdict(set)
    for dossier, version_id in base.execute(
            "SELECT i.dossier_id, p.version_id FROM issu_de i "
            "JOIN produite_par p ON p.texte_id = i.texte_id"):
        produites_par[dossier].add(version_id)
    date_de_la_version = dict(base.execute("SELECT id_legi, date_debut FROM version_article"))
    fonds = [(date_debut, version_id, normalise(texte or ""))
             for version_id, date_debut, texte in base.execute(
                 "SELECT id_legi, date_debut, texte FROM version_article "
                 "WHERE etat NOT IN ('MODIFIE_MORT_NE', 'ANNULE') ORDER BY date_debut")]

    def deja_dans_le_fonds(fenetre: str, version_id: str, dossier: str) -> bool:
        limite, siennes = date_de_la_version[version_id], produites_par[dossier]
        return any(fenetre in texte for date_debut, autre, texte in fonds
                   if date_debut < limite and autre not in siennes)

    # Classes de renumérotation : deux numéros d'articles reliés par une
    # recodification désignent la même disposition, et une fenêtre commune aux
    # deux n'est pas ambiguë.
    racine: dict[str, str] = {}

    def chercher(n: str) -> str:
        while racine.get(n, n) != n:
            n = racine[n]
        return n

    for cible, ancien in base.execute("""
            SELECT c.numero, a.numero FROM renumerote_de r
            JOIN article c ON c.id = r.article_id JOIN article a ON a.id = r.ancien_id"""):
        rc, ra = chercher(cible), chercher(ancien)
        if rc != ra:
            racine[rc] = ra

    aretes, preuves = [], []
    for dossier, segments in candidats.items():
        # Index construit au pas de 1 : c'est le côté dont les offsets doivent être
        # indépendants de ceux de l'autre.
        index: dict[str, set[str]] = defaultdict(set)
        numero_du_segment = {}
        for segment_id, numero, texte in segments:
            numero_du_segment[segment_id] = numero
            propre = normalise(texte)
            # Un article de code cite couramment le titre complet d'une loi. Ces
            # titres sont longs, identiques d'un code à l'autre, et un amendement
            # qui cite la même loi produit la même fenêtre sans avoir rien écrit :
            # six des dix-neuf arêtes fausses de l'échantillon étaient des titres
            # de loi. Les fenêtres qui commencent dans un intitulé ne sont pas
            # indexées — elles ne prouvent rien, dans aucun sens.
            titres = [m.start() for m in CITATION.finditer(propre)]
            for depart in range(0, max(1, len(propre) - FENETRE + 1)):
                # `bisect_right`, non `bisect_left` : un intitulé qui commence
                # exactement à la fenêtre doit compter. La première rédaction
                # laissait passer « loi n° 90-449 du 31 mai 1990 visant à… », qui
                # ouvrait la fenêtre sur son premier caractère.
                place = bisect_right(titres, depart)
                if place and depart - titres[place - 1] <= PORTEE_TITRE:
                    compte["fenetres_dans_un_titre"] += 1
                    continue
                index[propre[depart:depart + FENETRE]].add(segment_id)

        connus = set(numero_du_segment.values())
        connus_classes = {chercher(n) for n in connus}
        # `est_adopte`, non `sort = 'Adopté'` : Améli écrit aussi « Adopté - vote
        # unique », qui est un adopté et que la comparaison littérale écartait.
        # Voir `ingestion/sort_des_amendements.py`.
        for amendement_id, dispositif, chambre, corpus, subdivision in [
                (i, d, c, t, s) for i, sort, etat, d, c, t, s in base.execute(
                    "SELECT id, sort, etat, dispositif, chambre, texte_discute, subdivision "
                    "FROM amendement WHERE dossier_id = ? AND dispositif IS NOT NULL",
                    (dossier,))
                if est_adopte(sort, etat)]:
            # Cibles déclarées, ramenées à leurs classes de renumérotation. Un
            # dispositif qui ne nomme aucun article de ce code — il crée alors des
            # articles dont le numéro n'est pas encore fixé — n'impose rien.
            nommes = {chercher(n) for n in articles_nommes(dispositif or "")
                      if n in connus}
            # L'alinéa du texte que l'amendement nomme est-il sous une
            # instruction qui modifie un autre code ? Alors ce qu'il y insère
            # ne peut pas expliquer un alinéa du nôtre — sauf à le dire, par
            # une destination que la loi a produite.
            hote_etranger = etranger(chambre, corpus, subdivision, dispositif or "")
            touches: dict[str, tuple[str, int]] = {}
            declarees: set[str] = set()     # segments touchés par un passage qui leur est destiné
            for (destinataire, lecture), passage in passages_inseres(dispositif or ""):
                classe_destinataire = chercher(destinataire) if destinataire else None
                if hote_etranger and classe_destinataire not in connus_classes:
                    compte["alinea_sous_un_autre_code"] += 1
                    continue
                for position, fenetre in enumerate(fenetres(passage, pas=10)):
                    vises = index.get(fenetre)
                    if not vises:
                        continue
                    # La discriminance se mesure sur les numéros d'articles, non
                    # sur les segments : un même alinéa figure dans plusieurs
                    # versions du même article, ce qui n'est pas de l'ambiguïté.
                    numeros = {numero_du_segment[s] for s in vises}
                    if len({chercher(n) for n in numeros}) > 1:
                        compte["fenetres_non_discriminantes"] += 1
                        continue
                    classe = chercher(next(iter(numeros)))
                    if classe_destinataire is not None:
                        # Le rédacteur a dit où va ce passage. Si la loi a
                        # produit cet article, c'est lui et nul autre ; sinon —
                        # article d'un autre code, ou numéro que la navette a
                        # changé — le passage ne se rattache que s'il est
                        # neuf : une fenêtre que le fonds portait déjà avant la
                        # loi, ailleurs, est une formule, pas une écriture.
                        if classe_destinataire in connus_classes:
                            if classe != classe_destinataire:
                                compte["destination_autre"] += 1
                                continue
                        elif any(deja_dans_le_fonds(fenetre, version_du_segment[s], dossier)
                                 for s in vises):
                            compte["destination_inconnue_formule_ancienne"] += 1
                            continue
                    elif nommes and classe not in nommes:
                        compte["cible_non_declaree"] += 1
                        continue
                    elif any(deja_dans_le_fonds(fenetre, version_du_segment[s], dossier)
                             for s in vises):
                        # Sans destination lisible, une fenêtre que le fonds
                        # portait déjà avant la loi est une citation partagée :
                        # « l'article L. 32 du code des postes », « la loi
                        # n° 78-17 » — les deux fausses du quatrième tirage
                        # (docs/49 § 8), sur des amendements qui ne touchaient
                        # pas au code.
                        compte["sans_destination_formule_ancienne"] += 1
                        continue
                    # La preuve gardée est la première fenêtre — sauf si un
                    # passage **destiné** à cet article en apporte une : les
                    # amendements de 2013 qui écrivent la même phrase sous
                    # « L. 121-84-12 » (téléphonie) et « L. 121-91-1 » (énergie)
                    # montraient la fenêtre de la téléphonie pour L. 121-91-1,
                    # et le lecteur jugeait la preuve fausse (docs/49 § 8).
                    for segment_id in vises:
                        if classe_destinataire is not None and classe == classe_destinataire:
                            if segment_id not in declarees:
                                touches[segment_id] = (fenetre, position * 10)
                                declarees.add(segment_id)
                        else:
                            touches.setdefault(segment_id, (fenetre, position * 10))
            for segment_id, (fenetre, offset) in touches.items():
                preuves.append((prochaine_preuve, "appariement_exact", fenetre, offset))
                aretes.append((segment_id, amendement_id, "derivee", CONFIANCE,
                               prochaine_preuve))
                prochaine_preuve += 1

    base.executemany(
        "INSERT INTO preuve (id, methode, fenetre, source_offset) VALUES (?, ?, ?, ?)",
        preuves)
    base.executemany(
        "INSERT OR IGNORE INTO resulte_de (segment_id, amendement_id, methode,"
        " confiance, preuve_id) VALUES (?, ?, ?, ?, ?)", aretes)
    compte["aretes"] = len(aretes)
    return compte


def main() -> None:
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] not in ("--noeuds", "--aretes")):
        sys.exit(__doc__)
    racine, base = Path(sys.argv[1]), sqlite3.connect(Path(sys.argv[2]))
    base.execute("PRAGMA foreign_keys = ON")
    temps = sys.argv[3] if len(sys.argv) == 4 else None

    noeuds = charger_amendements(base, racine) if temps != "--aretes" else None
    if temps == "--noeuds":
        base.commit()
        print(f"acteurs                    : {noeuds['acteurs']}")
        print(f"amendements chargés        : {noeuds['amendements']}")
        print(f"  jeux ignorés (hors périmètre) : {noeuds['fichiers_ignores']}")
        base.close()
        return
    aretes = construire_resulte_de(base)
    base.commit()

    sorts = base.execute(
        "SELECT sort, count(*) FROM amendement GROUP BY sort ORDER BY 2 DESC LIMIT 4"
    ).fetchall()
    segments, amendements = base.execute(
        "SELECT count(DISTINCT segment_id), count(DISTINCT amendement_id) "
        "FROM resulte_de").fetchone()
    atteints = base.execute("""
        WITH RECURSIVE remonte(depart, courant) AS (
            SELECT s.id, s.id FROM segment s
            JOIN version_en_vigueur v ON v.id_legi = s.version_id
            UNION
            SELECT remonte.depart, r.segment_source_id
            FROM repris_de r JOIN remonte ON r.segment_id = remonte.courant)
        SELECT count(DISTINCT a.numero)
        FROM remonte JOIN resulte_de rd ON rd.segment_id = remonte.courant
        JOIN segment s ON s.id = remonte.depart
        JOIN version_article v ON v.id_legi = s.version_id
        JOIN article a ON a.id = v.article_id""").fetchone()[0]
    violations = base.execute("PRAGMA foreign_key_check").fetchall()

    if noeuds:
        print(f"acteurs                    : {noeuds['acteurs']}")
        print(f"amendements chargés        : {noeuds['amendements']}")
        print(f"  jeux ignorés (hors périmètre) : {noeuds['fichiers_ignores']}")
    for sort, n in sorts:
        print(f"    {sort or '(vide)':22s} {n}")
    print(f"\narêtes resulte_de          : {aretes['aretes']}")
    print(f"  segments touchés         : {segments}")
    print(f"  amendements rattachés    : {amendements}")
    print(f"  fenêtres écartées, non discriminantes : "
          f"{aretes['fenetres_non_discriminantes']}")
    print(f"  fenêtres écartées, cible non déclarée  : "
          f"{aretes['cible_non_declaree']}")
    print(f"  fenêtres non indexées, prises dans un intitulé : "
          f"{aretes['fenetres_dans_un_titre']}")
    print(f"  passages écartés, alinéa du texte sous une instruction d'un autre code : "
          f"{aretes['alinea_sous_un_autre_code']}")
    print(f"  fenêtres écartées, passage destiné à un autre article : "
          f"{aretes['destination_autre']}")
    print(f"  fenêtres écartées, destination hors de la loi et formule déjà dans le fonds : "
          f"{aretes['destination_inconnue_formule_ancienne']}")
    print(f"  fenêtres écartées, sans destination et formule déjà dans le fonds : "
          f"{aretes['sans_destination_formule_ancienne']}")
    print(f"\narticles en vigueur remontant à un amendement : {atteints}")
    print(f"intégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
