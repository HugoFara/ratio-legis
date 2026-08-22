# Ratio Legis

Graphe de provenance normative du droit français : pour un article de code **en
vigueur aujourd'hui**, remonter aux matériaux qui expliquent pourquoi il existe
sous cette forme — exposé des motifs, étude d'impact, avis du Conseil d'État,
amendements, débats, considérants européens.

Ce n'est pas un moteur de recherche juridique, et cela ne produit ni
interprétation ni conseil. Le produit est le **chaînage**, plus une couche de
restitution en langue naturelle strictement ancrée : aucune phrase affirmative
sans citation résoluble au niveau du passage.

Spécification complète : [`ratio-legis-feuille-de-route.md`](ratio-legis-feuille-de-route.md).

## État : phase 0 mesurée, jalon go/no-go franchi, validation humaine en attente

Aucun code de production n'est écrit, conformément au § 9 de la feuille de route.
Les trois livrables de la phase 0 sont produits.

| Livrable | Fichier |
|---|---|
| Note de cadrage et décision de périmètre | [`docs/00-note-de-cadrage.md`](docs/00-note-de-cadrage.md) |
| Rapport de vérification des sources | [`docs/01-rapport-verification-sources.md`](docs/01-rapport-verification-sources.md) |
| Golden set de 25 articles | [`docs/02-golden-set.md`](docs/02-golden-set.md) |
| Prototype du résolveur, jalon go/no-go | [`docs/03-prototype-resolveur.md`](docs/03-prototype-resolveur.md) |
| Source d'annotation externe | [`docs/04-annotation-externe.md`](docs/04-annotation-externe.md) |
| Généralisation aux 48 dossiers | [`docs/05-generalisation.md`](docs/05-generalisation.md) |
| Modèle de données au grain du segment | [`docs/06-modele-de-donnees.md`](docs/06-modele-de-donnees.md) |
| Schéma PostgreSQL | [`schema/001-graphe-provenance.sql`](schema/001-graphe-provenance.sql) |
| Jeu d'annotation humaine, 100 articles | [`data/golden-set/jeu-annotation-100-prerempli.csv`](data/golden-set/jeu-annotation-100-prerempli.csv) |
| Périmètre figé, 1 280 articles | [`data/perimetre-v1.csv`](data/perimetre-v1.csv) |
| Golden set, données machine | [`data/golden-set/golden-set-v1.json`](data/golden-set/golden-set-v1.json) |
| Chaînes `resulte_de` produites | [`data/prototype/chaines-resulte-de-2014-344.json`](data/prototype/chaines-resulte-de-2014-344.json) |
| Scripts de mesure et prototype | [`tools/`](tools/) |

**Verticale retenue :** Code de la consommation, partie législative, 1 280
articles en vigueur.

### Ce que la phase 0 a établi

Mesures sur les données réelles — dumps DILA du 13/07/2025, jeux Améli du Sénat,
open data de l'Assemblée nationale.

- `produite_par` : **99,0 %** de couverture déclarée, sans inférence.
- `issu_de` : **100 %** des articles d'origine législative.
- `renumerote_de` : **76,4 %** déclarée dans LEGI — les tables de concordance PDF
  prévues au § 4 phase 2 sont largement inutiles.
- La recodification de 2016 fait apparaître 78 % du code comme issu d'ordonnances.
  **Un seul saut de concordance rétablit l'origine réelle : 74 % d'origine
  législative.** C'est la thèse du projet, vérifiée sur son propre périmètre.
- Golden set : **5 chaînes sur 25** aboutissent à un document qui **nomme**
  l'article ; 21 sur 25 n'atteignent que le dossier. **0 sur 25** aboutissent à un
  amendement confirmé.

### Ce que la phase 0 a invalidé

- Le **tableau synoptique du Sénat** du § 2.2, premier échelon de la cascade
  `resulte_de`, **n'existe pas**.
- **DuraLex**, deuxième échelon, est **abandonné depuis février 2019**. L'arête
  critique du projet est donc entièrement à écrire.
- Les **amendements de l'Assemblée nationale** ne sont en open data que pour les
  16e et 17e législatures, dont 93 % de la population éligible du périmètre ne
  relève pas. Le prototype du résolveur montre que c'est bien la source qui
  manque : les 70 articles issus de la navette et non rattachés sont, selon toute
  vraisemblance, d'origine Assemblée.
- Le § 0 suppose les ordonnances sans motivation : **90,6 % d'entre elles ont un
  rapport au Président de la République**.
- **Atteindre le dossier n'est pas atteindre la motivation.** L'exposé des motifs
  ne nomme l'article que dans **6,4 %** des cas, l'étude d'impact dans **24,8 %**,
  l'un ou l'autre dans **42,2 %** sur les articles à documentation complète. C'est
  le plafond réel de la restitution ancrée exigée au § 4.3.
- **L'arête `resulte_de` ne peut pas s'attacher à la version en vigueur.** Sur les
  307 articles issus de la loi consommation de 2014, **aucun** n'a encore cette loi
  comme texte producteur de sa version en vigueur : elle est vide par construction
  sur un corpus recodifié. Elle n'a de sens qu'attachée à la version historique
  produite par l'amendement — c'est ainsi que le prototype la produit.

### Miroir DILA

Fait. Les incréments quotidiens ne remontent pas au-delà du dump global du
**13/07/2025**, seul point de reconstruction existant.
`tools/phase0/miroir_dila.sh` récupère global et incréments et produit un
manifeste horodaté avec taille et SHA-256 par fichier. À relancer quotidiennement.

## Jalon go/no-go : go, produit centré article

Le résolveur a été prototypé sur la loi consommation de 2014, qui produit 307 des
832 articles éligibles ([`docs/03-prototype-resolveur.md`](docs/03-prototype-resolveur.md)).

- **68 % des articles n'ont besoin d'aucune arête `resulte_de`** : leur rédaction
  figure déjà dans le texte initial du Gouvernement, et l'exposé des motifs y
  répond. L'arête critique n'est requise que sur les 32 % issus de la navette.
- Le maillon « article de la loi → article du code » **n'est pas à écrire** :
  LEGI le déclare, à 100 % sur ce pilote.
- Ce qui manquait est le rattachement de l'amendement, obtenu par **appariement
  textuel exact des passages cités**, avec un garde-fou de discriminance qui
  divise le rappel par deux — le prix de la règle « précision > rappel ».
- **C1 = 29,3 %** sur les 99 articles issus de la navette, avec une seule chambre
  sur deux. **10 chaînes complètes** vont de l'article en vigueur jusqu'à un
  amendement nommé et à sa justification.

L'extracteur d'amendements de l'Assemblée est réactivé : le résolveur fonctionne,
le goulot est redevenu la disponibilité de la source.

## Généralisation : le pilote était optimiste

Les chiffres du prototype reposaient sur une seule loi, 37 % du périmètre. Repris
sur les 48 dossiers ([`docs/05-generalisation.md`](docs/05-generalisation.md)) :

| Mesure | Pilote | Périmètre |
|---|---:|---:|
| Ancrage par un commentaire de rapport | 94,1 % | **79,1 %** |
| Part issue de la navette | 32 % | **59,2 %** |
| C1 — rattachement à un amendement du Sénat | 29,3 % | **13,8 %** |

La population qui a besoin de l'arête critique double. **39 articles portent
aujourd'hui une chaîne complète** de l'article en vigueur jusqu'à un amendement
nommé.

Résultat central : **39,8 % des articles sont repris du texte déposé entre 10 % et
90 %** — ni gouvernementaux ni parlementaires, mais les deux selon l'alinéa. La
partition n'a pas de sens au grain de l'article.

**Modélisation au segment approuvée et actée.** Au grain du segment, la part
ambiguë tombe à 20,9 % et surtout change de nature : « alinéa retouché » est une
catégorie nommable, là où « ni l'un ni l'autre » ne l'était pas. Le découpage en
alinéas est fiable — 0 % de versions sans segment exploitable, à condition de
couper sur `<br/>` autant que sur `<p>`, 26,5 % des articles n'ayant aucune
balise `<p>`. Modèle et schéma : [`docs/06-modele-de-donnees.md`](docs/06-modele-de-donnees.md).

## Prochaine étape

1. **Faire valider les 100 articles** du jeu d'annotation. 66 d'entre eux portent
   déjà un passage proposé et ses offsets, extraits des rapports de commission —
   la meilleure source de motivation au niveau de l'article, avec **94,1 %**
   d'articles nommés contre 24,8 % pour l'étude d'impact. Tant que la validation
   humaine n'est pas faite, la phase 0 reste ouverte.
2. **Construire l'extracteur d'amendements AN historiques** : 387 des 449 articles
   issus de la navette ne sont rattachés à aucun amendement du Sénat.
3. **Déployer le schéma** et vérifier ses contraintes sémantiques, qui n'ont pas
   pu l'être faute de serveur PostgreSQL dans l'environnement de mesure.

## Licence et attribution

Code sous [AGPL-3.0](LICENSE). Les données amont sont sous Licence Ouverte /
Etalab 2.0 et leur attribution est obligatoire : voir
[`ATTRIBUTION.md`](ATTRIBUTION.md).
