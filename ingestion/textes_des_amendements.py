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
             # Le projet de loi déposé, que `plan_textes_deposes.py` charge
             # depuis `docs/32` : sans cette forme, les amendements de
             # commission — déposés sur lui, `B1015` — restaient sans texte,
             # 50 jeux de la XIVe et 29 des suivantes (`docs/52`).
             re.compile(r"/\d+-projets-pl0*(\d+)"),
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
#                   disjoint (docs/44), Wilson 0,6396 — les trois fausses
#                   étaient données pour des sous-instructions que le parseur
#                   ne bornait pas. Elles ne l'étaient pas (docs/45) : deux
#                   comptaient la pastille du Sénat comme un alinéa, la
#                   troisième était déjà réparée par la ligne de statut ; et
#                   la « sous-instruction » — « a ter) Au début du premier
#                   alinéa de l'article L. 223-5, les mots : « … » sont
#                   remplacés » — était invisible parce que `porte_sur`
#                   s'arrêtait au deux-points de l'incise. Numérotation
#                   déclarée par la pastille, ancres d'amendements en garde,
#                   petite loi écartée : 16 / 20 sur un quatrième tirage
#                   disjoint, deux juges d'accord sur tout — trois fausses
#                   inséraient un article ou une instruction nouvelle après
#                   l'alinéa, une comptait une mention entre parenthèses.
#                   Les deux gardes posées, 19 / 20 sur un cinquième tirage
#                   disjoint, un arbitrage (docs/45 § 6) : Wilson 0,7639.
#   visee            7 / 10 (docs/42), puis 13 / 15 après les gardes de vise —
#                   ancre d'insertion, code hôte, numéro glissé, « L. 312-9-… ».
#                   Wilson 0,6212.
#   article_entier   7 / 10, puis 6 / 7 — Wilson 0,4869 : « N ne réécrit que A »
#                   repose sur porte_sur, qui ne voit pas tout ce que N réécrit.
# Deux juges (deepseek-v4p1-flash, glm-5p3-flash), qwen3p8-max en arbitrage.
#
# Re-mesurée le 24 septembre 2026 (docs/51) sur les 141 arêtes que les
# législatures XVI et XVII, la loi Hamon complète et onze dossiers ont
# ajoutées ; deux juges Sonnet 5 par fiche, un arbitre Opus 5 sur désaccord.
#   alinea          10 / 20 — neuf fausses d'une seule cause : « VI (nouveau). – »
#                   n'était pas une borne de paragraphe, et l'instruction du
#                   III sur L. 141-1 gouvernait les VI, VII et VIII nouveaux.
#                   Borne réparée, 20 / 20 sur un second tirage disjoint.
#                   Réunie au tirage de docs/45 : 39 / 40, Wilson 0,8712.
#   article_entier   3 / 20 — `porte_sur` ne relève que des articles de code, et
#                   l'article du texte qui réécrit la loi n° 71-1130 passait pour
#                   ne réécrire que L. 141-1. Garde de l'autre norme, qui retire
#                   les 17 fausses et aucune des 18 justes jugées de toutes les
#                   fiches ; 12 / 15 sur un second tirage disjoint — deux
#                   « Rédiger ainsi cet article » qui écrivent un article voisin,
#                   un amendement d'un autre texte rangé sous le même numéro par
#                   la source. Réunie aux 6 / 7 d'avant : 18 / 22, Wilson 0,6148.
#   visee            8 / 8 ; réunie aux 13 / 15 d'avant : 21 / 23, Wilson 0,7320.
#
# Re-mesurée le même jour (docs/52) sur les arêtes des 79 jeux de l'Assemblée
# que le projet de loi déposé rendait enfin appariables. Chaque tirage y compte
# ses fausses **d'avant** les réparations qu'il a dictées — un biais vers le
# bas, non vers le haut, et c'est pourquoi il est réuni aux autres.
#   alinea          19 / 20 — « L. 121-84-10-1 » lu « L121-84-1 » ; réunie :
#                   58 / 60, Wilson 0,8864.
#   article_entier  13 / 15 — un « I. – (Non modifié) » qui cachait L. 334-5,
#                   et un amendement qui écrit dans L. 621-6 ; réunie : 31 / 37,
#                   Wilson 0,6886.
#   visee           18 / 19 — un « Art. L. 423-2 » nouveau qui renumérote
#                   l'ancien ; réunie : 39 / 42, Wilson 0,8099.
# Puis 20 arêtes que le trait d'union insécable cachait : 18 / 18 par
# l'alinéa, 2 / 2 par la visée, dont quatre arbitrées — l'article que le texte
# de commission écrit sous « L. 224-114 » est l'actuel L. 224-115 (docs/47).
#   alinea          76 / 78, Wilson 0,9112 ; visee 41 / 44, Wilson 0,8177.
CONFIANCE_PAR_VOIE = {"visee": 0.8177, "alinea": 0.9112, "article_entier": 0.6886}

# La mention de navette entre le numéro et le point — « VI (nouveau). – »,
# « II bis (nouveau). – », « III (Supprimé). – » — est encore une borne. Elle ne
# l'était pas : l'instruction du III qui réécrit L. 141-1 gouvernait les VI,
# VII et VIII nouveaux de l'article 32 bis, et neuf arêtes `alinea` fausses sur
# vingt en venaient (docs/51).
PARAGRAPHE = re.compile(r"^[ \t]*[IVXL]{1,6}(?:\s*(?:bis|ter|quater|quinquies|sexies))?"
                        r"(?:\s*\([^)\n]{1,20}\))?\s*\.\s*[–-]", re.M)
# « Alinéa 29 », « Après l'alinéa 9 », et la plage : « Alinéas 22 à 26 ». La
# plage se lit en entier — supprimer les alinéas 22 à 26 quand 22 ouvre la
# section 2 bis et 24 écrit L. 423-4-1, ce n'est pas toucher l'article qui
# gouvernait le 21 (docs/45 § 6).
ALINEA = re.compile(r"\b(?:l['’]\s*)?alin[ée]as?\s+(\d{1,3})(?:\s*(à|et)\s+(\d{1,3}))?\b", re.I)


def alineas_nommes(trouve: re.Match) -> list[int]:
    """« Alinéa 29 » → [29] ; « Alinéas 22 à 26 » → 22…26 ; « Alinéas 2 et 4 » → [2, 4]."""
    premier = int(trouve.group(1))
    if not trouve.group(3):
        return [premier]
    dernier = int(trouve.group(3))
    if trouve.group(2).lower() == "et":
        return [premier, dernier]
    return list(range(premier, dernier + 1)) if dernier >= premier else [premier]
# Une division citée — « Section 2 bis », « Chapitre III » — et son intitulé,
# qui la suit, annoncent ce qui vient : l'instruction qui les gouverne est la
# suivante, pas la précédente, et elle n'est pas lue ici.
DIVISION = re.compile(r"^[«“]?\s*(?:(?:sous-)?section|chapitre|titre|livre)\s+[\divxl]", re.I)
# **Ce qu'on insère après l'alinéa N n'est pas toujours dans l'article qui
# gouverne N.** « Après l'alinéa 9, insérer : « Art. L. 423-1-1. – … » » crée un
# article ; « … : « III bis. – Le cinquième alinéa de l'article 2 de la loi
# n° 90-449 … » » ouvre une instruction sur une autre loi ; « … : …) Le
# premier alinéa de l'article L. 223-5 est complété » ouvre une
# sous-instruction dont la cible est la sienne. Trois des quatre `alinea`
# fausses du quatrième tirage (docs/45 § 6) étaient de ce type. L'Assemblée
# cite tout ce qu'elle insère, instructions comprises : le guillemet ne dit
# donc rien, c'est la forme de la tête qui parle — un article écrit, un
# paragraphe, un numéro en points de suspension, une division ; ou un
# numéro, une lettre suivis d'un verbe modificatif, qui distinguent
# « 3° À la première phrase, les mots … sont remplacés » de « 1° bis Les
# modalités de paiement », qui est du contenu.
INSERTION = re.compile(
    r"apr[èe]s\s+l['’]\s*alin[ée]a\s+\d{1,3}\s*,?\s*(?:ins[ée]rer|ajouter)[^:]{0,80}:\s*"
    r"([«“]?\s*[^\n]{0,240})", re.I | re.S)
ARTICLE_OU_DIVISION = re.compile(
    r"^[«“]?\s*(?:art\.|(?:sous-)?section\b|chapitre\b|titre\b|livre\b)", re.I)
# Un paragraphe, un numéro, une lettre : « VIII bis. – Le recours de pleine
# juridiction… » est un paragraphe de l'article qu'on écrit, « 1° bis Il est
# complété par les mots… » une sous-instruction qui prolonge le bloc sur le
# même article, « …) Le premier alinéa de l'article L. 223-5 est complété »
# une sous-instruction sur un autre. Le verbe et l'article nommé tranchent :
# les deux ensemble, la cible est ailleurs.
PARAGRAPHE_NUMERO_OU_LETTRE = re.compile(
    r"^[«“]?\s*(?:[IVX]+(?:\s*(?:bis|ter|quater|quinquies))?\s*\.?\s*[–‑-]"
    r"|(?:\d{1,2}|\.\.\.|…)\s*°(?:\s*(?:bis|ter|quater))?|(?:[a-z]{1,2}|\.\.\.|…)\)"
    r"|(?:\.\.\.|…)\s*[–‑-])\s", re.I)
NOMME_UN_ARTICLE = re.compile(r"\barticles?\s+(?:[LRD]\.?\s?)?\d", re.I)
VERBE_MODIFICATIF = re.compile(
    r"\b(?:est|sont)\s+(?:ainsi\s+(?:modifiée?s?|rédigée?s?|complétée?s?)|abrogée?s?"
    r"|supprimée?s?|remplacée?s?|complétée?s?|insérée?s?|rétablie?s?|ajoutée?s?)"
    r"|\bil\s+est\s+(?:inséré|ajouté|rétabli)\b", re.I)


def insere_une_instruction(dispositif: str) -> bool:
    """Vrai si l'amendement insère, après un alinéa, une instruction nouvelle —
    dont la cible n'est pas celle de l'alinéa qui précède."""
    trouve = INSERTION.search(dispositif)
    if not trouve:
        return False
    tete = trouve.group(1)
    if ARTICLE_OU_DIVISION.match(tete):
        return True
    if not PARAGRAPHE_NUMERO_OU_LETTRE.match(tete):
        return False
    hors_incises = re.sub(r"[«“][^»”]*[»”]", " ", tete[1:])
    return bool(VERBE_MODIFICATIF.search(hors_incises) and NOMME_UN_ARTICLE.search(hors_incises))
ARTICLE_ENTIER = re.compile(r"^\s*(?:I\.\s*[–-]\s*)?(supprimer|r[ée]diger ainsi|r[ée]tablir)\s+cet\s+article",
                            re.I)
AJOUT_EN_FIN = re.compile(r"^\s*(?:I\.\s*[–-]\s*)?compl[ée]ter\s+cet\s+article", re.I)
# Un autre texte normatif nommé par l'article du texte, hors citation : une loi,
# une ordonnance, un décret, ou un code qui n'est pas le nôtre. `porte_sur` ne
# relève que des articles de code ; l'article 13 du projet Macron réécrit la
# loi n° 71-1130 sur les avocats et touche L. 141-1 en passant, et passait pour
# ne réécrire que L. 141-1. Dix-sept arêtes sur vingt de la voie `article_entier`
# étaient de ce genre (docs/51).
AUTRE_NORME = re.compile(
    r"\b(?:loi|ordonnance|d[ée]cret)\s+(?:organique\s+)?n[°º]"
    r"|\bordonnance\s+du\s+\d"
    r"|\bcode\s+(?!de\s+la\s+consommation)"
    r"(?:de|des|du|d['’]|g[ée]n[ée]ral|mon[ée]taire|rural|civil|p[ée]nal|la|l['’])",
    re.I)


# Un paragraphe que le texte ne reproduit pas — « I. – (Non modifié) » en
# deuxième lecture — cache ce qu'il réécrit : l'article 22 quinquies du projet
# n° 1357 n'y montrait que L. 334-9, et son I, lu dans le texte de première
# lecture, modifie aussi L. 334-5 (docs/52). « Ne réécrit que A » ne se lit pas.
PARAGRAPHE_CACHE = re.compile(
    r"(?m)^[ \t]*(?:[IVXL]{1,6}|\d{1,2}°|[a-z]\))(?:\s*(?:bis|ter|quater|quinquies|sexies|[A-Z]))?"
    r"(?:\s*\([^)\n]{1,20}\))?\s*\.?\s*[–-]?\s*\(\s*non\s+modifi", re.I)


def paragraphe_cache(charge, numero: str) -> bool:
    if not charge or numero not in charge[1]:
        return False
    return bool(PARAGRAPHE_CACHE.search(charge[0][slice(*charge[1][numero])]))


def autre_norme_dans_l_article(charge, numero: str) -> bool:
    """L'article du texte nomme-t-il, hors citation, une autre norme que notre
    code ? Illisible vaut oui : la voie ne tient que si l'on a lu l'article."""
    if not charge or numero not in charge[1]:
        return True
    texte, articles = charge
    debut, fin = articles[numero]
    segment = texte[debut:fin]
    debuts = index_des_lignes(segment)
    return any(not dans_une_citation(segment, debuts, m.start())
               for m in AUTRE_NORME.finditer(segment))


# Les articles de code qu'un dispositif nomme lui-même : hors citation, ou en
# tête de l'article qu'il écrit (« « Art. L. 311-9-… »). Deux « Rédiger ainsi
# cet article » sous l'article 18, qui réécrit L. 311-8-1, écrivaient en fait
# un article L. 311-9-… sur le démarchage : la réécriture entière porte sur N,
# mais ce qu'elle met à la place peut dire qu'elle vise un voisin (docs/51).
NOMME_HORS_CITATION = re.compile(r"\b(?:articles?\s+|art\.\s*)([LRD])\.?\s*(\d+(?:\s*[-‑]\s*\d+)*)",
                                 re.I)
ECRIT_EN_TETE = re.compile(r"[«“]\s*Art\.?\s*([LRD])\.?\s*(\d+(?:\s*[-‑]\s*\d+)*)")


def articles_nommes_par(dispositif: str) -> set[str]:
    def cle(m: re.Match) -> str:
        return m.group(1).upper() + re.sub(r"\s", "", m.group(2)).replace("‑", "-")
    hors_citation = re.sub(r"[«“][^»”]*[»”]", " ", dispositif)
    return ({cle(m) for m in NOMME_HORS_CITATION.finditer(hors_citation)}
            | {cle(m) for m in ECRIT_EN_TETE.finditer(dispositif)})


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
# Et toute ligne qui n'est qu'une mention entre parenthèses — « (division et
# intitulé nouveaux) », « (procédure accélérée) », « (pour coordination) » :
# 90 formes, 1 853 lignes dans le corpus, aucune n'est un alinéa. Celle-là
# comptée sous l'intitulé de la section 15 décalait d'un cran tout l'article
# 11 du texte de commission de la loi consommation (docs/45 § 6).
# Le paragraphe qui n'est que son statut — « III et III bis. – (Non modifiés) » —
# reste compté. Ne pas le compter réparait une arête fausse (docs/51) et en
# décalait 29 autres ; les ancres des amendements le démentaient : 89 confirmant
# et 19 contredisant le compte, contre 92 et 16, et 34 articles à numérotation
# contredite au lieu de 11. L'Assemblée compte ces lignes.
STATUT = re.compile(r"^\s*\(?\s*(?:non modifiée?s?|supprimée?s?|conformes?|"
                    r"suppression (?:maintenue|conforme))\s*\)?\s*$"
                    r"|^\s*\([^()]{1,80}\)\s*$", re.I)


# **Le Sénat numérote lui-même ses alinéas, et le numéro est dans le texte.**
# Depuis 2017 environ, chaque alinéa d'un texte du Sénat est précédé d'une
# « pastille » : un `<span>` en police « Numero », `aria-label="pastille 12"`,
# dont le contenu est un glyphe de la zone privée d'Unicode. `texte_brut` garde
# le glyphe et perd l'attribut ; le glyphe seul suffit, parce que la police est
# un chiffrement régulier : de 1 à 9, une lettre de L à T ; au-delà, le chiffre
# des dizaines (ou des centaines) en chiffre, puis A à J pour les dizaines et
# a à j pour les unités — « 1Aa » se lit 100. Vérifié contre l'attribut sur les
# 873 glyphes distincts des 126 textes qui en portent : zéro écart.
#
# Avant cette lecture, la pastille était comptée comme un alinéa : chaque
# ligne de texte en valait deux, et « l'alinéa 22 » tombait au onzième. Deux
# des trois `alinea` fausses du troisième tirage (docs/44) venaient de là — le
# « a ter) » sur L. 223-5, le « d) » du 2° sur L. 512-18 — et la cause avait
# été nommée « sous-instruction ». Elle ne l'était pas.
PASTILLE = re.compile(r"^\s*([\ue000-\uf8ff]{1,3})\s*$")
# Ce qui ouvre un alinéa : un guillemet, une numérotation — « 1° », « a) »,
# « II. », « A. – » —, un tiret, une parenthèse ou un crochet.
MARQUE_DE_TETE = re.compile(
    r"^\s*(?:[«“]|\d+\s*[°)]|[a-z]{1,2}(?:\s+(?:bis|ter|quater))?\)"
    r"|[IVXL]+(?:\s*(?:bis|ter|quater))?\s*[.)]|[A-H]\s*\.\s*[–-]|[–-]\s|[(\[])")
# **L'amendement qui ancre lui-même le numéro.** « Alinéa 67 : Rédiger ainsi cet
# alinéa : « Art. L. 121-20. – … » » dit quel alinéa porte quel article écrit,
# et c'est une vérité déclarée sur la numérotation, gratuite. Elle sert de
# garde, article de texte par article de texte : si une seule ancre contredit
# le compte, aucun alinéa de cet article n'est lu. Deux causes connues : la
# petite loi, qui est le texte **adopté**, où les alinéas insérés en séance ont
# décalé ceux que les amendements numérotaient ; et le texte de commission
# amendé sur un état antérieur, que rien dans le corpus ne signale.
ANCRE = re.compile(
    r"^\s*(?:I\.\s*[–-]\s*)?alin[ée]a\s+(\d{1,3})\s*(?:,\s*[^R]{0,40})?\s*"
    r"r[ée]diger ainsi cet alin[ée]a\s*:?\s*[«“]\s*(art\.?\s*[LRD]\.?\s*\d+(?:[-‑]\d+)+)",
    re.I | re.S)


def sans_espaces(texte: str) -> str:
    return re.sub(r"\s+", "", texte).lower().replace("‑", "-").lstrip("«“")


def numero_de_pastille(glyphes: str) -> int | None:
    lettres = "".join(chr(ord(c) - 0xF000) for c in glyphes)
    if len(lettres) == 1:
        return "LMNOPQRST".index(lettres) + 1 if lettres in "LMNOPQRST" else None
    if lettres[0].isdigit() and lettres[-1] in "abcdefghij" and (
            len(lettres) == 2 or (len(lettres) == 3 and lettres[1] in "ABCDEFGHIJ")):
        dizaines = "ABCDEFGHIJ".index(lettres[1]) if len(lettres) == 3 else 0
        return int(lettres[0]) * (100 if len(lettres) == 3 else 10) \
            + dizaines * 10 + "abcdefghij".index(lettres[-1])
    return None


def alineas_de(texte: str, debut: int, fin: int) -> dict[int, tuple[int, int]]:
    """Numéro d'alinéa → bornes, dans l'article du texte.

    Numérotation **déclarée** quand le texte porte des pastilles : l'alinéa n
    est la ligne de texte qui suit la pastille n, et rien d'autre n'est un
    alinéa — ni la ligne de statut au-dessus de la première pastille, ni le
    titre de chapitre après la dernière. La lecture s'arrête au premier écart
    à cette forme : une pastille qui ne suit pas la précédente (un article
    que `ENTETE` n'a pas reconnu commence, et sa numérotation repart à 1), ou
    deux lignes de texte sous une même pastille (le tableau comparatif d'une
    petite loi, qui imprime les deux colonnes). Ce qui suit l'écart n'est pas
    numéroté plutôt que numéroté faux.

    Numérotation **comptée** sinon : une ligne non vide vaut un alinéa, la
    ligne de statut exclue, et un intitulé cité que le HTML coupe en deux —
    « IDENTIFICATION DES IMMEUBLES » / « RELEVANT DU STATUT DE LA
    COPROPRIÉTÉ » — recollé : une ligne sans marque de tête, entre deux lignes
    citées, continue la précédente. Sur les 76 amendements qui ancrent
    eux-mêmes un numéro d'alinéa (« Alinéa 67 : rédiger ainsi cet alinéa :
    « Art. L. 121-20 ») dans un texte sans pastille, le compte juste passe de
    56 à 63.
    """
    lignes, position = [], debut
    for ligne in texte[debut:fin].split("\n"):
        if ligne.strip():
            lignes.append((position, position + len(ligne), ligne))
        position += len(ligne) + 1
    pastilles = [(i, numero_de_pastille(m.group(1)))
                 for i, (_, _, ligne) in enumerate(lignes)
                 if (m := PASTILLE.match(ligne))]
    if not pastilles:
        recollees: list[tuple[int, int, str]] = []
        for i, (d, f, ligne) in enumerate(lignes):
            if (recollees and not MARQUE_DE_TETE.match(ligne)
                    and recollees[-1][2].lstrip().startswith(("«", "“"))
                    and i + 1 < len(lignes)
                    and lignes[i + 1][2].lstrip().startswith(("«", "“"))):
                recollees[-1] = (recollees[-1][0], f, recollees[-1][2] + " " + ligne)
                continue
            recollees.append((d, f, ligne))
        return {rang: (d, f) for rang, (d, f, ligne) in
                enumerate((l for l in recollees if not STATUT.match(l[2])), 1)}
    # Au-dessus de la première pastille, rien d'autre que la ligne de statut ou
    # la note de procédure entre crochets — « [Article examiné dans le cadre de
    # la législation partielle en commission] ». Une ligne de texte y dit que la
    # forme n'est pas celle-là : la petite loi en tableau comparatif imprime
    # l'alinéa **avant** sa pastille, et un article que `ENTETE` n'a pas
    # reconnu y laisse sa fin. Dans les deux cas la numérotation n'est pas lue.
    if any(not STATUT.match(ligne) and not ligne.lstrip().startswith("[")
           for _, _, ligne in lignes[:pastilles[0][0]]):
        return {}
    alineas: dict[int, tuple[int, int]] = {}
    for rang, (i, numero) in enumerate(pastilles):
        if numero is None or numero != len(alineas) + 1:
            break
        suivante = pastilles[rang + 1][0] if rang + 1 < len(pastilles) else len(lignes)
        sous_la_pastille = lignes[i + 1:suivante]
        if len(sous_la_pastille) != 1 and not (rang + 1 == len(pastilles)
                                               and len(sous_la_pastille) >= 1):
            break
        alineas[numero] = sous_la_pastille[0][:2]
    return alineas


class Textes:
    """Les textes en discussion, lus une fois, et leurs articles découpés."""

    def __init__(self, base: sqlite3.Connection, corpus: Path) -> None:
        self.base, self.corpus = base, corpus
        self.cache: dict[str, tuple[str, dict[str, tuple[int, int]]]] = {}
        self.alineas_lus: dict[tuple[str, str], dict[int, tuple[int, int]]] = {}

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
                trouvees.append((debut + m.start(), numero_de(m).replace(" ", "")))
        for m in ARTICLE_CREE.finditer(segment):
            trouvees.append((debut + m.start(), numero_de(m).replace(" ", "")))
        # Un paragraphe de tête — « III. – L'article 1er de la loi du 29 mars
        # 1944 est abrogé » — ouvre une instruction même quand elle ne vise aucun
        # article de code ; sans cette borne, le II sur L. 113-3 gouvernait
        # encore les alinéas du III. Une borne sans numéro rend l'alinéa
        # illisible plutôt que rattaché à l'instruction d'avant.
        for m in PARAGRAPHE.finditer(segment):
            trouvees.append((debut + m.start(), ""))
        return sorted(trouvees)

    def alineas(self, texte_id: str, numero: str) -> dict[int, tuple[int, int]]:
        cle = (texte_id, numero)
        if cle not in self.alineas_lus:
            texte, articles = self.charger(texte_id)
            self.alineas_lus[cle] = alineas_de(texte, *articles[numero])
        return self.alineas_lus[cle]

    def ancre_contredite(self, texte_id: str, numero: str, dispositif: str) -> bool | None:
        """None si le dispositif n'ancre rien ; sinon, l'ancre contredit-elle le
        compte des alinéas de cet article du texte."""
        ancre = ANCRE.match(dispositif)
        if not ancre:
            return None
        alineas = self.alineas(texte_id, numero)
        rang, attendu = int(ancre.group(1)), sans_espaces(ancre.group(2))
        if rang not in alineas:
            return True
        texte = self.charger(texte_id)[0]
        return not sans_espaces(texte[slice(*alineas[rang])]).startswith(attendu)

    def gouvernant(self, texte_id: str, numero: str, nommes: list[int],
                   mentions: dict[str, int | None]) -> list[int] | None | str:
        """Les articles du code que le texte réécrit aux alinéas `nommes` de
        l'article `numero` : pour chaque alinéa, la dernière instruction du
        texte avant sa fin, résolue par ce que `porte_sur` en sait. `mentions` :
        numéro cité → article_id, ou None si hors du code. Rend les
        identifiants distincts — « Alinéas 2 et 4 » peut en toucher deux —,
        None si l'une des instructions porte sur un autre code, 'illisible' si
        un alinéa n'existe pas, ouvre une division, ou si l'instruction qui le
        gouverne n'est pas connue."""
        charge = self.charger(texte_id)
        if not charge or numero not in charge[1]:
            return "illisible"
        texte, articles = charge
        alineas = self.alineas(texte_id, numero)
        instructions = self.instructions(texte, *articles[numero])
        cibles: list[int] = []
        for alinea in nommes:
            if alinea not in alineas:
                return "illisible"
            debut, fin_alinea = alineas[alinea]
            ligne = texte[debut:fin_alinea]
            precedent = texte[slice(*alineas[alinea - 1])] if alinea - 1 in alineas else ""
            if DIVISION.match(ligne) or (DIVISION.match(precedent)
                                         and not ARTICLE_OU_DIVISION.match(ligne)):
                return "illisible"   # une division, ou son intitulé
            precedentes = [i for i in instructions if i[0] <= fin_alinea]
            cle = precedentes[-1][1] if precedentes else ""
            if not cle or cle not in mentions:
                return "illisible"   # instruction sans numéro, ou non relevée
            if mentions[cle] is None:
                return None
            if mentions[cle] not in cibles:
                cibles.append(mentions[cle])
        return cibles


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
    numeros = dict(base.execute("SELECT id, numero FROM article"))
    visees: dict[int, set[int]] = defaultdict(set)
    # Les seules arêtes déclarées par le numéro : celles que le contenu désigne
    # (`inferee`, docs/50) sont mesurées pour `vise`, non pour la voie `visee`
    # de `depose_sur`, et les y admettre retirait une `alinea` jugée juste
    # (L311-17 ← 210 du Sénat).
    for amendement_id, article_id in base.execute(
            "SELECT amendement_id, article_id FROM vise WHERE methode = 'declaree'"):
        visees[amendement_id].add(article_id)
    textes = Textes(base, corpus_textes)

    lignes, aretes = [], []
    for chambre, corpus, texte_id in correspondances(base):
        etendue = base.execute("SELECT articles FROM texte_discute WHERE id = ?",
                               (texte_id,)).fetchone()[0]
        distinctes, dans_la_plage = set(), 0
        jeu = base.execute(
            "SELECT id, subdivision, coalesce(dispositif, '') FROM amendement "
            "WHERE chambre = ? AND texte_discute = ?", (chambre, corpus)).fetchall()
        # La numérotation d'un article du texte se vérifie avant de s'en servir :
        # chaque ancre d'amendement de ce jeu la confirme ou la contredit.
        contredits: set[str] = set()
        charge = textes.charger(texte_id)
        for _, subdivision, dispositif in jeu:
            numero = numero_de_subdivision(subdivision)
            if charge and numero in charge[1] \
                    and not ARTICLE_ADDITIONNEL.search(subdivision or ""):
                verdict = textes.ancre_contredite(texte_id, numero, dispositif)
                if verdict is not None:
                    compte["ancre_contredite" if verdict else "ancre_confirmee"] += 1
                if verdict:
                    contredits.add(numero)
        for amendement_id, subdivision, dispositif in jeu:
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
                # L'article déclaré lui-même d'abord ; la chaîne de
                # renumérotation ensuite. La recodification de 2016 a tiré
                # L. 223-1 à L. 223-5 d'un même article d'avant : par la
                # chaîne, ils se valent tous, et « L. 223-5 » déclaré sous un
                # article de texte qui les réécrit tous contredisait tout.
                communes = internes & declarees
                if len(communes) != 1:
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
                # La petite loi est le texte adopté : les alinéas qu'une
                # insertion adoptée en séance a décalés ne portent plus le
                # numéro que les amendements leur donnaient. Sa numérotation
                # n'est pas celle sur laquelle ils ont été déposés.
                if "petite-loi" in texte_id or numero in contredits:
                    compte["alinea_numerotation_contredite"] += 1
                    continue
                if insere_une_instruction(dispositif):
                    compte["insertion_d_une_instruction"] += 1
                    continue
                cible = textes.gouvernant(texte_id, numero, alineas_nommes(trouve),
                                          mentions.get((texte_id, numero), {}))
                if cible == "illisible":
                    compte["alinea_illisible"] += 1
                elif cible is None:
                    compte["alinea_hors_du_code"] += 1
                else:
                    for article_id in cible:
                        aretes.append((amendement_id, article_id, texte_id, numero,
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
            # Le dispositif aussi, quand il ne porte pas sur l'article entier :
            # « Dans le III de l'article L. 863-8 du code de la sécurité sociale
            # créé par le I de cet article » dit lui-même où il agit, et ce n'est
            # pas A. Un « Rédiger ainsi cet article » qui récrit l'article dans une
            # autre loi porte bien sur N, donc sur A — jugé juste (L141-6 ← 8 du Sénat).
            if autre_norme_dans_l_article(charge, numero) \
                    or (not ARTICLE_ENTIER.search(dispositif)
                        and AUTRE_NORME.search(re.sub(r"«[^»]*»", " ", dispositif))):
                compte["article_touchant_une_autre_norme"] += 1
                continue
            if paragraphe_cache(charge, numero):
                compte["paragraphe_non_reproduit"] += 1
                continue
            # La réécriture entière qui nomme des articles du code, et pas A :
            # elle écrit un voisin. Qui ne nomme rien garde la composition.
            cible = next(iter(vises))
            if ARTICLE_ENTIER.search(dispositif):
                nommes = articles_nommes_par(dispositif)
                if nommes and not nommes & {numeros[c] for c in chaine[cible] | {cible}}:
                    compte["reecriture_d_un_voisin"] += 1
                    continue
            aretes.append((amendement_id, cible, texte_id, numero,
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
    print(f"  ce qui est inséré après l'alinéa ouvre une instruction : "
          f"{compte['insertion_d_une_instruction']}")
    print(f"  numérotation contredite par une ancre, ou petite loi  : "
          f"{compte['alinea_numerotation_contredite']}")
    print(f"  ancres d'amendements — confirmant / contredisant le compte : "
          f"{compte['ancre_confirmee']} / {compte['ancre_contredite']}")
    print(f"  un paragraphe ajouté en fin d'article, cible inconnue : "
          f"{compte['ajout_en_fin_de_l_article']}")
    print("\narêtes par voie")
    print(f"  visee — le dispositif nomme l'article                : {compte['voie_visee']}")
    print(f"  alinea — l'instruction gouvernant l'alinéa           : {compte['voie_alinea']}")
    print(f"  article_entier — écarté, l'article touche une autre norme : "
          f"{compte['article_touchant_une_autre_norme']}")
    print(f"  article_entier — écarté, un paragraphe non reproduit : "
          f"{compte['paragraphe_non_reproduit']}")
    print(f"  article_entier — écarté, la réécriture écrit un voisin : "
          f"{compte['reecriture_d_un_voisin']}")
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
