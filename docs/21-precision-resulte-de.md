# Quinzième tranche — mesurer `resulte_de`, et décider

**Objet :** mesurer la précision de l'arête critique sur un échantillon qui
permette d'en conclure quelque chose, et rendre la décision go/no-go du § 8.
**Date : 23 août 2026.**
**Code :** `tools/mesures/precision_resulte_de.py`, gardes dans
`ingestion/amendements_vers_resulte_de.py`.
**Données :** `data/mesures/precision-resulte-de.tsv` (120 arêtes),
`data/mesures/precision-resulte-de-tirage-2.tsv` (60 arêtes disjointes).

---

## 1. Vingt-six arêtes ne mesurent rien

La feuille de route impose à `resulte_de` le seuil le plus haut du projet —
**précision > 95 %**, « cette métrique prime sur toutes les autres ». Elle était
mesurée sur 26 arêtes : 23 justes, borne inférieure de Wilson à 0,7102.

Vingt-six arêtes ne permettent pas de distinguer 88 % de 96 %. L'écart entre la
mesure et le seuil n'était pas un écart de qualité : c'était un manque
d'échantillon. Les tranches successives publiaient une borne qui montait — 0,6853
puis 0,7102 — sans jamais la confronter au 95 % exigé. **Une borne qui progresse
n'est pas une borne qui passe**, et personne ne l'avait écrit.

## 2. Un tirage reproductible

Chaque arête reçoit une clef de tri issue du SHA-256 de son couple (segment,
amendement). L'ordre qui en résulte est sans rapport avec la structure du corpus
— numéro d'article, dossier, chambre — et il est le même à chaque exécution, sans
graine à transmettre. Un échantillon qu'on ne peut pas retirer à l'identique
n'est pas une mesure.

La fiche donne, pour chaque arête, la fenêtre commune qui l'a fondée, le
dispositif complet de l'amendement, le segment retrouvé, et deux corroborations
calculées séparément : l'accord avec `vise` (qui vient du dispositif **déclaré**,
là où l'arête vient du **recouvrement textuel**), et le nombre de segments du
dossier portant la même fenêtre. Ces colonnes n'établissent rien ; elles
orientent l'examen.

## 3. Premier tirage : 83,3 %

| | |
|---|---:|
| Arêtes examinées | 120 |
| Justes | **100** |
| Fausses | 19 |
| Douteuses | 1 |
| Précision ponctuelle | **83,3 %** |
| Borne inférieure de Wilson à 95 % | 0,7565 |

La confiance inscrite dans le graphe — 0,7102 — était donc **honnête et
conservatrice**. Ce n'est pas le confort qui manquait, c'est la marge : la vraie
précision était très en deçà du seuil.

## 4. Les dix-neuf arêtes fausses tiennent en cinq causes

Aucune n'est un accident de calcul. Toutes sont des recouvrements réels de
soixante caractères entre du texte réellement inséré par l'amendement et du texte
réellement présent dans le segment. Le défaut est ailleurs : **le texte inséré
n'allait pas là**.

**a. Le texte hôte n'est pas ce code (8 arêtes).** Un amendement au projet de loi
consommation insère aussi dans le code de commerce, le code monétaire et
financier, le code de l'environnement ou une loi non codifiée. Les formules de
sanction et de renvoi y sont les mêmes mot pour mot :

> « … est passible d'une amende administrative dont le montant ne peut excéder
> 75 000 € … » — inséré dans le **code de commerce**, retrouvé dans L. 111-6-1 du
> code de la consommation.

**b. La fenêtre est l'intitulé d'un texte cité (6 arêtes).** Un article de code
cite couramment le titre complet d'une loi. Ces titres sont longs, identiques
d'un code à l'autre, et un amendement qui cite la même loi produit la même
fenêtre sans avoir rien écrit :

> « … loi n° 89-462 du 6 juillet 1989 tendant à améliorer les rapports locatifs
> … » — trois arêtes distinctes, sur trois amendements sans rapport.

**c. Le texte sortant pris pour un texte entrant (1 arête).** La convention du
Sénat inverse l'ordre habituel : « substituer aux mots : X les mots : Y » met le
texte supprimé **avant** sa marque, là où la rédaction ordinaire le met après. Le
filtre, qui ne lisait que l'aval du guillemet fermant, prenait donc la rédaction
supprimée pour une insertion.

**d. Un article réglementaire (1 arête).** Un amendement à un projet de loi
n'écrit pas un article de décret. La partie R du code porte pourtant les mêmes
formules que la partie L, et une arête rattachait R. 311-5 à un amendement de
l'Assemblée.

**e. Le droit existant cité comme contexte (1 arête).** Un amendement rend L.
115-16 applicable à Wallis-et-Futuna en **reproduisant son texte**. La
reproduction a été prise pour une écriture : l'arête vers l'article créé, L.
116-1, est juste ; celle vers L. 115-16, qui existait déjà, est fausse.

**f. Deux amendements jumeaux (2 arêtes).** Le même auteur dépose, à quelques
numéros d'écart, une disposition sur la téléphonie et son décalque sur
l'électricité. La partie commune dépasse soixante caractères. Les deux arêtes se
croisent.

## 5. Quatre gardes, tirées des cinq premières causes

- **le texte hôte** : on retient la dernière mention de texte hôte qui précède le
  guillemet ; l'absence de mention vaut « le même code », par convention
  légistique. Un passage inséré ailleurs qu'au code de la consommation n'entre
  plus dans l'index ;
- **l'intitulé** : les fenêtres qui commencent dans la citation d'une loi, d'une
  ordonnance ou d'un décret ne sont pas indexées. `règlement` en est
  volontairement absent : l'échantillon donne un cas juste où l'amendement écrit
  lui-même la référence à un règlement de l'Union ;
- **le sens de la substitution** : un passage précédé de « substituer aux mots : »
  est du texte sortant ;
- **la partie du code** : les segments des parties R et D ne sont plus candidats.

La sixième cause — les amendements jumeaux — **n'a pas de garde**, et elle a une
parente : une formule définitionnelle assez générale pour valoir dans deux
articles voisins du **même** code, comme « … de communications électroniques, au
sens du 6° de l'article L. 32 du code des postes … », qui rattache à L. 121-42 un
amendement créant L. 121-84-10-…

Ces deux modes ont la même cause profonde — soixante caractères ne suffisent pas
toujours à désigner un article — et la même parade : allonger la fenêtre. Elle
coûterait du rappel partout pour quelques arêtes. Ils restent donc les modes
d'échec résiduels connus, écrits ici plutôt que corrigés en apparence. L'arête
vers L. 224-43 que produit `restitution/note.py` en est un exemple visible.

## 6. Second tirage, sur pièces neuves : 95,0 %

Un correctif tiré d'un échantillon ne peut pas être mesuré sur ce même
échantillon. Un second tirage a donc été fait, **disjoint du premier** — l'option
`--sauf` du tirage écarte les arêtes déjà examinées.

| | Premier tirage | Second tirage |
|---|---:|---:|
| Arêtes examinées | 120 | 60 |
| Justes | 100 | **57** |
| Fausses | 19 | 2 |
| Douteuses | 1 | 1 |
| **Précision ponctuelle** | 83,3 % | **95,0 %** |
| Borne de Wilson à 95 % | 0,7565 | **0,8630** |

Les deux arêtes fausses restantes sont un intitulé de loi que la garde laissait
passer — la fenêtre commençait sur le premier caractère de l'intitulé, que la
recherche d'index excluait par une borne mal choisie — et une paire d'amendements
jumeaux. La borne d'index corrigée, la mesure passe à 57/59, soit 96,6 %.

**C'est 0,8630 qui est écrite dans le graphe, pas 0,8846.** La seconde valeur est
ajustée sur l'échantillon qui l'a produite ; la première ne l'est pas. Le § 5.4
demande une donnée, pas le meilleur chiffre disponible.

## 6 bis. Recensement complet : 93,9 %, et le seuil n'est pas atteint

Soixante arêtes laissaient encore ±5,5 points d'incertitude. Un troisième
tirage a donc pris **toutes les arêtes restantes** — 120, disjointes des deux
premiers. Les 277 arêtes du graphe sont désormais examinées une à une : **il n'en
reste aucune d'inconnue.**

| | Tirage 1 | Tirage 2 | Recensement | **Hors-échantillon (2 + 3)** |
|---|---:|---:|---:|---:|
| Arêtes | 120 | 60 | 120 | **179** |
| Justes | 100 | 57 | 111 | **168** |
| Fausses | 19 | 2 | 7 | 8 |
| Douteuses | 1 | 1 | 2 | 3 |
| Précision | 83,3 % | 95,0 % | 92,5 % | **93,9 %** |
| Borne de Wilson | 0,7565 | 0,8630 | — | **0,8933** |

**Les 95,0 % du second tirage étaient une fluctuation de petit échantillon.** La
mesure sur 179 arêtes hors-échantillon donne 93,9 %, et l'intervalle ne monte
plus jusqu'à 95 %. Le seuil du § 4.2 n'est pas atteint — c'est maintenant une
conclusion, non une incertitude. C'est 0,8933 qui est écrite dans le graphe.

Le recensement complet du graphe corrigé donne 94,6 % (262/277). Ce chiffre porte
sur les arêtes qui ont servi à corriger les gardes ; il décrit ce graphe-ci, il
ne prédit rien.

### Deux défauts de garde, révélés et corrigés

Le recensement a montré que la garde sur le texte hôte laissait passer deux
formes :

- **le trait d'union insécable.** Les dispositifs du Sénat écrivent « loi
  n° 78‑17 » avec U+2011. La classe de caractères ne reconnaissait que le tiret
  ASCII, et un amendement à la loi Informatique et Libertés se rattachait à
  L. 218-1 du code de la consommation ;
- **la mention d'hôte à l'intérieur du passage cité.** Quand le dispositif ouvre
  un guillemet sur un paragraphe entier — « III. – L'article L. 44 du code des
  postes … est ainsi modifié : « … » — regarder ce qui précède le guillemet ne
  suffit pas. La marque décisive n'est pas la mention seule, car un texte inséré
  cite couramment un autre code sans le modifier, mais la mention **suivie d'une
  formule modificative**.

Les deux corrections retirent exactement les deux arêtes visées et une troisième
juste, sur 282 → 277.

### Ce qui reste faux, et pourquoi

Quinze arêtes sur 277 sont fausses ou douteuses, en quatre familles :

| Famille | Arêtes | Exemple |
|---|---:|---|
| **Dispositions jumelles** | 5 | quatre amendements portant la même phrase sur la téléphonie et sur l'électricité rattachent tous L. 121-91-1 à la version téléphonie |
| **Formule passe-partout dans un autre article du même code** | 5 | « … sont recherchés et constatés dans les conditions prévues au … » |
| **Rédaction proposée non retenue** | 4 | l'amendement écrit « assorti d'un **programme** ouvrant droit à des avantages » ; le texte adopté dit « d'une **carte** » |
| **Droit existant reproduit comme contexte** | 1 | L. 115-16 rendu applicable à Wallis en recopiant son texte |

La quatrième famille est nouvelle et n'était pas visible sur 120 arêtes : un
amendement **adopté** n'est pas forcément adopté *verbatim*. La fenêtre commune
est alors le préfixe partagé entre ce qu'il proposait et ce qui a été voté.

**Le correctif identifié pour la deuxième famille** est l'en-tête d'article que
le dispositif déclare lui-même : « Art. L. 731-4. – … » dit où va le texte, et un
segment de L. 121-49 ne peut pas en venir. C'est le principe déjà retenu pour
`articles_nommes` — la déclaration prime — appliqué à l'intérieur du passage
cité, ce qui suppose de découper celui-ci à chaque en-tête plutôt que de le
traiter d'un bloc. Il retirerait trois des cinq arêtes de cette famille. Il n'est
pas écrit ici : **il ne reste plus une seule arête non examinée pour le mesurer
sur pièces neuves.** Sa validation attend les législatures XV à XVII de
l'Assemblée.

## 7. La décision go/no-go du § 8

Le § 8 prévoit une décision explicite en fin de phase 2 si la couverture de
`resulte_de` passe sous 40 %, au motif que « le produit perd sa raison d'être ».
Elle n'avait jamais été prise. Voici l'état, et la décision.

**Couverture : 79 articles sur 832 éligibles, soit 9,5 %.** Très en deçà du seuil
de 60 % du § 4.2, et en deçà du seuil critique de 40 % du § 8.

**Le repli proposé par le § 8 — « produit centré dossier plutôt qu'article » — est
refusé, parce qu'il est inutile.** Le raisonnement du § 8 suppose `resulte_de`
seule route vers la motivation au grain de l'article. Elle ne l'est pas :

| Voie vers le grain de l'article | Articles en vigueur atteints |
|---|---:|
| Commentaire de rapport nommant l'article | **695** (653 en partie L, soit 51,0 %) |
| Article du texte discuté (`porte_sur`) | 807 |
| Amendement (`resulte_de`) | 79 |

Le commentaire de rapport de commission, source que la feuille de route ne
listait pas et que `docs/04` a introduite, tient le grain de l'article là où
l'amendement ne le tient pas. **Le produit garde sa raison d'être ; c'est
l'hypothèse du § 8 sur le chemin qui était fausse, pas le produit.**

Ce que `resulte_de` apporte reste irremplaçable et ne se substitue pas : l'auteur,
le sort, l'exposé sommaire, c'est-à-dire *qui* a voulu cette phrase et *pourquoi
il disait la vouloir*. Aucune autre arête ne le dit. Elle reste donc la cible
d'amélioration prioritaire, sans être une condition de survie.

**Décision : go.** Avec deux conséquences écrites :

1. **le seuil de couverture de 60 % du § 4.2 est déclaré non atteint et non
   atteignable** sur ce corpus dans l'état des sources. Les amendements de
   l'Assemblée n'existent en open data que depuis la XIVe législature ; et le
   premier échelon de la cascade du § 3 — le tableau synoptique du Sénat, seule
   voie `declaree` prévue — **n'existe pas**, ce qu'avait établi la vérification
   des sources de la phase 0 ([`docs/01`](01-rapport-verification-sources.md)
   § 3.2). La cascade est donc amputée de son échelon le plus fiable, non par
   défaut d'implémentation mais faute d'objet ;
2. **le seuil de précision de 95 % n'est pas atteint** — 93,9 % sur 179 arêtes
   hors-échantillon, borne de Wilson 0,8933 (§ 6 bis). Le graphe est intégralement
   recensé : ce n'est plus une incertitude d'échantillon, c'est un écart mesuré de
   l'ordre d'un point. Le combler demande des gardes supplémentaires, dont une est
   identifiée, et un corpus neuf pour les valider.

## 8. Coût en rappel des gardes

| | Arêtes | Segments | Articles atteints |
|---|---:|---:|---:|
| Avant les gardes | 337 | 272 | 94 |
| Après | **282** | 236 | **79** |

Quinze articles perdent leur rattachement à un amendement. Six arêtes justes de
l'échantillon en font partie — la garde sur le texte hôte se trompe quand un
dispositif nomme un autre code entre deux dispositions de celui-ci, et retient
alors la mauvaise mention.

C'est le prix explicite du § 5.3 : *un lien faux détruit la confiance dans
l'ensemble ; un lien manquant est un trou honnête*. On passe de 19 faux et 100
justes à 2 faux et 57 justes sur des tirages comparables. Le trou est plus grand
et il est honnête.
