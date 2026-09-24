# Quarante-sixième tranche — les projets déposés, et le trait d'union insécable

**Objet :** les 79 jeux d'amendements de l'Assemblée que `docs/50` § 8
laissait sans texte discuté, et les fausses `depose_sur` que `docs/51` § 7
laissait sans garde. Le premier chantier n'était pas un trou de corpus, et le
tirage qui l'a mesuré a trouvé derrière lui un défaut plus large : depuis
2017, l'Assemblée écrit ses numéros d'articles avec un trait d'union
insécable, que `porte_sur` ne lisait pas.
**Date : 24 septembre 2026.**
**Code :** `ingestion/textes_des_amendements.py`, `ingestion/textes_deposes.py`,
`ingestion/visees.py`, `ingestion/renvois.py`,
`ingestion/amendements_vers_resulte_de.py`.
**Données :** `precision-depose-sur-projets-{alinea,article-entier,visee}.tsv`,
`precision-depose-sur-trait-insecable.tsv`,
`precision-porte-sur-trait-insecable.tsv`.

---

## 1. Les 79 jeux : une forme d'identifiant non lue

`docs/50` § 8 attribuait les 79 jeux non appariés aux textes des XVIe et
XVIIe législatures « qui n'ont que des adresses `/dyn/` ». C'était faux : 50
des 79 sont de la XIVe. Ce sont les amendements **de commission**, déposés sur
le texte déposé — `B1015`, le projet de loi consommation n° 1015 —, que le
plan dérivé de `docs/50` a fait entrer. Ces textes étaient au corpus depuis
`docs/32` et chargés en base sous `14-projets-pl1015.asp`, 73 articles. Mais
l'appariement ne connaissait que les formes `propositions-pion`,
`ta-commission`, `rapports` et `dyn-…-textes` : jamais `projets-pl`.

Une ligne de plus dans `ASSEMBLEE` : **192 jeux sur 192** trouvent leur texte.
C'est la famille de défauts que `docs/32` § 3 décrivait déjà — une expression
qui ne reconnaît rien rend une liste vide, et une liste vide passe pour une
absence de donnée.

Effets de bord, vérifiés un à un : trois `resulte_de` quittent la base. Leurs
textes enfin appariés, la garde d'hôte de `docs/49` voit que l'alinéa nommé
est sous une instruction qui porte sur le code monétaire et financier
(L. 112-11, L. 533-12-7) : ce que ces amendements écrivent ne peut pas
expliquer un alinéa du nôtre. Le harnais rend exactement le même résultat
avant et après.

## 2. Les gardes de `docs/51`

**La réécriture qui écrit un voisin** est posée. Un « Rédiger ainsi cet
article » (ou « Supprimer », « Rétablir ») qui nomme des articles du code —
hors citation, ou en tête de l'article qu'il écrit (« « Art. L. 311-9-… ») —
sans nommer A ni un de ses numéros de renumérotation, écrit un voisin. Sur la
base d'alors, elle retire les deux fausses qui la dictaient et rien d'autre.

**Le lot n° 434 n'a pas de garde.** L'idée était de lire les mots que le
dispositif remplace (« remplacer les mots « les médecins » ») et d'exiger
qu'ils soient dans l'article du texte. Sous sa première forme, elle retirait
31 arêtes jugées justes : elle lisait aussi les mots que l'amendement
*insère*. Restreinte aux mots qui doivent préexister, et coupée au premier
« insérer » ou « ainsi rédigé », elle retirait encore 7 arêtes : la fausse du
lot, et six non jugées dont trois, lues, sont justes — une citation imbriquée,
une coquille de l'amendement (« agrée »), un « Rétablir … dans la rédaction
suivante » du Sénat. Une fausse pour trois justes : abandonnée.

## 3. Le tirage des projets déposés

Parmi les arêtes nouvelles, disjointes de toute arête d'avant et de toute
fiche jugée : 20 `alinea`, les 15 `article_entier`, 19 des 21 `visee`. Deux
juges Sonnet 5 par fiche, colonnes séparées ; un arbitre Opus 5 sur désaccord.

| voie | juge A | juge B | accord | arbitrage | verdict |
|---|---:|---:|---:|---:|---:|
| `alinea` | 19 | 19 | 20 | — | **19 / 20** |
| `article_entier` | 14 | 13 (1 douteux) | 14 | 1 → faux | **13 / 15** |
| `visee` | 18 | 18 | 19 | — | **18 / 19** |

**`alinea` : un numéro coupé dans un nombre.** L'amendement 211 cite l'alinéa 2
de l'article 5 bis A, qui écrit « Art. L. 121-84-10-1 ». Le graphe lisait
L121-84-1 — les avances aux opérateurs de téléphonie, sans rapport. `REFERENCE`
admettait trois nombres ; devant le quatrième, sa garde de fin refusait
« 121-84-10 », et l'expression revenait en arrière jusqu'à « 121-84-1 », en
coupant « 10 ». Les références admettent désormais quatre nombres et ne
s'arrêtent jamais au milieu d'un nombre. Le même motif, sans garde de fin,
était dans `visees.py`, `renvois.py` et deux expressions de
`amendements_vers_resulte_de.py`, qui lisaient L121-84-10 : réparés de même.

**`article_entier` : le paragraphe non reproduit.** « Supprimer cet
article » sur l'article 22 quinquies du projet n° 1357, qui en deuxième lecture
n'écrit que « I. – (Non modifié) » puis un II sur L. 334-9. L'arbitre a lu
le I dans le texte de première lecture : il modifie aussi L. 334-5. Le texte
qui ne reproduit pas un paragraphe cache ce qu'il réécrit, et « N ne réécrit
que A » ne se lit plus : la voie s'abstient désormais devant un paragraphe
« (Non modifié) ». Sur la base finale, 8 arêtes ; la seule jugée est la fausse.

**Les deux fausses sans garde.** L'amendement 8 au projet n° 3814 insère au
début de l'article 7 (une référence corrigée dans L. 623-24) une suppression
dans L. 621-6 : il écrit ailleurs que là où il est déposé. L'amendement 19 au
projet n° 1015 insère un « Art. L. 423-2 » nouveau et renumérote l'ancien
L. 423-2-1 : il nomme A pour en prendre le numéro. Chacune est seule de son
espèce ; aucune garde n'est posée sur une arête.

## 4. Le trait d'union insécable

La base reconstruite, `porte_sur` gagnait 874 arêtes internes et 26 000
externes. Un seul texte de la XVe législature donnait 3 051 références à la
nouvelle expression, **77** à l'ancienne. L'Assemblée écrit depuis 2017
« L. 123‑9‑1 » avec U+2011, le trait d'union insécable ; `REFERENCE` ne
connaissait que le trait d'union ordinaire, et des textes entiers n'avaient
presque aucune cible. En admettant U+2011 et le tiret demi-cadratin comme
séparateurs — l'un et l'autre dans les numéros, jamais après —, `porte_sur`
les voit enfin.

Deux tirages sur ce qui en est né, disjoints de toute arête d'avant :

| arête | juge A | juge B | accord | arbitrage | verdict |
|---|---:|---:|---:|---:|---:|
| `porte_sur` | 18 | 18 | 20 | — | **18 / 20** |
| `depose_sur` | 16 | 17 | 19 | 1 + 3 → juste | **20 / 20** |

**`porte_sur`, « L. 132-1 A ».** La lettre qui suit un numéro en fait partie,
et L132-1 A existe au fonds : l'article 14 d'un texte de la XVIIe législature en modifie le
troisième alinéa, et le graphe lisait L. 132-1. Les références portent
désormais leur lettre, sauf quand un nombre la suit (« L. 441-2 L. 441-3 »).

**`porte_sur`, l'ancre d'insertion — non réparée.** « Après l'article
L. 224‑54, il est inséré un article L. 224‑54‑2 » : le verbe suit L. 224-54,
qui devient une cible. Les deux juges la disent fausse — l'ancre n'est pas
modifiée —, et `visees.py` écarte déjà l'ancre depuis `docs/42`. La même
garde, posée ici, retirait **337** arêtes internes, et le harnais a nommé
six ancres jugées **justes** dans des tirages antérieurs (`declaree`,
`hote-derive`), dont celle de L. 112-7 (« après l'article L. 112-7, il est
inséré un article L. 112-7-1 »), et une `depose_sur` qui en dépendait. Deux
verdicts contre six, sur la même forme : c'est un désaccord de définition, et
la garde est retirée. L'arête reste dans la base, nommée par le harnais.

**`depose_sur`, les quatre arbitrées.** Une divergence ordinaire (L. 223-1,
jugée juste par l'arbitre) ; et trois arêtes que les deux juges disaient
fausses d'accord, soumises quand même à l'arbitre, parce que la question qui
les décide ne leur avait pas été posée. Le texte de commission écrit sous
« Art. L. 224‑114 » l'identité des sous-traitants et les informations du
contrat ; les juges ont constaté que les alinéas cités sont sous ce numéro,
et que l'arête dit L. 224-115. Mais la loi a rangé ce contenu sous
L. 224-115 — le L. 224-114 en vigueur est l'article sur le label, écrit par
l'amendement 85 —, et `porte_sur` l'a suivi par le contenu (`docs/47`).
L'arbitre, sur pièces : les trois amendements portaient sur l'actuel
L. 224-115, justes. **La consigne des juges ne dit pas contre quel numéro
juger quand le texte et le code divergent** ; c'est à préciser avant le
prochain tirage.

## 5. Les constantes

Chaque tirage compte les fausses qu'il a trouvées **avant** les réparations
qu'il a dictées. La convention de `docs/45` écarte les tirages qui ont dicté
une garde, parce que relus après elle ils surestiment ; lus avant, ils
sous-estiment, et c'est pourquoi ils sont réunis aux autres.

| constante | tirages | avant | après |
|---|---|---:|---:|
| `depose_sur` · `alinea` | 39 / 40 + 19 / 20 + 18 / 18 | 0,8712 | **0,9112** |
| `depose_sur` · `article_entier` | 18 / 22 + 13 / 15 | 0,6148 | **0,6886** |
| `depose_sur` · `visee` | 21 / 23 + 18 / 19 + 2 / 2 | 0,7320 | **0,8177** |
| `porte_sur` · déclarée | 74 / 75 + 16 / 18 | 0,9283 | **0,9094** |
| `porte_sur` · citation | 18 / 20 + 2 / 2 | 0,6996 | **0,7218** |

| en base | avant | après |
|---|---:|---:|
| jeux de l'Assemblée appariés | 113 / 192 | **192 / 192** |
| `porte_sur` internes | 6 967 | **7 833** |
| `depose_sur` | 1 156 | **1 836** (1 660 · 42 · 134) |
| `vise` | 632 | 663 |
| `resulte_de` | 448 | 446 |
| `motive` | 1 721 | 1 732 |

Au grain de l'article : 964 articles reliés à un article de texte (960),
799 remontant à un passage qui les motive (801), 142 à un amendement (143).
Les deux baisses sont des arêtes que la liste complète des cibles défait :
l'article 6 d'un texte de la XVe législature ne montrait qu'une partie de ses
cibles, les autres étant écrites au trait insécable ; il en montre quatre, et
le passage de rapport qui le commente ne se rattache plus à un article unique.

Le harnais échoue de **treize** arêtes : les dix de `docs/51` qui restaient,
les deux fausses sans garde du § 3, l'ancre du § 4. Aucune juste perdue.

## 6. Ce qui n'est pas fait

**L'ancre d'insertion**, pour la relecture humaine : six verdicts anciens la
disent juste, deux récents fausse. La garde est écrite et mesurée (§ 4) ; la
décision est de définition.

**La consigne des juges**, à compléter sur le numéro de référence quand le
texte en discussion et le code divergent (§ 4).

**Le lot n° 434** : toujours sans garde (§ 2).

**`vise` et `resulte_de`** gagnent 31 et perdent 2 arêtes par les mêmes
correctifs ; leurs constantes ne sont pas re-mesurées ici.
