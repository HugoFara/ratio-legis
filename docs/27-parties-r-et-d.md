# Vingt et unième tranche — les parties R et D entrent dans le périmètre

**Objet :** la note de cadrage que `docs/00` § 5 exige de tout élargissement du
périmètre. Elle porte sur les 811 articles réglementaires en vigueur, exclus en
phase 0 pour une raison qui se révèle fausse.
**Date : 23 août 2026.**
**Code :** `tools/phase0/perimetre.py`, `tools/dila/plan_rapports.py`,
`pipeline.sh`, `ingestion/dossiers_des_textes.py`.
**Donnée :** `data/perimetre-v2.csv`.

---

## 1. La raison écrite de l'exclusion est fausse

`docs/00` § 1 fige le périmètre sur la partie législative et donne son motif dans
un tableau :

| Exclu | N | Motif |
|---|---:|---|
| Partie réglementaire (articles R) | 670 | Aucun dossier législatif : rattachement à DOLE mesuré à 0 % |
| Partie réglementaire (articles D) | 168 | Idem |

La mesure était juste et la conclusion ne l'était pas. Elle avait été faite sur le
rattachement **direct** d'un décret à DOLE, qui est bien nul — DOLE est le fonds
des dossiers *législatifs*, un décret n'en a pas. Elle n'avait pas remonté la
chaîne de renumérotation, c'est-à-dire qu'elle n'avait pas fait ce que le projet
fait.

En la refaisant sur le graphe, ascendance comprise :

| | R | D | total |
|---|---:|---:|---:|
| Articles en vigueur | 632 | 179 | 811 |
| Ayant un dossier législatif dans leur ascendance | 63 | 1 | **64** |
| Éligibles à `resulte_de` | 63 | 1 | **64** |

**7,9 %, pas 0 %.** Ce sont les articles déclassés — une disposition écrite par le
législateur, puis reclassée en partie réglementaire, garde son dossier dans son
ascendance. D824-3 en est le cas d'école : il était l'article L541-1, il a été
commenté par les deux chambres sur la loi d'avenir pour l'agriculture, et il est
aujourd'hui un article D dont le rapport de commission explique encore le contenu.

## 2. Ce qu'un fichier figé empêche de voir

Le périmètre était un artefact de phase 0 : 1 280 lignes versionnées, **sans le
code qui les avait produites**. Rien ne pouvait donc démentir la phrase du
tableau, puisque rien ne se recalculait.

C'est la vraie leçon de cette tranche, et elle a un corollaire immédiat :
`data/corpus/plan-rapports.tsv` était figé de la même façon. En ajoutant les
parties R et D, deux dossiers législatifs nouveaux sont apparus — et **aucun
moyen d'en récupérer les rapports**, le plan ne pouvant pas suivre. Un corpus qui
ne suit pas son périmètre fait passer une limite d'outillage pour un silence du
fonds documentaire : exactement l'erreur que ce projet dit ne pas vouloir
commettre.

`tools/dila/plan_rapports.py` comble ce trou. La donnée était là depuis le début,
dans l'`<ARBORESCENCE>` de DOLE, à côté de celle que `plan_textes.py` lit déjà ;
seul le premier mot du libellé les distingue. Le plan généré retrouve **253
rapports** là où le fichier figé en portait 221 : 39 nouveaux, dont ceux des
dossiers de la XIIe législature que la version gelée n'avait jamais eus, et 8 en
moins — des rapports d'information, écartés à dessein, dont on a vérifié qu'ils ne
portaient **aucune arête `motive`**.

**Un troisième défaut est tombé avec.** `dossiers_des_textes.py` lisait la
législature d'un dossier avec `<LEGISLATURE>(\d+)</LEGISLATURE>`. La balise est un
conteneur : elle porte `<NUMERO>` et `<DATE_DEBUT>`. L'extraction n'a donc
**jamais** rien rendu, et la colonne était en réalité remplie par
`rapports_vers_motive.py` depuis le périmètre — qui la tenait de la phase 0. Le
défaut ne s'est vu qu'en inversant l'ordre des deux étapes, quand les 64 lignes
nouvelles sont sorties avec une éligibilité de 0.

## 3. La décision

**Le périmètre couvre désormais les trois parties du code : 2 091 articles.** Il
n'est plus une entrée du pipeline, c'est une sortie — dérivé du fonds à
l'étape 1 bis, avant tout ce qui en dépend.

Les 1 280 lignes de la partie L sont **reprises telles quelles**. Leur colonne
`texte_origine` porte la thèse du projet — « la loi rétablie dans l'ascendance » —
et la procédure qui les a produites n'a pas été conservée. Trois définitions
candidates ont été confrontées à ces lignes : la meilleure en retrouve 670 sur
1 279. Redéfinir en silence la colonne qui porte la thèse, pour gagner un format
uniforme, coûterait plus que la non-uniformité ; `perimetre.py` documente la règle
des lignes nouvelles et dit qu'elle diffère.

Les garde-fous par comptage de `pipeline.sh` — « plus de 200 fichiers dans le
corpus, on passe » — sont retirés. Ils faisaient l'inverse de leur objet le jour
où le périmètre a bougé, en déclarant le corpus complet alors qu'il manquait les
dossiers nouveaux. Les téléchargeurs sautent déjà ce qui est présent.

## 4. Ce que l'élargissement rapporte, mesuré

La mesure a été faite en deux temps, pour séparer ce qui vient du périmètre de ce
qui vient du corpus.

**Le périmètre seul**, sur le corpus inchangé : **+5 arêtes `motive`**, deux
articles R passant d'*origine située* à *passage motivant*. Aucun article muet
n'en sort. C'est peu, et c'était prévisible : la chaîne d'ascendance portait déjà
l'essentiel jusqu'aux articles R par le verdict.

**Le périmètre et le corpus qu'il entraîne** — deux dossiers, leurs rapports,
leurs textes, leurs études d'impact, leurs amendements :

| | avant | après |
|---|---:|---:|
| Arêtes `motive` | 624 | **639** |
| Rapports de commission chargés | 221 | **252** |
| Textes en discussion | 355 | **371** |
| Amendements du Sénat | 20 342 | **22 102** |
| Articles éligibles à `resulte_de` | 832 | **896** |
| Articles L — un passage les motive | 693 | **696** |
| Articles R — un passage les motive | 41 | **44** |
| Articles D — un passage les motive | 0 | **1** |
| Articles sans raison documentée | 701 | **699** |

Aucune régression sur la partie L. Le premier article D de l'histoire du projet
porte un passage motivant.

## 5. Le résultat, et il ne bouge pas

| partie | articles | un passage motive | origine située | texte seul | **raison non documentée** |
|---|---:|---:|---:|---:|---:|
| L | 1 293 | 696 | 177 | 415 | **5 — 0,4 %** |
| R | 632 | 44 | 14 | 47 | **527 — 83,4 %** |
| D | 179 | 1 | 0 | 11 | **167 — 93,3 %** |
| **total** | **2 104** | 741 | 191 | 473 | **699 — 33,2 %** |

**C'est le chiffre du projet, et il faut le publier tel quel.** 83,4 % des
articles R et 93,3 % des articles D du code de la consommation n'ont, dans aucune
des sources dépouillées, la moindre phrase expliquant pourquoi ils sont écrits
ainsi — quand la partie législative est documentée à 99,6 %.

Et il ne faut pas laisser croire que le périmètre en était la cause. Il n'y était
pour rien : l'élargir l'a déplacé de 701 à 699. **Ce silence est un état du fonds
documentaire français**, pas un artefact de méthode. Un décret n'a ni exposé des
motifs, ni débat, ni amendement ; son projet n'est pas publié, l'avis du Conseil
d'État sur un décret ne l'est pas non plus, et la notice au Journal officiel dit
ce que le texte fait, jamais pourquoi. Il n'existe pas de source à dépouiller.

Ce sont pourtant les articles R et D qui portent la masse des obligations
qu'une entreprise ou une association rencontre réellement. Le produit répond
aujourd'hui sur eux comme sur les autres — même fiche, même verdict, même
retentissement — et sa réponse la plus fréquente y est *raison non documentée*.
C'est une réponse, et c'est un résultat.

## 6. Ce que cette tranche ne fait pas

Elle n'ajoute aucune source. Les décrets n'en ont pas dans le fonds ouvert, et en
inventer une serait sortir du § 5.1.

Elle ne prétend pas que 83,4 % et 93,3 % soient des bornes définitives. Deux
gisements restent hors du projet et pourraient les faire baisser : les **circulaires
et instructions** publiées sur Légifrance, qui commentent souvent le décret
qu'elles appliquent, et les **avis du Conseil d'État sur les projets de décret**,
non publiés à ce jour. Le premier est un chantier de corpus ; le second est une
question de droit d'accès, pas d'outillage.
