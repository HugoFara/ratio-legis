#!/usr/bin/env python3
"""Onzième tranche : les textes en discussion, et ce sur quoi ils portent.

Le chaînon manquant. Le graphe savait ce qu'un **article du code** était devenu,
et ce qu'un **article du texte en discussion** avait suscité — un amendement s'y
dépose, un rapport le commente, une étude d'impact le chiffre. Relier les deux
n'était possible nulle part : ce lien n'est écrit qu'à un seul endroit, le texte
lui-même, « L'article L. 121-1 du code de la consommation est ainsi modifié ».

C'est la fonction qu'assurait DuraLex, abandonné depuis février 2019 (`docs/01`
§ 3.2). Il faut donc l'écrire, en s'en tenant à ce que la convention légistique
garantit.

**La convention est celle du code nommé une seule fois.** Un texte nomme le code
qu'il modifie, puis dit « du même code » — parfois pendant vingt articles. Le
suivi se fait donc au niveau du **texte entier**, jamais de l'article : « Le livre
V du même code » à l'article 2 renvoie au code nommé à l'article 1. Un suivi par
article aurait perdu tout ce qui suit la première mention, sans rien signaler.

**Le code est cherché d'abord en aval, dans la même phrase, puis en amont.**
« L'article L. 121-1 du code de la consommation » nomme le code *après* la
référence ; « Dans le même code, les articles L. 521-1 à L. 521-5 » la nomme
avant. Les deux formes coexistent dans la même page.

**Un code nommé dans une citation ne déclare pas l'hôte.** C'est la règle du
§ 4 de `docs/16` — « le texte cité n'est pas le texte qui cite » — appliquée aux
noms de code comme elle l'était aux références. Sans elle, « sont insérés les mots :
« … mentionnées à l'article L. 121-16 du code de la consommation » » faisait
basculer dans ce code tout ce que le dispositif modifiait ensuite (`docs/34`).

**Aucune référence n'est attribuée par défaut.** Contrairement à `renvoie_a`, où
une référence sans code nommé vise le code courant — parce qu'on lit un article de
ce code —, un texte en discussion peut modifier n'importe quel code, et en
modifie souvent plusieurs. Sans code nommé, la portée est `non_resolue`.

**Les plans sont pluriels.** DOLE ne lie pas le texte déposé d'un projet de loi
— il ne lie que celui des propositions, qui n'ont jamais d'étude d'impact
(`docs/15` § 5). Le numéro de dépôt se lit ailleurs, et
`tools/an/plan_textes_deposes.py` en produit un second plan. Les charger en deux
passes ne marcherait pas : ce script reconstruit `texte_discute` et `porte_sur`,
et la seconde passe effacerait la première. Il prend donc tous les plans à la
fois.

Usage :
    textes_deposes.py <corpus/textes/> <plan-textes.tsv> <base.sqlite> [plan...]
"""

from __future__ import annotations

import bisect
import csv
import html
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import fitz          # pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lignees import Resolveur  # noqa: E402

# La série latine va plus loin que « duodecies », et un rang manquant ne se
# rattrape pas : « Article 17 quindecies » n'est alors pas reconnu comme en-tête,
# et **son contenu est rattaché à l'article précédent** — le défaut que le
# commentaire ci-dessous nomme comme le pire possible. 39 en-têtes du corpus
# étaient dans ce cas. Les rangs composés d'un rang listé — « terdecies » se lit
# « ter » puis « decies » — n'ont pas besoin d'entrée propre ; les autres si.
ORDINAL = (r"(?:er|bis|ter|quater|quinquies|sexies|septies|octies|nonies|decies"
           r"|undecies|duodecies|quindecies|sexdecies|septdecies|octodecies"
           r"|novodecies|vicies|unvicies|duovicies|tervicies)")
# L'en-tête peut porter deux lettres — « Article 4 bis BB » — et une mention de
# navette entre parenthèses — « Article 18 B (nouveau) », « Article 27 quater
# (Non modifié) ». Une première version n'admettait ni l'une ni l'autre : les
# articles concernés n'étaient pas reconnus comme des en-têtes, et **leur contenu
# était rattaché à l'article précédent**. C'est le défaut le plus grave possible
# ici, puisqu'il produit un rattachement faux plutôt qu'une absence.
ENTETE = re.compile(r"^[ \t]*Article\s+(\d{1,3}(?:\s*" + ORDINAL + r")*"
                    r"(?:\s*[A-H]{1,2})?)[ \t]*"
                    r"(?:\(?\s*(?:nouveau|non\s+modifié|supprimé|conforme)"
                    r"[^\n]{0,24}\)?)?[ \t]*$", re.M | re.I)
# Le verbe modificatif de la légistique. Il suit la référence dans la même phrase :
# « L'article L. 217-12 du code de la consommation **est complété** par… ». Sans
# lui, la référence n'est qu'une citation — l'article du texte la mentionne, il
# n'agit pas dessus.
ACTION = re.compile(r"\b(?:est|sont)\s+(?:ainsi\s+(?:modifiée?s?|rédigée?s?"
                    r"|complétée?s?)|abrogée?s?|supprimée?s?|remplacée?s?"
                    r"|complétée?s?|insérée?s?|rétablie?s?|ajoutée?s?)"
                    r"|\bdevien(?:t|nent)\b"
                    r"|\bil\s+est\s+(?:inséré|ajouté|rétabli)"
                    r"|\bainsi\s+(?:rédigée?s?|modifiée?s?)", re.I)
# Un alinéa cité s'ouvre par un guillemet, et la convention légistique le rouvre à
# chaque alinéa sans jamais le refermer avant le dernier : suivre la profondeur
# des guillemets ne mène nulle part — essayé, 42 références sur 18 070 étaient
# vues hors citation. C'est le **début de ligne** qui tranche, après la
# numérotation éventuelle.
ALINEA_CITE = re.compile(r"^\s*(?:[0-9]+[°)]\s*|[a-z][)]\s*|[IVX]+\.\s*[–-]?\s*)*[«“]")
# Trois ou quatre chiffres : le code de la santé publique numérote L. 2133-1, le
# code des transports L. 6761-1. Avec trois chiffres seuls, ces références
# n'étaient pas même vues — ni internes, ni externes —, et un article de texte
# qui modifiait deux articles de la santé publique et un du nôtre passait pour
# n'en réécrire qu'un (docs/42, `article_entier`).
REFERENCE = re.compile(r"\b([LRD])\.?\s?(\d{3,4})-(\d{1,3})(?:-(\d{1,3}))?(?!\s?-\s?\S)")
# **L'article écrit dans la citation.** Un article de projet de loi qui réécrit une
# section entière ne nomme aucune cible dans son instruction : il dit « la section
# 2 du même code sont remplacées par les dispositions suivantes : », puis écrit le
# droit nouveau, où chaque article s'ouvre par « Art. L. 121-16. – ». La règle
# générale — une référence citée n'est jamais une cible — écarte ces numéros,
# et à juste titre : ce sont des morceaux de la règle nouvelle.
#
# Mais l'en-tête d'un alinéa cité n'est pas une référence à du droit existant.
# C'est la **désignation de l'article qu'on écrit**, et c'est la seule chose que
# le texte en dise. L'article 5 du projet de loi consommation réécrit vingt-huit
# articles de cette façon, et `porte_sur` n'en voyait aucun : sur les treize
# articles à cible interne du texte déposé, ni l'article 5, ni l'article 13, ni
# l'article 21 — c'est-à-dire précisément ceux dont l'étude d'impact parle.
#
# La forme est exacte et vérifiable : un guillemet ouvrant, puis « Art. », puis le
# numéro. `visees.py` retient la même depuis la cinquième tranche.
ARTICLE_CREE = re.compile(
    r"[«“\"]\s*Art\.?\s*([LRD])\.?\s?(\d{3,4})-(\d{1,3})(?:-(\d{1,3}))?(?!\s?-\s?\S)", re.I)
CODE_NOMME = re.compile(r"\b(?:du|le|au|dans le|de ce)\s+(code\s+[^,;.:)]{3,45})", re.I)
MEME_CODE = re.compile(r"\b(?:du|le|au|dans le)\s+même\s+code\b", re.I)
BORNE = re.compile(r"(?<![LRD])(?<!art)(?<!n°)[.;:]")
# Coupures de reprise, reprises de `renvois.py`. Ne **pas** y mettre « de » : la
# première version le faisait, et tronquait « code de la consommation » en
# « code » — 54 123 rattachements sur 77 019 portaient ce nom vide, et pas un
# seul ne se résolvait.
REPRISE = re.compile(r"\s+(?:et\s+(?:aux?\s+)?(?:articles?|des\s+ar)"
                     r"|ainsi\s+que|prévoit|pour\s|dans\s|sont\s|est\s)")
NOTRE_CODE = re.compile(r"consommation", re.I)
FENETRE_MINI = 60
AVAL = 140                    # portée du regard en aval, dans la même phrase

# Précision mesurée à la main sur 20 rattachements tirés au sort (`docs/16`
# § 4, 20/20), puis par deux juges indépendants sur 15 de plus le 19 septembre
# 2026, population d'aujourd'hui (`docs/41`) : 14 justes sur 15. Les deux
# tirages réunis, 34 sur 35 ; borne inférieure de Wilson à 95 %.
CONFIANCE = 0.8558
# La voie de la citation est mesurée à part, parce qu'elle ne vaut pas la même
# chose : 15 arêtes justes sur 15 vérifiées à la main **après** la garde de
# corroboration (`docs/33` § 4), puis 3 sur 5 le 19 septembre 2026 — dont une
# fausse par glissement de numérotation en navette : le texte adopté écrit
# « Art. L. 423-5 », promulgué L. 423-6. Réunis, 18 sur 20 ; Wilson à 95 %.
CONFIANCE_CREE = 0.6996


def sans_controles(texte: str) -> str:
    """Remplace les caractères de contrôle par une espace, sans décaler les offsets.

    L'extraction PDF rend des NUL. Python les compte, `length()` de SQLite s'arrête
    au premier : une fenêtre de 196 caractères en valait 33 pour la contrainte
    `length(fenetre) >= 60`, qui l'a refusée — à juste titre, puisque la preuve
    stockée aurait été tronquée à la lecture. Les supprimer décalerait les
    offsets ; ils sont donc remplacés, pas retirés.
    """
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", texte)


def texte_brut(chemin: Path) -> str:
    """Texte du fichier, qu'il soit HTML ou PDF — le contenu décide, pas le nom.

    L'Assemblée publie ses textes anciens en HTML latin-1, le Sénat en UTF-8, et
    l'Assemblée ne publie plus les récents qu'en PDF. Les trois cohabitent dans le
    même corpus ; le nombre magique tranche.

    Les retours à la ligne du HTML sont écrasés **avant** de traduire les balises
    de bloc : sans cela le Sénat rend « Le titre I / er / du livre V du code de la
    / propriété intellectuelle », où plus aucune expression n'est reconnaissable.
    """
    brut = chemin.read_bytes()
    if brut.startswith(b"%PDF"):
        with fitz.open(chemin) as document:
            pages = [page.get_text() for page in document]
        lignes = [re.sub(r"[ \t\xa0]+", " ", l).strip()
                  for l in sans_controles("\n".join(pages)).split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lignes))
    # L'encodage se lit dans l'octet, pas dans la déclaration : plusieurs pages de
    # l'Assemblée annoncent un charset qu'elles ne respectent pas, et le
    # remplacement silencieux rendait « code mon\ufffdtaire et financier ».
    try:
        page = brut.decode("utf-8")
    except UnicodeDecodeError:
        page = brut.decode("latin-1")
    page = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page)
    page = page.replace("\r", " ").replace("\n", " ")
    page = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h[1-6]>|</tr>|</li>|</table>",
                  "\n", page)
    page = html.unescape(re.sub(r"<[^>]+>", "", page))
    lignes = [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in page.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lignes))


def numero(m: re.Match) -> str:
    return f"{m.group(1)}{m.group(2)}-{m.group(3)}" + (f"-{m.group(4)}" if m.group(4)
                                                       else "")


def mentions_de_code(texte: str, debuts: list[int]) -> list[tuple[int, str]]:
    """Positions et noms des codes **déclarés**, « du même code » résolu au précédent.

    Le report se fait sur le texte entier : c'est la convention légistique, et la
    restreindre à l'article courant perdrait tout ce qui suit la première mention.

    **Un code nommé dans un passage cité ne déclare pas l'hôte.** C'est la règle
    du § 4 de `docs/16` — « le texte cité n'est pas le texte qui cite » — qui
    n'avait été appliquée qu'aux références, jamais aux codes, et l'oubli
    produisait précisément les rattachements que deux contrôles à la main ont
    trouvés faux (`docs/31` § 4, `docs/33` § 3) :

    > Au 1° du I de l'article L. 310-3 **du code de commerce**, après les mots :
    > « pour ces deux périodes, », sont insérés les mots : « et pour les ventes
    > autres que celles mentionnées à l'article L. 121-16 **du code de la
    > consommation** ».

    Le code que ce dispositif modifie est le premier ; le second est un morceau
    des mots insérés. Retenu comme dernière mention, il faisait basculer dans le
    code de la consommation tout ce qui suivait — « Le chapitre II du titre II du
    livre V **du même code** », c'est-à-dire les magasins généraux du code de
    commerce. Sur quinze arêtes tirées de la population que cette dérive touche,
    sept étaient fausses, et les sept prennent leur hôte dans une citation.
    """
    reperes: list[tuple[int, str]] = []
    evenements = [(m.start(), REPRISE.split(m.group(1))[0].strip().lower())
                  for m in CODE_NOMME.finditer(texte)]
    evenements += [(m.start(), None) for m in MEME_CODE.finditer(texte)]
    dernier = None
    for position, nom in sorted(evenements):
        if dans_une_citation(texte, debuts, position):
            continue
        if nom is not None:
            dernier = nom
        if dernier is not None:
            reperes.append((position, dernier))
    return reperes


def code_de(texte: str, reperes: list[tuple[int, str]], debut: int,
            fin: int) -> str | None:
    """Code auquel se rattache une référence : en aval dans la phrase, sinon en amont."""
    borne = BORNE.search(texte, fin)
    limite = min(borne.start() if borne else len(texte), fin + AVAL)
    for position, nom in reperes:
        if fin <= position < limite:
            return nom
    amont = [nom for position, nom in reperes if position < debut]
    return amont[-1] if amont else None


def articles_du_texte(texte: str) -> list[tuple[str, int, int]]:
    """(numéro d'article du texte, début, fin), par découpe sur les en-têtes."""
    entetes = list(ENTETE.finditer(texte))
    decoupe = []
    for rang, entete in enumerate(entetes):
        fin = entetes[rang + 1].start() if rang + 1 < len(entetes) else len(texte)
        decoupe.append((re.sub(r"\s+", " ", entete.group(1)).strip().lower(),
                        entete.end(), fin))
    return decoupe


def index_des_lignes(texte: str) -> list[int]:
    return [0] + [m.end() for m in re.finditer(r"\n", texte)]


def dans_une_citation(texte: str, debuts: list[int], position: int) -> bool:
    """Vrai si la référence est du texte **cité**, non de l'instruction.

    Un texte en discussion alterne l'instruction — « L'article L. 121-1 est ainsi
    modifié » — et le contenu cité, entre guillemets. Une référence citée est un
    morceau de la règle nouvelle ou de l'ancienne, jamais la cible de la
    modification.

    Deux formes, et il faut les deux. L'alinéa entier cité s'ouvre par un
    guillemet en tête de ligne et ne se referme qu'au dernier alinéa de la série.
    Mais la citation **en incise** est aussi fréquente, et c'est elle qui produit
    les rattachements les plus trompeurs : « la référence : "L. 132-2" est
    remplacée par la référence : "L. 534-1" » désigne L. 132-1 comme cible, et
    L. 132-2 comme simple texte remplacé. À l'intérieur d'une ligne, les
    guillemets sont appariés, et l'incise se lit sans ambiguïté.
    """
    rang = bisect.bisect_right(debuts, position) - 1
    debut = debuts[rang]
    fin = texte.find("\n", debut)
    ligne = texte[debut:fin if fin >= 0 else len(texte)]
    if ALINEA_CITE.match(ligne):
        return True
    local, ouverture = position - debut, None
    for marque in re.finditer(r"[«»]", ligne):
        if marque.group(0) == "«":
            ouverture = marque.end()
        elif ouverture is not None:
            if ouverture <= local < marque.start():
                return True
            ouverture = None
    return False


# Le deux-points qui ouvre une incise citée sur la même ligne — « les mots :
# « X » sont remplacés par » — n'est pas une fin de phrase : c'est la forme la
# plus courante de la légistique, et la borne s'y arrêtait. 22 604 références
# hors citation sur 123 162 étaient suivies d'un verbe modificatif que la borne
# cachait — « Au 3° de l'article L. 511-5, les mots : « , II et III » sont
# remplacés par les mots : « à III bis » » n'était pas une cible. Le
# deux-points suivi d'un retour à la ligne, lui, reste une borne : « est ainsi
# rédigé :\n« … » ferme l'instruction, et le verbe la précède.
INCISE = re.compile(r":[ \xa0]*[«“]")
FIN_D_INCISE = re.compile(r"[»”]")


def phrase_hors_incises(texte: str, fin: int, limite: int) -> list[tuple[int, int]]:
    """Les morceaux de la phrase qui suit `fin`, jusqu'à sa borne, les incises
    citées retirées : le verbe qu'on y cherche doit être celui de
    l'instruction, pas un mot de la citation."""
    morceaux, position = [], fin
    while (borne := BORNE.search(texte, position, limite)):
        if borne.group(0) != ":" or not INCISE.match(texte, borne.start()):
            morceaux.append((position, borne.start()))
            return morceaux
        morceaux.append((position, borne.start()))
        fermeture = FIN_D_INCISE.search(texte, borne.end(), limite)
        if not fermeture:
            return morceaux
        position = fermeture.end()
    morceaux.append((position, limite))
    return morceaux


def est_une_cible(texte: str, debut: int, fin: int) -> bool:
    """Vrai si un verbe modificatif suit la référence, dans la même phrase."""
    return any(ACTION.search(texte, a, b)
               for a, b in phrase_hors_incises(texte, fin, min(len(texte), fin + 300)))


def bornes(texte: str, debut: int, fin: int) -> tuple[int, int]:
    """Bornes de la fenêtre de preuve autour d'une référence.

    Séparées de `fenetre` parce que la garde d'hôte s'y adosse : le code est dit
    **nommé** quand sa mention tombe dans cette fenêtre, **supposé** quand elle
    est plus loin. La preuve stockée et la garde regardent ainsi exactement le
    même passage — une garde qui jugerait sur plus que ce que la preuve montre
    ne serait pas vérifiable.
    """
    marge = max(0, (200 - (fin - debut)) // 2)
    return max(0, debut - marge), fin + marge


def fenetre(texte: str, debut: int, fin: int) -> str | None:
    gauche, droite = bornes(texte, debut, fin)
    extrait = re.sub(r"\s+", " ", texte[gauche:droite]).strip()
    return extrait if len(extrait) >= FENETRE_MINI else None


def main() -> None:
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    corpus, plan, chemin_base = (Path(a) for a in sys.argv[1:4])
    plans = [plan] + [Path(a) for a in sys.argv[4:]]
    base = sqlite3.connect(chemin_base)
    schema = Path(__file__).resolve().parent.parent / "schema" / "006-textes-discutes.sql"
    base.executescript(schema.read_text(encoding="utf-8"))
    base.execute("DELETE FROM preuve WHERE methode IN "
                 "('texte_en_discussion', 'article_cree')")

    connus = {d for (d,) in base.execute("SELECT id_dole FROM dossier")}
    # Le numéro se résout à la date du dossier : un texte de 2010 qui modifie
    # « L. 313-10 » modifie le cautionnement, pas la fiche standardisée qui porte
    # ce numéro depuis 2016 (`lignees.py`).
    resolveur = Resolveur(base)
    # **Corroboration par LEGI**, exigée de la seule voie de la citation. Le code
    # hôte y est implicite : l'instruction le nomme une fois, loin en amont, et un
    # texte qui modifie plusieurs codes à la suite fait dériver la dernière
    # mention. Sur quinze arêtes vérifiées à la main, huit étaient fausses de ce
    # seul fait — des articles du code du tourisme, de la propriété
    # intellectuelle ou monétaire et financier rattachés au nôtre.
    #
    # La garde ne devine pas le bon code : elle demande à une **source
    # indépendante** si la loi issue de ce dossier a produit une version de cet
    # article. Si elle ne l'a pas produite, l'article du texte ne l'écrivait pas.
    # Les huit fausses de l'échantillon y tombent toutes.
    #
    # La voie déclarée, elle, n'y est pas soumise : son code est nommé dans la
    # même phrase, et `docs/16` § 4 en mesure la précision à 20/20.
    produits = defaultdict(set)
    for dossier_id, article_id in base.execute(
            "SELECT i.dossier_id, v.article_id FROM issu_de i "
            "JOIN produite_par p ON p.texte_id = i.texte_id "
            "JOIN version_article v ON v.id_legi = p.version_id"):
        produits[dossier_id].add(article_id)
    suivant = (base.execute("SELECT COALESCE(MAX(id), 0) FROM preuve").fetchone()[0]) + 1

    textes, liens, preuves = [], [], []
    compte = {"interne": 0, "externe": 0, "non_resolue": 0, "absents": 0,
              "hors_perimetre": 0, "sans_preuve": 0, "cite": 0,
              "citee_sans_action": 0, "cree": 0, "cree_deja_declare": 0,
              "cree_non_corrobore": 0}

    lues = [ligne for chemin in plans
            for ligne in csv.DictReader(chemin.open(encoding="utf-8"),
                                        delimiter="\t")]
    for ligne in lues:
        fichier = corpus / f"{ligne['dossier']}__{ligne['fichier']}"
        if not fichier.exists():
            compte["absents"] += 1
            continue
        if ligne["dossier"] not in connus:
            compte["hors_perimetre"] += 1
            continue
        contenu = texte_brut(fichier)
        decoupe = articles_du_texte(contenu)
        debuts = index_des_lignes(contenu)
        reperes = mentions_de_code(contenu, debuts)
        identifiant = f"{ligne['chambre']}/{ligne['fichier']}"
        textes.append((identifiant, ligne["dossier"], ligne["chambre"],
                       ligne["stade"], ligne["url"], len(decoupe)))
        vus = set()
        for article_du_texte, debut, fin in decoupe:
            for reference in REFERENCE.finditer(contenu, debut, fin):
                cle = numero(reference)
                if (article_du_texte, cle) in vus:
                    continue
                if dans_une_citation(contenu, debuts, reference.start()):
                    compte["cite"] += 1
                    continue
                if not est_une_cible(contenu, reference.start(), reference.end()):
                    compte["citee_sans_action"] += 1
                    continue
                code = code_de(contenu, reperes, reference.start(), reference.end())
                if code is None:
                    portee, article_id = "non_resolue", None
                elif NOTRE_CODE.search(code):
                    article_id = resolveur.du_dossier(cle, ligne["dossier"])
                    portee = "interne" if article_id else "non_resolue"
                else:
                    portee, article_id = "externe", None
                extrait = fenetre(contenu, reference.start(), reference.end())
                if extrait is None:
                    compte["sans_preuve"] += 1
                    continue
                vus.add((article_du_texte, cle))
                compte[portee] += 1
                preuves.append((suivant, "texte_en_discussion", extrait,
                                reference.start()))
                liens.append((identifiant, article_du_texte, article_id, cle,
                              code, portee, "derivee", CONFIANCE, suivant))
                suivant += 1

            # Seconde passe : les articles que l'article du texte **écrit**, et
            # qu'il ne désigne nulle part ailleurs. Elle vient après la première
            # et partage son ensemble `vus` : une cible déjà déclarée dans
            # l'instruction est mieux établie que la même relevée dans la
            # citation, et ne doit pas être comptée deux fois.
            for creation in ARTICLE_CREE.finditer(contenu, debut, fin):
                # « Art. L. 120-1 A » n'est pas l'article L. 120-1. La lettre
                # fait partie du numéro, et le fonds n'en porte aucune : le
                # numéro suffixé ne se résout pas, l'arête reste `non_resolue`
                # au lieu de tomber sur l'article voisin. Trois arêtes, toutes
                # sur la vente en vrac, et toutes fausses sans cette lecture.
                # Dans un en-tête d'alinéa cité la lettre est sans ambiguïté —
                # aucun « à » ne suit un numéro d'article à cet endroit.
                lettre = re.match(r"\s+([A-H]{1,2})\b", contenu[creation.end():
                                                                creation.end() + 6])
                cle = numero(creation) + (f" {lettre.group(1)}" if lettre else "")
                if (article_du_texte, cle) in vus:
                    compte["cree_deja_declare"] += 1
                    continue
                code = code_de(contenu, reperes, creation.start(), creation.end())
                if code is None:
                    portee, article_id = "non_resolue", None
                elif NOTRE_CODE.search(code):
                    article_id = resolveur.du_dossier(cle, ligne["dossier"])
                    portee = "interne" if article_id else "non_resolue"
                else:
                    portee, article_id = "externe", None
                if (portee == "interne"
                        and article_id not in produits.get(ligne["dossier"], ())):
                    compte["cree_non_corrobore"] += 1
                    continue
                extrait = fenetre(contenu, creation.start(), creation.end())
                if extrait is None:
                    compte["sans_preuve"] += 1
                    continue
                vus.add((article_du_texte, cle))
                compte[portee] += 1
                compte["cree"] += 1
                preuves.append((suivant, "article_cree", extrait, creation.start()))
                liens.append((identifiant, article_du_texte, article_id, cle,
                              code, portee, "derivee", CONFIANCE_CREE, suivant))
                suivant += 1

    base.executemany("INSERT INTO texte_discute (id, dossier_id, chambre, stade, "
                     "url, articles) VALUES (?, ?, ?, ?, ?, ?)", textes)
    base.executemany("INSERT INTO preuve (id, methode, fenetre, source_offset) "
                     "VALUES (?, ?, ?, ?)", preuves)
    base.executemany(
        "INSERT INTO porte_sur (texte_id, article_du_texte, article_id, "
        "numero_cite, code_cite, portee, methode, confiance, preuve_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", liens)
    base.commit()

    violations = base.execute("PRAGMA foreign_key_check").fetchall()
    couverts, en_vigueur = base.execute(
        "SELECT (SELECT count(DISTINCT article) FROM articles_du_texte), "
        "(SELECT count(DISTINCT article_id) FROM version_en_vigueur)").fetchone()

    print(f"plans lus                  : {len(plans)} ({len(lues)} lignes)")
    print(f"textes chargés             : {len(textes)}")
    print(f"  absents du corpus        : {compte['absents']}")
    print(f"  dossier hors périmètre   : {compte['hors_perimetre']}")
    print(f"  articles de texte relevés : {sum(t[5] for t in textes)}")
    print(f"rattachements relevés      : {len(liens)}")
    for portee in ("interne", "externe", "non_resolue"):
        part = 100 * compte[portee] / len(liens) if liens else 0
        print(f"  {portee:12s}           : {compte[portee]} ({part:.1f} %)")
    print(f"  écartés faute de preuve  : {compte['sans_preuve']}")
    print("références écartées :")
    print(f"  dans un passage cité, donc non cibles : {compte['cite']}")
    print(f"  sans verbe modificatif, donc citées : {compte['citee_sans_action']}")
    print(f"\narticles écrits dans la citation, relevés : {compte['cree']}")
    print(f"  déjà déclarés par l'instruction : {compte['cree_deja_declare']}")
    print(f"  écartés, non corroborés par LEGI : {compte['cree_non_corrobore']}")
    print(f"\narticles en vigueur reliés à un article de texte : {couverts} "
          f"({100 * couverts / en_vigueur:.1f} %)")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
