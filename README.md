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

## État : phase 0 terminée, en attente de validation humaine

Aucun code de production n'est écrit, conformément au § 9 de la feuille de route.
Les trois livrables de la phase 0 sont produits.

| Livrable | Fichier |
|---|---|
| Note de cadrage et décision de périmètre | [`docs/00-note-de-cadrage.md`](docs/00-note-de-cadrage.md) |
| Rapport de vérification des sources | [`docs/01-rapport-verification-sources.md`](docs/01-rapport-verification-sources.md) |
| Golden set de 25 articles | [`docs/02-golden-set.md`](docs/02-golden-set.md) |
| Jeu d'annotation humaine, 100 articles | [`data/golden-set/jeu-annotation-100.csv`](data/golden-set/jeu-annotation-100.csv) |
| Périmètre figé, 1 280 articles | [`data/perimetre-v1.csv`](data/perimetre-v1.csv) |
| Golden set, données machine | [`data/golden-set/golden-set-v1.json`](data/golden-set/golden-set-v1.json) |
| Scripts de mesure, reproductibles | [`tools/phase0/`](tools/phase0/) |

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
  relève pas. Mais la mesure côté Sénat, où la couverture est complète, donne
  **0 rattachement sur 307 articles** : le goulot n'est pas la chambre, c'est le
  résolveur manquant. L'extracteur AN est donc reporté, pas priorisé.
- Le § 0 suppose les ordonnances sans motivation : **90,6 % d'entre elles ont un
  rapport au Président de la République**.
- **Atteindre le dossier n'est pas atteindre la motivation.** L'exposé des motifs
  ne nomme l'article que dans **6,4 %** des cas, l'étude d'impact dans **24,8 %**,
  l'un ou l'autre dans **42,2 %** sur les articles à documentation complète. C'est
  le plafond réel de la restitution ancrée exigée au § 4.3.
- **L'arête `resulte_de` n'a jamais été produite.** Sur les 307 articles issus de
  la loi consommation de 2014, **aucun** n'a encore cette loi comme texte
  producteur de sa version en vigueur : elle est vide par construction sur un
  corpus recodifié, sauf à l'attacher à la version historique.

### Miroir DILA

Fait. Les incréments quotidiens ne remontent pas au-delà du dump global du
**13/07/2025**, seul point de reconstruction existant.
`tools/phase0/miroir_dila.sh` récupère global et incréments et produit un
manifeste horodaté avec taille et SHA-256 par fichier. À relancer quotidiennement.

## Prochaine étape

Deux travaux parallèles, avant la phase 1 :

1. **Prototyper le résolveur « article du projet de loi → article du code »** sur
   la loi consommation de 2014 — 307 des 832 articles éligibles. C'est le jalon
   go/no-go : il détermine si le produit est centré article ou centré dossier.
2. **Faire annoter les 100 articles** avec offsets des passages motivants. Tant
   que ce n'est pas fait, la phase 0 reste ouverte.

## Licence et attribution

Code sous [AGPL-3.0](LICENSE). Les données amont sont sous Licence Ouverte /
Etalab 2.0 et leur attribution est obligatoire : voir
[`ATTRIBUTION.md`](ATTRIBUTION.md).
