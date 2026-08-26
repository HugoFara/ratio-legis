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

## Cloner et lancer

**Pour voir ce que ça produit, rien à installer** : les rendus sont versionnés
dans [`restitution/exemples/`](restitution/exemples/) — le graphe d'un article,
la note sous contrat, le surlignage alinéa par alinéa, et ce qu'une modification
déplacerait. Ouvrez un `.html`.

Pour faire tourner le projet, il faut le construire. Le dépôt ne contient **que
du code, des plans de récupération et des mesures** : ni le fonds, ni les
corpus, ni la base. C'est délibéré — `travail/` est un cache reconstructible, et
les rapports de commission qu'il contient n'ont pas de régime de réutilisation
confirmé ([`ATTRIBUTION.md`](ATTRIBUTION.md)).

```bash
git clone <dépôt> ratio-legis && cd ratio-legis
python3 -m venv .venv && . .venv/bin/activate
pip install -e .              # pymupdf, la seule dépendance
pip install -e ".[api]"       # + fastapi et uvicorn, si vous servez l'API

bash tools/phase0/miroir_dila.sh data/raw/dila   # 6,4 Go — long, une seule fois
./pipeline.sh                                     # miroir + plans → base complète

python3 restitution/graphe.py travail/ratio-legis.sqlite L224-43
```

**Prérequis** : Python ≥ 3.14 (`pipeline.sh` refuse de démarrer en deçà), plus
`curl`, `tar` et `git`. Rien d'autre : une seule dépendance hors bibliothèque
standard, `pymupdf`, et elle ne sert qu'à lire les PDF des études d'impact et
des avis du Conseil d'État.

**Ce que ça coûte.** Le miroir DILA pèse 6,4 Go et sa première récupération est
longue ; ensuite elle est incrémentale et prend quelques secondes. Les corpus
téléchargés par le pipeline — rapports, amendements, textes en discussion —
ajoutent environ 740 Mo. L'ingestion elle-même, une fois tout sur le disque,
prend **environ cinq minutes** ; c'est elle que rejoue `quotidien.sh` chaque
matin. Comptez 8 Go de disque au total.

**Si quelque chose manque**, le pipeline le dit et s'arrête plutôt que de
produire une base incomplète en silence. Chaque étape est idempotente : la
relancer ne refait que ce qui manque.

Pour tenir la base à jour ensuite, voir [Tenir à jour](#tenir-à-jour) — un
minuteur systemd utilisateur, décrit dans [`docs/26-quotidien.md`](docs/26-quotidien.md).

Contribuer : [`CONTRIBUTING.md`](CONTRIBUTING.md).

## État : phase 2 close avec deux dérogations écrites, phase 4 entamée, validation humaine de la phase 0 toujours ouverte

Le graphe est chargé et interrogeable article par article. Les quatre critères de
sortie de la phase 2 ont été **mesurés contre leurs seuils**, ce qui n'avait
jamais été fait :

| Critère § 4.2 | Seuil | Mesuré | |
|---|---:|---:|---|
| couverture `produite_par` | > 95 % | 2 081 / 2 104 — **98,9 %** | atteint |
| couverture `issu_de` | > 90 % | 68 / 68 lois et ordonnances utiles — **100 %** | atteint, [`docs/20`](docs/20-dossiers-des-textes.md) |
| couverture `resulte_de` | > 60 % | 79 / 832 — **9,5 %** | **non atteint**, décision go du § 8 rendue |
| **précision `resulte_de`** | **> 95 %** | 168 / 179 hors-échantillon — **93,9 %** | **non atteint**, et mesuré |

**Toutes les arêtes `resulte_de` du graphe ont été examinées une à une** — 277
sur 277, en trois tirages reproductibles. Aucune n'est inconnue, et quinze sont
identifiées comme fausses ou douteuses, en quatre familles nommées.

La décision go/no-go du § 8, restée ouverte, est rendue dans
[`docs/21`](docs/21-precision-resulte-de.md) § 7 : **go**, parce que le grain de
l'article est tenu par le commentaire de rapport (695 articles) et par le texte
discuté (807), non par l'amendement (79) — l'hypothèse du § 8 sur le chemin était
fausse, pas le produit.

**La phase 2 est close** avec ces deux dérogations, écrites au § 4.2 de la feuille
de route plutôt que laissées tacites. La phase 4 est entamée : interroger le
graphe coûtait 425 ms par article, il en coûte 9.

Ce que le projet ne peut toujours pas faire, c'est se déclarer conforme : les
confiances portées par les arêtes sont des bornes de Wilson calculées sur mes
propres échantillons, et le critère de la phase 3 (évaluation humaine en aveugle)
suppose un jugement extérieur. Tant que les 100 articles du jeu d'annotation ne
sont pas validés à la main, **la phase 0 reste ouverte**, quoi qu'affichent les
compteurs.

### Ce que la base contient

Reconstruite d'une commande depuis le miroir et les plans versionnés
(`pipeline.sh`), 262 Mo, zéro violation d'intégrité.

| Nœuds | | Arêtes | |
|---|---:|---|---:|
| Articles (dont **2 104 en vigueur**) | 3 464 | `produite_par` — quel texte a produit la version | 8 145 |
| Versions d'articles | 6 362 | `repris_de` — continuité d'un alinéa par-delà la recodification | 6 137 |
| **Segments (alinéas)** | **28 294** | `renumerote_de` | 1 882 |
| Documents (rapports, exposés, études d'impact, avis) | 372 | `motive` — un passage qui motive, avec offsets | 686 |
| Amendements (22 102 Sénat, 11 115 Assemblée) | 33 217 | `renvoie_a` — le graphe de renvois | 12 534 |
| Acteurs | 1 478 | `resulte_de` — l'amendement qui a écrit l'alinéa | 279 |
| **Actes de l'Union** | **284** | `cite_acte_ue` / `transpose` | 1 572 / 8 |
| **Considérants de l'Union** | **7 674** | `article_acte_ue` — articles d'actes déclarés | 6 237 |
| **Textes en discussion** | **424** | **`porte_sur`** — l'article du texte → l'article du code | **43 786** |
| **Sorts d'amendements, en huit familles** | **33 217** | **`vise`** — l'amendement qui visait l'article, abouti ou non | **276** |
| Correspondances de texte entre les deux corpus | 106 | **`depose_sur`** — l'article du code réécrit par l'article du texte sur lequel l'amendement fut déposé | **874** |

Ce que cela donne au grain de l'article en vigueur, qui est le seul grain qui
compte pour le produit :

### Le verdict

Pour chaque article en vigueur, le graphe rend un verdict — y compris, et surtout,
quand il est négatif. Le taux global de 33,2 % d'articles sans raison documentée
ne veut rien dire : il faut séparer les parties, parce qu'un décret n'a ni exposé
des motifs, ni débat, ni amendement.

| partie | articles | un passage les motive | origine située | motivation du texte | **raison non documentée** |
|---|---:|---:|---:|---:|---:|
| **L** | 1 293 | 756 (58,5 %) | 199 | 333 | **5 (0,4 %)** |
| **R** | 632 | 44 | 14 | 47 | **527 (83,4 %)** |
| **D** | 179 | 1 | 0 | 11 | **167 (93,3 %)** |

**La partie législative du code de la consommation est documentée à 99,6 %. La
partie réglementaire l'est à 14,4 %** — et c'est elle qui porte la masse des
obligations que rencontre un consommateur.

Ce n'est pas un effet de périmètre. Les parties R et D en étaient exclues depuis
la phase 0, pour un motif écrit — « rattachement à DOLE mesuré à 0 % » — que
[`docs/27`](docs/27-parties-r-et-d.md) montre faux : 64 articles réglementaires
sur 811 ont un dossier législatif dans leur ascendance. Le périmètre a été élargi
aux trois parties, le corpus a suivi, et le nombre d'articles sans raison
documentée est passé de 701 à **699**. **Le silence de la partie réglementaire est
un état du fonds documentaire français**, et il est désormais mesuré sur un
périmètre qui ne l'exclut plus.

Détail et mises en garde : [`docs/18`](docs/18-verdict-et-hygiene.md). Toutes les
métriques : [`data/mesures/hygiene.tsv`](data/mesures/hygiene.tsv).

**Au grain de l'article** — ce qui répond à « pourquoi *cet article* dit ceci » :

| | |
|---|---:|
| **Articles remontant à un passage qui les motive** | **701 (33,3 %)** |
| Articles reliés à un article de texte en discussion | 812 (38,6 %) |
| Articles nommant un acte de l'Union | 117 |
| Articles remontant à un amendement identifié | 83 |
| Articles cités par un autre article du fonds | 1 039 (49,4 %) |

**Au grain du texte** — ce qui répond à « pourquoi ce *texte* existe ». Un rapport
au Président motive une ordonnance de plusieurs centaines d'articles, pas l'alinéa
qu'on lit ; la restitution affiche l'avertissement chaque fois qu'elle sert l'un
faute de l'autre :

| | |
|---|---:|
| **Articles atteignant un document motivant le texte** | **1 195 (56,8 %)** |
| dont par un rapport au Président | 988 |
| dont par un exposé des motifs | 162 |
| dont par une étude d'impact | 136 |
| dont par un avis du Conseil d'État | 135 |
| Articles atteignant un considérant européen | 117 |
| Articles atteignant une transposition déclarée | 60 |

Tous ces comptes suivent la **chaîne de renumérotation**. Un compteur qui ne le
dit pas est ininterprétable sur ce corpus : `motive` couvre 84 articles par leur
numéro d'aujourd'hui, et 701 dès qu'on remonte aux numéros d'avant 2016.

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
| 10. Motivation gouvernementale | exposé des motifs, étude d'impact, avis du Conseil d'État | [`docs/15`](docs/15-motivation-gouvernementale.md) |
| 11. Textes en discussion | sous quel article du texte l'article du code a été débattu | [`docs/16`](docs/16-textes-discutes.md) |
| 12. Sections appariées | les commentaires de rapport que rien ne rattachait | [`docs/17`](docs/17-sections-appariees.md) |
| 13. Verdict et hygiène | `raison non documentée`, et les métriques publiables | [`docs/18`](docs/18-verdict-et-hygiene.md) |
| **Phase 3** | **la note « pourquoi cet article », sous contrat** | [`docs/19`](docs/19-note-phase-3.md) |
| 14. Dossiers des textes | le dossier législatif de chaque texte, déclaré par DOLE | [`docs/20`](docs/20-dossiers-des-textes.md) |
| 15. Précision de `resulte_de` | les 277 arêtes examinées une à une, six gardes, la décision go/no-go | [`docs/21`](docs/21-precision-resulte-de.md) |
| 16. Lecture et performance | 425 ms → 9 ms par article, et une restitution redevenue reproductible | [`docs/22`](docs/22-lecture-et-performance.md) |
| 17. Dump ouvert | republier le graphe, sans rediffuser ce qu'on n'a pas le droit de rediffuser | [`docs/23`](docs/23-dump-ouvert.md) |
| 18. API de lecture | interroger le graphe en 12 ms, avec l'attribution qui voyage avec la donnée | [`docs/24`](docs/24-api.md) |
| 19. Surlignage par étape | quel texte a introduit chaque alinéa, malgré la recodification | [`docs/25`](docs/25-surlignage.md) |
| 20. Réincrémentation quotidienne | le fonds avait un an de retard ; l'orchestration le maintient à jour | [`docs/26`](docs/26-quotidien.md) |
| 21. Parties R et D | le périmètre couvre les trois parties ; le silence réglementaire n'en venait pas | [`docs/27`](docs/27-parties-r-et-d.md) |
| 22. Classement intra-document | classer sans rattacher, quand aucune arête ne désigne le passage | [`docs/28`](docs/28-classement-intra-document.md) |
| 23. Retentissement | « si je modifie cet article, qu'est-ce qui bouge », en produit à part | [`docs/29`](docs/29-retentissement.md) |

### Tenir à jour

```
./quotidien.sh                # miroir → incréments → reconstruction → dump → rapport
```

`pipeline.sh` n'extrayait le code que de l'archive **globale** de la DILA, datée
du 13 juillet 2025, alors que le miroir recevait un incrément par jour ouvré : le
fonds avait **un an de retard**, et rien ne le disait. 200 des 406 incréments en
attente touchaient ce code.

`quotidien.sh` enchaîne miroir, incréments, reconstruction, dump et rapport de
différences, journalise chaque étape et s'arrête tôt quand rien n'a bougé.
Déclenché par un minuteur systemd utilisateur ([`deploiement/`](deploiement/)) —
pas par Dagster : le pipeline est une séquence linéaire de huit étapes, et ce
qu'il lui faut est un déclencheur, un journal et l'idempotence.

L'incrément porte sur la **source** ; le graphe, lui, est reconstruit en entier.
Une base servie un mardi est donc exactement celle qu'on obtiendrait en repartant
de zéro.

### Reconstruire

**Prérequis : Python ≥ 3.14 et `pymupdf`**, déclarés dans `pyproject.toml` — la
seule dépendance hors bibliothèque standard, et elle ne sert qu'à extraire le
texte des études d'impact et des avis du Conseil d'État, qui n'existent qu'en
PDF. `pipeline.sh` refuse de démarrer sur un interpréteur plus ancien : un
pipeline dont l'interpréteur n'est écrit nulle part n'est rejouable que là où il
a été écrit.

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
| Périmètre de phase 0, figé, 1 280 articles L | [`data/perimetre-v1.csv`](data/perimetre-v1.csv) |
| Périmètre en vigueur, 2 091 articles, les trois parties | [`data/perimetre-v2.csv`](data/perimetre-v2.csv) |
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

**La note est écrite, l'évaluation ne l'est pas.** `restitution/note.py` produit
la note « pourquoi cet article » sous le contrat du § 4.3 : 11 656 constats sur
les 2 104 articles, zéro phrase écartée faute de citation, aucune note vide
([`docs/19`](docs/19-note-phase-3.md)). Le critère de sortie de la phase 3 est en
revanche une **évaluation humaine en aveugle** sur le golden set, qui suppose le
jeu d'annotation validé.

**Bloquant, et hors de portée du code.** Faire valider à la main les 100 articles
du jeu d'annotation. 66 d'entre eux portent déjà un passage proposé et ses
offsets. Tant que cette validation n'est pas faite, la phase 0 reste ouverte et
aucune mesure de précision du projet n'est autre chose qu'une auto-évaluation.

**Trois couches de motivation ne sont pas construites.**

1. ~~Les considérants européens.~~ **Faite** : 7 674 considérants chargés,
   117 articles atteints ([`docs/14`](docs/14-considerants.md)). Reste ouvert le
   seul chemin connu vers un lien au grain de l'article : les tableaux de
   concordance annexés aux textes de transposition. À défaut d'arête, les
   considérants sont désormais **classés** par proximité lexicale avec l'article,
   sous étiquette ([`docs/28`](docs/28-classement-intra-document.md)).
2. ~~Les études d'impact.~~ ~~Les avis du Conseil d'État.~~ **Chargés** : 27
   études, 15 avis, 41 exposés des motifs, 135 à 162 articles atteints chacun
   ([`docs/15`](docs/15-motivation-gouvernementale.md)). Mais **au grain du texte
   seulement** : aucune de ces trois sources n'emploie la convention de citation
   en en-tête qui produit une arête au grain de l'article, et le rapprochement par
   le numéro d'article du projet est faux, les articles étant renumérotés à chaque
   lecture. Confronter l'impact annoncé au dispositif voté — le second but du
   produit — suppose d'abord de charger les textes déposés.

**Le chaînon est posé, mais il ne débloque pas ce qu'on en attendait.** 812
articles en vigueur savent désormais sous quel article de quel texte ils ont été
discutés ([`docs/16`](docs/16-textes-discutes.md)). En revanche, **aucun des
dossiers ayant une étude d'impact n'a de texte déposé dans le corpus** : DOLE ne
lie le texte déposé que pour les propositions de loi, qui n'ont jamais d'étude
d'impact. Le rapprochement de l'étude d'impact reste donc à faire, et il passera
par le numéro de dépôt de la chambre, non par DOLE.

**La table de correspondance des identifiants de texte est écrite, et elle ne
rattrape pas les amendements orphelins.** C'était l'hypothèse ; elle est fausse.
106 jeux d'amendements sur 114 sont appariés à leur texte — identité de document,
pas rapprochement, contrôlée par la concordance du dossier et par la plage
d'articles (98,0 %). Ce qu'elle révèle est ailleurs : sur les amendements des
jeux appariés, **7 790 portent sur un article additionnel**. Ils ne visent aucun
article existant du code parce qu'ils en créent un, dont le numéro ne sera fixé
qu'à la codification. Aucune table ne peut leur donner une cible.
[`docs/31`](docs/31-correspondance-des-textes.md).

**Les textes déposés de l'Assemblée sont chargés**, par le numéro que le rapport
de commission déclare — « sur le projet de loi … (n° 2060) » — et non par DOLE,
qui ne lie ce texte que pour les propositions de loi. 55 numéros relevés, 55
servis. Le fonds passe de 371 à 424 textes en discussion et de 30 337 à 33 772
arêtes `porte_sur` ; **la partie législative gagne douze articles** qui passent
d'« origine située » à « un passage les motive », le texte déposé étant un état
de plus sur lequel les états doivent s'accorder.

**L'étude d'impact est arrivée au grain de l'article**, mais le découpeur n'a pas
suffi : il rendait trois articles. Le chaînon était plus haut. `porte_sur` était
**aveugle aux réécritures de section entière** — l'article 5 du projet de loi
consommation réécrit vingt-huit articles sous la forme `« Art. L. 121-16. – »`, et
aucun n'était vu, précisément ceux dont l'étude d'impact parle. L'en-tête d'un
alinéa cité n'est pas une référence à du droit existant : c'est la désignation de
l'article qu'on écrit.

Les articles en vigueur reliés à un article de texte passent de 819 à **964**, et
**79 articles de la partie législative montent d'un rang** dans le verdict. Le
code hôte étant implicite dans une citation, cette voie porte une garde propre —
LEGI doit confirmer que la loi du dossier a bien produit l'article — et sa
confiance mesurée à part, 0,796 contre 0,839.

**La voix du Gouvernement existe enfin au grain de l'article** : quinze articles
portent un passage de l'étude d'impact qui les chiffre, là où `motive` ne venait
que des rapports de commission. Quinze, et le plafond est mesuré : sur les 2 016
articles de texte des dossiers ayant une étude d'impact, 220 seulement touchent ce
code. [`docs/32`](docs/32-textes-deposes-assemblee.md),
[`docs/33`](docs/33-article-ecrit-dans-la-citation.md).

**Trous de couverture dans ce qui existe.** Les amendements de l'Assemblée pour
les législatures XV à XVII (103 articles éligibles, mécanique). La XIIIe, jamais
publiée en open data, reconstructible seulement page par page depuis Wayback —
arbitrage à rendre entre le coût et un trou déclaré. Les textes déposés, dont
l'absence laisse subsister le dernier mode d'échec de `resulte_de`. Les débats en
séance : le graphe sait ce que le Parlement a **fait**, pas ce qu'il a **dit**.

**Le régime de réutilisation des rapports parlementaires est établi** — il n'est
plus un préalable. Vérification faite aux sources en août 2026 : le CRPA exclut
les documents parlementaires (art. L300-2), et chaque chambre a publié ses
conditions. Elles diffèrent, et aucune ne permet de replacer le corps d'un rapport
sous Licence Ouverte : l'Assemblée interdit l'usage commercial, le Sénat exige la
gratuité de la diffusion. Le corps reste donc hors du dépôt et hors du dump, dont
la table `regime_de_reutilisation` porte l'écart entre les deux chambres. Les
extraits de 400 caractères, eux, sont couverts deux fois plutôt qu'une : soit le
rapport n'est pas protégé — position des deux chambres —, soit il l'est et
l'exception de courte citation s'applique.

**Deux gisements pourraient faire baisser le silence réglementaire, et aucun
n'est dans le projet.** Les **circulaires et instructions** publiées sur
Légifrance, qui commentent souvent le décret qu'elles appliquent : c'est un
chantier de corpus, faisable. Les **avis du Conseil d'État sur les projets de
décret**, non publiés à ce jour : c'est une question de droit d'accès, pas
d'outillage. Tant qu'ils manquent, 83,4 % et 93,3 % ne sont pas des bornes
définitives, et [`docs/27`](docs/27-parties-r-et-d.md) le dit.

## Le dump ouvert

```
python3 tools/diffusion/dump.py travail/ratio-legis.sqlite data/diffusion
python3 tools/diffusion/dump.py travail/ratio-legis.sqlite data/diffusion --strict
```

126 Mo, plus les mêmes arêtes en TSV, un dictionnaire des tables et un manifeste
haché. Le **texte des 252 rapports de commission n'y est pas** : leur régime de
réutilisation n'est pas confirmé par les assemblées. URL, hachage et offsets
restent, ce qui suffit à refaire le lien depuis la source ; les fenêtres de preuve
qui en viennent sont ramenées aux soixante caractères que le schéma exige au
minimum — la preuve irréductible, pas de l'extrait. `--strict` rend l'arbitrage
inverse et recalcule le verdict pour que la base reste cohérente avec elle-même.

Le dump n'est pas versionné : il se refait d'une commande, et seuls son manifeste
et sa notice le sont — comme pour les miroirs.

## Le surlignage

```
python3 restitution/surlignage.py base.sqlite L111-1 --html sortie.html
```

Sur le texte d'un article, la **couleur** donne le texte qui a introduit l'alinéa,
la **trame** signale qu'il a été retouché depuis, la **marque** nomme l'amendement
quand la chaîne y mène. 99,1 % des 7 504 alinéas en vigueur ont un texte
introducteur ; **un article sur six est composite**, écrit par deux textes ou plus.
Exemples dans [`restitution/exemples/surlignage/`](restitution/exemples/surlignage/).

## L'API

```
pip install '.[api]'
RATIO_LEGIS_BASE=data/diffusion/ratio-legis.sqlite uvicorn restitution.api:app
```

`GET /articles/{numero}` rend la fiche de provenance, `/note` la note sous
contrat, `/surlignage` l'origine de chaque alinéa,
`/retentissement` ce qu'une modification déplacerait, `/tentatives` ce qui a été
tenté sur l'article et ce qui l'a fait échouer, `/renvois/sommet` les articles
que le plus d'autres articles citent, `/tentatives/sommet` les plus disputés,
`/mesures` les métriques, `/docs` la documentation OpenAPI. **12 ms de médiane, 21 ms au 95ᵉ centile**, bout en
bout. Chaque réponse porte l'attribution et l'avertissement de non-interprétation
— en en-tête et dans la charge utile, parce qu'une API se consomme sans lire ce
fichier.

## Le retentissement

```
python3 restitution/retentissement.py base.sqlite L111-1            # ce qui bougerait
python3 restitution/retentissement.py base.sqlite L111-1 --profondeur 2
python3 restitution/retentissement.py base.sqlite --sommet 25       # les articles les plus cités
```

La question du légiste n'est pas celle du chercheur. `graphe.py` remonte à
l'origine ; celui-ci descend aux conséquences, par onde : le rang 1 cite
l'article, le rang 2 cite un article du rang 1. **Sur L111-1, 69 articles
bougeraient, dont 20 dont la raison n'est pas documentée** — c'est le coût que la
métrique d'hygiène chiffre à l'échelle du code, rendu au grain d'une décision.

Il dit ce qu'il faudrait relire ; il ne dit pas ce qu'il faudrait y écrire, et il
ne le dira jamais. Exemples dans
[`restitution/exemples/retentissement/`](restitution/exemples/retentissement/),
détail dans [`docs/29`](docs/29-retentissement.md).

## Ce qui a été tenté

```
python3 restitution/tentatives.py base.sqlite L511-7        # ce qu'on a tenté, et ce qui l'a bloqué
python3 restitution/tentatives.py base.sqlite --sommet 25   # les articles les plus disputés
```

Le graphe dit ce qui a écrit le droit. Il sait aussi dire **ce qu'on a voulu y
écrire et qui n'y est pas** : sur les amendements du corpus, une petite minorité a
produit un alinéa qui subsiste ; tout le reste est du droit qui n'existe pas, et
c'est ce corpus-là qu'un légiste consulte avant de rédiger.

Le sort était en base depuis onze tranches, et la fiche en portait une table — mal
lue. Le tri comparait le libellé à la chaîne « Adopté », si bien qu'« Adopté -
vote unique » passait pour un échec. Le libellé était rendu brut, si bien
qu'« Irrecevable art. 45, al. 1 C (cavalier) » n'apprenait rien. Et surtout,
**l'Assemblée affichait zéro irrecevabilité quand le Sénat en affichait 1 735** :
son sort, vide pour 1 149 amendements, est écrit dans la colonne voisine — 694
retirés, 447 irrecevables, 8 réellement en attente.

Les huit familles de sort sont désormais comparables, et **aucun des 33 217
amendements n'a plus de libellé illisible** — 63 en avaient un, fragments de
feuille de style Word que les tabulations d'Améli avaient poussés dans la colonne
du sort.

| | Assemblée | Sénat |
|---|---:|---:|
| **déclaré irrecevable** | **447** *(0 avant)* | 1 735 |
| retiré | **1 885** *(1 191 avant)* | 5 810 |
| rejeté · adopté | 3 280 · 2 677 | 6 655 · 5 112 |
| sort illisible | 0 | 0 *(63 avant)* |

Sur les 2 182 amendements écartés sans discussion : **905 au titre de l'article
40** — ils aggravaient une charge publique —, 603 comme cavaliers, 117 au titre
de la règle de l'entonnoir, 93 comme relevant du décret.

Au grain de l'article en vigueur, **165 articles sur 2 104 portent au moins une
tentative** — 689 tentatives rendues, dont 460 non abouties. Les jeux
d'amendements de l'Assemblée sont appariés à leur texte **39 sur 39**.

Trois voies de rattachement, jamais confondues : l'**alinéa écrit** (`resulte_de`,
confiance 0,893), la **cible déclarée** par le dispositif (`vise`, 0,621), la
seule ouverte à un amendement rejeté, et la **subdivision déposée** (`depose_sur`,
0,796) — l'amendement fut discuté sur l'article du texte qui a réécrit celui-ci,
et cet article du texte n'en a réécrit aucun autre. Le sort est nommé, jamais
interprété : « retiré » ne dit pas si l'auteur a cédé ou obtenu satisfaction, et
cela se lit dans le compte rendu de séance, que le graphe ne contient pas.
[`docs/30`](docs/30-sort-des-amendements.md),
[`docs/31`](docs/31-correspondance-des-textes.md).

## Classer sans rattacher

Un rapport au Président, une étude d'impact, un acte de l'Union motivent le
**texte entier**. Aucune arête ne désigne le passage qui concerne tel article, et
deux méthodes pour en fabriquer une ont été mesurées puis écartées. La restitution
en tirait la conséquence qu'il ne fallait rien choisir — et affichait donc le
document depuis l'offset 0, c'est-à-dire l'adresse au Président.

Or afficher un document depuis son début n'est pas s'abstenir de choisir : c'est
choisir l'ordre du document, qui est le pire des ordres pour la question posée.
Les passages sont désormais **classés par recouvrement lexical** avec le texte de
l'article, chaque terme pesé par sa rareté dans ce document-là, les trois
meilleurs affichés avec leurs offsets et **les termes communs qui ont produit le
classement**. L'étiquette est portée à l'écran :

> classé par proximité lexicale avec le texte de l'article — aucun lien déclaré,
> aucune arête créée

Aucun corpus extérieur, aucun apprentissage, aucun vecteur : tout est calculé sur
le document interrogé, le classement se rejoue à l'identique et s'explique en
montrant ce qui l'a produit. Sous deux termes communs, rien n'est classé et la
page le dit. [`docs/28`](docs/28-classement-intra-document.md).

## Licence et attribution

Code sous [AGPL-3.0](LICENSE). Les données amont sont sous Licence Ouverte /
Etalab 2.0 et leur attribution est obligatoire.

**Une exception, et elle est documentée** : le corps des rapports de commission ne
relève ni du CRPA — l'article L300-2 en exclut les documents parlementaires — ni
de la Licence Ouverte des portails, qui n'ouvrent que les métadonnées. Il obéit
aux conditions propres à chaque chambre, incompatibles avec une rediffusion sous
Licence Ouverte. Il n'est donc ni versionné, ni rediffusé : voir
[`ATTRIBUTION.md`](ATTRIBUTION.md).

## Voir le graphe

`restitution/graphe.py` interroge la base et restitue, pour un article en vigueur,
tout ce que le graphe sait dire de lui : les passages qui le motivent, la
provenance de chaque alinéa jusqu'à l'amendement qui l'a écrit, ce qui le cite, et
ce qui a été tenté sur lui sans aboutir.

```
python3 restitution/graphe.py base.sqlite L224-43              # le graphe, arête par arête
python3 restitution/note.py   base.sqlite L224-43              # la note, sous contrat § 4.3
python3 restitution/note.py   base.sqlite --contrat            # éprouver le contrat
python3 restitution/graphe.py base.sqlite L111-1 --html out.html
```

Sept notes versionnées dans `restitution/exemples/notes/`. **Aucun modèle de
langue n'intervient** : la note est composée par assemblage de gabarits
déterministes, les passages cités sont verbatim. L'article 50 du règlement (UE)
2024/1689 vise le contenu synthétique produit par un système d'IA ; il ne trouve
pas à s'appliquer, et la note l'écrit plutôt que d'afficher une étiquette
trompeuse.

Douze rendus versionnés dans `restitution/exemples/`, choisis pour ce qu'ils
montrent : **L224-43** une chaîne complète jusqu'à l'amendement et son but déclaré,
**L111-1** un article très cité, **L511-7** un article que le droit de l'Union
sature, **L112-1-1** un article sans aucune motivation parlementaire dont la seule
raison connue est une directive, **L122-23** les quatre paroles du § 4.3 côte à
côte — Gouvernement, chiffrage, Conseil d'État, Parlement —, **L521-2** un article
suivi à travers la navette et la recodification, **L722-10** un article dont la
seule motivation vient d'une section que rien ne rattachait avant la douzième
tranche, **L224-109** l'un des cinq articles de la partie législative dont le
verdict est *raison non documentée*, **R121-1** un article réglementaire que son
ascendance législative documente encore, **D824-3** le seul article D du code
qu'un rapport de commission explique, **R512-31** la réponse ordinaire de la
partie réglementaire — *raison non documentée*, alors que sept articles le
citent —, **D120-7** un article dont la seule raison connue vient de quatre
règlements de l'Union.

Cinq tentatives versionnées dans `restitution/exemples/tentatives/`, et le
classement des articles les plus disputés : **L732-3** trois amendements écartés
comme cavaliers, dont celui du Gouvernement ; **L312-9** la délégation d'assurance
emprunteur ; **L113-3** les deux chambres et un sort lu dans l'état procédural ;
**L224-43** quatre amendements adoptés dont l'alinéa subsiste ; **L511-7**
l'article le plus travaillé du fonds, 91 tentatives, que chaque loi de
consommation vient allonger.

La restitution n'ajoute aucune donnée : elle applique les règles § 5.1 (provenance
ou silence), § 5.4 (la confiance est une donnée) et § 4.3 (toute phrase produite
est citable). Elle distingue à l'écran ce qui porte sur **l'article** de ce qui ne
porte que sur le **texte entier** — un rapport au Président ou une transposition
déclarée motivent une ordonnance, pas l'alinéa qu'on lit.
