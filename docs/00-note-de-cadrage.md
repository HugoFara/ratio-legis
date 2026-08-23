# Note de cadrage — phase 0

**Livrable § 9.1 de la feuille de route.**
**Date : 22 août 2026. Révision 2.**
**Objet : trancher le périmètre de la V1 et corriger les hypothèses de la feuille de route invalidées par les données.**

Toutes les mesures citées ont été produites sur les données réelles (dump LEGI du
13/07/2025, dump DOLE du 13/07/2025, jeux Améli du Sénat, open data de
l'Assemblée nationale), et non sur la documentation. Elles sont reproductibles
avec `tools/phase0/`.

---

## 1. Verticale retenue

**Code de la consommation, partie législative, articles en vigueur : 1 280 articles.**

Périmètre figé dans `data/perimetre-v1.csv`, un article par ligne, avec pour
chacun son identifiant LEGI, son article prédécesseur avant la recodification de
2016, son texte producteur et son dossier législatif d'origine.

Exclus du périmètre V1, et pourquoi :

| Exclu | N | Motif |
|---|---:|---|
| Partie réglementaire (articles R) | 670 | Aucun dossier législatif : rattachement à DOLE mesuré à 0 % |
| Partie réglementaire (articles D) | 168 | Idem |

> **Révisé le 23 août 2026 par [`docs/27`](27-parties-r-et-d.md).** Le motif porté
> aux deux premières lignes est faux. La mesure avait été faite sur le
> rattachement **direct** d'un décret à DOLE, qui est bien nul, sans remonter la
> chaîne de renumérotation : **64 des 811 articles réglementaires en vigueur ont
> un dossier législatif dans leur ascendance**. Le périmètre couvre désormais les
> trois parties du code, dans `data/perimetre-v2.csv`, et il est dérivé du fonds
> au lieu d'être figé.
| Versions d'articles non en vigueur, tout le code | 3 992 | Le produit répond sur le droit en vigueur ; l'historique reste ingéré — il porte la chaîne — mais n'est pas une cible de restitution |

Le périmètre est donc de 1 280 articles, dans la fourchette N ≈ 2 000–5 000
demandée au § 1 en tenant compte du fait que cette fourchette visait
implicitement un code entier. Les 838 articles réglementaires restent ingérés
— ils sont nécessaires au graphe — mais ne font pas partie de la cible de
restitution ni des métriques de sortie.

### Ce qui confirme le choix

Les quatre critères du § 1 tiennent, et deux d'entre eux se vérifient mieux que
prévu sur les données.

**Renumérotation unique et documentée.** C'est le point le plus favorable, et il
est meilleur que ce qu'anticipe la feuille de route. **76,4 % des articles en
vigueur portent au moins un lien de renumérotation déclaré dans LEGI**
(`CONCORDANCE`, `CONCORDE`, `CODIFICATION`, `TRANSFERE`, `DEPLACE`). Le § 4
phase 2 prévoyait de reconstruire ces chaînes en extrayant les tables de
concordance PDF ; c'est inutile pour l'essentiel du corpus. L'arête
`renumerote_de` est `declaree`, pas `inferee`.

**Corpus récent.** 76,4 % des articles ont une version en vigueur postérieure à
2016.

**Transposition UE.** Massive et structurante, comme espéré : ordonnance
2021-1247 (directives 2019/770 et 2019/771 sur la garantie de conformité, 60
articles), loi 2014-344 (directive 2011/83/UE sur les droits des consommateurs),
ordonnance 2016-351 (directive 2014/17/UE sur le crédit immobilier).

**Demande professionnelle.** Inchangée, pas de mesure à apporter.

### Ce qui contredit le choix, et n'est pas rédhibitoire

Le profil du code est beaucoup plus **ordonnantiel** que ne le laisse entendre la
feuille de route.

| Mesure sur les 1 280 articles L en vigueur | Résultat |
|---|---:|
| Texte producteur de la version en vigueur : ordonnance | 1 002 (78,3 %) |
| Texte producteur de la version en vigueur : loi | 265 (20,7 %) |
| Nombre moyen de textes ayant touché un article | 19,5 |

Pris tel quel, cela condamnerait le projet : un article produit par une
ordonnance n'a **aucun amendement**, donc aucune arête `resulte_de` possible.

Mais c'est précisément l'artefact que le projet existe pour dissiper. En
franchissant le saut de renumérotation de 2016 — un seul saut, celui de
l'ordonnance 2016-301 — l'origine réelle réapparaît :

| Origine substantielle, après un saut de concordance | Résultat |
|---|---:|
| Loi | 949 (74,1 %) |
| Ordonnance | 327 (25,6 %) |
| Décret, par reclassement réglementaire → législatif | 3 (0,2 %) |

**La recodification de 2016 masque l'origine parlementaire de la moitié du code,
et un unique saut déclaré dans LEGI suffit à la rétablir.** C'est la démonstration
de la thèse du projet sur son propre périmètre, obtenue en phase 0 et sur données
réelles. Elle justifie à elle seule de retenir cette verticale.

---

## 2. Deux corrections à apporter à la feuille de route

### 2.1 La cascade `resulte_de` du § 3 repose sur deux échelons qui n'existent pas

Le § 3 définit une cascade à quatre échelons. Vérification faite (détail dans
`01-rapport-verification-sources.md`) :

| Échelon § 3 | État réel |
|---|---|
| 1. Tableau synoptique du Sénat → `declaree` | **N'existe pas.** Aucun artefact du Sénat ne relie une modification à son amendement |
| 2. Parsing duraLex de l'amendement → `derivee` | **Outil abandonné depuis février 2019**, antérieur à la migration du format LEGI d'octobre 2023 |
| 3. Alignement textuel → `inferee` | Praticable, inchangé |
| 4. Pas de rattachement → arête absente | Inchangé, et doit rester la règle |

L'arête critique du projet repose donc entièrement sur du code à écrire. C'est le
principal écart entre la feuille de route et la réalité, et il doit être
provisionné en phase 2.

**Cascade de remplacement, mesurée en phase 0.** Deux méthodes ont été essayées
sur les 1 059 amendements déposés au Sénat sur le projet de loi consommation
(deux lectures, 228 adoptés). Le détail et les faux positifs sont dans
`02-golden-set.md` § 4.

| Méthode | Articles ciblés | Amendements exploités | Fiabilité |
|---|---:|---:|---|
| Toute citation d'un numéro `L. xxx-xx` dans le dispositif | 104 | 74 / 228 (32 %) | **~10 %** — inutilisable |
| Cible désignée par une formule modificative | 9 | 9 / 228 (4 %) | exploitable |

L'appariement naïf échoue pour deux raisons systématiques : un numéro d'article ne
dit pas de quelle loi vient l'amendement, et il ne distingue pas l'article
*modifié* de l'article simplement *cité* en renvoi. Sur le golden set, 9 des 10
rattachements ainsi obtenus étaient faux.

D'où la cascade retenue :

1. **Cible du langage modificatif** dans le dispositif de l'amendement adopté
   (« l'article L. X est ainsi modifié »), restreinte aux amendements du dossier
   du texte d'origine, et confirmée par la présence de la rédaction dans la loi
   promulguée → `derivee`. Rendement mesuré : **4 % des amendements adoptés**.
2. **Résolution par l'article du projet de loi.** Le champ `Subdivision` d'Améli
   donne l'article du *projet*, jamais celui du code, et la plupart des amendements
   modifient un alinéa du projet sans nommer le code. Il faut parser le langage
   modificatif de l'article du projet pour atteindre l'article du code. C'est la
   fonction de duraLex, à réécrire. **C'est ce composant, et non le précédent, qui
   détermine la couverture réelle de l'arête.**
3. **Alignement textuel** sur n-grammes entre dispositif de l'amendement et diff
   constaté → `inferee`.
4. **Aucun rattachement → arête absente.** Règle intangible.

L'échelon 1 seul plafonne à 4 % des amendements adoptés. La feuille de route
suppose implicitement qu'un rattachement bon marché existe ; la mesure dit le
contraire.

Point d'architecture qui en découle : **le rattachement n'a fonctionné, dans nos
essais, que via la numérotation antérieure à 2016, jamais via la numérotation
actuelle.** L'arête `renumerote_de` n'est donc pas un confort de navigation, c'est
une dépendance dure de l'arête `resulte_de`. Elle doit être construite en premier.

### 2.2 Les ordonnances ne sont pas des trous noirs

Le § 0 pose que les ordonnances de l'article 38 n'ont « aucun débat », ce qui est
exact, et le § 7 en déduit implicitement une absence de motivation, ce qui est
faux. Mesure sur les 1 116 ordonnances du fonds DOLE : **1 011 (90,6 %)
référencent un *Rapport au Président de la République*** publié au *Journal
officiel* avec l'ordonnance.

Pour les 327 articles du périmètre d'origine ordonnantielle, il existe donc une
motivation gouvernementale récupérable. Ce n'est pas un débat contradictoire, et
la restitution doit le dire, mais ce n'est pas « raison non documentée ».

Conséquence sur le § 4.3 : la distinction visuelle prévue à quatre catégories
(gouvernement, parlement, Conseil d'État, Bruxelles) en demande une cinquième, ou
bien la catégorie « gouvernement » doit distinguer explicitement l'exposé des
motifs d'un projet de loi soumis au débat du rapport au Président de la République
qui ne l'est pas.

---

## 3. Ce que le périmètre permet d'atteindre, chiffré

### Arêtes obtenues sans effort d'inférence

| Arête | Couverture mesurée | Critère § 4 phase 2 | Statut |
|---|---:|---|---|
| `produite_par` | **99,0 %** (1 267 / 1 280) | > 95 % | ✅ atteint sur données déclarées |
| `issu_de` | **100 %** des articles d'origine législative | > 90 % | ✅ atteint sur données déclarées |
| `renumerote_de` | 76,4 % déclarée | non fixé | — |

Les deux premiers critères de sortie de la phase 2 sont satisfaits par la donnée
brute. L'effort d'ingénierie doit se concentrer ailleurs.

### Atteindre le dossier n'est pas atteindre la motivation

Une arête `motive_par` vers un exposé des motifs ou une étude d'impact ne dit pas
que le document parle de *cet* article. La mesure a été faite : recherche du
numéro d'article — actuel et antérieur à 2016 — dans le texte de ces documents.

| Document | Articles éligibles où l'article est nommé |
|---|---:|
| Exposé des motifs | **6,4 %** |
| Étude d'impact | **24,8 %** |
| L'un ou l'autre, sur les 493 articles à documentation complète | **42,2 %** |
| idem, restreint aux 307 articles issus de la loi consommation | **55,7 %** |

Deux conséquences opérationnelles.

**L'étude d'impact prime sur l'exposé des motifs**, dans un rapport de un à
quatre. L'étude d'impact est structurée article par article, l'exposé des motifs
est un texte politique. La feuille de route les traite au même rang au § 3 ; la
priorité d'ingestion et d'extraction doit aller à l'étude d'impact.

**Le plafond de restitution ancrée est de l'ordre de 42 %, pas de 92 %.** Le
§ 4.3 interdit toute phrase sans citation résoluble au niveau du passage : sur un
article dont aucun document ne parle nommément, le système n'a rien à citer et
doit rendre `raison non documentée` — même si la chaîne jusqu'au dossier est
complète. C'est le chiffre à retenir pour dimensionner la phase 3, et il faut
noter qu'il s'agit d'une borne : un passage peut motiver une disposition sans la
nommer, mais un tel passage n'est pas ancrable automatiquement.

### L'arête `resulte_de` ne peut pas atteindre 60 % du périmètre

La population sur laquelle un amendement peut exister est bornée : il faut une
origine législative **et** un dossier couvert par l'open data parlementaire
(fiable à partir de 2008, soit la 13e législature).

| Population | N | Part du périmètre |
|---|---:|---:|
| Périmètre total | 1 280 | 100 % |
| Origine législative | 949 | 74,1 % |
| **Éligible : origine législative, législature ≥ 13** | **832** | **65,0 %** |
| dont amendements AN disponibles en open data (16e-17e) | 54 | 4,2 % |
| dont amendements AN **non** disponibles (12e-15e) | 778 | 60,8 % |

Le critère « couverture `resulte_de` > 60 % » du § 4 phase 2 suppose donc de
réussir le rattachement sur 768 des 832 articles éligibles, soit 92 % de la
population éligible. Ce n'est pas atteignable, et le seuil affiché comme
« réaliste, ne pas le gonfler » l'est en réalité.

**Un seuil unique ne convient pas**, parce que l'objectif dépend de deux
composants qui n'existent ni l'un ni l'autre : le résolveur « article du projet de
loi → article du code » et l'extracteur d'amendements AN historiques. Un chiffre
agrégé ne dirait pas lequel des deux a échoué. D'où deux cibles mesurées
séparément :

| Cible | Mesure | Ce qu'elle teste |
|---|---|---|
| **C1 — résolveur** | Part des articles éligibles pour lesquels le dispositif d'un amendement adopté est résolu jusqu'à l'article du code, **toutes chambres confondues** | Le composant qui remplace duraLex |
| **C2 — couverture par chambre** | Part des articles éligibles rattachés à un amendement, mesurée séparément Sénat et Assemblée | Si l'extracteur AN est nécessaire |

C1 est le verrou : sans lui, C2 vaut zéro quelle que soit la source. C2 dit si
l'extracteur AN doit être construit ou non.

**Le critère « identification de la population inéligible > 95 % » est retiré du
go/no-go.** Lire `naturetexte = ORDONNANCE` est un test, pas un résultat : le
garder comme critère de sortie gonflerait le tableau de bord d'un chiffre acquis
d'avance. Il devient un test de non-régression du pipeline.

### La mesure Sénat, faite

Améli couvre le Sénat sur toute la période utile, ce qui pouvait sortir
l'extracteur AN du chemin critique. Mesure sur les 307 articles du périmètre issus
de la loi consommation de 2014, le plus gros contributeur (37 % des éligibles) :

| Mesure | Résultat |
|---|---:|
| Articles rattachés à un amendement du Sénat sur une version quelconque | 5 / 307 |
| Articles rattachés à un amendement du Sénat sur la **version en vigueur** | **0 / 307** |

La raison du second zéro n'est pas le Sénat :

> **Aucun des 307 articles n'a encore la loi de 2014 comme texte producteur de sa
> version en vigueur.** 192 ont été réécrits par la recodification de 2016
> elle-même, les autres par des textes postérieurs.

Deux conclusions. D'abord, **le Sénat seul ne suffit pas, mais l'Assemblée ne
manquerait pas davantage** : le goulot n'est pas la chambre, c'est le résolveur.
L'extracteur AN historique est donc **suspendu** jusqu'à ce que C1 soit mesuré.

Ensuite, et c'est plus grave : l'arête `resulte_de` attachée à la version en
vigueur est **vide par construction** sur un corpus recodifié. Elle n'a de sens
qu'attachée à la version historique produite par l'amendement, assortie d'une
assertion vérifiable « repris sans modification de fond par la recodification du
14 mars 2016 ». Cet objet est absent du § 3 de la feuille de route et doit y être
ajouté avant la phase 2. Sans lui, le produit ne peut pas dire « cet article
existe sous cette forme à cause de cet amendement » sans mentir sur la chaîne.

### Jalon go/no-go, avant la phase 1 et non pendant la phase 2

Construire trois semaines d'ingestion avant de savoir si le produit est centré
article ou centré dossier serait le mauvais ordre.

**Prototyper le résolveur « article du projet de loi → article du code » sur la
seule loi consommation de 2014**, avant d'engager la phase 1 complète. Deux à
trois semaines, sur 307 des 832 articles éligibles, soit 37 %. Le corpus
nécessaire est déjà disponible : Améli pour les amendements, DOLE pour les textes
adoptés à chaque étape, LEGI pour les versions successives.

Décision au vu de C1 sur ces 307 articles :

- **C1 ≥ 50 %** : le produit reste centré article, la phase 1 démarre comme prévu.
- **C1 < 50 %** : repli du § 8 sur un produit centré dossier, décidé avant toute
  ingestion.

> **Fait. Verdict : go, produit centré article.** Voir
> `03-prototype-resolveur.md`. Le seuil portait sur le mauvais dénominateur :
> **68 % des 307 articles ont une rédaction déjà présente dans le texte initial du
> Gouvernement** et n'ont donc besoin d'aucune arête `resulte_de`. Sur les 99
> articles issus de la navette, C1 = **29,3 %** avec les seuls amendements du
> Sénat, l'Assemblée étant hors open data. La couverture de la motivation, toutes
> voies confondues, atteint **77,2 %**, et 10 chaînes vont de l'article en vigueur
> jusqu'à un amendement nommé.
>
> Deux conséquences : la cible C1 se mesure désormais sur la population issue de
> la navette, et **l'extracteur d'amendements AN historiques est réactivé** — le
> résolveur fonctionne, le goulot est redevenu la source.

### Le chemin critique n'est pas celui prévu

**778 articles éligibles sur 832, soit 93 %, dépendent de législatures dont les
amendements de l'Assemblée nationale ne sont pas en open data.** Les dumps de
`data.assemblee-nationale.fr` ne servent que les 16e et 17e législatures ; les
13e, 14e et 15e renvoient 404. Les pages HTML historiques de l'Assemblée restent
en ligne et répondent normalement.

Une première lecture en concluait qu'un extracteur de ces pages était le chemin
critique de la phase 2. **La mesure Sénat ci-dessus infirme cette conclusion** :
avec les deux chambres réunies, le rattachement resterait nul tant que le
résolveur n'existe pas. L'extracteur AN est donc reporté et conditionné à C2.

Le vrai chemin critique est le **résolveur « article du projet de loi → article du
code »**, qui conditionne tout le reste et qu'aucun outil vivant ne fournit.

---

## 4. Trois angles morts à traiter avant la phase 2

**Le modèle est de niveau article, le produit sera de niveau segment.** Avec 19,5
textes ayant touché un article en moyenne, « le texte à l'origine de la
disposition » est une simplification : chaque alinéa a sa provenance propre. Toute
la mesure de phase 0 est de niveau article ; la fonctionnalité de surlignage
prévue en phase 4 suppose du niveau segment. La méthode employée ici — retenir le
lien `CREE` le plus ancien du prédécesseur — produit une réponse plausible et
fausse dans une part indéterminée des cas, et rien dans les données mesurées ne
permet aujourd'hui de borner cette part.

C'est une décision de modèle, pas un raffinement d'implémentation : soit le nœud
porteur de provenance devient le segment et non l'article, soit le produit assume
de ne répondre qu'au niveau de l'article et le dit explicitement dans chaque
restitution. À trancher avant la phase 2, parce que le schéma relationnel du § 3
en dépend.

**La recodification n'est pas à rang constant.** Trois articles législatifs ont
pour prédécesseur un article réglementaire, abrogé en 2016 et remonté au rang
législatif. Ce n'est pas une erreur de la DILA — le signalement envisagé aurait
été un contresens auprès du seul fournisseur de données du projet. Pour ces
articles la motivation est dans un décret, qui n'a ni exposé des motifs, ni étude
d'impact, ni débat : c'est le cas le plus défavorable du corpus. Détail dans
`01-rapport-verification-sources.md` § 2.3 bis.

**25 articles ne mesurent pas une précision à 95 %.** Un seul faux positif pèse
4 points. La population éligible étant de 832 articles, le jeu d'annotation est
porté à **100 articles** stratifiés
(`data/golden-set/jeu-annotation-100.csv`), échantillonnés de façon déterministe
et reproductible. Le livrable attendu de l'annotateur n'est plus « chaîne complète
oui / non » mais **l'offset du passage qui motive l'article**, ou son absence —
seul livrable qui teste le contrat de génération du § 4.3. Protocole dans
`02-golden-set.md` § 6.

---

## 5. Décision et état des conditions

**Verticale retenue : Code de la consommation, partie législative, 1 280 articles
en vigueur.** Périmètre figé dans `data/perimetre-v1.csv`. Tout élargissement
passe par une nouvelle note de cadrage (§ 8).

> **Élargi le 23 août 2026.** La note de cadrage exigée est
> [`docs/27`](27-parties-r-et-d.md) : le périmètre couvre les trois parties du
> code, 2 091 articles, et il est recalculé par `tools/phase0/perimetre.py` à
> chaque exécution du pipeline. Les 1 280 lignes de la partie L sont reprises
> telles quelles.

| Condition posée en révision 1 | État |
|---|---|
| Réviser les critères de sortie de la phase 2 | **Réécrite** en deux cibles séparées C1 et C2 (§ 3) ; le critère sur la population inéligible est retiré du go/no-go |
| Provisionner l'extracteur d'amendements AN historiques en phase 1 | **Suspendue.** La mesure Sénat montre que le goulot est le résolveur, pas la chambre ; conditionnée à C2 |
| Miroiter le dump global DILA et les incréments | **Faite.** `tools/phase0/miroir_dila.sh`, manifeste horodaté avec taille et SHA-256 par fichier, dans `data/raw/dila/` |

Le miroir n'était pas une décision et n'aurait pas dû figurer parmi les conditions
d'une note : c'est une commande, et elle aurait dû être lancée avant la rédaction
du rapport qui la qualifiait d'urgente.

### Ce qui bloque maintenant

**Prototyper le résolveur « article du projet de loi → article du code » sur la
loi consommation de 2014, avant la phase 1.** Deux à trois semaines, 307 des 832
articles éligibles. Le résultat détermine si le produit est centré article ou
centré dossier — et donc s'il faut construire l'ingestion prévue ou une autre.

**Faire annoter les 100 articles** de `data/golden-set/jeu-annotation-100.csv`,
avec offsets. Tant que ce n'est pas fait, la phase 0 reste ouverte et aucune
métrique de phase 2 n'a de vérité terrain contre quoi se mesurer.

Ces deux travaux sont indépendants et peuvent être menés en parallèle.

### Ce qui reste inchangé

Les six règles du § 5 de la feuille de route. Rien dans les mesures de phase 0 ne
les met en cause, et la règle 3 — précision plutôt que rappel — en sort renforcée :
c'est en l'appliquant qu'on a découvert que 9 rattachements d'amendements sur 10
étaient faux, et que le rappel s'effondre de 32 % à 4 % dès qu'on exige la
précision.
