# Trente-quatrième tranche — un texte en discussion est un état, pas une loi

**Objet :** mesurer, puis retenir, les arêtes `porte_sur` qui situent un article
sous un article de texte que la loi promulguée n'a jamais appliqué.
**Date : 19 septembre 2026.**
**Code :** `schema/006-textes-discutes.sql` (colonne `survecu` de
`articles_du_texte`), `ingestion/verdict.py`, `restitution/graphe.py`.

---

## 1. Ce que la relecture a vu

Trois des quatre `non_documente` que la base disait « origine située »
(`docs/39`, relecture) reposaient sur le même mécanisme : le projet de loi,
à un stade de la navette, portait un article qui visait l'article du code ; la
loi promulguée ne l'a pas touché. L412-2 sous l'article 121 de la loi
2011-525 — supprimé en séance ; L321-2 sous l'article 72 quater de la loi
Hamon, deuxième lecture du Sénat ; L313-39 sous le 10 ter a de la CMP de la
loi Chatel. `porte_sur` lit chaque **état** du texte, et c'est sa force — un
article du code peut n'être nommé qu'en première lecture — ; mais un état est
une tentative, pas une origine, tant que LEGI ne dit pas que la loi issue de
ce dossier a écrit l'article.

## 2. Mesuré

La corroboration est celle de `docs/33` : la loi du dossier a-t-elle produit
une version de l'article — créée ou modifiée, jamais seulement abrogée ? La
voie de la citation (`article_cree`) l'exigeait déjà ; la voie de
l'instruction (`texte_en_discussion`), non.

| | |
|---|---:|
| arêtes `porte_sur` internes | 5 705 |
| corroborées par LEGI | 4 941 |
| **non corroborées** | **764** — 728 par la voie de l'instruction, 36 par la citation |
| couples (dossier, article) non corroborés | 233 |
| dont un état de CMP ou définitif porte aussi l'arête | 75 |
| articles en vigueur atteints, chaîne comprise | 949 |
| **dont seulement par des arêtes non corroborées** | **31** |
| verdicts « origine située » qui n'en avaient pas d'autre appui | 31 |

Les 158 couples portés par des états intermédiaires seuls sont la classe
de L412-2. Les 75 portés aussi par un état final sont d'une autre nature :
sondés au hasard, L313-8 sous l'article 42 bis de la CMP de la loi ASAP
(2020-1525) et L112-1 sous le 37 ter de la CMP de la loi Chatel n'ont, selon
LEGI, jamais été touchés par ces lois — dispositions censurées ou retirées
avant promulgation, ou liens absents de LEGI. La distinction n'est pas faite
ici ; les deux cas ne fondent pas une origine.

## 3. Ce qui change

`articles_du_texte` porte `survecu`. **L'arête reste** : la tentative a eu
lieu, et la restitution l'affiche — « ⚠ état intermédiaire : la loi n'a pas
touché l'article » —, parce qu'un lecteur qui cherche pourquoi un article dit
ceci a le droit de savoir qu'on a voulu le changer. Ce qui change est le
**verdict** : « origine située » exige désormais `survecu`.

| | avant | après |
|---|---:|---:|
| partie L — origine située seulement | 143 | **117** |
| partie L — motivation du texte seule | 317 | 334 |
| partie L — raison non documentée | 70 | **79** (6,1 %) |
| partie R — origine située seulement | 12 | 7 |
| raison non documentée, les trois parties | 760 | **770** (36,6 %) |
| sur le jeu : `non_documente` que la base rend tels quels | 7 / 15 | **9 / 15** |
| concordance verdict annoté / verdict de la base | 68 / 100 | 70 / 100 |

Le chiffre d'affiche de la partie législative recule encore, de 94,6 % à
**93,9 %** documentée, et c'est le troisième recul de la journée — lignées,
définition de « non documenté », états intermédiaires — chaque fois pour la
même raison : une vérité extérieure a montré qu'un lien affirmé n'en était pas
un. Le graphe compte moins, et compte juste.

## 4. Ce que la tranche ne fait pas

Elle ne distingue pas la disposition morte en séance du lien manquant dans
LEGI ; les 75 couples portés par un état final le demanderaient, un par un.
Elle ne re-mesure pas la précision de `porte_sur` : les 20 arêtes de
`precision-porte-sur-corpus-elargi.tsv` restent à juger, et `survecu` y sera
une colonne de lecture utile.
