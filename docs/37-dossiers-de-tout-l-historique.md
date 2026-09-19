# Trente et unième tranche — le corpus suit tout l'historique, pas le premier dossier

**Objet :** dériver les dossiers à récupérer de tous les textes qui ont touché un
article en vigueur, et non du seul dossier d'origine du périmètre.
**Date : 19 septembre 2026.**
**Code :** `tools/dila/dossiers_du_perimetre.py` (nouveau), les cinq plans de
`tools/dila/` et `tools/senat/plan_ameli.py`, `ingestion/rapports_vers_motive.py`,
`ingestion/sections_vers_motive.py`, `tools/dila/plan_textes.py`, `pipeline.sh`.

---

## 1. Une convention de phase 0 devenue la frontière du corpus

Le périmètre porte un dossier par article : `id_dole_origine`, celui du texte
qui a **créé** le prédécesseur, un seul saut. C'était une convention pour
trouver *une* origine par article, et la phase 0 l'a mesurée comme telle. Mais
les six plans de récupération — rapports, textes en discussion, études d'impact,
exposés des motifs, rapports au Président, jeux d'amendements du Sénat — en
avaient fait leur liste de dossiers, et l'ingestion des rapports en avait fait
sa garde : « dossier hors périmètre : rien à motiver ».

Le corpus disait donc qu'un texte qui **modifie** un article n'a pas de dossier
à charger. `docs/36` l'a vu sur une fiche : L621-3 descend de quatre articles
d'avant 2016, dont un créé par la loi LME de 2008, et le jeu le disait « sans
document ». Mesuré sur toute la base :

| | |
|---|---:|
| dossiers d'origine (la liste des plans) | 95 |
| dossiers dans l'historique complet des articles en vigueur | **188** |
| absents du corpus, aucun fichier | **94** — 61 lois, 33 ordonnances |
| articles en vigueur dont un texte de l'historique avait un dossier absent | **451** |

Aucun des 451 n'était « raison non documentée » : ils sont motivés par leur
dossier d'origine. Leurs réécritures ultérieures, elles, n'avaient aucune raison
documentée, et le corpus le faisait passer pour un silence du fonds — l'erreur
que `plan_rapports.py` dit en tête ne pas vouloir commettre.

## 2. La liste se lit dans la base

`dossiers_du_perimetre.py` écrit `data/dossiers-du-perimetre.tsv` depuis ce que
la base déclare : `produite_par` (quel texte a produit chaque version),
`issu_de` (le dossier du texte), `renumerote_de` (les numéros d'avant 2016).
Un dossier, sa nature — « ordonnance » prime quand le dossier porte aussi la
loi de ratification, parce que le rapport au Président n'existe que pour elle —,
sa législature, les articles en vigueur qu'il touche, ses textes.

Les six plans lisent cette liste. `pipeline.sh` la régénère à chaque exécution
et, quand elle change, efface les plans pour qu'ils se refassent : un plan
figé sur une liste périmée est exactement ce qui avait produit le § 1.

L'ingestion suit : `rattachements_legi()` ne lit plus le périmètre mais la base,
et chaque numéro d'article — courant ou ancien — porte les dossiers de ses
propres versions plus ceux de ses ancêtres. La corroboration par LEGI, qui
retient une section de rapport nommant l'article seulement si le dossier a
produit une version de cet article, s'élargit d'autant ; la garde du code nommé
reste. Le bloc qui réinsérait `dossier` et `issu_de` depuis le périmètre est
retiré : `dossiers_des_textes.py` le fait, avant le périmètre, depuis DOLE.

## 3. Ce que le corpus a pris

| | avant | après |
|---|---:|---:|
| rapports de commission au plan | 253 | **549** — 939 fichiers, versions `_mono` comprises |
| documents en base | 393 | **785** (572 rapports, 77 exposés, 63 rapports au PR, 46 études d'impact, 27 avis) |
| textes en discussion | 424 | **854** — 24 URL en échec sur 759 |
| jeux d'amendements du Sénat | 75 | 143 |
| amendements du Sénat | 22 102 | **31 027** |

Deux défauts se sont montrés au passage, et ils sont corrigés :

- **DOLE liste parfois la même page sous deux libellés** — « Proposition de
  loi … » et « Texte adopté en 1ère lecture … » pour une seule URL. Sur 379
  textes, cela ne s'était pas produit ; sur 759, deux fois, et l'identifiant en
  base étant le fichier, `texte_discute` a refusé le doublon. Le plan ne garde
  qu'une ligne par (dossier, fichier).
- **Le pipeline ne s'arrêtait pas sur une ingestion en échec.** `set -uo
  pipefail`, sans `-e` : la collision ci-dessus a laissé `texte_discute` vide,
  les tranches suivantes ont tourné sur le trou, et l'hygiène a publié « 0 texte
  en discussion » comme un chiffre. Le README promettait l'inverse. Les appels
  d'ingestion passent par `ingere`, qui arrête tout à la première erreur ; un
  téléchargement peut échouer, le pipeline le compte, une ingestion non.

## 4. Ce que le graphe y gagne

| | avant | après |
|---|---:|---:|
| arêtes `motive` | 751 | **1 566** |
| **articles en vigueur qu'un passage motive, chaîne comprise** | 812 (38,6 %) | **938 (44,6 %)** |
| par leur numéro d'aujourd'hui | 115 | 245 |
| **partie L — un passage les motive** | 801 (61,9 %) | **907 (70,1 %)** |
| partie L — origine située seulement | 211 | 121 |
| partie R — un passage les motive | 44 | 51 |
| articles remontant à un amendement identifié | 83 | **122** |
| arêtes `resulte_de` | 279 | 308 |
| arêtes `porte_sur` | 44 097 | **59 076** |
| articles reliés à un article de texte | 1 066 | 1 079 |
| arêtes `depose_sur` | 476 | **550** — 29 articles en vigueur, 20 sans tentative connue |
| articles atteignant un document motivant le texte | 1 195 | **1 258** |
| raison non documentée, les trois parties | 699 | 698 |

Le déplacement est là où il devait être : **106 articles de la partie L
gagnent un passage qui les motive** — 90 n'avaient que leur origine située, 16
n'avaient qu'un document motivant le texte entier. Ce n'étaient pas des
silences du fonds, c'étaient des rapports que personne n'avait demandés.
La partie réglementaire ne bouge presque pas — 527 → 526 muets — et c'est
cohérent : un décret n'a pas de dossier, quel que soit l'historique.

## 5. Ce qui a baissé, et ce qui reste à mesurer

**Le contrôle d'appariement des amendements descend de 98,2 % à 96,1 %.** Les
jeux du Sénat appariés à leur texte passent de 67 / 75 à 124 / 143, et leurs
subdivisions dans la plage du texte de 97,7 % à 95,1 %. `docs/31` a posé ce
contrôle comme le garde-fou de `depose_sur` : « un texte faux s'y verrait en
premier ». Il n'est pas tombé, mais il a bougé, sur une population qui a
presque doublé — et une arête composée mesurée sur l'ancienne population ne
vaut rien sur la nouvelle (`docs/35`).

Deux tirages sont donc faits, disjoints des précédents, à juger à la main
avant de reprendre les constantes de confiance :

- `data/mesures/precision-depose-sur-corpus-elargi.tsv`, 15 arêtes ;
- `data/mesures/precision-porte-sur-corpus-elargi.tsv`, 20 arêtes.

Tant qu'ils ne sont pas jugés, `CONFIANCE` de `depose_sur` (0,7961) et de
`porte_sur` décrivent la population d'août.

**Les arêtes `motive` nouvelles n'ont pas de mesure propre.** Leur précision
est celle du golden set, et c'est le jeu d'annotation qui la donnera : les
fiches de `travail/annotation/` sont régénérées sur ce corpus, 449 documents
au lieu de 295, le pré-remplissage inchangé à 74 (il ne regarde que le dossier
d'origine, et c'est voulu — la proposition mesure cette voie-là).

**24 textes en discussion n'ont pas été récupérés** — presque tous sur
`ameli.senat.fr/publication_pl/`, sessions 2005 à 2008, un hôte que le Sénat ne
sert plus — et un rapport de l'Assemblée répond 404 (`docs/36` § 3). Comptés,
pas cachés ; Wayback est la piste, non suivie ici.
