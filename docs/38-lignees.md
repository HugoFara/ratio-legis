# Trente-deuxième tranche — un numéro n'est pas un article

**Objet :** scinder le nœud `article` en lignées, une par disposition qui a
porté le numéro ; résoudre chaque numéro cité à la date du document qui le
cite.
**Date : 19 septembre 2026.**
**Code :** `schema/001-graphe-provenance.sql`, `ingestion/legi_vers_graphe.py`,
`ingestion/lignees.py` (nouveau), `ingestion/rapports_vers_motive.py`,
`ingestion/sections_vers_motive.py`, `ingestion/textes_deposes.py`,
`ingestion/visees.py`, `ingestion/verdict.py`, et tout ce qui entre par un
numéro dans `restitution/` et `tools/`.

---

## 1. Ce qu'une annotation a trouvé

Le premier article du jeu annoté par un agent (`docs/36` § 5, protocole
`tools/annotation/CONSIGNES.md`) fut L313-10 — la fiche standardisée
d'information sur l'assurance emprunteur. L'agent a rendu `motive`, sur le
rapport du Sénat de 2013 qui a créé la fiche (loi de séparation bancaire,
article 60, ancien L312-6-2). Puis il a signalé ce qui l'avait gêné : **la
fiche de l'article portait l'historique d'un autre article.** L313-10, de 1993
à 2016, c'était le cautionnement disproportionné. La base n'avait qu'un nœud
pour les deux.

`docs/02` § 7 l'avait écrit dès la phase 0, avec un exemple : « Résoudre par
identifiant, jamais par numéro. Un même numéro d'article peut désigner deux
dispositions sans rapport à deux époques. `R531-2` en est le cas type. » Le
modèle avait pourtant clé le nœud `article` par `(code, numero)`, et rien ne
l'avait rattrapé en trente et une tranches — parce que chaque mesure comparait
la base à elle-même. Il a fallu une vérité extérieure.

## 2. La taille du défaut, mesurée avant de corriger

| | |
|---|---:|
| numéros en vigueur ayant eu une version abrogée avant le 1er juillet 2016 | 289 |
| dont le texte d'avant et d'après partagent moins de 15 % de leur vocabulaire | **285** |
| dont plus de 50 % (même disposition, recodifiée sous le même numéro) | 4 |
| entre les deux | 0 |
| **articles en vigueur motivés par un document d'avant 2016 — donc sur l'autre disposition** | **96** |
| dont sans aucun passage d'après 2016 | 82 |

Le seuil de similarité ne tranche rien de discutable : la distribution est
bimodale, 285 d'un côté, 4 de l'autre. La recodification de 2016 a réattribué
presque tous les numéros.

Quatre-vingt-seize articles portaient donc un « passage motivant » qui
expliquait une autre disposition. C'est la classe d'erreur que le § 5.3 place
au-dessus de toutes — un lien faux coûte plus que dix liens manquants — et
elle était dans le chiffre d'affiche : « la partie législative est documentée
à 99,6 % », dont 70,1 % par un passage.

## 3. Le modèle : une lignée par disposition

`article` gagne une colonne `lignee`, rang de la disposition qui a porté le
numéro ; la contrainte devient `UNIQUE (code, numero, lignee)`. Le rang
s'incrémente à chaque **discontinuité** : la version en cours est abrogée, et
la version qui reprend le numéro n'a pas le même texte (Jaccard sur les mots
de quatre lettres et plus, sous 0,5). Une version mort-née ou annulée ne fait
pas lignée : elle rejoint la vivante qui entre en vigueur à sa date si elle en
est la rédaction, sinon la disposition en cours, sinon elle fait lignée à part
— L313-8 en 2016 avait une version mort-née qui était la fiche standardisée
(renumérotée L313-10 en juillet) et n'avait rien à voir avec le L313-8 vivant ;
les fondre faisait remonter à L313-10, par la concordance, le rapport de 2022
sur L313-8.

Deux vues servent tout le reste :

- `article_courant` : la lignée la plus haute parmi celles qui ont eu une
  version vivante — pour ce qui entre par un numéro **sans date** (la
  restitution, l'API, les mesures sur le droit en vigueur) ;
- `periode_article` : le début et la fin de chaque lignée, pour résoudre un
  numéro cité par un document **daté**.

`ingestion/lignees.py` fait la résolution datée, et elle a deux étages parce
que la date seule ne suffit pas : l'ordonnance de recodification est datée de
mars 2016 pour des versions qui entrent en vigueur en juillet. D'abord la
lignée dont un texte du dossier a **écrit** une version — créée ou modifiée,
jamais seulement abrogée — ; c'est LEGI qui le déclare. À défaut, la lignée
dont la période couvre la date du texte du dossier.

Chaque endroit qui résolvait un numéro l'a repris : les rapports de commission
(`rapports_vers_motive`, `sections_vers_motive`), les textes en discussion
(`textes_deposes`), les dispositifs d'amendements (`visees`) résolvent à la
date de leur dossier ; le verdict, la restitution, l'API, les mesures et les
fiches d'annotation passent par `article_courant`. `renvois.py` résolvait déjà
par date de version : il n'a pas bougé, et il était le seul.

`renumerote_de` se construit désormais entre versions, non entre numéros : la
concordance déclarée par LEGI sur une version relie la lignée de cette version
à la lignée de son prédécesseur. Sur L313-10, la chaîne s'arrête à la version
mort-née de L313-8 — LEGI ne déclare pas L312-6-2 — et le graphe dit donc
« aucun passage n'explique cet article », ce qui est exact du point de vue de
ses sources, là où il servait la veille le rapport de 2022 sur l'article
voisin.

## 4. Ce que cela retire, et pourquoi c'est un gain

| | avant | après |
|---|---:|---:|
| nœuds `article` | 3 464 | **3 877** (452 lignées d'un numéro réutilisé, dont 127 de versions mort-nées seules) |
| arêtes `renumerote_de` | 1 882 | 1 929 |
| arêtes `motive` | 1 566 | 1 557 |
| **partie L — un passage les motive** | 907 (70,1 %) | **763 (59,0 %)** |
| partie L — origine située seulement | 121 | 143 |
| partie L — motivation du texte seule | 260 | 382 |
| partie L — raison non documentée | 5 | 5 |
| partie R — un passage les motive | 51 | 43 |
| partie R — raison non documentée | 526 | 530 |
| articles en vigueur motivés, chaîne comprise | 938 | **783** |
| par leur numéro d'aujourd'hui | 245 | 162 |
| articles reliés à un article de texte | 1 079 | 949 |
| articles remontant à un amendement identifié | 122 | 104 |
| articles L ayant une loi dans leur ascendance | 1 080 | 1 043 |
| raison non documentée, les trois parties | 698 | 702 |

**144 articles de la partie L perdent leur « passage motivant »** : 96 dont le
passage commentait l'autre disposition, et ceux qu'un texte en discussion ou
un amendement d'avant 2016 atteignait par un numéro qui ne désignait pas
encore la disposition actuelle. Les 22 qui restent au-dessus de « origine
située » viennent des documents que la tranche précédente a rattachés : ce
n'était pas la même population.

Le chiffre d'affiche recule de onze points, et c'est le chiffre qui était
faux. La partie législative reste « documentée » à 99,6 % — cinq articles
sans rien — mais ce que « documentée » veut dire est plus exact : 59 % par un
passage qui parle de l'article, 11 % par l'article du texte sous lequel il a
été discuté, 29,5 % par un document qui motive le texte entier.

## 5. Ce que la tranche ne fait pas

**Elle ne retrouve pas ce que LEGI ne déclare pas.** L313-10 descend de
L312-6-2, et aucune concordance ne le dit : la chaîne s'arrête. Le rapport de
2013 est dans le corpus, l'annotation l'a désigné, la mesure le compte comme
`autre_passage` — la base sait maintenant qu'elle ne sait pas, elle ne sait pas
encore. Retrouver une concordance non déclarée par le texte des versions
serait une arête `inferee`, à mesurer comme telle.

**Elle ne re-mesure pas les précisions.** `resulte_de` (308 arêtes,
inchangées), `depose_sur` (550), `porte_sur` (59 076) ont la même population
qu'après `docs/37` ; les deux tirages de `docs/37` § 5 restent à juger. Ce qui
a changé est la cible des arêtes, pas leur nombre : une arête qui pointait
vers la lignée d'aujourd'hui pointe vers celle de son époque.

**Elle ne relit pas le jeu d'annotation.** Les fiches sont régénérées sur la
base scindée ; l'historique de L313-10 ne porte plus le cautionnement. Le
verdict de l'agent tient, et il est maintenant en désaccord avec la base dans
le bon sens : l'humain a trouvé un passage, la base n'en a pas.
