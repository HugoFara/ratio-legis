# Prototype du résolveur — jalon go/no-go

**Objet :** décider, avant d'engager la phase 1, si le produit est centré article
ou centré dossier (`00-note-de-cadrage.md` § 3).
**Date : 22 août 2026.**
**Code :** `tools/prototype/resolveur.py`. **Sortie :**
`data/prototype/chaines-resulte-de-2014-344.json`.

Périmètre du test : la loi n° 2014-344 du 17 mars 2014, qui produit **307 des 832
articles éligibles** du périmètre, soit 37 %.

---

## 1. Verdict

**Go, produit centré article.** Mais la décision ne se prend pas sur le chiffre
attendu, parce que le problème n'était pas celui qu'on croyait.

| Mesure | Résultat |
|---|---:|
| Articles imputables à la loi | 307 |
| **A. Rédaction déjà présente dans le texte initial du Gouvernement** | **208 (68 %)** |
| **B. Rédaction issue de la navette** | **99 (32 %)** |
| C1 — articles de B rattachés à un amendement du Sénat | **29 / 99 (29,3 %)** |
| Chaînes complètes jusqu'à la version en vigueur | **10** |
| **Couverture de la motivation, toutes voies confondues** | **237 / 307 (77,2 %)** |

Le seuil posé en fin de phase 0 était « C1 ≥ 50 % ». Il portait sur le mauvais
dénominateur : il supposait que les 307 articles avaient tous besoin d'une arête
`resulte_de`. Ils ne l'ont pas — voir § 2. Sur la population qui en a réellement
besoin, C1 vaut 29,3 % **avec une seule chambre sur deux**, l'autre étant hors
open data.

## 2. Le résultat qui change le cadrage : 68 % des articles n'ont pas besoin de
l'arête critique

Pour chaque article, on cherche si sa rédaction figure déjà, mot pour mot, dans le
texte du projet de loi tel que déposé par le Gouvernement.

**208 articles sur 307 (68 %) sont dans ce cas.** Le Parlement ne les a pas
touchés. Leur motivation est l'exposé des motifs et l'étude d'impact du projet, et
c'est une réponse complète : il n'y a pas d'amendement à trouver, parce qu'il n'y
en a pas eu.

La feuille de route traite l'arête `resulte_de` comme « le cœur du projet et la
seule qui n'existe nulle part » (§ 3). C'est vrai, mais elle n'est requise que sur
**32 % du corpus**. Pour les deux tiers restants, la chaîne
`article → texte → dossier → exposé des motifs` suffit, et elle est déclarée de
bout en bout.

Conséquence sur les métriques : **la couverture de `resulte_de` ne doit jamais
être rapportée à la population éligible**, mais à la sous-population dont la
rédaction vient de la navette. Rapportée à 832, elle plafonnerait mécaniquement
sous les 32 % et déclencherait à tort le no-go du § 8.

## 3. Le maillon manquant n'était pas celui prévu

La feuille de route (§ 3, échelon 2) suppose qu'il faut parser le langage
modificatif pour résoudre « article du projet de loi → article du code ». C'est
inutile : **LEGI déclare déjà quels articles du code chaque article de la loi
promulguée a modifiés.**

Mesure sur la loi 2014-344 : 76 de ses 161 articles portent des liens déclarés
vers **280 articles distincts** du Code de la consommation, et **307 des 307**
articles imputables sont ainsi rattachés à un article de la loi. Couverture
100 %, coût nul.

Ce qui manque réellement est le rattachement de l'**amendement** à ce qu'il a
produit, la numérotation des articles changeant à chaque lecture.

## 4. Méthode retenue, et ce qu'elle coûte en précision

**Appariement textuel exact sur les passages cités.** Le langage législatif
français cite entre guillemets le texte qu'il insère. Si un passage cité par un
amendement adopté se retrouve mot pour mot dans une version d'article du code,
l'amendement a produit ce passage. Déterministe, vérifiable, sans vecteurs ni LLM
— règles § 5.5 et § 5.6 respectées.

Fenêtre glissante de **60 caractères** : exiger la correspondance du passage
entier ferait manquer les cas, majoritaires, où l'amendement est réécrit ensuite
en deuxième lecture ou en commission mixte paritaire.

**Garde-fou de discriminance.** Une fenêtre retrouvée dans plus de deux numéros
d'articles est du texte type. Distribution mesurée sur les fenêtres appariées :

| Numéros d'articles touchés par une fenêtre | Fenêtres |
|---|---:|
| 1 | 261 |
| 2 | 306 |
| 3 à 11 | 101 |
| 28 à 53 | 4 |

Le seuil de deux n'est pas un compromis : **84 % des fenêtres à deux numéros
désignent le même article sous ses numérotations d'avant et d'après 2016.** Les
16 % restants sont des articles voisins au texte proche, ambiguïté réelle à
trancher article par article.

Ce que coûte ce garde-fou, mesuré :

| Seuil de discriminance | Articles atteints | C1 sur les 307 |
|---|---:|---:|
| Aucun | 243 | 32,2 % |
| ≤ 5 | 115 | 20,8 % |
| ≤ 3 | 91 | 19,5 % |
| **≤ 2 (retenu)** | **77** | **17,3 %** |
| ≤ 1 | 32 | 9,1 % |

Le rappel est divisé par deux entre « aucun seuil » et « ≤ 2 ». C'est le prix de
la règle § 5.3, et il est assumé : les 166 articles perdus l'étaient sur des
fenêtres de texte type qui n'auraient rien prouvé.

## 5. Une chaîne complète, vérifiée à la main

C'est la première fois que l'arête `resulte_de` est produite de bout en bout dans
ce projet. Exemple, l'article **L224-65** du Code de la consommation, en vigueur
depuis le 1er juillet 2016 :

> « Lorsque le consommateur prend personnellement livraison des objets transportés
> et lorsque le voiturier ne justifie pas lui avoir laissé la possibilité de
> vérifier effectivement leur bon état, le délai mentionné à l'article L. 133-3 du
> code de commerce **qui éteint toute action contre le voiturier** est porté à dix
> jours. »

Chaîne reconstituée :

| Maillon | Contenu | Méthode |
|---|---|---|
| Article en vigueur | L224-65, `LEGIARTI000032226573` | — |
| Numérotation antérieure | L121-105 | lien `CONCORDANCE`, déclaré |
| Texte producteur | ordonnance 2016-301, recodification | lien `CREE`, déclaré |
| Origine de la disposition | loi 2014-344, article 11 | lien déclaré |
| **Amendement** | **Sénat n° 682, M. Fauconnier, au nom de la commission des affaires économiques** | **appariement textuel, 10 fenêtres communes** |
| Raison | l'objet de l'amendement : les transporteurs « n'offrent pas toujours la possibilité aux consommateurs de vérifier l'intégrité des colis », et sans réserves sur le bon de livraison le consommateur « ne dispose d'aucun recours » | citation résoluble |

Détail notable : l'amendement insère un « Art. L. 121-104 », publié en L. 121-105,
devenu L224-65. **L'appariement textuel franchit les deux renumérotations sans
avoir à les modéliser** — là où un rattachement par numéro d'article aurait échoué
deux fois.

Le passage en gras de l'article en vigueur n'est pas dans l'amendement : il a été
ajouté ensuite. La chaîne établit donc que l'amendement a produit *ce passage-là*,
pas l'article entier. C'est une raison de plus de modéliser la provenance au
niveau du segment (`00-note-de-cadrage.md` § 4).

## 6. Ce que le prototype ne fait pas

**Une seule chambre.** Les amendements de l'Assemblée nationale ne sont pas en
open data pour la 14e législature. Les 70 articles de la population B non
rattachés sont, selon toute vraisemblance, d'origine Assemblée — le projet y a été
déposé et y a connu deux lectures. C1 = 29,3 % est donc **une borne inférieure
imposée par la disponibilité des sources, pas par la méthode.**

Cela renverse la décision prise en fin de phase 0 : l'extracteur d'amendements AN
historiques était suspendu au motif que le goulot était le résolveur. Le résolveur
existe maintenant et fonctionne ; **le goulot est redevenu la source.** La cible
C2 doit être mesurée en priorité.

**Aucune vérification de non-régression sémantique.** L'appariement prouve qu'un
texte identique circule, pas que l'amendement en est la cause première : un
amendement peut reprendre un texte déjà présent. Sur les 29 chaînes, la partition
gouvernement / navette écarte ce cas, mais la garantie n'est pas formelle.

**Le taux de survie n'est pas expliqué.** 10 chaînes sur 29 vont jusqu'à la
version en vigueur ; pour les 19 autres, le texte de l'amendement a été réécrit
depuis. Ce n'est pas un échec — l'arête reste vraie sur la version historique —
mais la restitution devra dire « cet amendement a produit une rédaction
ultérieurement modifiée », ce qui suppose l'assertion de conservation du fond
décrite au § 3 de la note de cadrage.

## 7. Décision et suite

**Go, produit centré article.** Les trois maillons de la chaîne existent, le
dernier a été produit et vérifié à la main.

Trois corrections à porter dans la feuille de route avant la phase 1 :

1. **La cible C1 se mesure sur la population issue de la navette**, pas sur la
   population éligible. Sur ce pilote : 99 articles sur 307, soit 32 %.
2. **L'échelon 2 de la cascade du § 3 est remplacé** : pas de parsing du langage
   modificatif pour atteindre l'article du code — LEGI le déclare — mais
   appariement textuel des passages cités par l'amendement.
3. **L'extracteur d'amendements AN historiques est réactivé** et devient la
   priorité de la phase 1, la mesure C2 dépendant entièrement de lui.

Le pilote reste à étendre : il porte sur une loi, sur une chambre, et les 29
chaînes produites n'ont pas été validées par un humain autrement que par
échantillon.
