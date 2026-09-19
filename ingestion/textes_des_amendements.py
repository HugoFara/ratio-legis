#!/usr/bin/env python3
"""Vingt-cinquième tranche : la correspondance des identifiants de texte.

`docs/16` § 6 la posait comme le dernier verrou du chaînon des textes en
discussion : « `vise` relie un amendement à sa subdivision — "Article 10" — et
`porte_sur` relie cette subdivision au code. Les deux se joindraient, mais les
identifiants de texte des deux corpus ne se correspondent pas. Une table de
correspondance est nécessaire, et elle n'est pas écrite. »

Elle l'est ici, et elle n'est pas devinée.

**Sénat.** Un document du Sénat est numéroté par (session, numéro) : le texte
n° 283 de la session 2013-2014. C'est exactement la clef d'une URL Améli, et
c'est aussi ce que porte le nom du fichier récupéré depuis DOLE —
`leg/pjl13-283.html`, ou `petite-loi-ameli/2013-2014/283.html`. Les deux
identifiants désignent le même document.

Les liens `tas` sont écartés : `leg/tas06-135.html` est le **texte adopté**
n° 135, série distincte de celle des textes déposés. Les confondre rattacherait
des amendements à un document qu'ils n'ont jamais amendé.

**Assemblée.** La référence d'un amendement porte la série et le numéro —
`L14B1015` pour le texte déposé, `L14BTC2442` pour le texte de commission —, et
`amendement.texte_discute` en garde la forme `B1015` / `BTC2442`. Les documents
de l'Assemblée présents dans le corpus emploient le même numéro : `l14b2442` dans
les URL `dyn`, `r2442-a0` pour un texte de commission annexé à son rapport. La
série `ta{N}` est écartée pour la même raison que `tas` au Sénat.

**Deux contrôles, tous deux rejoués à chaque exécution.**

1. *Le dossier concorde.* Le texte trouvé par le numéro doit appartenir au même
   dossier DOLE que les amendements. 67 jeux sur 67 au Sénat, 26 sur 39 à
   l'Assemblée — les 13 restants n'ont aucun document de la bonne série dans le
   corpus, ce qui est un trou de corpus et non un désaccord.
2. *Les subdivisions tombent dans la plage.* Un amendement déposé sur l'article 12
   suppose que le texte ait au moins douze articles, et `texte_discute.articles`
   les compte. 3 578 sur 3 655, soit 97,9 %. C'est le contrôle qui tranche : un
   appariement faux s'y verrait avant tout autre.

Un troisième a servi à décider, sans être rejouable en une passe : apparier
chaque jeu à un texte tiré au hasard fait tomber la concordance des subdivisions
avec `porte_sur` de 40,9 % à 15,3 % au Sénat, de 7,6 % à 2,4 % à l'Assemblée.

**Ce que la correspondance débloque, et ce qu'elle ne débloque pas.** Voir
`docs/31`. En deux mots : l'arête existe, elle est déclarée aux deux bouts, et
elle ne rattrape presque aucun amendement orphelin — parce qu'un amendement
orphelin ne vise pas un article existant, il en crée un.

Usage :
    textes_des_amendements.py <base.sqlite> [schema/011-textes-des-amendements.sql]
"""

from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textes_deposes import (ARTICLE_CREE, REFERENCE, articles_du_texte,  # noqa: E402
                            dans_une_citation, est_une_cible, index_des_lignes,
                            numero as numero_de, texte_brut)

# --- identification des documents, par chambre --------------------------------
# Sénat : (session, numéro). `petite-loi-ameli` porte la session en entier ; les
# préfixes `pjl`/`ppl` la portent sur deux chiffres — `pjl13-283` est le texte 283
# de la session 2013-2014.
SENAT_PETITE = re.compile(r"petite-loi-ameli-(\d{4})-(\d{4})-(\d+)")
SENAT_DEPOSE = re.compile(r"leg-(?:pjl|ppl)(\d{2})-(\d+)")
# Assemblée : la série « b », celle des textes déposés et des textes de
# commission, seule comparable à la référence des amendements.
ASSEMBLEE = (re.compile(r"dyn-\d+-textes-l\d+b0*(\d+)_"),
             re.compile(r"/\d+-propositions-pion0*(\d+)"),
             re.compile(r"/\d+-ta-commission-r0*(\d+)-"),
             re.compile(r"/\d+-rapports-r0*(\d+)-"))
# `B(?:TC)?`, non `BTC?` : le second se lit « B, puis T, puis C facultatif »,
# et ne reconnaît donc jamais une référence `B1247`. Les treize jeux que
# `docs/31` § 3 donnait pour non appariés étaient exactement ceux-là.
AMENDEMENT_AN = re.compile(r"^B(?:TC)?(\d+)/")

# --- lecture d'une subdivision -------------------------------------------------
# Le Sénat écrit « Article 12 », l'Assemblée « ART. 12 » ; les deux écrivent
# « premier » pour 1. Le suffixe latin fait partie du numéro : l'article 19 octies
# n'est pas l'article 19.
#
# **La lettre aussi.** « Article 60 bis A », « ART. 18 D » : la navette insère des
# articles nouveaux et les distingue par une lettre, exactement comme `ENTETE` le
# lit du côté du texte depuis la onzième tranche. Sans elle, l'amendement déposé
# sur l'article 60 bis A était rattaché à l'article 60 bis — un autre article, un
# autre objet. Trois arêtes sur quinze tirées au sort en venaient ; 1 230
# subdivisions portent une lettre, et 454 articles de texte en portent une dans
# `porte_sur`, ce qui est le même besoin vu des deux bouts.
#
# **Et la série latine va au-delà de « decies ».** « Article 5 sexdecies » était
# lu « article 5 » : la quinzième arête du tirage de la vingt-neuvième tranche,
# fausse pour cette seule raison. Les rangs composés — « terdecies » = « ter » +
# « decies » — se lisaient déjà ; les autres non.
# Les rangs composés d'abord, et une frontière de mot après le rang : sans elle,
# « 72 terdecies » se lisait « 72 ter » — un amendement rétablissant l'article
# 72 terdecies était rattaché à l'article 72 ter, et l'arête jugée fausse par
# trois juges (docs/42).
SUBDIVISION = re.compile(
    r"\bart(?:icle)?\.?\s+(premier|1er|\d+)\s*"
    r"(terdecies|quaterdecies|quindecies|sexdecies|septdecies|octodecies"
    r"|novodecies|unvicies|duovicies|tervicies|vicies|undecies|duodecies"
    r"|bis|ter|quater|quinquies|sexies|septies|octies|nonies|decies)?\b"
    r"(?:\s*([A-H]{1,2})\b)?", re.I)
# « art. add. après Article 19 » ne vise pas l'article 19. L'amendement demande la
# création d'un article qui n'existe pas encore, dont le numéro dans le code n'est
# pas fixé et ne le sera qu'à la codification. La subdivision ne dit alors rien du
# code, et la lire comme une cible serait le contresens le plus coûteux possible.
ARTICLE_ADDITIONNEL = re.compile(
    r"art\.?\s*add|article\s+additionnel|apr[èe]s\s+(?:l')?\s*art|avant\s+(?:l')?\s*art",
    re.I)

# Borne inférieure de Wilson à 95 % pour 15 arêtes justes sur 15 vérifiées à la
# main sur le graphe d'aujourd'hui — hôte réparé (`docs/34`), garde retirée,
# subdivision lue en entier. Tirage disjoint de celui qui a servi à décider.
#
# La valeur est celle que portait déjà `docs/31` § 4, et elle ne décrit plus la
# même arête : entre les deux, la réparation de `porte_sur` avait fait tomber la
# précision réelle à 3 sur 15 sans que rien ne le signale (`docs/35` § 3). Une
# confiance écrite en constante ne se surveille pas toute seule ; celle-ci est
# désormais adossée à une fiche rejouable,
# `data/mesures/precision-depose-sur.tsv`.
#
# Ce n'est pas la confiance de `porte_sur` (0,8389) reprise telle quelle : une
# chaîne de deux liens ne vaut pas son maillon le plus fort.
#
# Re-mesurée le 19 septembre 2026 par deux juges indépendants sur quinze arêtes
# de la population d'aujourd'hui — cibles comptées dans tous les codes — :
# **7 justes sur 15**, Wilson 0,2481 (`precision-depose-sur-cibles-tous-codes.tsv`,
# `docs/41`). La composition est formellement exacte bien plus souvent que
# cela ; ce qui tombe, c'est ce que l'arête prétend : « l'amendement portait sur
# cet article ». Un amendement déposé sur l'article 18 du texte peut ne toucher
# que le code monétaire, et l'arête le rattache à L. 311-8-1. La confiance
# porte la mesure, pas la définition.
CONFIANCE = 0.2481            # composition seule, population d'avant les voies, docs/41
# Chaque voie mesurée à part le 19 septembre 2026, par trois juges — qwen3p8-max
# (compté), deepseek-v4p1-flash, glm-5p3-flash —, tirages disjoints (docs/42) :
#   alinea          18 / 20 (docs/42), puis 16 / 20 sur un second tirage disjoint
#                   après les corrections de docs/43 — les quatre fausses sont
#                   des alinéas gouvernés par une instruction que porte_sur n'a
#                   pas relevée (article inséré, instruction sautée) : la portée
#                   d'une instruction n'est pas bornée par la suivante. Puis,
#                   l'instruction lue dans le texte à toutes ses occurrences,
#                   bornée par le paragraphe de tête, les lignes de statut du
#                   Sénat exclues du compte : 17 / 20 sur un troisième tirage
#                   disjoint (docs/44), Wilson 0,6396 — les trois fausses sont
#                   des sous-instructions (a bis), 2°) que le parseur ne borne
#                   pas encore.
#   visee            7 / 10 (docs/42), puis 13 / 15 après les gardes de vise —
#                   ancre d'insertion, code hôte, numéro glissé, « L. 312-9-… ».
#                   Wilson 0,6212.
#   article_entier   7 / 10, puis 6 / 7 — Wilson 0,4869 : « N ne réécrit que A »
#                   repose sur porte_sur, qui ne voit pas tout ce que N réécrit.
# Deux juges (deepseek-v4p1-flash, glm-5p3-flash), qwen3p8-max en arbitrage.
CONFIANCE_PAR_VOIE = {"visee": 0.6212, "alinea": 0.6396, "article_entier": 0.4869}

PARAGRAPHE = re.compile(r"^[ \t]*[IVXL]{1,6}(?:\s*(?:bis|ter|quater|quinquies|sexies))?\s*\.\s*[–-]",
                        re.M)
ALINEA = re.compile(r"\b(?:l['’]\s*)?alin[ée]as?\s+(\d{1,3})\b", re.I)
ARTICLE_ENTIER = re.compile(r"^\s*(?:I\.\s*[–-]\s*)?(supprimer|r[ée]diger ainsi|r[ée]tablir)\s+cet\s+article",
                            re.I)
AJOUT_EN_FIN = re.compile(r"^\s*(?:I\.\s*[–-]\s*)?compl[ée]ter\s+cet\s+article", re.I)


def numero_de_subdivision(subdivision: str | None) -> str | None:
    trouve = SUBDIVISION.search(subdivision or "")
    if not trouve:
        return None
    tete = trouve.group(1).lower()
    tete = "1er" if tete in ("premier", "1er") else tete
    return tete + "".join(" " + partie.lower() for partie in trouve.groups()[1:]
                          if partie)


def tete_numerique(numero: str) -> int | None:
    chiffres = numero.split(" ")[0]
    return int(chiffres) if chiffres.isdigit() else (1 if chiffres == "1er" else None)


# La ligne de statut que le Sénat imprime sous le titre — « (Non modifié) »,
# « (Supprimé) », « (Conforme) » — n'est pas un alinéa : la numérotation des
# amendements l'exclut, et la compter décalait tout d'un cran (docs/44).
STATUT = re.compile(r"^\s*\(?\s*(?:non modifiée?s?|supprimée?s?|conformes?|"
                    r"suppression (?:maintenue|conforme))\s*\)?\s*$", re.I)


def alineas_de(texte: str, debut: int, fin: int) -> list[tuple[int, int]]:
    """Bornes de chaque alinéa de l'article du texte : une ligne non vide."""
    bornes, position = [], debut
    for ligne in texte[debut:fin].split("\n"):
        if ligne.strip() and not STATUT.match(ligne):
            bornes.append((position, position + len(ligne)))
        position += len(ligne) + 1
    return bornes


class Textes:
    """Les textes en discussion, lus une fois, et leurs articles découpés."""

    def __init__(self, base: sqlite3.Connection, corpus: Path) -> None:
        self.base, self.corpus = base, corpus
        self.cache: dict[str, tuple[str, dict[str, tuple[int, int]]]] = {}

    def charger(self, texte_id: str) -> tuple[str, dict[str, tuple[int, int]]] | None:
        if texte_id in self.cache:
            return self.cache[texte_id]
        ligne = self.base.execute("SELECT dossier_id FROM texte_discute WHERE id = ?",
                                  (texte_id,)).fetchone()
        fichier = self.corpus / f"{ligne[0]}__{texte_id.split('/', 1)[1]}" if ligne else None
        if not fichier or not fichier.exists():
            self.cache[texte_id] = None
            return None
        texte = texte_brut(fichier)
        articles = {numero: (debut, fin) for numero, debut, fin in articles_du_texte(texte)}
        self.cache[texte_id] = (texte, articles)
        return self.cache[texte_id]

    def instructions(self, texte: str, debut: int, fin: int) -> list[tuple[int, str]]:
        """Chaque instruction de l'article du texte, à sa position : une référence
        hors citation qui est une cible (« L'article L. 218-7 est complété »), ou
        un article que le texte écrit (« Art. L. 333-6. – »). **Toutes** les
        occurrences, là où `porte_sur` n'en retient qu'une par numéro : la
        portée d'une instruction est bornée par la suivante, quelle qu'elle soit
        — quatre arêtes fausses sur vingt venaient d'une instruction que
        `porte_sur` n'avait pas relevée et qui gouvernait pourtant l'alinéa
        (docs/43 § 2)."""
        segment = texte[debut:fin]
        debuts = index_des_lignes(segment)
        trouvees = []
        for m in REFERENCE.finditer(segment):
            if dans_une_citation(segment, debuts, m.start()):
                continue
            if est_une_cible(segment, m.start(), m.end()):
                trouvees.append((debut + m.start(), numero_de(m)))
        for m in ARTICLE_CREE.finditer(segment):
            trouvees.append((debut + m.start(), numero_de(m)))
        # Un paragraphe de tête — « III. – L'article 1er de la loi du 29 mars
        # 1944 est abrogé » — ouvre une instruction même quand elle ne vise aucun
        # article de code ; sans cette borne, le II sur L. 113-3 gouvernait
        # encore les alinéas du III. Une borne sans numéro rend l'alinéa
        # illisible plutôt que rattaché à l'instruction d'avant.
        for m in PARAGRAPHE.finditer(segment):
            trouvees.append((debut + m.start(), ""))
        return sorted(trouvees)

    def gouvernant(self, texte_id: str, numero: str, alinea: int,
                   mentions: dict[str, int | None]) -> int | None | str:
        """L'article du code que le texte réécrit à l'alinéa `alinea` de l'article
        `numero` : la dernière instruction du texte avant la fin de cet alinéa,
        résolue par ce que `porte_sur` en sait. `mentions` : numéro cité →
        article_id, ou None si hors du code. Rend l'identifiant, None si
        l'instruction porte sur un autre code, 'illisible' si l'alinéa n'existe
        pas ou si l'instruction qui le gouverne n'est pas connue."""
        charge = self.charger(texte_id)
        if not charge or numero not in charge[1]:
            return "illisible"
        texte, articles = charge
        bornes = alineas_de(texte, *articles[numero])
        if not 1 <= alinea <= len(bornes):
            return "illisible"
        fin_alinea = bornes[alinea - 1][1]
        precedentes = [i for i in self.instructions(texte, *articles[numero])
                       if i[0] <= fin_alinea]
        if not precedentes:
            return "illisible"
        cle = precedentes[-1][1]
        if not cle or cle not in mentions:
            return "illisible"       # instruction sans numéro, ou non relevée
        return mentions[cle]


def correspondances(base: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """(chambre, clef du corpus d'amendements, identifiant du texte discuté)."""
    par_clef: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for identifiant, dossier, chambre in base.execute(
            "SELECT id, dossier_id, chambre FROM texte_discute"):
        if chambre == "senat":
            trouve = SENAT_PETITE.search(identifiant)
            if trouve:
                clef = f"{trouve.group(1)}-{trouve.group(2)}_{trouve.group(3)}.csv"
                par_clef[("senat", clef)].append((identifiant, dossier))
                continue
            trouve = SENAT_DEPOSE.search(identifiant)
            if trouve:
                debut = 2000 + int(trouve.group(1))
                clef = f"{debut}-{debut + 1}_{trouve.group(2)}.csv"
                par_clef[("senat", clef)].append((identifiant, dossier))
            continue
        for marque in ASSEMBLEE:
            trouve = marque.search(identifiant)
            if trouve:
                par_clef[("assemblee", trouve.group(1))].append((identifiant, dossier))

    trouvees = []
    for dossier, chambre, corpus in base.execute(
            "SELECT DISTINCT dossier_id, chambre, texte_discute FROM amendement"):
        if chambre == "assemblee":
            reference = AMENDEMENT_AN.match(corpus)
            clef = reference.group(1) if reference else None
        else:
            clef = corpus
        # Le dossier doit concorder : le numéro seul se répète d'une session à
        # l'autre et d'une chambre à l'autre. Sans cette condition, un texte
        # homonyme d'un autre dossier passerait, et c'est le mode d'échec que la
        # phase 0 a payé le plus cher.
        candidats = [i for i, d in par_clef.get((chambre, clef or ""), [])
                     if d == dossier]
        if candidats:
            trouvees.append((chambre, corpus, sorted(candidats)[0]))
    return trouvees


def construire(base: sqlite3.Connection, schema: Path, corpus_textes: Path) -> dict:
    base.executescript(schema.read_text(encoding="utf-8"))
    compte: dict[str, int] = defaultdict(int)

    # **La garde d'hôte est retirée, et ce n'est pas un relâchement.** Elle
    # existait parce que `porte_sur` attribuait le code hôte à des références
    # qu'il ne gouvernait pas : exiger que la fenêtre de preuve nomme le code
    # écartait les fausses. Ce défaut est corrigé à la source (`docs/34`) — un
    # code nommé dans une citation ne déclare plus l'hôte —, et la garde n'a
    # donc plus de fausses à retirer. Ce qu'elle retirait ensuite, ce sont des
    # cibles **vraies**, et l'effet était pire que le mal : en retranchant des
    # cibles d'un article de texte qui en réécrit plusieurs, elle le faisait
    # passer pour n'en réécrire qu'un, et fabriquait ainsi l'unicité que la
    # règle ci-dessous exige.
    #
    # Mesuré : sur quinze arêtes tirées du graphe encore gardé, **501 des 906**
    # reposaient sur un article de texte à cibles multiples, et l'accord avec la
    # cible que l'amendement déclare lui-même tombait à 2 sur 17 — contre 12 sur
    # 15 pour les articles à cible unique. Voir `docs/35` § 3.
    cibles: dict[tuple[str, str], set[int]] = defaultdict(set)
    for texte_id, article_du_texte, article_id in base.execute(
            "SELECT texte_id, lower(article_du_texte), article_id "
            "FROM porte_sur WHERE portee = 'interne'"):
        cibles[(texte_id, article_du_texte)].add(article_id)
    # « Et aucun autre » vaut pour tous les codes, pas pour le seul nôtre. Un
    # article de texte qui réécrit L. 224-3 et cinq articles du code de
    # l'énergie n'a pas une cible unique : l'amendement déposé sur lui peut
    # porter sur le gaz. Jugées par deux modèles, les quatre arêtes du tirage
    # de docs/37 sur lesquelles ils se contredisaient étaient toutes de ce type
    # — 304 des 550 arêtes en dépendaient (docs/41).
    # Une cible non résolue en est une aussi : « il est inséré un article
    # L. 522-7-1 » que la loi promulguée n'a jamais porté reste, dans le texte,
    # un second article réécrit (docs/42 § 3).
    for texte_id, article_du_texte in base.execute(
            "SELECT DISTINCT texte_id, lower(article_du_texte) "
            "FROM porte_sur WHERE portee IN ('externe', 'non_resolue')"):
        if (texte_id, article_du_texte) in cibles:
            cibles[(texte_id, article_du_texte)].add(-1)   # cible hors du code, ou non résolue

    # Les mentions de `porte_sur` avec leur offset, internes et externes : c'est
    # ce qui dit quel article du code le texte réécrit à tel endroit.
    mentions: dict[tuple[str, str], dict[str, int | None]] = defaultdict(dict)
    for texte_id, article_du_texte, article_id, portee, cle in base.execute(
            "SELECT texte_id, lower(article_du_texte), article_id, portee, numero_cite "
            "FROM porte_sur"):
        mentions[(texte_id, article_du_texte)][cle.replace(" ", "")] = (
            article_id if portee == "interne" else None)
    # Ce que l'amendement déclare viser lui-même, chaîne de renumérotation comprise.
    chaine: dict[int, set[int]] = defaultdict(set)
    for origine, courant in base.execute("""
        WITH RECURSIVE c(origine, courant) AS (
            SELECT id, id FROM article
            UNION SELECT c.origine, r.ancien_id FROM renumerote_de r JOIN c ON r.article_id = c.courant
            UNION SELECT c.origine, r.article_id FROM renumerote_de r JOIN c ON r.ancien_id = c.courant)
        SELECT origine, courant FROM c"""):
        chaine[origine].add(courant)
    visees: dict[int, set[int]] = defaultdict(set)
    for amendement_id, article_id in base.execute("SELECT amendement_id, article_id FROM vise"):
        visees[amendement_id].add(article_id)
    textes = Textes(base, corpus_textes)

    lignes, aretes = [], []
    for chambre, corpus, texte_id in correspondances(base):
        etendue = base.execute("SELECT articles FROM texte_discute WHERE id = ?",
                               (texte_id,)).fetchone()[0]
        distinctes, dans_la_plage = set(), 0
        for amendement_id, subdivision, dispositif in base.execute(
                "SELECT id, subdivision, coalesce(dispositif, '') FROM amendement "
                "WHERE chambre = ? AND texte_discute = ?", (chambre, corpus)):
            numero = numero_de_subdivision(subdivision)
            if numero and numero not in distinctes:
                distinctes.add(numero)
                tete = tete_numerique(numero)
                if tete is not None and etendue and tete <= etendue:
                    dans_la_plage += 1
            # L'article additionnel se reconnaît avant que le numéro soit lu :
            # « art. add. après Article 77 bis » en est un, que la tête du numéro
            # se laisse extraire ou non. Tester dans l'autre ordre en rangeait
            # vingt parmi les subdivisions illisibles, et faisait diverger ce
            # compte de celui des mesures d'hygiène.
            if ARTICLE_ADDITIONNEL.search(subdivision or ""):
                compte["article_additionnel"] += 1
                continue
            if not numero:
                compte["subdivision_illisible"] += 1
                continue
            vises = cibles.get((texte_id, numero))
            if not vises:
                compte["subdivision_sans_cible_dans_le_code"] += 1
                continue
            internes = {v for v in vises if v != -1}

            # 1. Le dispositif nomme l'article du code : c'est lui, s'il est
            #    l'une des cibles de l'article du texte (chaîne comprise).
            declarees = visees.get(amendement_id, set())
            if declarees:
                communes = {c for c in internes if chaine[c] & declarees}
                if len(communes) == 1:
                    aretes.append((amendement_id, communes.pop(), texte_id, numero,
                                   "visee", "derivee", CONFIANCE_PAR_VOIE["visee"]))
                    compte["voie_visee"] += 1
                else:
                    compte["visee_contredite"] += 1
                continue

            # 2. Le dispositif nomme un alinéa : l'instruction qui gouverne cet
            #    alinéa dans le texte dit quel article du code est réécrit là.
            trouve = ALINEA.search(dispositif)
            if trouve:
                cible = textes.gouvernant(texte_id, numero, int(trouve.group(1)),
                                          mentions.get((texte_id, numero), {}))
                if cible == "illisible":
                    compte["alinea_illisible"] += 1
                elif cible is None:
                    compte["alinea_hors_du_code"] += 1
                else:
                    aretes.append((amendement_id, cible, texte_id, numero,
                                   "alinea", "derivee", CONFIANCE_PAR_VOIE["alinea"]))
                    compte["voie_alinea"] += 1
                continue

            # 3. Tout l'article du texte, ou rien qu'on sache lire : la composition
            #    seule, et seulement si l'article ne réécrit que cet article-là.
            if AJOUT_EN_FIN.search(dispositif):
                compte["ajout_en_fin_de_l_article"] += 1   # un paragraphe nouveau : cible inconnue
                continue
            if len(vises) > 1:
                compte["cible_non_unique"] += 1
                continue
            aretes.append((amendement_id, next(iter(vises)), texte_id, numero,
                           "article_entier", "derivee", CONFIANCE_PAR_VOIE["article_entier"]))
            compte["voie_article_entier" if ARTICLE_ENTIER.search(dispositif)
                   else "voie_article_entier_par_defaut"] += 1
        lignes.append((chambre, corpus, texte_id, "numero_declare",
                       len(distinctes), dans_la_plage))

    base.executemany(
        "INSERT INTO texte_des_amendements (chambre, texte_corpus, texte_id,"
        " methode, subdivisions, dans_la_plage) VALUES (?, ?, ?, ?, ?, ?)", lignes)
    base.executemany(
        "INSERT OR IGNORE INTO depose_sur (amendement_id, article_id, texte_id,"
        " article_du_texte, voie, methode, confiance) VALUES (?, ?, ?, ?, ?, ?, ?)", aretes)
    compte["jeux_apparies"] = len(lignes)
    compte["aretes"] = len(aretes)
    return compte


def main() -> None:
    if not 2 <= len(sys.argv) <= 3:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    racine = Path(__file__).resolve().parent.parent
    schema = Path(sys.argv[2]) if len(sys.argv) == 3 else \
        racine / "schema" / "011-textes-des-amendements.sql"
    corpus_textes = racine / "travail" / "corpus" / "textes"
    base.execute("PRAGMA foreign_keys = ON")
    compte = construire(base, schema, corpus_textes)
    base.commit()

    jeux = base.execute(
        "SELECT chambre, count(*), sum(subdivisions), sum(dans_la_plage) "
        "FROM texte_des_amendements GROUP BY 1").fetchall()
    total = dict(base.execute(
        "SELECT chambre, count(DISTINCT texte_discute) FROM amendement GROUP BY 1"))
    print("correspondances établies")
    for chambre, jeux_apparies, subdivisions, plage in jeux:
        print(f"  {chambre:10s} {jeux_apparies:3d} jeux sur {total[chambre]:3d}"
              f"   subdivisions dans la plage du texte : "
              f"{plage}/{subdivisions} ({100 * plage / max(1, subdivisions):.1f} %)")

    print("\namendements écartés, et pourquoi")
    print(f"  article additionnel — ne vise aucun article existant : "
          f"{compte['article_additionnel']}")
    print(f"  subdivision sans cible interne dans le code          : "
          f"{compte['subdivision_sans_cible_dans_le_code']}")
    print(f"  l'article du texte en modifie plusieurs              : "
          f"{compte['cible_non_unique']}")
    print(f"  subdivision illisible                                : "
          f"{compte['subdivision_illisible']}")
    print(f"  la cible déclarée par le dispositif contredit l'article : "
          f"{compte['visee_contredite']}")
    print(f"  l'alinéa nommé est gouverné par un autre code        : "
          f"{compte['alinea_hors_du_code']}")
    print(f"  l'alinéa nommé est illisible dans le texte           : "
          f"{compte['alinea_illisible']}")
    print(f"  un paragraphe ajouté en fin d'article, cible inconnue : "
          f"{compte['ajout_en_fin_de_l_article']}")
    print("\narêtes par voie")
    print(f"  visee — le dispositif nomme l'article                : {compte['voie_visee']}")
    print(f"  alinea — l'instruction gouvernant l'alinéa           : {compte['voie_alinea']}")
    print(f"  article_entier — supprimer / rédiger cet article     : {compte['voie_article_entier']}")
    print(f"  article_entier — dispositif non lu, cible unique     : "
          f"{compte['voie_article_entier_par_defaut']}")

    articles, amendements = base.execute(
        "SELECT count(DISTINCT article_id), count(DISTINCT amendement_id) "
        "FROM depose_sur").fetchone()
    en_vigueur = base.execute(
        "SELECT count(DISTINCT d.article_id) FROM depose_sur d "
        "JOIN version_en_vigueur v ON v.article_id = d.article_id").fetchone()[0]
    neufs = base.execute("""
        SELECT count(DISTINCT a.numero) FROM depose_sur d
        JOIN article a ON a.id = d.article_id
        JOIN version_en_vigueur v ON v.article_id = a.id
        WHERE a.numero NOT IN (SELECT article FROM tentative_sur_article)"""
    ).fetchone()[0]
    print(f"\narêtes depose_sur          : {compte['aretes']}")
    print(f"  amendements positionnés  : {amendements}")
    print(f"  articles du code atteints: {articles}  (en vigueur : {en_vigueur})")
    print(f"  dont sans aucune tentative déclarée jusqu'ici : {neufs}")
    print(f"intégrité : {len(base.execute('PRAGMA foreign_key_check').fetchall())} "
          "violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
