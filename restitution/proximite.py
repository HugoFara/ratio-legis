#!/usr/bin/env python3
"""Classer les passages d'un document par proximité lexicale avec un article.

**Ce module ne crée aucune arête, et n'affirme rien.** Il ordonne. La distinction
n'est pas de forme : le § 5.1 de la feuille de route interdit d'affirmer sans
source, le § 5.6 interdit qu'un modèle décide d'une arête. Ni l'un ni l'autre
n'interdit de trier, parce qu'un ordre n'est pas une assertion — et parce que
l'alternative n'est pas l'absence d'ordre.

C'est le point qui manquait. Un rapport au Président, une étude d'impact, un acte
de l'Union motivent le **texte entier** ; aucune arête ne désigne le passage qui
concerne tel article, et deux méthodes pour en fabriquer une ont été mesurées
puis écartées (`docs/14` § 5). La restitution en tirait la conséquence qu'il ne
fallait rien choisir, et affichait donc le document depuis l'offset 0 — le début
de l'adresse au Président, les premiers considérants dans l'ordre du texte. Or
**l'ordre du document est lui aussi un ordre**, et c'est le pire de tous : il est
sans rapport avec la question posée, et il était présenté sans étiquette, donc le
lecteur le prenait pour un choix. La rigueur avait été appliquée aux arêtes et
pas à la présentation, alors que l'utilité vit dans la présentation.

**Ce qui est calculé.** Le recouvrement du vocabulaire de l'article avec celui de
chaque passage, chaque terme pesé par sa rareté **dans le fonds** — les 28 294
alinéas du code, `log(N / df)` — et non dans le document interrogé. La première
version pesait dans le document : « consommateur », partout dans un rapport sur
le droit de la consommation, tombait à zéro, ce qui était le but. Mais « prix »,
présent dans dix considérants sur soixante, tombait avec lui, tandis que
« lesquelles » ou « égard », rares dans ce document-là, montaient au maximum.
Rare dans le document n'est pas discriminant pour l'article ; rare dans le
fonds l'est, parce que le fonds est ce dans quoi l'article est écrit.

**Ce qui est refusé.** Un passage n'est classé que s'il partage avec l'article
`TERMES_MINIMUM` termes au moins ; un considérant — une unité entière, non une
fenêtre — que s'il en partage **`DISCRIMINANTS_MINIMUM` discriminants**, de
poids au moins `DISCRIMINANT`, c'est-à-dire présents dans moins d'un alinéa du
code sur deux cents.
Sans cette exigence, deux mots quelconques suffisaient, et L112-1-1 — les
annonces de réduction de prix — recevait en tête trois considérants qui
partageaient avec lui « indique, égard, pendant, exception » : les termes qui le
définissent, « réduction », « annonce », « antérieur », n'apparaissent dans
aucun considérant de la directive 2019/2161, qui a créé la règle par son
article 2 sans la motiver. La bonne réponse est « rien à classer », et la
restitution le dit. Un classement qui départage des passages sans rien de
propre en commun avec l'article donnerait au premier une autorité qu'aucune
mesure ne soutient : précision > rappel (§ 5.3).

Aucun corpus extérieur, aucun apprentissage, aucun vecteur : les poids viennent
de la base interrogée, donc le classement se rejoue à l'identique et s'explique
en montrant les termes qui l'ont produit — ce que la restitution affiche. La
mesure : `tools/mesures/rappel_classement.py`, vingt couples (article,
considérant attendu) et un « aucun » constitués à la main,
`data/mesures/rappel-classement-considerants.tsv` — 17 sur 21, 13 en tête ; et
les rapports au Président du jeu d'annotation, `tools/annotation/verifier.py` —
le passage annoté dans les trois montrés 12 fois sur 17, contre 11 avec la
pondération locale.

**Fenêtre et affichage sont la même chose.** Les passages font
`citation.PLAFOND_EXTRAIT` caractères, soit exactement ce qui sera montré. Classer
sur plus large que ce qu'on affiche ferait juger au lecteur un extrait sur les
mérites d'un texte qu'il ne voit pas. Le recouvrement d'une demi-fenêtre évite
qu'une phrase coupée en deux perde ses deux moitiés.

Les offsets rendus sont ceux du document d'origine : la citation reste résoluble
au sens du § 4.3.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citation import PLAFOND_EXTRAIT  # noqa: E402

# La fenêtre de classement est la fenêtre d'affichage : voir `citation.py`.
TAILLE_PASSAGE = PLAFOND_EXTRAIT
PASSAGES_MONTRES = 3
# Un seul terme commun ne discrimine pas : dans un rapport sur le droit de la
# consommation, tout passage partage « consommateur » avec tout article.
TERMES_MINIMUM = 2
# Et, pour une unité entière — un considérant, mille signes —, deux termes
# quelconques non plus : deux au moins doivent être rares dans le fonds,
# log(200), présents dans moins d'un alinéa du code sur deux cents.
# « réduction » (6,0), « annonce » (5,6), « démarchage » (5,7) comptent ;
# « pratique » (4,7), « prix » (3,7), « consommateur » (2,3) ne comptent pas.
# Un seul ne suffit pas : « rapide », rare dans le code (8,9), suffisait à
# classer sous L112-1-1 un considérant sur le prix personnalisé qui n'a rien à
# voir avec lui. Sur les vingt-et-un couples de la fiche, sans cette exigence
# ou avec un seul terme : 17 réussites et ce considérant reste ; avec deux :
# 17, et il s'en va. La barre ne s'applique pas aux fenêtres de 400 signes des
# documents français : sur les 17 rapports au Président du jeu d'annotation,
# elle ferait passer le passage annoté de 12 à 7 fois dans les trois montrés,
# parce qu'une fenêtre courte partage peu de termes, rares ou non.
DISCRIMINANT = math.log(200)
DISCRIMINANTS_MINIMUM = 2
# Au-delà, on ne classe pas : le coût dépasserait le temps de réponse annoncé, et
# un classement qu'on n'a pas fait doit se dire, non se deviner (§ 5.1).
PLAFOND_DOCUMENT = 4_000_000

ETIQUETTE = ("classé par proximité lexicale avec le texte de l'article — "
             "aucun lien déclaré, aucune arête créée")
RIEN = ("aucun passage de ce document ne partage assez de vocabulaire avec "
        "l'article pour être classé ; son début est montré tel quel")

# Repli des accents **caractère à caractère**, et non par décomposition NFD : la
# décomposition allonge la chaîne, et les offsets rendus ne seraient plus ceux du
# document cité.
_ACCENTS = {c: unicodedata.normalize("NFD", c)[0]
            for c in "àâäáãçéèêëíìîïñóòôöõúùûüýÿœæ"}
_ACCENTS.update({"œ": "o", "æ": "a", "'": " ", "’": " "})
REPLI = str.maketrans(_ACCENTS)

MOT = re.compile(r"[a-z0-9]{4,}")

# Mots-outils français d'au moins quatre lettres : pronoms, adverbes, verbes
# auxiliaires, et le vocabulaire de la rédaction juridique qui ne dit rien du
# sujet — « alinéa », « égard », « exception », « lesquelles », « pendant »
# étaient les « termes communs » que le classement affichait au lecteur sur
# L112-1-1. La liste reste courte : elle écarte ce qui est vide de sujet dans
# tout texte de droit, pas ce qui est fréquent — la rareté dans le fonds s'en
# charge, et une liste longue finirait par écarter du fond.
OUTILS = frozenset("""
alors ainsi apres aucun aucune aussi autre autres avaient avait avec avoir
cela celle celles celui cependant certain certaines certains cette chaque
comme dans deja depuis donc dont elle elles encore entre etaient etait etant
etre eux face fait faire leur leurs lors lorsque mais meme memes moins
notamment outre parmi plus pour pourrait pouvait pouvoir puis quand quel
quelle quelles quels sans selon seulement soit sont sous sur toute toutes
tous tout toutefois trois vers voir etre ceux
afin ailleurs alinea alineas apres aupres autant avant cadre celles-ci cependant
compris dernier derniere dernieres derniers desdits devrait devraient doit
doivent duquel egard ensuite etant exception faut hors indique laquelle
lequel lesquelles lesquels lieu lorsqu mention mentionne mentionnee mentionnees
mentionnes meme notamment paragraphe paragraphes pendant point points prevu
prevue prevues prevus present presente presentes presents relatif relative
relatives relatifs sens suivant suivante suivantes suivants titre vise visee
visees vises devant desquels desquelles auquel auxquels auxquelles duquel
""".split())


_RARETE: dict[str, dict[str, float]] = {}


def rarete(base) -> dict[str, float]:
    """Le poids de chaque terme dans le fonds : log(N / df) sur les alinéas du code.

    Calculé une fois par base et gardé en mémoire — 0,3 s pour 28 294 alinéas et
    6 600 termes, ce qu'un appel de la ligne de commande paie une fois et l'API
    jamais plus. Un terme que le fonds ne porte pas — il ne peut venir que d'un
    passage, jamais de l'article — reçoit le poids maximal, log(N) : il n'entre
    de toute façon dans aucun sac, un sac étant l'intersection avec l'article.
    """
    clef = base.execute("PRAGMA database_list").fetchone()[2]
    if clef not in _RARETE:
        frequence: dict[str, int] = {}
        documents = 0
        for (texte,) in base.execute("SELECT texte FROM segment"):
            documents += 1
            for mot in {m for _, m in termes(texte)}:
                frequence[mot] = frequence.get(mot, 0) + 1
        poids = {mot: math.log(documents / n) for mot, n in frequence.items()}
        poids[""] = math.log(max(documents, 1))          # le poids par défaut
        _RARETE[clef] = poids
    return _RARETE[clef]


def _poids(poids: dict[str, float], mot: str) -> float:
    return poids.get(mot, poids[""])


def _classable(sac: set[str], poids: dict[str, float], unite: bool) -> bool:
    """Assez de termes communs — et, pour une unité entière, assez de rares."""
    if len(sac) < TERMES_MINIMUM:
        return False
    return (not unite
            or sum(_poids(poids, m) >= DISCRIMINANT for m in sac) >= DISCRIMINANTS_MINIMUM)


@dataclass(frozen=True)
class Passage:
    """Un extrait du document, avec de quoi le retrouver et le juger."""
    debut: int
    fin: int
    texte: str
    score: float
    termes: tuple[str, ...]


def _ordonner(sac: set[str], poids: dict[str, float]) -> tuple[str, ...]:
    """Les termes communs, du plus rare au plus courant — et le tri est total.

    Trier sur le seul poids ne suffit pas : deux termes de même fréquence ont le
    même poids, et l'ordre d'itération d'un `set` de chaînes varie d'un processus
    à l'autre. Les exemples versionnés changeaient donc à chaque régénération sans
    qu'aucune donnée ait bougé, ce qui contredit `docs/28` — « le classement se
    rejoue à l'identique » — et la règle § 5.2. Le terme lui-même départage.
    """
    return tuple(sorted(sac, key=lambda mot: (-_poids(poids, mot), mot)))


def termes(texte: str) -> list[tuple[int, str]]:
    """(offset, terme) pour chaque mot retenu, offsets du texte d'origine.

    La marque du pluriel est retirée au-delà de cinq lettres : « annonces de
    réductions de prix » et « annonce d'une réduction de prix » désignent la même
    chose, et les compter comme quatre termes distincts reviendrait à conclure que
    le passage qui répond ne parle pas du sujet. Le seuil épargne « prix », que
    tronquer produirait « pri ».
    """
    plat = texte.lower().translate(REPLI)
    releves = []
    for trouve in MOT.finditer(plat):
        mot = trouve.group()
        if mot in OUTILS:
            continue
        if len(mot) > 5 and mot.endswith("s") and not mot.endswith("ss"):
            mot = mot[:-1]
        if mot not in OUTILS:
            releves.append((trouve.start(), mot))
    return releves


def occurrences(voulus: set[str], texte: str):
    """(offset, terme) pour chaque occurrence d'un terme de `voulus` dans `texte`.

    Sur les documents lourds — 7,4 Mo pour l'article que le droit de l'Union
    sature — la forme naïve, `termes(texte)` puis filtrage, construit 562 000
    chaînes pour en garder 120 000 : 422 ms. Ici la table des formes est
    construite une fois, et la boucle ne fait qu'un accès de dictionnaire par
    jeton : 185 ms. Une alternation compilée sur les 198 termes de l'article a
    aussi été mesurée, et elle est **plus lente** que les deux — 741 ms ; le
    moteur d'expressions régulières ne factorise pas les grandes alternances.
    """
    formes = {}
    for mot in voulus:
        formes[mot] = mot
        formes[mot + "s"] = mot
    for outil in OUTILS:
        formes.pop(outil, None)
    plat = texte.lower().translate(REPLI)
    for trouve in MOT.finditer(plat):
        souche = formes.get(trouve.group())
        if souche is not None:
            yield trouve.start(), souche


def fenetrer(texte: str, taille: int = TAILLE_PASSAGE) -> list[tuple[int, int]]:
    """Fenêtres glissantes à demi-recouvrement, en offsets du document."""
    if not texte:
        return []
    pas = max(1, taille // 2)
    bornes = [(d, min(d + taille, len(texte)))
              for d in range(0, max(1, len(texte) - taille // 2), pas)]
    return bornes


# Recherche d'une frontière de phrase autour d'une borne de fenêtre. Une fenêtre
# glissante tombe où elle tombe ; un extrait qui commence à « à des annonces de
# réductions de prix » a perdu son sujet, et un projet qui vend le verbatim ne
# peut pas afficher des phrases amputées aux deux bouts.
FIN_DE_PHRASE = re.compile(r"[.;:!?]\s")
JEU = 140


def _recadrer(texte: str, debut: int, fin: int) -> tuple[int, int, bool, bool]:
    """(début, fin, phrase entière au début, phrase entière à la fin).

    Les bornes rendues sont celles du document : elles restent citables telles
    quelles. Quand aucune frontière de phrase n'est à portée, on se rabat sur une
    frontière de mot et on le signale — le lecteur voit alors les points de
    suspension, plutôt qu'une phrase qui semble commencer là où elle ne commence
    pas.
    """
    net_debut = debut == 0
    if debut > 0:
        avance = FIN_DE_PHRASE.search(texte, debut, min(debut + JEU, fin))
        recul = None
        for trouve in FIN_DE_PHRASE.finditer(texte, max(0, debut - JEU), debut):
            recul = trouve
        if recul is not None:
            debut, net_debut = recul.end(), True
        elif avance is not None:
            debut, net_debut = avance.end(), True
        else:
            espace = texte.find(" ", debut, min(debut + 40, fin))
            debut = espace + 1 if espace != -1 else debut

    fin = min(len(texte), debut + TAILLE_PASSAGE)
    net_fin = fin == len(texte)
    if not net_fin:
        dernier = None
        for trouve in FIN_DE_PHRASE.finditer(texte, max(debut, fin - JEU), fin):
            dernier = trouve
        if dernier is not None:
            fin, net_fin = dernier.start() + 1, True
        else:
            espace = texte.rfind(" ", debut, fin)
            fin = espace if espace > debut else fin
    return debut, fin, net_debut, net_fin


def _mise_en_forme(texte: str, debut: int, fin: int,
                   net_debut: bool, net_fin: bool) -> str:
    corps = " ".join(texte[debut:fin].split())
    return ("" if net_debut else "…") + corps + ("" if net_fin else "…")


def classer_fenetres(reference: str, texte: str, poids: dict[str, float],
                     garder: int = PASSAGES_MONTRES) -> list[Passage]:
    """Les `garder` meilleurs passages disjoints de `texte`, au regard de `reference`.

    `poids` est la rareté dans le fonds (`rarete`). Rend une liste vide si rien
    n'atteint le seuil, ou si le document dépasse `PLAFOND_DOCUMENT` : dans les
    deux cas l'appelant doit le dire au lecteur.
    """
    if not texte or len(texte) > PLAFOND_DOCUMENT:
        return []
    voulus = {m for _, m in termes(reference)}
    if not voulus:
        return []

    bornes = fenetrer(texte)
    if len(bornes) < 2:
        bornes = [(0, len(texte))]
    pas = max(1, TAILLE_PASSAGE // 2)
    # Un jeton appartient à toutes les fenêtres qui le couvrent — au plus deux,
    # le recouvrement étant d'une demi-fenêtre. Une passe sur les jetons suffit
    # donc, là où une passe par fenêtre relirait le document deux fois.
    sacs: list[set[str]] = [set() for _ in bornes]
    for position, mot in occurrences(voulus, texte):
        premiere = max(0, (position - TAILLE_PASSAGE) // pas + 1)
        for k in range(premiere, min(position // pas, len(bornes) - 1) + 1):
            if bornes[k][0] <= position < bornes[k][1]:
                sacs[k].add(mot)

    classes = []
    for k, sac in enumerate(sacs):
        if not _classable(sac, poids, unite=False):
            continue
        classes.append((sum(_poids(poids, mot) for mot in sac), k, sac))
    # Le tri est total — score, puis offset : deux passages de même score doivent
    # sortir dans le même ordre à chaque exécution (§ 5.2).
    classes.sort(key=lambda x: (-x[0], x[1]))

    retenus: list[Passage] = []
    for score, k, sac in classes:
        debut, fin, net_debut, net_fin = _recadrer(texte, *bornes[k])
        if any(debut < p.fin and p.debut < fin for p in retenus):
            continue                      # déjà couvert par un meilleur passage
        retenus.append(Passage(
            debut, fin, _mise_en_forme(texte, debut, fin, net_debut, net_fin),
            score, _ordonner(sac, poids)))
        if len(retenus) == garder:
            break
    return retenus


def classer_unites(reference: str, unites: list[str], poids: dict[str, float],
                   garder: int = PASSAGES_MONTRES) -> list[tuple[int, float, tuple]]:
    """Même classement, sur des unités déjà découpées — les considérants d'un acte.

    Rend (rang dans la liste reçue, score, termes communs), les meilleurs d'abord.
    Ce qui n'atteint pas le seuil n'est pas rendu : l'appelant garde alors l'ordre
    du document, en le disant.
    """
    voulus = {m for _, m in termes(reference)}
    if not voulus or not unites:
        return []
    sacs = [{m for _, m in termes(u)} & voulus for u in unites]

    classes = []
    for indice, sac in enumerate(sacs):
        if not _classable(sac, poids, unite=True):
            continue
        score = sum(_poids(poids, mot) for mot in sac)
        classes.append((indice, score, _ordonner(sac, poids)))
    classes.sort(key=lambda x: (-x[1], x[0]))
    return classes[:garder]
