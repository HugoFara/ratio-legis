# Quatorzième tranche — le dossier législatif de chaque texte

**Objet :** rendre l'arête `issu_de` complète là où elle peut l'être.
**Date : 23 août 2026.**
**Code :** `ingestion/dossiers_des_textes.py`.

---

## 1. Une colonne manquante, pas une source manquante

L'arête `issu_de` du § 3 relie un texte normatif à son dossier législatif. Elle
était construite depuis le périmètre, qui ne porte qu'une colonne de dossier :
`id_dole_origine`, celui du texte ayant **créé** l'article. Les textes qui se
contentent de le **modifier** n'ont jamais été résolus.

Sur les 68 lois et ordonnances qui produisent une version en vigueur, **24
restaient sans dossier** : loi Macron de 2015, Sapin II, loi du 10 mai 2024 sur
l'espace numérique. Toutes postérieures à 2015. Toutes avec un dossier DOLE
existant. Rien ne manquait à la source ; l'ingestion ne l'avait pas demandé.

C'est le genre de trou qu'une mesure de couverture révèle et qu'un développement
ne révèle jamais : le code marchait, il répondait simplement à une question plus
étroite que celle qu'on croyait poser.

## 2. Le rattachement est déclaré, il ne se devine pas

Chaque dossier DOLE énumère ses textes sous `<ID_TEXTE_n>` :

```
<ID_TEXTE_1>JORFTEXT…</ID_TEXTE_1>   l'ordonnance
<ID_TEXTE_2>JORFTEXT…</ID_TEXTE_2>   le rapport au Président
<ID_TEXTE_4>JORFTEXT…</ID_TEXTE_4>   la loi de ratification
```

L'index inverse de ces listes est la réponse. Un texte peut figurer dans
plusieurs dossiers — l'ordonnance apparaît aussi dans celui de la loi qui la
ratifie. On retient alors le dossier dont **le titre porte le numéro du texte**,
et aucun si l'ambiguïté subsiste : deux textes sont dans ce cas et restent sans
arête, comme l'exige le § 5.3.

## 3. La vérification a précédé l'écriture

La méthode a d'abord été passée sur les arêtes qu'une **autre** source avait déjà
produites :

| | |
|---|---:|
| Arêtes existantes retrouvées | **89 / 89** |
| Arêtes ajoutées | 111 |
| Textes résolus dont le dossier ne les liste pas | **0** |

Les deux signaux — le numéro dans le titre du dossier, et l'appartenance à la
liste `ID_TEXTE_n` — ne se contredisent nulle part. Ce n'est pas une méthode qui
remplace la précédente : c'est la même réponse, obtenue plus largement.

## 4. Résultat

| Mesure | Avant | Après | Seuil § 4.2 |
|---|---:|---:|---:|
| Lois et ordonnances utiles avec dossier | 44 / 68 (64,7 %) | **68 / 68 (100 %)** | > 90 % |
| Articles en vigueur atteignant un dossier | 1 190 | **1 268** | — |
| Arêtes `issu_de` | 89 | **200** | — |

**Le critère de sortie de phase 2 sur `issu_de` est atteint.** Il ne l'était pas,
et rien dans le code ne le disait.

## 5. Ce que la méthode ne trouve pas, et pourquoi

212 décrets et 2 arrêtés ne sont listés par aucun dossier. DOLE est le fonds des
**dossiers législatifs** ; un décret n'en a pas. Ce silence est structurel, et
c'est le même constat que celui de la treizième tranche sur la partie R du code :
le pouvoir réglementaire ne laisse pas de trace de délibération, parce qu'il n'y
en a pas eu.

26 lois ne sont listées par aucun dossier non plus. Elles ne produisent aucune
version en vigueur du périmètre — ce sont des textes modificateurs entièrement
recouverts depuis.

## 6. Effet de bord, mesuré

Deux étapes en aval ne considèrent que les dossiers ayant produit un article du
code, et cette liste dépend de `issu_de` :

- `visees.py` n'écarte plus aucun amendement pour « dossier ne touchant pas ce
  code » (contre plusieurs auparavant) ;
- `amendements_vers_resulte_de.py` voit davantage de segments candidats — les
  arêtes passent de 286 à 337 avant les gardes de la quinzième tranche.

L'ordre dans `pipeline.sh` a été fixé en conséquence : cette étape précède les
amendements et les visées.
