# Trente-neuvième tranche — la pastille du Sénat, et le deux-points de l'incise

**Objet :** attaquer ce que `docs/44` § 2 avait nommé « sous-instruction » —
les trois `alinea` fausses du troisième tirage — et constater que la cause
nommée n'était pas la cause.
**Date : 20 septembre 2026.**
**Code :** `ingestion/textes_deposes.py` (`est_une_cible`),
`ingestion/textes_des_amendements.py` (`alineas_de`, `Textes`).
**Données :** `precision-depose-sur-alinea-4.tsv`,
`precision-porte-sur-incise.tsv` — tirés, **non jugés**.

---

## 1. Les trois fausses, relues

`docs/44` les donnait pour « des sous-instructions — "a bis)" sous un 1°,
"2°" sous un I — que le parseur ne borne pas ». Rejouées une à une sur le
texte :

| amendement | texte, article, alinéa | arête | ce que les juges lisaient | cause réelle |
|---|---|---|---|---|
| Sénat 111 rect. quater | ppl24-469, art. 3, al. 22 | L223-1 | a ter) sur L. 223-5 | l'alinéa 22 tombait sur la ligne 22, qui était la **onzième** : chaque alinéa comptait double |
| Sénat 123 | pjl19-454, art. 1er undecies, al. 9 | L511-10 | d) du 2° sur L. 512-18 | même chose |
| Sénat 350 | pjl13-283, art. 11, al. 29 | L121-101 | Art. L. 121-102 | déjà réparée par la ligne de statut de `docs/44`, la fiche avait été tirée avant |

**Chaque alinéa comptait double** parce que le Sénat numérote lui-même ses
alinéas, et que ce numéro est dans le texte : depuis 2017 environ, chaque
alinéa est précédé d'une « pastille », un `<span>` en police « Numero »,
`aria-label="pastille 22"`, dont le contenu est un glyphe de la zone privée
d'Unicode. `texte_brut` garde le glyphe et perd l'attribut ; le glyphe
faisait une ligne, et la ligne un alinéa. 113 textes du Sénat et 58 de
l'Assemblée sur 872 en portent.

Le glyphe seul suffit, parce que la police est un chiffrement régulier : de 1
à 9, une lettre de L à T ; au-delà, le chiffre des dizaines (ou des centaines)
en chiffre, puis A à J pour les dizaines et a à j pour les unités — « 1Aa »
se lit 100. Vérifié contre l'attribut sur les **873 glyphes distincts** des
126 textes qui en portent : zéro écart. La numérotation des alinéas est donc
**déclarée** là où la pastille existe, et `alineas_de` la lit : l'alinéa n
est la ligne qui suit la pastille n, rien d'autre n'est un alinéa — ni la
ligne de statut au-dessus de la première, ni le titre de chapitre après la
dernière. La lecture s'arrête au premier écart à cette forme — une pastille
qui ne suit pas la précédente, deux lignes sous une même pastille — plutôt
que de numéroter faux.

Et une fois l'alinéa 22 posé sur le bon alinéa — « a ter) Au début du
premier alinéa de l'article L. 223-5, les mots : « Les interdictions
prévues… » sont remplacés par les mots : « … » » —, l'arête restait fausse :
l'instruction n'était pas relevée, et l'alinéa remontait au « a bis) » sur
L. 223-4. Là est la « sous-instruction », et elle n'a rien d'une question de
bornage.

## 2. Le deux-points de l'incise

`est_une_cible` — la règle qui fait d'une référence une cible de `porte_sur`
depuis la onzième tranche — cherche un verbe modificatif entre la référence
et la fin de la phrase, et lit la fin de phrase au premier `.`, `;` ou `:`.
Le deux-points de « les mots : « X » sont remplacés par » est une fin de
phrase pour cette règle ; le verbe est après ; la référence n'est pas une
cible. C'est **la forme la plus courante de la légistique**.

Mesuré sur les 872 textes : **22 604 références hors citation sur 123 162**
sont suivies d'un verbe modificatif que ce deux-points cachait. « Au 3° de
l'article L. 511-5, les mots : « , II et III » sont remplacés par les mots :
« à III bis » » n'était pas une cible ; « Dans la première phrase de
l'article L. 211-16 du code de la consommation, après le mot : « consentie »,
sont insérés les mots : « … » » non plus.

La règle corrigée saute l'incise — un deux-points immédiatement suivi d'un
guillemet ouvrant, jusqu'au guillemet fermant — et cherche le verbe **hors**
de l'incise seulement : « au sens de l'article L. 223-5 : « le contrat est
ainsi modifié » » ne fait pas de L. 223-5 une cible. Le deux-points suivi
d'un retour à la ligne reste une borne : « est ainsi rédigé : » ferme
l'instruction, et le verbe la précède.

Ce que cela fait au graphe, pipeline rejoué de zéro :

| | avant | après |
|---|---:|---:|
| `porte_sur` | 77 182 | **97 676** |
| dont internes | 5 702 | **6 971** |
| articles en vigueur reliés à un article de texte | 949 | **987** |
| `vise` | 569 | 564 |
| `depose_sur` | 1 115 | **1 214** |
| dont `alinea` / `visee` / `article_entier` | 1 051 / 51 / 13 | 1 122 / 76 / 16 |
| verdict `passage_motivant` | 807 | 825 |
| verdict `origine_situee` | 124 | 135 |
| verdict `raison_non_documentee` | 770 | 769 |

`porte_sur` gagne un cinquième d'arêtes internes d'un coup, et **toutes
sont de la forme la plus simple qui soit** — une instruction qui nomme un
article et remplace, supprime ou insère des mots. Sa précision a été mesurée
sur une population qui les excluait (34/35, `docs/41`) ; celle des arêtes
nouvelles ne l'est pas encore. `precision-porte-sur-incise.tsv` en tire vingt,
parmi les arêtes que la règle a créées.

## 3. Deux gardes de plus sur la numérotation comptée

Les textes sans pastille — le Sénat avant 2017, l'Assemblée — restent
comptés : une ligne non vide vaut un alinéa. Cette règle se vérifie, parce
que les amendements la déclarent eux-mêmes : « Alinéa 67 : Rédiger ainsi cet
alinéa : « Art. L. 121-20. – … » » dit quel alinéa porte quel article écrit.
Sur ces **ancres**, prises dans les textes sans pastille :

| compte | juste | décalé de +1 | de +3 ou +4 | introuvable |
|---|---:|---:|---:|---:|
| une ligne, un alinéa | 56 | 11 | 3 | 6 |
| + intitulé coupé recollé | 63 | 4 | 3 | 6 |

Le « +1 » est un intitulé cité que le HTML coupe en deux — « IDENTIFICATION
DES IMMEUBLES » / « RELEVANT DU STATUT DE LA COPROPRIÉTÉ » : une ligne sans
marque de tête entre deux lignes citées continue la précédente. Ce qui reste
décalé a une autre cause, et elle est structurelle : **la petite loi est le
texte adopté**. Les alinéas qu'une insertion adoptée en séance a décalés ne
portent plus le numéro que les amendements leur donnaient ; l'alinéa 10 de la
petite loi 85 (2013-2014) est un « L. 141-23-1 (nouveau) » que l'amendement,
déposé avant, ne pouvait pas compter. La voie `alinea` n'est plus prise sur
une petite loi.

Et les ancres servent de garde : article de texte par article de texte, si
une seule ancre contredit le compte, aucun alinéa de cet article n'est lu.
**88 ancres confirment le compte, 18 le contredisent** ; 13 amendements sont
écartés à ce titre.

## 4. Sur les arêtes déjà jugées

Avant tout nouveau tirage, les trois fiches `alinea` rejouées sur la base
d'aujourd'hui :

- **aucune des 51 justes n'a bougé** — même amendement, même article, les
  deux arbitrées comprises ;
- des 9 fausses : **5 rendent désormais l'article que les juges nommaient**
  (L. 223-5, L. 512-18, L. 121-102, L. 218-7, L. 218-5-3), **3 sont
  retirées** (alinéa gouverné par un autre code, ou par un paragraphe sans
  numéro), 1 est inchangée : l'alinéa 110 de l'article 5 du projet de loi
  consommation, que les juges comptent deux rangs plus bas que le texte de
  2013, sans pastille, ne le permet.

Sur les fiches `visee` et `article_entier`, rien de ce qui était juste n'a
bougé, et quatre `article_entier` fausses sont retirées — l'article du texte
avait une seconde cible que le deux-points cachait.

## 5. Ce qui n'est pas fait

**Rien n'est jugé.** Les deux fiches sont tirées, disjointes de toutes les
précédentes, et vides : `alinea-4` sur vingt arêtes de la population
d'aujourd'hui, `porte-sur-incise` sur vingt arêtes que la règle de l'incise a
créées. La constante `alinea` reste 0,6396 — celle du troisième tirage, qui
ne décrit plus exactement cette arête —, et `porte_sur` garde 0,8558 sur une
population qui a grossi d'un cinquième. Les deux sont à re-mesurer avant
d'être crues.

**Le décalage de deux** de l'alinéa 110 n'est pas expliqué. Le texte 283 de
2013-2014 n'a pas de pastille, et rien dans ses lignes ne dit ce que le Sénat
comptait alors.
