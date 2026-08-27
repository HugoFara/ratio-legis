# Vingt-neuvième tranche — `depose_sur` ne survit pas à la réparation de son maillon

**Objet :** relâcher la garde d'hôte de `depose_sur`, et mesurer ce qui reste.
**Date : 27 août 2026.**
**Code :** `ingestion/textes_des_amendements.py`, `ingestion/textes_deposes.py`,
`tools/mesures/precision_depose_sur.py`.

---

## 1. Ce que la réparation de `porte_sur` a fait à cette arête

`docs/34` § 8 laissait une question ouverte, avec son chiffre : la garde de
`docs/31` — la fenêtre de preuve doit nommer le code — écartait **3 823 cibles**
pour 906 arêtes `depose_sur` retenues, et l'hôte étant désormais attribué
correctement à la source, elle paraissait faire double emploi.

La relâcher devait donc rendre du rappel. Elle en retire : **906 arêtes deviennent
491**. Le compteur qui explique tout est un autre : « l'article du texte en modifie
plusieurs » passe de 170 à 1 193.

La garde ne servait plus de filtre. Elle servait de **désambiguïsateur**.

## 2. Une garde qui fabriquait l'unicité qu'elle était censée constater

`depose_sur` a une définition étroite, et c'est ce qui en fait le prix :
l'amendement fut déposé sur l'article X du texte, et l'article X réécrit l'article
A du code — **et aucun autre**. Sans cette dernière condition, l'arête ne dit rien :
un amendement déposé sur un article qui en réécrit douze ne se rattache à aucun
des douze.

En retirant des cibles vraies d'un article de texte qui en réécrit plusieurs, la
garde le faisait passer pour n'en réécrire qu'un. L'unicité n'était plus constatée,
elle était produite par le filtre — et l'article retenu était celui dont la fenêtre
de preuve nommait le code, c'est-à-dire un accident de rédaction.

**Mesuré sur le graphe réparé, garde encore en place :**

| | arêtes | dont l'amendement déclare une cible | dont la cible déclarée concorde |
|---|---:|---:|---:|
| article du texte à cible unique | 405 | 15 | **12** |
| article du texte à cibles multiples | **501** | 17 | **2** |

La concordance est calculée sur la chaîne de renumérotation, et elle vient d'une
source indépendante : `vise` lit le **dispositif** de l'amendement, `depose_sur`
compose deux liens de `porte_sur`. Douze sur quinze d'un côté, deux sur dix-sept
de l'autre : la cellule des cibles multiples n'est pas moins bonne, elle est
fausse.

## 3. Ce que l'arête valait, mesuré à la main

`tools/mesures/precision_depose_sur.py` tire un échantillon reproductible, du même
gabarit que ceux de `resulte_de` et de `porte_sur`. Quinze arêtes du graphe encore
gardé : **3 justes, 1 douteuse, 11 fausses**, borne inférieure de Wilson
**0,0705**
([`precision-depose-sur-avec-garde.tsv`](../data/mesures/precision-depose-sur-avec-garde.tsv)).

L'arête portait alors la valeur `0,7961`, mesurée par `docs/31` à 15/15 — sur un
graphe où la garde retirait encore des cibles **fausses**. La réparation de
l'hôte a fait basculer la population sous elle sans que rien ne le signale : c'est
le risque propre à une confiance écrite en constante et à une arête composée.

**Onze fausses, deux familles.** Huit reposaient sur un article de texte à cibles
multiples. Trois venaient d'ailleurs, et c'est la seconde moitié de la tranche.

## 4. Le numéro de subdivision n'était pas lu en entier

Un amendement déclare la subdivision qu'il amende — « Article 60 bis A »,
« ART. 18 D », « Article 5 sexdecies ». Le module en lisait le numéro et le rang
latin, pas le reste :

- **La lettre.** « Article 60 bis A » était lu *60 bis*, et l'amendement rattaché
  à un autre article du texte, d'un autre objet. `ENTETE`, du côté du texte, lit
  cette lettre depuis la onzième tranche : le besoin est le même vu des deux
  bouts. **1 230 subdivisions** portent une lettre, et 454 articles de texte en
  portent une dans `porte_sur`.
- **Le rang latin au-delà de `decies`.** « Article 5 sexdecies » était lu
  *article 5*. Les rangs composés d'un rang connu — « terdecies » se lit « ter »
  puis « decies » — passaient déjà ; « quindecies », « sexdecies », « septdecies »,
  « octodecies », « novodecies » et la série en « vicies » n'avaient aucune entrée.

Le second défaut ne touchait pas que les amendements : `ENTETE` a la même lacune,
et **39 en-têtes du corpus n'étaient pas reconnus comme tels**. Leur contenu était
donc rattaché à l'article précédent — exactement ce que le commentaire de ce
module appelle « le pire défaut possible ici, puisqu'il produit un rattachement
faux plutôt qu'une absence ». Les deux listes sont alignées sur la même série.

## 5. Ce que l'arête vaut maintenant

Tirage postérieur aux deux corrections, disjoint du précédent : **15 arêtes justes
sur 15**, borne inférieure de Wilson **0,7961**
([`precision-depose-sur.tsv`](../data/mesures/precision-depose-sur.tsv)). Les
quinze reposent, par construction cette fois, sur un article de texte à cible
unique, et leur subdivision est lue en entier.

La constante ne change donc pas de valeur — `CONFIANCE = 0,7961` — mais elle ne
décrit plus la même arête, et c'est tout l'objet de la tranche. Son commentaire
dit désormais de quelle mesure elle vient.

## 6. Ce que la tranche rapporte, mesuré

| | avant | après |
|---|---:|---:|
| **précision mesurée à la main** | **3/15 — Wilson 0,0705** | **15/15 — Wilson 0,7961** |
| arêtes `depose_sur` | 906 | **476** |
| dont sur un article de texte à cibles multiples | 501 | **0** |
| amendements positionnés sur un article en vigueur | 461 | 231 |
| tentatives rendues, toutes voies | 689 | **457** |
| dont non abouties | 460 | 254 |
| **articles en vigueur atteints** | 19 | **21** |
| dont sans aucune tentative déclarée jusqu'ici | 12 | **14** |
| subdivisions lisibles tombant dans la plage du texte | 3 842 / 3 922 (98,0 %) | **4 368 / 4 449 (98,2 %)** |
| en-têtes d'articles de texte reconnus | 31 368 | **31 407** |

Deux lectures valent d'être tenues ensemble. L'arête perd **47 %** de ses effectifs
et **gagne** deux articles en vigueur : ce qu'elle retire, ce sont des
rattachements qui ne désignaient rien ; ce qu'elle ajoute vient de subdivisions
qu'on ne savait pas lire. Et le contrôle d'appariement, qui est le garde-fou de la
vingt-cinquième tranche, monte de 98,0 % à 98,2 % **sur 527 subdivisions de
plus** — un correctif de lecture qui aurait faussé l'appariement l'aurait fait
baisser.

`porte_sur` ne bouge pas : 44 032 arêtes, 5 193 internes, 1 066 articles en
vigueur reliés. Les 39 en-têtes retrouvés déplacent 14 rattachements d'un article
de texte à un autre, aucun interne.

## 7. Ce que la tranche ne fait pas

**Elle ne rend pas les 1 226 articles de texte à cibles multiples.** Un amendement
déposé sur un article qui réécrit douze articles du code reste sans rattachement,
et ce n'est pas un défaut de lecture : le texte ne dit pas lequel des douze
l'amendement touche. Ce qui le dirait, c'est le dispositif de l'amendement — donc
`vise`, une autre voie, avec sa confiance propre. Les composer serait une
troisième arête, à mesurer comme telle.

**Elle ne relit pas les 1 615 subdivisions illisibles.** Elles ne portent pas de
numéro d'article — « Intitulé du projet de loi », « Division additionnelle » —, ou
un intitulé que ce module ne sait pas ramener à un numéro. Le compte est publié,
la cause n'est pas ventilée.

**Elle ne corrige pas la lettre du côté de `resulte_de`.** `visees.py` lit lui
aussi des numéros d'article ; la même série latine y est peut-être tronquée. Non
vérifié, donc non prétendu.
