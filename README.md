# Ratio Legis

Pour un article de code français **en vigueur aujourd'hui**, répondre à une
seule question : *pourquoi existe-t-il sous cette forme ?* — en remontant aux
matériaux publics qui l'expliquent : exposé des motifs, étude d'impact, avis du
Conseil d'État, commentaire du rapport de commission, amendement qui a écrit
l'alinéa, considérant de la directive transposée.

Le produit est un **graphe de provenance normative** dans une base SQLite, et une
couche de restitution strictement ancrée : aucune phrase affirmative sans
citation résoluble au passage. Périmètre actuel : le **Code de la
consommation**, ses trois parties, 2 104 articles en vigueur.

Spécification : [`ratio-legis-feuille-de-route.md`](ratio-legis-feuille-de-route.md).
Contribuer : [`CONTRIBUTING.md`](CONTRIBUTING.md). Attribution des sources :
[`ATTRIBUTION.md`](ATTRIBUTION.md).

**Ce que le graphe vaut, en deux chiffres, et par qui ils ont été mesurés.**
Sur les 100 articles du jeu d'annotation, annotés indépendamment par sept
modèles de langue ([`docs/39`](docs/39-cent-verdicts-d-agents.md)), le graphe
désigne **le bon document 65 fois sur 74**, et quand il affirme qu'un passage
motive l'article, **c'est le passage annoté 30 fois sur 53** — 56,6 %, borne de
Wilson 0,43 ; sur les 73 articles que l'annotateur a motivés, il retrouve le
passage 30 fois. Il trouve le rapport qui explique l'article ; il ne trouve
qu'une fois sur deux le paragraphe qui l'explique (rejoué sur la base du jour
par `tools/annotation/verifier.py`). **Aucun de ces
verdicts n'est humain**, et aucune confiance de ce dépôt ne l'est : le
producteur des arêtes est déterministe, l'instrument qui les mesure est
l'auteur ou des agents, jugeant sur des tirages reproductibles. Tant que le jeu
d'annotation n'est pas relu à la main, tout chiffre de ce fichier est une
auto-évaluation, et il est présenté comme tel.

## Pourquoi ce projet existe

Les matériaux sont publics. Ce qui manque est le **chaînage** entre le texte
consolidé qu'on lit et ces matériaux, et la chaîne est rompue en aval de la
promulgation : la codification à droit constant renumérote, les lois sans
rapport thématique modifient, les amendements se justifient en une ligne, la
raison d'une transposition est à Bruxelles, une ordonnance n'a pas de débat, un
décret n'a pas d'exposé des motifs.

Sur le code de la consommation, la rupture se mesure. **78 % des articles de la
partie législative semblent issus d'une ordonnance** — la recodification de
2016 — et **80,7 % ont une loi dans leur ascendance** dès qu'on franchit un
saut de renumérotation. Un rapport de 2013 commente L. 121-105, jamais
L. 224-65 : `motive` atteint 162 articles par leur numéro d'aujourd'hui, 783
en remontant les numéros d'avant. Le graphe existe pour tenir cette chaîne, et
pour dire honnêtement où elle s'arrête.

## Ce qu'il fait

Cinq questions, chacune rendue en ligne de commande, en HTML, et par l'API.
**Rien à installer pour voir le résultat** : les rendus d'exemple sont
publiés à [hugofara.github.io/ratio-legis](https://hugofara.github.io/ratio-legis/)
— une page d'entrée dit lequel regarder pour quoi. Les mêmes fichiers sont
versionnés dans [`restitution/exemples/`](restitution/exemples/).

**Pourquoi cet article.** La fiche de provenance, arête par arête, et la note
« pourquoi cet article » sous le contrat du § 4.3 — toute phrase produite est
citable, celles qui ne le sont pas sont supprimées et le compte s'affiche en
pied de page (zéro sur 11 641 constats). Aucun modèle de langue n'intervient :
la note est assemblée par gabarits, les passages sont verbatim.

```
python3 restitution/graphe.py travail/ratio-legis.sqlite L224-43
python3 restitution/note.py   travail/ratio-legis.sqlite L224-43
python3 restitution/note.py   travail/ratio-legis.sqlite --contrat     # éprouver le contrat
```

**Qui a écrit chaque alinéa.** Le surlignage : la couleur donne le texte qui a
introduit l'alinéa, la trame signale qu'il a été retouché depuis, la marque
nomme l'amendement quand la chaîne y mène. 99,1 % des 7 504 alinéas en vigueur
ont un texte introducteur ; un article sur six est écrit par deux textes ou
plus ([`docs/25`](docs/25-surlignage.md)).

```
python3 restitution/surlignage.py travail/ratio-legis.sqlite L111-1 --html sortie.html
```

**Ce qu'on a voulu y écrire et qui n'y est pas.** Les 97 226 amendements des
deux chambres avec leur sort en huit familles comparables, et l'irrecevabilité
lue là où la chambre l'écrit — sur 11 800 irrecevabilités, 3 097 au titre de
l'article 40, 1 218 cavaliers.
248 articles en vigueur portent au moins une tentative, par trois voies jamais
confondues : l'alinéa écrit qui subsiste (`resulte_de`), la cible que le
dispositif déclare (`vise`, la seule ouverte à un amendement rejeté), la
subdivision du texte sur laquelle il fut déposé (`depose_sur`)
([`docs/30`](docs/30-sort-des-amendements.md)).

```
python3 restitution/tentatives.py travail/ratio-legis.sqlite L111-3        # 67 tentatives, 56 non abouties
python3 restitution/tentatives.py travail/ratio-legis.sqlite --sommet 25   # les plus disputés
```

**Ce qui bougerait si je modifiais cet article.** Le retentissement descend le
graphe des 12 534 renvois, par onde : sur L111-1, 69 articles à relire, dont 20
dont la raison n'est pas documentée. Il dit ce qu'il faudrait relire ; il ne
dit pas ce qu'il faudrait y écrire ([`docs/29`](docs/29-retentissement.md)).

```
python3 restitution/retentissement.py travail/ratio-legis.sqlite L111-1 --profondeur 2
python3 restitution/retentissement.py travail/ratio-legis.sqlite --sommet 25
```

**Ce que le fonds documentaire tait.** Pour chaque article en vigueur, un
verdict — et surtout le verdict négatif, `raison non documentée`, qui distingue
« nous n'avons pas cherché » de « nous avons cherché dans treize sources et il
n'y a rien ». Les métriques d'hygiène législative sont dans
[`data/mesures/hygiene.tsv`](data/mesures/hygiene.tsv) et sous `/mesures`
([`docs/18`](docs/18-verdict-et-hygiene.md)).

**Ce qu'on peut lui dire.** Chaque arête de chaque page porte un lien
*signaler*, qui ouvre un rapport pré-rempli — article, arête, cible, preuve —
dans les issues du dépôt. Un lien faux coûte plus que dix liens manquants, et
le lecteur qui en voit un est le seul juge humain que le projet ait.

**Ce qui est classé, non affirmé.** Un rapport au Président, une étude
d'impact, une directive motivent le texte entier ; aucune arête ne désigne le
passage qui concerne l'article, et le graphe n'en fabrique pas. Il *classe* les
passages par le vocabulaire qu'ils partagent avec l'article, pesé par sa
rareté dans le code, montre les termes qui ont produit le classement, et se
tait quand rien ne partage un terme propre à l'article. Mesuré : le passage
attendu dans les trois montrés 12 fois sur 17 rapports au Président, 17 fois
sur 21 couples (article, considérant) ([`docs/28`](docs/28-classement-intra-document.md),
[`docs/48`](docs/48-classement-harnais-accueil.md)).

**Pour les outils tiers**, la même chose en API et en dump ouvert :

```
pip install '.[api]'
RATIO_LEGIS_BASE=data/diffusion/ratio-legis.sqlite uvicorn restitution.api:app
# GET /articles/{numero}  /note  /surlignage  /retentissement  /tentatives
# GET /renvois/sommet  /tentatives/sommet  /mesures  /docs
python3 tools/diffusion/dump.py travail/ratio-legis.sqlite data/diffusion
```

12 ms de médiane, 21 ms au 95ᵉ centile. Chaque réponse porte l'attribution et
l'avertissement de non-interprétation, en en-tête et dans la charge utile
([`docs/24`](docs/24-api.md), [`docs/23`](docs/23-dump-ouvert.md)).

## Ce qu'il ne fait pas

**Il n'interprète pas.** Il ne dit ni ce qu'un article veut dire, ni s'il
s'applique à votre cas, ni ce qu'il faudrait y écrire. Il rend des matériaux et
le chemin qui y mène ; l'usage des travaux préparatoires en interprétation est
juridiquement discuté et n'est pas la bataille du projet. Ce n'est pas un
moteur de recherche juridique : consulter le droit positif est un problème que
Légifrance a résolu.

**Il ne couvre qu'un code.** Le code de la consommation a été choisi pour ses
défauts utiles — recodifié, très transposé, récent. Tout élargissement passe
par une nouvelle note de cadrage, pas par une option.

**Il ne contient pas les débats.** Le graphe sait ce que le Parlement a
**fait** — déposé, adopté, rejeté, déclaré irrecevable —, pas ce qu'il a
**dit**. « Retiré » ne dit pas si l'auteur a cédé ou obtenu satisfaction, et
cela se lit dans le compte rendu de séance, qui n'y est pas.

**Il ne rediffuse pas les rapports parlementaires.** Leur corps n'est ni dans
le dépôt ni dans le dump : le CRPA exclut les documents parlementaires
(art. L300-2), et les conditions des deux chambres ne se transmettent pas sous
Licence Ouverte. Restent l'URL, le hachage, les offsets, et des extraits de 400
caractères au plus ([`ATTRIBUTION.md`](ATTRIBUTION.md)).

**Aucun modèle de langue ne décide d'une arête**, et aucun n'écrit une phrase de
la restitution. Des agents ont servi de **juges** dans les mesures de précision
récentes — deux par fiche, en colonnes séparées, arbitre sur désaccord, et le
fichier dit qui a tranché — jamais de producteurs de lien. La topologie du
graphe vient de règles déterministes et de correspondances textuelles
vérifiables.

**Il ne se déclare pas conforme.** Les confiances portées par les arêtes sont
des bornes inférieures de Wilson à 95 %, calculées sur des tirages
reproductibles jugés par l'auteur ou par des agents — celles de `porte_sur`,
`vise` et `depose_sur` dans le tableau ci-dessous viennent toutes de juges
Sonnet, deux par fiche, un arbitre sur désaccord ; la fiche dit qui a tranché.
Le critère de sortie de la phase 3 est une évaluation humaine en aveugle sur un
jeu d'annotation validé, et ce jeu ne l'est pas. **Tant que les 100 articles ne
sont pas relus à la main, la phase 0 reste ouverte** et chaque mesure du projet
est une auto-évaluation. Les agents ont rendu ce bloquant moins visible, pas
plus petit.

**Il ne comble pas le silence réglementaire.** La partie législative est
documentée à 94 % ; la partie réglementaire à 15 %, et c'est elle qui porte la
masse des obligations qu'un consommateur rencontre. C'est un état du fonds
documentaire français, pas un défaut du périmètre, et il est mesuré plutôt que
masqué. Deux gisements le feraient baisser — les circulaires, les avis du
Conseil d'État sur les décrets — et aucun n'est dans le projet.

## Pour qui

**Le légiste** — qui rédige dans une administration, une commission, un
cabinet. Avant d'écrire, il consulte ce qui a été tenté sur l'article et ce qui
l'a bloqué ; après avoir écrit, ce que sa modification déplacerait ; en lisant,
qui a écrit chaque alinéa et à quel moment de la navette.

**Le chercheur et le journaliste** — les métriques d'hygiène législative
publiables : part des articles sans aucune motivation traçable, par partie du
code ; part des amendements adoptés sans objet publié ; fondements
d'irrecevabilité ; durée de la navette. Tout est dans un TSV versionné et se
recalcule d'une commande.

**Le juriste praticien, la DGCCRF, l'association de consommateurs** — la fiche
de provenance d'un article, pour retrouver l'étude d'impact qui l'a chiffré ou
l'amendement qui l'a écrit. Avec la mise en garde qui s'affiche à chaque page :
ce sont des matériaux, pas une interprétation.

**L'outilleur** — la base SQLite, l'API, le dump sous Licence Ouverte avec
l'attribution qui voyage avec la donnée. Le code est sous AGPL-3.0 : un service
bâti dessus rend son code.

**Ce n'est pas pour** qui cherche le droit applicable à une situation, ni pour
qui veut une réponse en langue naturelle à « que veut dire cet article ».

### Lire un score

Chaque arête porte une **méthode** — `declaree` (une source dit le lien),
`derivee` (une correspondance textuelle l'établit), `inferee` (un alignement de
contenu la désigne) — et une **confiance**, qui n'est pas un ressenti : c'est la
borne inférieure de Wilson d'un tirage jugé, dont la fiche est versionnée dans
[`data/mesures/`](data/mesures/) avec le nom du juge. Une arête à 0,76 vient
d'un tirage de vingt jugé 19 sur 20. Une confiance qui n'a pas de fiche n'existe
pas dans ce dépôt.

## Cloner et lancer

Le dépôt ne contient **que du code, des plans de récupération et des mesures** :
ni le fonds, ni les corpus, ni la base. `travail/` est un cache reconstructible.

```bash
git clone https://github.com/HugoFara/ratio-legis.git && cd ratio-legis
python3 -m venv .venv && . .venv/bin/activate
pip install -e .              # pymupdf, la seule dépendance
pip install -e ".[api]"       # + fastapi et uvicorn, si vous servez l'API

bash tools/phase0/miroir_dila.sh data/raw/dila   # 6,4 Go — long, une seule fois
./pipeline.sh                                     # miroir + plans → base complète

python3 restitution/graphe.py travail/ratio-legis.sqlite L224-43
```

**Prérequis** : Python ≥ 3.14 (`pipeline.sh` refuse de démarrer en deçà), plus
`curl`, `tar` et `git`. Une seule dépendance hors bibliothèque standard,
`pymupdf`, qui ne sert qu'à lire les PDF des études d'impact et des avis du
Conseil d'État.

**Ce que ça coûte.** Le miroir DILA pèse 6,4 Go et sa première récupération est
longue ; ensuite elle est incrémentale. Les corpus téléchargés — rapports,
amendements, textes en discussion — ajoutent 1,5 Go, le miroir EUR-Lex des
284 actes de l'Union 153 Mo. L'ingestion, une fois tout sur le disque, prend
**environ quinze minutes** et produit une base de 466 Mo, zéro violation
d'intégrité. Comptez 9 Go de disque.

**Si quelque chose manque**, le pipeline le dit et s'arrête plutôt que de
produire une base incomplète en silence. Chaque étape est idempotente.

**Tenir à jour** : `./quotidien.sh` enchaîne miroir, incréments, reconstruction,
dump et rapport de différences, et s'arrête tôt quand rien n'a bougé. Il est
déclenché par un minuteur systemd utilisateur ([`deploiement/`](deploiement/),
[`docs/26`](docs/26-quotidien.md)). L'incrément porte sur la source ; le graphe
est reconstruit en entier, si bien qu'une base servie un mardi est exactement
celle qu'on obtiendrait en repartant de zéro.

Deux étapes demandent le réseau au-delà des sources : la vérification des
identifiants CELEX auprès de Cellar, dont le résultat est versionné, et le
miroir EUR-Lex, stocké hors dépôt avec son manifeste horodaté.

## État

**Phase 2 close avec deux dérogations écrites, phase 4 entamée, validation
humaine de la phase 0 toujours ouverte.** Les critères de sortie de la phase 2
mesurés contre leurs seuils :

| Critère § 4.2 | Seuil | Mesuré | |
|---|---:|---:|---|
| couverture `produite_par` | > 95 % | 2 081 / 2 104 — **98,9 %** | atteint |
| couverture `issu_de` | > 90 % | 70 / 70 lois et ordonnances utiles — **100 %** | atteint — les incréments DOLE sont lus depuis [`docs/50`](docs/50-increments-doublons-legislatures.md) |
| couverture `resulte_de` | > 60 % | 83 / 896 — **9,3 %** | **non atteint**, décision go du § 8 rendue dans [`docs/21`](docs/21-precision-resulte-de.md) § 7 : le grain de l'article est tenu par le commentaire de rapport et par le texte discuté, non par l'amendement |
| précision `resulte_de` | > 95 % | 71 / 77 hors-échantillon — **92,2 %**, Wilson 0,8402 | **non atteint** ; re-mesuré le 24 septembre 2026 sur la population d'après `docs/52`, 18 / 20, deux juges et un arbitre ([`docs/53`](docs/53-trait-insecable-a-la-lecture.md)) ; 18 / 20 sur les arêtes des législatures XVI et XVII ([`docs/50`](docs/50-increments-doublons-legislatures.md) § 7, une fausse arbitrée juste en [`docs/55`](docs/55-trois-arbitrages.md)), 35 / 37 sur la population du 21 septembre |

### Ce que la base contient

| Nœuds | | Arêtes | |
|---|---:|---|---:|
| Articles — lignées (dont **2 104 en vigueur**) | 3 877 | `produite_par` — quel texte a produit la version | 8 145 |
| Versions d'articles | 6 362 | `repris_de` — continuité d'un alinéa par-delà la recodification | 6 137 |
| Segments (alinéas) | 28 294 | `renumerote_de` | 1 929 |
| Documents (rapports, exposés, études d'impact, avis) | 834 | `motive` — un passage qui motive, avec offsets | 1 727 |
| Amendements (33 199 Sénat, 64 027 Assemblée, législatures XIV, XVI et XVII) | 97 226 | `renvoie_a` — le graphe de renvois | 12 535 |
| Acteurs | 2 656 | `resulte_de` — l'amendement qui a écrit l'alinéa | 446 (confiance 0,82) |
| Actes de l'Union | 284 | `cite_acte_ue` / `transpose` / `transpose_article` — l'article de la directive que l'article du code transpose, lu dans les tableaux de concordance | 1 572 / 8 / 33 (0,90) |
| Considérants de l'Union | 7 674 | `article_acte_ue` — articles d'actes déclarés | 6 237 |
| Textes en discussion | 925 | `porte_sur` — l'article du texte → l'article du code | 123 862 (7 494 internes, 0,91 ; 236 résolues par le contenu, 0,84) |
| Sorts d'amendements, en huit familles | 97 226 | `vise` — l'amendement qui visait l'article, abouti ou non | 663 (652 par le numéro, 0,86 ; 11 par le contenu, 0,74) |
| Correspondances de texte entre les deux corpus | 322 | `depose_sur` — l'article du code que l'amendement touche, par l'alinéa du texte qu'il nomme | 1 835 (0,91 par l'alinéa, 0,82 par l'article nommé, 0,69 par l'article entier) |

### Le verdict

Le taux global d'articles sans raison documentée ne veut rien dire : il faut
séparer les parties, parce qu'un décret n'a ni exposé des motifs, ni débat, ni
amendement.

| partie | articles | un passage les motive | origine située | motivation du texte | **raison non documentée** |
|---|---:|---:|---:|---:|---:|
| **L** | 1 293 | 787 (60,9 %) | 129 | 307 | **70 (5,4 %)** |
| **R** | 632 | 43 | 7 | 58 | **524 (82,9 %)** |
| **D** | 179 | 1 | 0 | 11 | **167 (93,3 %)** |

Les parties R et D étaient exclues du périmètre initial pour un motif que
[`docs/27`](docs/27-parties-r-et-d.md) a montré faux ; le périmètre couvre les
trois parties et le silence réglementaire est mesuré sur un périmètre qui ne
l'exclut plus.

**Au grain de l'article** — « pourquoi *cet article* dit ceci ». Les deux
tableaux sont recalculés à chaque reconstruction par
[`tools/mesures/grain.py`](tools/mesures/grain.py), avec les définitions du
verdict, dans [`data/mesures/grain.tsv`](data/mesures/grain.tsv) :

| | |
|---|---:|
| Articles remontant à un passage qui les motive | **799 (38,0 %)** |
| Articles reliés à un article de texte en discussion | 964 (45,8 %) |
| Articles nommant un acte de l'Union | 117 |
| Articles reliés à un article d'acte de l'Union par un tableau de concordance | 35 |
| Articles remontant à un amendement identifié | 142 |
| Articles cités par un autre article du fonds | 1 031 (49,0 %) |

**Au grain du texte** — « pourquoi ce *texte* existe ». Un rapport au Président
motive une ordonnance de plusieurs centaines d'articles, pas l'alinéa qu'on
lit ; la restitution affiche l'avertissement chaque fois qu'elle sert l'un
faute de l'autre. Un texte qui n'a fait que recodifier l'article ne le motive
pas ([`docs/39`](docs/39-cent-verdicts-d-agents.md) § 3) :

| | |
|---|---:|
| Articles atteignant un document motivant le texte | **1 282 (60,9 %)** |
| dont par un rapport au Président | 799 |
| dont par un exposé des motifs | 938 |
| dont par une étude d'impact | 701 |
| dont par un avis du Conseil d'État | 245 |
| Articles atteignant un considérant européen | 117 |
| Articles atteignant une transposition déclarée | 75 |

Les chiffres publiés jusqu'au 24 septembre 2026 avaient été recopiés à la main,
par des requêtes perdues ; la ventilation par type de document, en
particulier, ne suivait pas la réserve de la recodification (994 rapports au
Président, 206 exposés des motifs). Ceux-ci se recalculent.

Tous ces comptes suivent la chaîne de renumérotation ; un compteur qui ne le
dit pas est ininterprétable sur ce corpus.

### Ce qui reste à faire

**Bloquant, et hors de portée du code : la validation à la main des 100
articles du jeu d'annotation.** Ils portent cent verdicts d'agents
([`docs/39`](docs/39-cent-verdicts-d-agents.md)) — une pré-annotation, pas une
vérité terrain. L'outillage de l'annotateur est prêt
([`docs/36`](docs/36-jeu-d-annotation-prepare.md)). Après elle, l'évaluation
humaine en aveugle de la note, critère de sortie de la phase 3.

**Couverture.** Les amendements de la XVe législature : le serveur de
l'Assemblée coupe le transfert de son archive de 650 Mo, et le pipeline la
prendra au premier passage où il la sert ; les constantes seront alors à
re-mesurer ([`docs/50`](docs/50-increments-doublons-legislatures.md) § 8). Les
192 jeux d'amendements de l'Assemblée trouvent tous leur texte discuté
([`docs/52`](docs/52-projets-deposes-et-trait-insecable.md)). La XIIIe, jamais publiée en open
data, reconstructible page par page depuis Wayback — arbitrage à rendre entre
le coût et un trou déclaré. Les tableaux de concordance sont lus dans deux
études d'impact ([`docs/54`](docs/54-tableaux-de-concordance.md)) ; les autres
ne transposent vers notre code aucune disposition.

**Huit arêtes jugées fausses sont dans la base**, et le harnais
(`tools/mesures/rejouer.py`) les nomme à chaque passage. Quatre sont des
`depose_sur` sans garde : un amendement que la source range sous un autre
texte et un alinéa mal cité ([`docs/51`](docs/51-depose-sur-re-mesuree.md)),
un amendement qui écrit dans un autre article que celui du texte et un
« Art. L. 423-2 » nouveau qui renumérote l'ancien
([`docs/52`](docs/52-projets-deposes-et-trait-insecable.md)). Quatre sont des
`resulte_de` sans garde, des tirages de
[`docs/50`](docs/50-increments-doublons-legislatures.md) § 7 et de
[`docs/53`](docs/53-trait-insecable-a-la-lecture.md) : deux formules
administratives partagées par un passage destiné ailleurs, une rédaction non
retenue, un alinéa attribué au mauvais amendement du dossier. Les autres ont
été réparées à la source, ou arbitrées sur pièces
([`docs/55`](docs/55-trois-arbitrages.md)) : l'ancre d'une insertion n'est
pas une cible, et la garde qui l'écarte est posée ; les cinq verdicts humains
de [`docs/21`](docs/21-precision-resulte-de.md) contestés en
[`docs/49`](docs/49-les-dix-du-harnais.md) § 6 et l'agrément « Mon
Accompagnateur Rénov' » sont justes.

**Les arêtes récentes ont chacune leur maille nommée**, dans la section « ce
qui n'est pas fait » de leur document — les dernières : le plan propre d'un
amendement hors glissement, les 124 articles écrits que rien ne contient
([`docs/47`](docs/47-le-numero-glisse-par-le-contenu.md) § 5), laissés pour
les raisons de [`docs/54`](docs/54-tableaux-de-concordance.md) § 4 ; les
formules banales de `resulte_de`, dont aucune règle mesurée ne sépare les
justes (`docs/54` § 1).

**Le silence réglementaire** ne baissera que par des corpus qui ne sont pas dans
le projet : les circulaires, faisables ; les avis du Conseil d'État sur les
décrets, non publiés — question de droit d'accès, pas d'outillage.

## Les tranches

Le projet avance par tranches, chacune documentée dans `docs/` avec ce qu'elle
a mesuré et ce qu'elle laisse ouvert. Les chiffres ci-dessus sont ceux
d'aujourd'hui ; ceux des documents sont ceux de leur date.

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
| 24. Sort des amendements | huit familles comparables, et l'irrecevabilité lue là où la chambre l'écrit | [`docs/30`](docs/30-sort-des-amendements.md) |
| 25. Correspondance des textes | apparier les identifiants de texte des deux corpus, et mesurer leur plafond | [`docs/31`](docs/31-correspondance-des-textes.md) |
| 26. Textes déposés de l'Assemblée | charger par le numéro de dépôt que le rapport déclare, faute de lien DOLE | [`docs/32`](docs/32-textes-deposes-assemblee.md) |
| 27. Article écrit dans la citation | l'en-tête d'un alinéa cité désigne l'article qu'on écrit, non du droit existant | [`docs/33`](docs/33-article-ecrit-dans-la-citation.md) |
| 28. Hôte du code cité | un code nommé dans une citation ne déclare pas ce que le texte modifie | [`docs/34`](docs/34-hote-du-code-cite.md) |
| 29. `depose_sur` re-mesuré | une garde devenue fabricante d'unicité, et un numéro de subdivision lu en entier | [`docs/35`](docs/35-depose-sur-apres-la-reparation.md) |
| 30. Jeu d'annotation, prêt | 25 offsets sur 66 ne résolvaient plus, la XVIe législature n'avait pas de corps ; l'outillage de l'annotateur | [`docs/36`](docs/36-jeu-d-annotation-prepare.md) |
| 31. Dossiers de tout l'historique | le corpus ne suivait que le dossier d'origine ; 94 dossiers, 106 articles L motivés de plus | [`docs/37`](docs/37-dossiers-de-tout-l-historique.md) |
| 32. Lignées | un numéro n'est pas un article : 285 numéros réutilisés en 2016, 144 « passages motivants » qui expliquaient une autre disposition | [`docs/38`](docs/38-lignees.md) |
| 33. Cent verdicts d'agents | le jeu annoté par sept modèles pour 72 $ ; `motive` retrouvé au passage 29/72, rapport au Président sans arête 18/72 ; ce que cela ne vaut pas | [`docs/39`](docs/39-cent-verdicts-d-agents.md) |
| 34. États intermédiaires | 764 arêtes `porte_sur` que la loi promulguée n'a pas confirmées ; 31 « origines situées » qui n'en étaient pas | [`docs/40`](docs/40-etats-intermediaires.md) |
| 35. Deux tirages jugés à deux | `porte_sur` 34/35 et 18/20 ; `depose_sur` 7/15 — la composition est exacte, ce qu'elle prétend ne l'est pas ; 304 arêtes à cibles hors du code retirées | [`docs/41`](docs/41-deux-tirages-juges-par-des-agents.md) |
| 36. `depose_sur` par l'alinéa | trois voies — l'article nommé, l'alinéa du texte, l'article entier — mesurées à trois juges : 18/20, 7/10, 7/10 ; 1 155 arêtes | [`docs/42`](docs/42-depose-sur-par-l-alinea.md) |
| 37. `vise` et `porte_sur` corrigés | l'ancre, le code hôte, le numéro glissé, les quatre chiffres ; `vise` mesurée pour la première fois : 9/20 avant, 16/20 après | [`docs/43`](docs/43-vise-et-porte-sur-corriges.md) |
| 38. L'instruction qui gouverne l'alinéa | lue dans le texte à toutes ses occurrences, bornée par le paragraphe de tête ; `alinea` 17/20, `vise` 20/20 | [`docs/44`](docs/44-l-instruction-qui-gouverne-l-alinea.md) |
| 39. La pastille et l'incise | la « sous-instruction » n'en était pas une : la pastille du Sénat comptait pour un alinéa, et le deux-points de « les mots : « … » sont remplacés » cachait 22 604 cibles à `porte_sur` ; +1 269 internes jugées 20/20 ; `alinea` 16/20 puis 19/20 après deux gardes, jugée par des agents Sonnet | [`docs/45`](docs/45-la-pastille-et-l-incise.md) |
| 40. Le code hôte de l'instruction | le numéro nu sous un article multi-codes, rattaché par l'instruction qui le porte ou qui gouverne l'alinéa nommé ; `vise` +40, jugées 19/20 ; la fausse est un numéro glissé que la garde ne voit pas | [`docs/46`](docs/46-le-code-hote-de-l-instruction.md) |
| 41. Le numéro glissé par le contenu | l'article que le texte écrit sous un numéro que la loi a donné à un autre : 358 contredits, 234 résolus vers la version qui les contient, jugés 20/20 ; `vise` suit sauf plan propre (3/14 avant la garde) | [`docs/47`](docs/47-le-numero-glisse-par-le-contenu.md) |
| 42. Classement, harnais, accueil | le classement pèse par la rareté dans le fonds et sait se taire, mesuré 17/21 ; le harnais rejoue 700 verdicts contre la base et trouve dix fausses servies ; « signaler cette arête » sur chaque arête | [`docs/48`](docs/48-classement-harnais-accueil.md) |
| 43. Les dix du harnais, et la re-mesure | neuf réparées à la source : le bloc guillemeté et la date du texte pour `vise`, l'en-tête de la petite loi pour `porte_sur` (2 837 en-têtes rendus), la destination du passage et l'hôte de l'alinéa pour `resulte_de` ; le harnais voit les lignées, les voies, et reconnaît une arête dont l'identifiant a glissé ; re-mesuré par dix juges Sonnet 5 : `vise` 47/50, `resulte_de` 35/37, `porte_sur` 20/20 ; cinq verdicts humains contestés | [`docs/49`](docs/49-les-dix-du-harnais.md) |
| 44. Incréments DOLE, doublons, législatures XVI et XVII | les incréments DOLE et JORF enfin lus (`issu_de` 70/70) ; un même amendement de l'Assemblée publié deux fois, 6 112 copies fondues ; le projet de loi Hamon perdu par un saut de ligne ; 55 000 amendements de plus ; `vise` résolue par le contenu vers un article que la loi a créé, 10/10 ; re-mesuré : `vise` 64/70, `resulte_de` 52/57 | [`docs/50`](docs/50-increments-doublons-legislatures.md) |
| 45. `depose_sur` re-mesurée | sur les arêtes nouvelles : `alinea` 10/20, « VI (nouveau). – » n'était pas une borne ; `article_entier` 3/20, l'article qui réécrit une autre loi passait pour mono-cible ; réparées, 20/20 et 12/15 sur un second tirage disjoint ; la reconstruction reprend 15 minutes | [`docs/51`](docs/51-depose-sur-re-mesuree.md) |
| 46. Projets déposés et trait insécable | les 79 jeux de l'Assemblée sans texte l'étaient faute de lire `projets-pl` : 192 sur 192 ; les textes de l'Assemblée depuis 2017 écrivent « L. 123‑9 » avec un trait insécable, que `porte_sur` ne lisait pas — 866 arêtes internes de plus ; « L. 121-84-10-1 » lu « L121-84-1 » ; deux gardes `article_entier` ; `depose_sur` 1 156 → 1 836, mesurée 19/20, 13/15, 18/19, 20/20 | [`docs/52`](docs/52-projets-deposes-et-trait-insecable.md) |
| 47. Le trait insécable à la lecture | U+2011 ramené à « - » par les deux `texte_brut`, textes et rapports — 37 490 numéros lus dans les rapports au lieu de 34 988, `motive` +2 / −1 ; `vise` re-mesurée 20/20 et 1/1, `resulte_de` 18/20 : 0,8621, 0,7412, 0,8240 | [`docs/53`](docs/53-trait-insecable-a-la-lecture.md) |
| 48. Tableaux de concordance | l'article de la directive que l'article du code transpose, lu dans les annexes des études d'impact avec la position des blocs du PDF : 33 arêtes, 33/33, 35 articles en vigueur ; deux gardes `resulte_de` mesurées et abandonnées ; les fiches montrent la version écrite par la loi du dossier | [`docs/54`](docs/54-tableaux-de-concordance.md) |
| 49. Trois arbitrages | l'ancre d'une insertion n'est pas une cible de `porte_sur` — garde posée, 339 arêtes internes retirées, six anciens « justes » rendus sur le code hôte arbitrés faux ; on juge contre l'article du fonds, non le numéro écrit ; cinq verdicts humains contestés et « Mon Accompagnateur Rénov' » arbitrés justes, `resulte_de` 71/77, Wilson 0,8402 ; le harnais échoue de 8 arêtes au lieu de 15 | [`docs/55`](docs/55-trois-arbitrages.md) |
| 50. Tisseuse contre `vise`, et legi.py | l'extracteur de Tricoteuses sur les 199 arêtes jugées : l'article retrouvé 47 fois sur 163 justes, muet sur « ainsi rédigé » et la création, 3 de nos 34 fausses commises aussi, toutes de version ; legi.py non retenu, la décision écrite | [`docs/56`](docs/56-tisseuse-contre-vise.md) |

## D'où ça vient

La phase 0 a produit une note de cadrage, un rapport de vérification des
sources, un golden set de 25 articles chaînés à la main et un prototype du
résolveur ([`docs/00`](docs/00-note-de-cadrage.md) à
[`docs/05`](docs/05-generalisation.md)). Ce qu'elle a établi tient encore :

- **Un seul saut de concordance rétablit l'origine réelle.** 78 % du code semble
  issu d'ordonnances ; 74 % est d'origine législative dès qu'on remonte la
  recodification de 2016. C'est la thèse du projet, vérifiée sur son périmètre.
- **Atteindre le dossier n'est pas atteindre la motivation.** L'exposé des motifs
  ne nomme l'article que dans 6,4 % des cas, l'étude d'impact dans 24,8 % : c'est
  le plafond réel d'une restitution ancrée au grain de l'article, et pourquoi la
  restitution sépare ce qui porte sur l'article de ce qui porte sur le texte.
- **L'arête `resulte_de` ne peut pas s'attacher à la version en vigueur** sur un
  corpus recodifié ; elle s'attache à la version historique que l'amendement a
  écrite, et le graphe remonte les segments.
- **Le modèle est au grain du segment**, parce que 39,8 % des articles sont
  repris du texte déposé entre 10 % et 90 % — ni gouvernementaux ni
  parlementaires, mais les deux selon l'alinéa ([`docs/06`](docs/06-modele-de-donnees.md)).

Ce qu'elle a invalidé : le tableau synoptique du Sénat prévu comme premier
échelon n'existe pas ; DuraLex, deuxième échelon, est abandonné depuis 2019 ;
les ordonnances ne sont pas sans motivation — 90,6 % ont un rapport au
Président. Et une conclusion de la phase 0 était fausse : les amendements de
l'Assemblée de la XIVe législature sont bien en open data ; un 404 sur une URL
recopiée prouve que l'URL est mauvaise, jamais que la donnée est absente
([`docs/10`](docs/10-amendements-non-adoptes.md) § 4).

Les écarts pris sur la stack recommandée — SQLite plutôt que PostgreSQL, un
minuteur systemd plutôt que Dagster, des expressions régulières plutôt que lxml
— sont écrits au § 6 bis de la feuille de route, pour qu'ils soient des
décisions et non des dérives.

## Projets voisins

Aucun ne pose la même question. Chacun en tient un morceau. État vérifié le
26/09/2026 : dates des derniers commits et contenu des pages.

**En France, sur les mêmes sources.**

- **Tricoteuses** : « La loi sous git » publie les codes consolidés avec leur
  historique, et `tricoteuses-legifrance` lit LEGI, JORF, DOLE et KALI, dossiers
  législatifs compris (TypeScript, PostgreSQL, AGPL). Son module **Tisseuse**
  trouve les liens entre textes et extrait les instructions modificatives
  (`insert_after`, `replace`, `delete`, avec le rang d'occurrence). Il fait donc
  ce que DuraLex faisait, et il est maintenu. Passé sur les 199 arêtes `vise`
  jugées, il retrouve l'article 47 fois sur 163 justes : il ne modélise ni
  « est ainsi rédigé » ni la création d'un article, et ne choisit pas la
  version ([`docs/56`](docs/56-tisseuse-contre-vise.md)). Son grain de retouche
  et ses 538 tests unitaires sont à reprendre ; ce n'est pas un substitut.
- **legi.py** (Legilibre) : parse LEGI vers SQLite, commits en septembre 2026.
  Non retenu : il oriente les liens par l'attribut `sens`, qui n'est pas fiable,
  et ne découpe pas l'alinéa ([`docs/56`](docs/56-tisseuse-contre-vise.md) § 4).
- **La Fabrique de la loi** (Regards Citoyens, médialab) : la navette jusqu'à la
  promulgation, et le premier surlignage par étape. Le parser n'a pas de commit
  depuis mars 2022, le corpus s'arrête au 29/07/2024, et le certificat TLS du site
  est expiré.
- **Archéo Lex, DuraLex, SedLex** (Legilibre) : arrêtés en 2019, antérieurs au
  format LEGI d'octobre 2023. Ils servent de références de conception, pas de
  dépendances.

**Ailleurs, la même chaîne sous d'autres formes.**

- **legislation.gov.uk** rattache les *Explanatory Notes* du gouvernement à
  chaque section d'une loi en vigueur, avec ses versions. C'est le chaînage
  officiel le plus proche, sans les amendements et sans les renumérotations.
- **buzer.de** donne, pour chaque paragraphe d'une loi fédérale allemande, la
  loi qui l'a modifié en dernier. Il ne lie la *Begründung* du Bundestag qu'au
  niveau de la loi entière.
- **Legislative Influence Detector** (DSSG Chicago, KDD 2016) et **LobbyPlag**
  (RGPD, 2013) demandent qui a écrit le passage, par similarité de texte
  (Smith-Waterman) avec des lois-types ou des notes de lobbies, et non par le
  chaînage documentaire. Les deux sont arrêtés.
- **Parltrack** suit les procédures et les amendements du Parlement européen. Il
  est maintenu. C'est la couche en amont de la directive, que les considérants ne
  couvrent pas.

Ce qu'aucun ne fait : franchir une recodification à droit constant, tenir
l'amendement rejeté comme une provenance, et ne rien affirmer sans citation
résoluble au passage.

## Licence et attribution

Code sous [AGPL-3.0](LICENSE). Les données amont sont sous Licence Ouverte /
Etalab 2.0 et leur attribution est obligatoire — dans l'interface, dans l'API,
dans tout export. Une exception, documentée : le corps des rapports de
commission, qui n'est ni versionné ni rediffusé ([`ATTRIBUTION.md`](ATTRIBUTION.md)).
