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

## État : dix tranches en base, validation humaine de la phase 0 toujours ouverte

Le graphe est chargé et interrogeable article par article. Ce qu'il ne peut pas
encore faire, c'est se déclarer conforme : le critère de sortie de la phase 2
(**précision de `resulte_de` > 95 %**) et celui de la phase 3 (évaluation humaine
en aveugle) supposent tous deux un jugement extérieur. Les confiances portées par
les arêtes sont des bornes de Wilson calculées sur mes propres échantillons ; tant
que les 100 articles du jeu d'annotation ne sont pas validés à la main, **aucune
phase n'est close**, quoi qu'affichent les compteurs.

### Ce que la base contient

Reconstruite d'une commande depuis le miroir et les plans versionnés
(`pipeline.sh`), 201 Mo, zéro violation d'intégrité.

| Nœuds | | Arêtes | |
|---|---:|---|---:|
| Articles (dont **2 139 en vigueur**) | 3 428 | `produite_par` — quel texte a produit la version | 7 809 |
| Versions d'articles | 6 131 | `repris_de` — continuité d'un alinéa par-delà la recodification | 5 766 |
| **Segments (alinéas)** | **26 524** | `renumerote_de` | 1 877 |
| Documents (rapports, exposés, études d'impact, avis) | 337 | `motive` — un passage qui motive, avec offsets | 519 |
| Amendements (20 342 Sénat, 11 115 Assemblée) | 31 457 | `renvoie_a` — le graphe de renvois | 11 656 |
| Acteurs | 1 419 | `resulte_de` — l'amendement qui a écrit l'alinéa | 286 |
| **Actes de l'Union** | **284** | `cite_acte_ue` / `transpose` | 1 478 / 8 |
| **Considérants de l'Union** | **7 674** | `article_acte_ue` — articles d'actes déclarés | 6 237 |

Ce que cela donne au grain de l'article en vigueur, qui est le seul grain qui
compte pour le produit :

| | |
|---|---:|
| Articles cités par un autre article du fonds | **1 064 (49,7 %)** |
| **Articles atteignant un document motivant le texte** — grain : le texte entier | **1 160** |
| dont par un rapport au Président | 997 |
| dont par un exposé des motifs | 147 |
| dont par une étude d'impact | 125 |
| dont par un avis du Conseil d'État | 125 |
| Articles nommant un acte de l'Union | 113 |
| Articles atteignant un considérant européen — grain : l'acte entier | 113 |
| Articles atteignant une transposition déclarée — grain : le texte entier | 63 |
| **Articles remontant à un amendement identifié** | **82** |
| **Articles remontant à un passage qui les nomme** | **65** |

Seules les deux dernières lignes répondent à « pourquoi **cet article** dit
ceci ». Les autres répondent à « pourquoi ce **texte** existe » — un rapport au
Président motive une ordonnance de plusieurs centaines d'articles, pas l'alinéa
qu'on lit. Ce n'est pas la même question, et la restitution refuse de les
confondre : elle affiche l'avertissement chaque fois qu'elle sert l'un faute de
l'autre.

### Les tranches

| Tranche | Ce qu'elle produit | Document |
|---|---|---|
| 1. LEGI → graphe | articles, versions, segments, `repris_de` | [`docs/06`](docs/06-modele-de-donnees.md) |
| 2. Rapports → `motive` | le passage d'un rapport qui commente l'article | [`docs/07`](docs/07-tranche-motive.md) |
| 3. Renvois | « si je modifie cet article, qu'est-ce qui bouge » | [`docs/08`](docs/08-graphe-de-renvois.md) |
| 4. Amendements → `resulte_de` | l'amendement qui a écrit l'alinéa | [`docs/09`](docs/09-tranche-amendements.md) |
| 5. Amendements non adoptés | ce qui a été tenté sans aboutir | [`docs/10`](docs/10-amendements-non-adoptes.md) |
| 6. Assemblée nationale | la XIVe législature, les deux chambres chargées | [`docs/11`](docs/11-tranche-assemblee.md) |
| 7. But déclaré et rapports au Président | l'objet de l'amendement, la motivation des ordonnances | [`docs/12`](docs/12-but-declare.md) |
| 8. Couche européenne | l'acte de l'Union que l'article cite, la transposition déclarée | [`docs/13`](docs/13-couche-europeenne.md) |
| 9. Considérants | le motif que l'Union écrit elle-même, et l'article visé de l'acte | [`docs/14`](docs/14-considerants.md) |
| 10. **Motivation gouvernementale** | exposé des motifs, étude d'impact, avis du Conseil d'État | [`docs/15`](docs/15-motivation-gouvernementale.md) |

### Reconstruire

```
./pipeline.sh                 # miroir DILA + plans versionnés → base complète
```

Tout est reconstructible depuis ce qui est versionné : le miroir DILA
(`data/raw/dila/`, 6,4 Go, hors dépôt), le périmètre, et les plans de récupération
`data/corpus/*.tsv`. Ce script a été écrit après avoir **perdu tous les corpus
dérivés** dans un vidage de `/tmp` : la règle « la donnée brute est sacrée » du
§ 5.2 ne vaut que si l'on sait aussi la retrouver.

Deux étapes demandent le réseau au-delà des téléchargements de sources : la
vérification des identifiants CELEX auprès de Cellar, dont le résultat est
versionné, et le miroir EUR-Lex des 284 actes de l'Union (153 Mo), stocké hors
dépôt comme celui de la DILA, avec son manifeste horodaté.

## Phase 0

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
| Schéma SQLite | [`schema/001-graphe-provenance.sql`](schema/001-graphe-provenance.sql) |
| Ingestion, première tranche | [`ingestion/legi_vers_graphe.py`](ingestion/legi_vers_graphe.py) |
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
- ~~Les **amendements de l'Assemblée nationale** ne sont en open data que pour les
  16e et 17e législatures.~~ **Faux, et corrigé depuis** : la XIVe législature est
  publiée, sous le chemin `amendements_legis_XIV`. La conclusion venait d'une URL
  périmée recopiée de la page d'archives de l'Assemblée elle-même. Un 404 sur une
  URL recopiée prouve que l'URL est mauvaise, jamais que la donnée est absente
  ([`docs/10`](docs/10-amendements-non-adoptes.md) § 4). 11 115 amendements de
  l'Assemblée sont chargés.
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

## Phase 1, première tranche : chargée

LEGI → articles, versions, **segments**, et l'arête `repris_de` qui porte la
continuité d'un alinéa à travers une recodification. 3,5 secondes, 26 Mo, zéro
violation d'intégrité. Les compteurs de cette tranche figurent dans le tableau
d'état plus haut.

Les premiers chiffres publiés ici — 3 849 arêtes `renumerote_de`, 9 830
`repris_de` — étaient **gonflés par un graphe non orienté**. LEGI porte un
attribut `sens` qui n'est pas fiable et que le projet ignore ; sans lui, 3 848 des
3 849 arêtes avaient leur réciproque, et la remontée d'ascendance bouclait. La
direction est désormais reprise de la chronologie des dates d'effet, et les 48
couples à date égale sont **abandonnés plutôt que devinés** (§ 5.1). Compteurs
réels : `renumerote_de` 1 877, `repris_de` 5 766.

Base SQLite plutôt que PostgreSQL : le volume ne justifie pas un serveur, et les
contraintes du schéma ont pu être **réellement testées** — chacune en essayant de
la violer. Contrepartie à trancher avant la phase 3 : `pg_trgm` et `pgvector`
disparaissent, remplacés par FTS5 et, pour le rappel vectoriel, un index externe.

## Ce qui reste à faire

**Bloquant, et hors de portée du code.** Faire valider à la main les 100 articles
du jeu d'annotation. 66 d'entre eux portent déjà un passage proposé et ses
offsets. Tant que cette validation n'est pas faite, la phase 0 reste ouverte et
aucune mesure de précision du projet n'est autre chose qu'une auto-évaluation.

**Trois couches de motivation ne sont pas construites.**

1. ~~Les considérants européens.~~ **Faite** : 7 674 considérants chargés,
   113 articles atteints ([`docs/14`](docs/14-considerants.md)). Reste ouvert le
   seul chemin connu vers un lien au grain de l'article : les tableaux de
   concordance annexés aux textes de transposition.
2. ~~Les études d'impact.~~ ~~Les avis du Conseil d'État.~~ **Chargés** : 25
   études, 15 avis, 39 exposés des motifs, 125 à 147 articles atteints chacun
   ([`docs/15`](docs/15-motivation-gouvernementale.md)). Mais **au grain du texte
   seulement** : aucune de ces trois sources n'emploie la convention de citation
   en en-tête qui produit une arête au grain de l'article, et le rapprochement par
   le numéro d'article du projet est faux, les articles étant renumérotés à chaque
   lecture. Confronter l'impact annoncé au dispositif voté — le second but du
   produit — suppose d'abord de charger les textes déposés.

**Ce qui reste, pour descendre au grain de l'article.** Les textes déposés :
c'est la pièce qui manque à trois chantiers à la fois — le dernier mode d'échec de
`resulte_de`, le rapprochement de l'étude d'impact, et les tableaux de concordance
qui apparient un article de directive à un article du code.

**Trous de couverture dans ce qui existe.** Les amendements de l'Assemblée pour
les législatures XV à XVII (103 articles éligibles, mécanique). La XIIIe, jamais
publiée en open data, reconstructible seulement page par page depuis Wayback —
arbitrage à rendre entre le coût et un trou déclaré. Les textes déposés, dont
l'absence laisse subsister le dernier mode d'échec de `resulte_de`. Les débats en
séance : le graphe sait ce que le Parlement a **fait**, pas ce qu'il a **dit**.

**La licence de réutilisation des rapports parlementaires** n'est toujours pas
confirmée auprès des deux chambres. Elle conditionne toute publication.

**Phases 3 et 4 non commencées.** `restitution/graphe.py` montre le graphe ; il ne
produit pas la note « pourquoi cet article » avec son contrat strict et son verdict
explicite `raison non documentée` — qui est pourtant le résultat de premier ordre
du projet. Manquent aussi l'étiquetage IA de l'article 50 du règlement (UE)
2024/1689, l'API, le dump ouvert et le surlignage par étape.

## Licence et attribution

Code sous [AGPL-3.0](LICENSE). Les données amont sont sous Licence Ouverte /
Etalab 2.0 et leur attribution est obligatoire : voir
[`ATTRIBUTION.md`](ATTRIBUTION.md).

## Voir le graphe

`restitution/graphe.py` interroge la base et restitue, pour un article en vigueur,
tout ce que le graphe sait dire de lui : les passages qui le motivent, la
provenance de chaque alinéa jusqu'à l'amendement qui l'a écrit, ce qui le cite, et
ce qui a été tenté sur lui sans aboutir.

```
python3 restitution/graphe.py base.sqlite L224-43
python3 restitution/graphe.py base.sqlite L111-1 --html sortie.html
```

Cinq rendus versionnés dans `restitution/exemples/`, choisis pour ce qu'ils
montrent : **L224-43** une chaîne complète jusqu'à l'amendement et son but déclaré,
**L111-1** un article très cité, **L511-7** un article que le droit de l'Union
sature, **L112-1-1** un article sans aucune motivation parlementaire dont la seule
raison connue est une directive, **L122-23** les quatre paroles du § 4.3 côte à
côte — Gouvernement, chiffrage, Conseil d'État, Parlement.

La restitution n'ajoute aucune donnée : elle applique les règles § 5.1 (provenance
ou silence), § 5.4 (la confiance est une donnée) et § 4.3 (toute phrase produite
est citable). Elle distingue à l'écran ce qui porte sur **l'article** de ce qui ne
porte que sur le **texte entier** — un rapport au Président ou une transposition
déclarée motivent une ordonnance, pas l'alinéa qu'on lit.
