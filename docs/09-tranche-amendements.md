# Quatrième tranche — les amendements et l'arête `resulte_de`

**Objet :** relier un alinéa du code à l'amendement qui l'a écrit, avec son auteur
et son sort. C'est l'arête critique de la feuille de route.
**Date : 23 août 2026.** **Code :** `ingestion/amendements_vers_resulte_de.py`.

---

## 1. Pourquoi elle devient possible seulement maintenant

La phase 0 avait établi qu'**aucun** des 307 articles issus de la loi de 2014 n'a
plus cette loi comme texte producteur de sa version en vigueur. Attachée à
l'article, l'arête est vide par construction sur un corpus recodifié — c'est ce
qui avait ramené le golden set à 0/25.

Le grain du segment lève l'obstacle. On n'apparie pas l'amendement au texte
d'aujourd'hui : on l'apparie au segment de la **version que sa propre loi a
produite**, et l'arête `repris_de` de la première tranche porte le lien jusqu'à
l'article en vigueur.

```
article en vigueur --repris_de*--> segment historique --resulte_de--> amendement
```

Cette restriction n'est pas qu'une commodité de calcul : elle **supprime par
construction** la confusion inter-dossiers qui avait produit neuf faux
rattachements sur dix dans la première version du golden set. Un amendement ne
peut plus s'accrocher à un article d'une autre loi.

## 2. Ce que la tranche charge

| | |
|---|---:|
| Acteurs | 933 |
| **Amendements** | **19 078** |
| dont adoptés | 4 091 (21,4 %) |
| **dont rejetés** | **5 913 (31,0 %)** |
| retirés · non soutenus | 3 638 · 1 659 |
| irrecevables art. 40 · cavaliers art. 45 | 795 · 597 |

Le corpus des amendements **non** adoptés est chargé et interrogeable. Il ne
produit aucune arête de provenance — un amendement rejeté n'a écrit aucun texte —
mais c'est le gisement le plus intéressant pour le législateur : ce qui a déjà été
tenté, et ce qui l'a fait échouer.

Une correction de modèle imposée par la donnée : la clef `(dossier, chambre,
numéro)` du § 3 fait collisionner l'amendement n° 1 de première lecture avec celui
de deuxième lecture. Un dossier passe plusieurs textes en navette et chacun
renumérote à partir de 1. La colonne `texte_discute` entre dans la clef.

## 3. Ce que la tranche produit

| | |
|---|---:|
| Arêtes `resulte_de` | **164** |
| Segments touchés · amendements rattachés | 140 · 79 |
| **Articles en vigueur remontant à un amendement nommé** | **53** |
| Fenêtres écartées, non discriminantes | 347 |
| Fenêtres écartées, cible non déclarée | 159 |

```
L121-19  ←  amdt 664 (LE GOUVERNEMENT, adopté)   [loi n° 2014-344 du 17 mars 2014]
L131-3   ←  amdt 848 rect. (M. BIZET, adopté)    [loi n° 2015-990 du 6 août 2015]
L211-3   ←  amdt 564 (Mme LAMURE, adopté)        [loi n° 2014-344 du 17 mars 2014]
```

Ces chaînes traversent une recodification. C'est ce que la feuille de route
demandait et que la phase 0 avait déclaré hors d'atteinte au grain de l'article.

## 4. Trois filtres, chacun tiré d'une erreur vérifiée à la main

La première exécution donnait 210 arêtes. Le contrôle à la main de sept d'entre
elles en a validé quatre. Trois filtres l'ont portée à 13/14 pour 164 arêtes.

**Le texte remplacé n'est pas le texte inséré.** Un dispositif cite entre
guillemets deux choses opposées : ce qu'il introduit et ce qu'il abroge. « Les
mots : *X* sont remplacés par les mots : *Y* » les introduit de la même façon.
`passages_cites` de la phase 0 les confondait, et rattachait donc l'amendement à
la rédaction qu'il faisait disparaître. Le sens se lit dans ce qui **suit** le
guillemet fermant, jamais dans ce qui le précède.

**La discriminance est vérifiée au lieu d'être supposée.** La phase 0 tolérait
qu'une fenêtre désigne deux numéros d'articles, au motif que 84 % de ces cas
étaient le même article de part et d'autre de la recodification de 2016. Les 16 %
restants sont de vraies ambiguïtés. `renumerote_de` permet de trancher : deux
numéros sont acceptés s'ils appartiennent à la même classe de renumérotation, et
refusés sinon. Coût : 35 arêtes.

**La déclaration du rédacteur prime sur l'appariement.** Un dispositif modifie
souvent plusieurs articles voisins avec des rédactions presque identiques —
L. 215-2-2 et L. 215-2-4 dans le même amendement. Quand le dispositif nomme des
articles de ce code, la cible appariée doit être parmi eux. Quand il n'en nomme
aucun — il crée alors des articles dont le numéro n'est pas encore fixé, « Art.
L. …. » — il n'impose rien. Coût : 10 arêtes.

**Confiance : 0,6853**, borne inférieure de Wilson à 95 % pour 13 succès sur 14.
C'est la plus faible du graphe — `motive` et `renvoie_a` sont à 0,839 — et c'est
exact : l'appariement textuel d'un amendement à un alinéa est l'inférence la plus
fragile du projet. Elle doit être présentée comme telle.

## 5. Ce que la tranche ne fait pas

**Le Sénat seulement.** 19 078 amendements, aucun de l'Assemblée. La phase 0 avait
mesuré que 387 des 449 articles issus de la navette ne sont rattachés à aucun
amendement du Sénat, et que l'Assemblée est la chambre de dépôt de la plupart de
ces textes. L'extracteur AN reste le plus gros gain de rappel disponible.

**Le sort n'est pas exploité.** Les 5 913 amendements rejetés, les 795
irrecevabilités au titre de l'article 40 et les 597 cavaliers sont en base et
n'alimentent aucune restitution. C'est le produit législateur qui reste à écrire,
pas la donnée qui manque.

**L'appariement reste textuel.** Un amendement dont la rédaction a été entièrement
réécrite en commission mixte paritaire ne laisse aucune fenêtre commune et
n'apparaît pas. La couverture — 53 articles en vigueur — est une borne basse dont
on ne connaît pas la distance au vrai.
