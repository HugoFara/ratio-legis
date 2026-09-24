# Quarante-septième tranche — le trait insécable à la lecture, et `vise` et `resulte_de` re-mesurées

**Objet :** `docs/52` avait réparé le trait d'union insécable dans les deux
expressions qui lisent les numéros d'articles des textes en discussion. Il
restait à savoir s'il se cachait ailleurs, et à re-mesurer `vise` et
`resulte_de`, que les mêmes correctifs avaient modifiées sans tirage.
**Date : 24 septembre 2026.**
**Code :** `ingestion/textes_deposes.py`, `tools/prototype/commentaires_rapports.py`,
`ingestion/rapports_vers_motive.py`, `ingestion/visees.py`,
`ingestion/amendements_vers_resulte_de.py`, `restitution/api.py`,
`restitution/tentatives.py`.
**Données :** `precision-vise-remesure.tsv`, `precision-vise-par-le-contenu-2.tsv`,
`precision-resulte-de-remesure.tsv`.

---

## 1. Où est le trait insécable

| source | fichiers | U+2011 | entité `&#8209;` |
|---|---:|---:|---:|
| textes en discussion | 943 | 38 fichiers, 16 384 | 273 fichiers, 120 462 |
| rapports | 1 093 | 66 fichiers, 681 | 73 fichiers, 18 342 |
| études d'impact | 79 | 5 fichiers, 6 | — |
| jeux Améli | 151 | 0 | — |
| segments LEGI | 28 294 | 0 | — |
| dispositifs d'amendements | 97 226 | 29 899 amendements | — |

Les dispositifs étaient déjà servis : `visees.py` et
`amendements_vers_resulte_de.py` y ramènent U+2011 à « - » avant toute
lecture (`TIRETS`, `TRAITS`). Les textes l'étaient depuis `docs/52`, mais
expression par expression — celles des bornes de paragraphe, des en-têtes
d'articles, des ancres admettaient chacune leur propre classe de tirets, ou
ne l'admettaient pas.

**Les rapports ne l'étaient pas.** `commentaires_rapports.py` lit les numéros
cités dans un rapport par `L\.?\s?(\d{3})-(\d{1,3})`, trait d'union ordinaire
seulement, et coupait en outre à trois nombres : « L. 121-84-2-1 » se lisait
L121-84-2.

## 2. La réparation : à la lecture, une fois

Les deux `texte_brut` — celui des textes, celui des rapports — ramènent
désormais U+2011 et U+2010 à « - » après le décodage des entités. Un caractère
pour un caractère : aucun offset ne bouge, ni ceux de `motive`, ni ceux des
preuves, ni ceux du jeu d'annotation, dont `verifier.py` recalcule les
empreintes des deux côtés. `ARTICLE` des rapports admet quatre nombres et ne
s'arrête plus au milieu d'un nombre.

Sur les 91 rapports concernés, 37 490 numéros lus au lieu de 34 988. Les
rapports écrivaient surtout le trait ordinaire, et l'effet sur le graphe est
petit : `motive` gagne deux rattachements et en perd un.

- **Gagnés** : L121-84-10-1 dans deux rapports sur l'article 5 bis A du projet
  consommation (Sénat, Assemblée) — le numéro à quatre nombres ;
  L132-11-2 dans le rapport n° 144 de la XVIe législature — le trait
  insécable. Ce dernier existait déjà, à un autre offset.
- **Perdu** : L121-84-2 dans le rapport du Sénat de 2007, dont l'article
  6 bis porte sur « L. 121-84-2-1 » : l'arête était la troncature.

Aucune autre arête ne change ; le harnais rend le même résultat.

## 3. `vise` et `resulte_de`, re-mesurées

Les correctifs de `docs/52` ont ajouté 31 `vise` et retiré 2 `resulte_de`
sans tirage. La base d'avant n'ayant pas été gardée, les arêtes nouvelles ne
se distinguent plus une à une ; le tirage est fait dans la population
d'aujourd'hui, **disjoint de toute fiche jugée** par une clef qui survit aux
reconstructions — (chambre, dossier, dispositif, article) pour `vise`,
(segment, chambre, dossier, numéro) pour `resulte_de`. Deux juges Sonnet 5
par fiche, colonnes séparées ; un arbitre Opus 5 sur désaccord.

| arête | population non jugée | tirées | juge A | juge B | accord | arbitrage | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|
| `vise` · déclarée | 489 / 652 | 20 | 20 | 20 | 20 | — | **20 / 20** |
| `vise` · par le contenu | 1 / 11 | 1 | 1 | 1 | 1 | — | **1 / 1** |
| `resulte_de` | 120 / 446 | 20 | 18 | 18 | 18 | 2 → 1 juste, 1 faux | **18 / 20** |

**Les deux fausses `resulte_de`.** Un alinéa de L. 215-1-1 attribué à
l'amendement 405, qui rédigeait une clause propre aux contrats d'assurance,
quand c'est le 269 du même dossier qui l'a écrit — les deux juges d'accord.
Et la formule d'injonction administrative — « en lui impartissant un délai
raisonnable, de se conformer » — qu'un VII de L. 141-1 partage avec un alinéa
de L. 218-5-5, destinée au livre Ier et retrouvée au livre II : la famille
des formules banales de `docs/50` § 7, qui n'a toujours pas de garde.

**L'arbitrage juste.** La définition de l'obsolescence programmée (L. 213-4-1)
attribuée à l'amendement 757 de première lecture : le juge B la donnait au
433 de deuxième lecture, qui l'a rétablie après le Sénat. L'arbitre : le I du
433 reprend mot pour mot celui du 757, et le segment codifié en est la forme
condensée. Les deux arêtes seraient justes.

## 4. Les constantes

| constante | tirages | avant | après |
|---|---|---:|---:|
| `vise` · déclarée | 64 / 70 + 20 / 20 | 0,8253 | **0,8621** |
| `vise` · par le contenu | 10 / 10 + 1 / 1 | 0,7225 | **0,7412** |
| `resulte_de` | 52 / 57 + 18 / 20 | 0,8105 | **0,8240** |

`resulte_de` : 70 sur 77, **90,9 %** en ponctuel. Le seuil de 95 % du § 4.2
n'est pas atteint, et la cause restante est la même depuis `docs/50` : la
formule administrative partagée par un passage destiné ailleurs.

## 5. Ce qui n'est pas fait

**La formule banale.** Trois des cinq dernières fausses `resulte_de` en sont.
Une garde demanderait de savoir qu'une fenêtre est commune à plusieurs
articles *hors du dossier* — la rareté d'une fenêtre dans tout le fonds, non
dans le seul dossier comme `nb_segments_fenetre`.

**L'attribution entre amendements d'un même dossier.** L'alinéa écrit par le
269 était aussi attribué au 405 : deux amendements proches, l'un pour les
contrats d'assurance, l'autre général. Quand deux amendements d'un dossier
partagent la fenêtre, le mieux accordé au segment entier devrait l'emporter.
