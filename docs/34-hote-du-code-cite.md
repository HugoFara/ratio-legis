# Vingt-huitième tranche — le code nommé dans une citation ne déclare pas l'hôte

**Objet :** réparer l'attribution du code hôte de `porte_sur`, à la source.
**Date : 26 août 2026.**
**Code :** `ingestion/textes_deposes.py`, `tools/mesures/precision_porte_sur.py`.

---

## 1. Un défaut trouvé deux fois, réparé nulle part

`porte_sur` est devenue la colonne vertébrale du produit : 43 786 arêtes, 964
articles en vigueur reliés à un article de texte, et deux arêtes construites
par-dessus — `depose_sur` (`docs/31`) et le rattachement de l'étude d'impact au
grain de l'article (`docs/33`).

Deux contrôles à la main l'avaient prise en défaut, à un mois d'intervalle et sur
la même cause :

| | contrôle | fausses | cause nommée |
|---|---|---:|---|
| `docs/31` § 4 | 15 arêtes `depose_sur` | **2** | « l'hôte est déclaré une seule fois, en tête du bloc, hors de la fenêtre de preuve » |
| `docs/33` § 3 | 15 arêtes de la voie citée | **8** | « dans la citation le code a été nommé une fois, loin en amont, et un texte qui modifie plusieurs codes fait dériver la dernière mention » |

Chaque fois, la réponse a porté sur l'arête **nouvelle** : une fenêtre de preuve
qui doit nommer le code pour `depose_sur`, une corroboration par LEGI pour la voie
citée. Chaque fois, `docs/31` § 7 et `docs/33` § 8 ont écrit la même phrase — « la
garde protège l'arête nouvelle, elle ne répare pas l'ancienne » — et l'ont laissée
en dette, au motif que corriger `porte_sur` demandait de re-mesurer la onzième
tranche.

C'est cette dette-là qui est payée ici, et re-mesurée.

## 2. La règle existait déjà : elle n'avait pas été appliquée aux codes

`docs/16` § 4 pose la règle qui a fait passer la précision de la onzième tranche
de 8/20 à 20/20 : **le texte cité n'est pas le texte qui cite.** Une référence
entre guillemets est un morceau de la règle nouvelle ou de l'ancienne, jamais la
cible de la modification. 61 809 références sont écartées à ce titre.

La règle n'avait jamais été appliquée aux **noms de code**. `mentions_de_code`
relevait toutes les mentions du texte, citées comprises, et retenait la dernière
avant la référence. Or :

> Au 1° du I de l'article L. 310-3 **du code de commerce**, après les mots :
> « pour ces deux périodes, », sont insérés les mots : « et pour les ventes autres
> que celles mentionnées à l'article L. 121-16 **du code de la consommation** ».

Le code que ce dispositif modifie est le premier. Le second est un morceau des
mots insérés — mais c'est lui, dernière mention en date, qui gouvernait tout ce
qui suivait. Trois articles plus loin, « Le chapitre II du titre II du livre V
**du même code** est ainsi modifié : 1° L'article L. 522-2 est ainsi rédigé »
désignait les magasins généraux du code de commerce, et le graphe l'attribuait à
l'article L. 522-2 du code de la consommation, qui traite de la prescription des
amendes administratives.

La correction tient en une ligne : **une mention de code prise dans une citation
ne déclare pas l'hôte**, exactement comme une référence prise dans une citation
n'est pas une cible. Le report du « même code » reste ce qu'il était — une
convention légistique juste, qui porte la moitié des rattachements.

## 3. Ce que la population dérivée valait : 8 justes sur 15

La distinction se mesure avant de se réparer.
`tools/mesures/precision_porte_sur.py` tire un échantillon reproductible — clef de
tri SHA-256 du triplet (texte, article du texte, numéro cité), comme pour
`resulte_de` — et sépare trois populations qui ne valent pas la même chose :

- **`hote`** : le code est-il nommé *dans la fenêtre de preuve*, ou reporté d'une
  mention plus lointaine ? Sur les 2 860 arêtes internes de la voie déclarée,
  1 573 vivaient d'un report.
- **`legi`** : la loi issue de ce dossier a-t-elle produit une version de cet
  article ? Source indépendante du texte en discussion.
- **`voie`** : l'instruction déclare la cible, ou c'est l'en-tête d'un alinéa cité
  qui la désigne.

Quinze arêtes tirées de la population la plus exposée — hôte reporté, et non
corroborée par LEGI, 195 arêtes — donnent **8 justes et 7 fausses**, borne
inférieure de Wilson **0,3012**
([`precision-porte-sur-hote-derive.tsv`](../data/mesures/precision-porte-sur-hote-derive.tsv)).
Les sept fausses rattachaient au code de la consommation des articles du code de
commerce, du code de la propriété intellectuelle et du code de la construction et
de l'habitation. **Les sept prennent leur hôte dans une citation.** Les huit
justes le prennent dans l'instruction de leur propre article de texte.

C'est ce partage-là, et non la corroboration par LEGI, qui sépare le vrai du faux :
sur les quinze, les quinze sont désormais classées comme il faut.

## 4. Ce que la correction déplace

Elle ne fait pas que retrancher. Un code cité pouvait aussi **détourner** l'hôte
d'un dispositif qui modifiait bien le code de la consommation :

| | avant | après |
|---|---:|---:|
| arêtes internes devenues externes | | **58** |
| arêtes externes devenues internes | | **1 817** |

Le second nombre est le plus instructif : la dérive coûtait trente fois plus en
rappel qu'en précision, et personne ne l'avait vu, parce qu'une arête `externe`
ne se donne pas à examiner — elle sort du produit sans bruit.

## 5. Deux voies, deux précisions, mesurées sur pièces neuves

Un correctif tiré d'un échantillon ne se mesure pas sur ce même échantillon.
Les deux tirages qui suivent sont postérieurs à la correction et disjoints du
précédent.

| voie | tirage | justes | Wilson 95 % | fiche |
|---|---:|---:|---:|---|
| déclarée — l'instruction nomme la cible | 20 | **20** | **0,8389** | [`declaree`](../data/mesures/precision-porte-sur-declaree.tsv) |
| citation — l'en-tête d'alinéa la désigne | 15 | **15** | **0,7961** | [`citation`](../data/mesures/precision-porte-sur-citation.tsv) |

**Sept des vingt arêtes de la voie déclarée sont des arêtes que la correction a
créées**, et les sept sont justes. Les deux bornes sont celles que le code portait
déjà : la tranche ne relève pas la confiance, **elle rend vraie la population que
cette confiance décrit**. C'est le sens du § 5.4 — la confiance est une donnée, et
une donnée porte sur un ensemble nommé.

Un mot sur l'écart avec `docs/16` § 4, qui mesurait déjà 20/20. Les deux mesures
sont justes : le tirage de la onzième tranche portait sur la population entière,
où la cellule dérivée pèse 6,8 %, et une erreur qui touche une arête sur quinze
d'un sous-ensemble n'apparaît pas dans vingt tirages de l'ensemble. C'est pourquoi
la fiche enregistre désormais **de quelle population** l'échantillon vient.

## 6. « Art. L. 120-1 A » n'est pas l'article L. 120-1

Le tirage de la voie citée a rendu une seule fausse, d'une autre famille : le
texte écrit « « Art. L. 120-1 A (nouveau). – La vente en vrac se définit… » », et
le relevé retenait `L120-1` — un article existant, qui traite des pratiques
commerciales déloyales. La lettre fait partie du numéro.

Le fonds ne porte aucun numéro d'article suffixé d'une lettre : le numéro complet
ne se résout donc pas, et l'arête reste `non_resolue` au lieu de tomber sur
l'article voisin. Trois arêtes dans tout le graphe, toutes sur la vente en vrac,
toutes fausses sans cette lecture. Dans un en-tête d'alinéa cité la lettre est
sans ambiguïté — aucun « à » ne suit un numéro d'article à cet endroit —, ce qui
n'est pas vrai partout : la règle n'est donc appliquée qu'à cette forme.

## 7. Ce que la tranche rapporte, mesuré

| | avant | après |
|---|---:|---:|
| arêtes `porte_sur` | 43 786 | **44 032** |
| dont internes au code | 3 434 | **5 193** |
| dont par l'instruction | 2 860 | 3 639 |
| dont par l'en-tête d'alinéa cité | 574 | 1 554 |
| **articles en vigueur reliés à un article de texte** | 964 (45,8 %) | **1 066 (50,7 %)** |
| arêtes `motive` | 686 | **734** |
| **articles en vigueur qu'un passage motive, chaîne comprise** | 701 | **806** |
| arêtes `depose_sur` | 874 | **906** |
| écartées, non corroborées par LEGI (voie citée) | 179 | 63 |

**Le verdict de la partie législative :**

| partie L | avant | après |
|---|---:|---:|
| un passage les motive | 756 (58,5 %) | **796 (61,6 %)** |
| origine située seulement | 199 | 216 |
| motivation du texte seule | 333 | 276 |
| raison non documentée | 5 | 5 |

Quarante articles de plus remontent à un passage qui les motive, et cinquante-sept
quittent la motivation au grain du texte pour celle au grain de l'article. Les
cinq muets restent cinq : cette tranche ne trouve pas de motivation là où il n'y
en a pas, elle rattache mieux celle qui existe.

## 8. Ce que la tranche ne fait pas

*(Addendum du 27 août 2026 : la garde de `docs/31` est retirée dans
[`docs/35`](35-depose-sur-apres-la-reparation.md), et le raisonnement ci-dessous
était incomplet — elle ne coûtait pas du rappel, elle fabriquait de l'unicité.)*

**Elle ne relâche pas les deux gardes locales, qui coûtent maintenant plus
qu'elles ne rapportent.** La garde de `docs/31` — la fenêtre de preuve doit nommer
le code — écartait 1 398 cibles ; elle en écarte **3 823** maintenant que
`porte_sur` en propose davantage, pour 906 arêtes `depose_sur` retenues. À la
source, l'hôte est désormais attribué correctement ; cette garde fait donc, pour
l'essentiel, double emploi. La relâcher demande de mesurer la précision de
`depose_sur` sur pièces neuves, ce qui est le chantier suivant, pas celui-ci.

**Elle ne qualifie toujours pas le lien.** `porte_sur` sait si l'article du texte
modifie, abroge ou complète, et ne le conserve pas (`docs/16` § 7). Inchangé.

**Elle ne déplie pas les plages.** « Les articles L. 521-1 à L. 521-5 sont ainsi
rédigés » ne produit toujours que les deux bornes.

**Le nom de code stocké reste sale quand il court sur deux lignes.** 1 197 arêtes
portent un `code_cite` du genre « code de la consommation ⏎ article 23 ⏎ le code
de la » : la coupure de reprise ne coupe pas sur le retour à la ligne. Vérifié :
aucune des 95 arêtes internes qui en portent un ne doit sa portée à un nom d'un autre code lu
plus bas — le défaut est d'affichage, pas d'attribution. Il n'est pas corrigé ici
parce que la permissivité qui le cause est celle qui rattrape « code de la ⏎
consommation », et que les deux se règlent ensemble ou pas du tout.
