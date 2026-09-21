# Quarante-troisième tranche — les dix du harnais

**Objet :** les dix arêtes jugées fausses que le harnais de `docs/48` nommait
à chaque passage, réparées à la source — le producteur, non la fiche ; puis
la re-mesure des constantes de confiance sur la population d'après, par dix
juges, qui a dicté cinq réparations de plus et révélé que le harnais ne
reconnaissait pas une arête dont l'identifiant a glissé. Neuf sur dix ne sont
plus dans la base ; la dixième y est, avec quatre autres du même genre, et
ce sont les verdicts qui sont contestés, sur pièces.
**Date : 21 septembre 2026.**
**Code :** `ingestion/visees.py`, `ingestion/lignees.py`,
`ingestion/textes_deposes.py`, `ingestion/amendements_vers_resulte_de.py`,
`tools/mesures/rejouer.py`, `pipeline.sh`.

---

## 1. Les dix, et ce qu'elles avaient en commun

| famille | arête | la cause, une fois lue | sort |
|---|---|---|---|
| `vise` | L411-1 ← 12394 (Sénat) | le nom de code lu dans le texte inséré — « le présent code » de l'alinéa inséré au code de la mutualité — et non dans l'instruction | absente |
| `vise` | L522-5 ← 32859 | « du code de la consommation » lu dans la liste citée au p), sous « Le code des assurances est ainsi modifié » | absente |
| `vise` | L141-3 ← 26732 | le numéro résolu à la date de la loi (novembre 2016), après la recodification, alors que l'amendement est de novembre 2015 | vers la lignée de 2005 |
| `depose_sur` | L121-79-4 ← 342 | jugée fausse par la voie « article entier, cible unique » quand `porte_sur` ne connaissait qu'une cible à l'article 64 ; posée aujourd'hui par ses alinéas 6 et 7 | par une autre voie |
| `porte_sur` | L224-42-2 ← 21 A | « (CMP) Article 21 48 » n'était pas un en-tête ; l'article 48 entier tombait sous « Article 21 A (Suppression maintenue) » | absente |
| `porte_sur` | L141-1 ← 5 | même cause : la petite loi n° 211 n'avait qu'un en-tête reconnu, l'article 5 recevait le texte entier | absente |
| `resulte_de` | L115-16 ← 993 | le passage est écrit sous « Art. L. 116-1 » et recopie L. 115-16 pour Wallis-et-Futuna | absente |
| `resulte_de` | L122-14 ← 28 | écrit sous « L'article L. 121-79-4 est ainsi rédigé » ; la formule pénale est la même mot pour mot | absente |
| `resulte_de` | L121-49 ← 377 | « Substituer à l'alinéa 11 » de l'article 24 du texte, sous une instruction qui modifie un autre code | absente |
| `resulte_de` | L136-2 ← 624 | le verdict manuel de `docs/21` est contredit par le texte adopté par l'Assemblée : voir § 6 | **présente** |

`docs/48` § 3 en avait deviné deux ; les autres ont chacune demandé de lire
l'amendement, le texte et la fiche. Aucune n'était un cas isolé : chaque
cause, une fois nommée, touchait des dizaines d'arêtes non jugées, dans les
deux sens.

## 2. `vise`

**Le bloc guillemeté.** Ce qu'un dispositif met entre « » est le texte qu'il
insère, non l'instruction qui l'insère ; un code nommé là ne qualifie pas un
numéro écrit hors de ce bloc. Mais le bloc n'est pas un masque : un
amendement de l'Assemblée qui complète un article du projet met *tout* entre
guillemets — « V. – Le livre Ier du code de la consommation est ainsi
modifié : « 2° L'article L. 113-9 est abrogé » — et le code nommé en tête du
bloc gouverne ses numéros. La règle est donc de portée : un nom de code vaut
pour un numéro si le bloc qui contient le nom contient aussi le numéro, ou si
le nom n'est dans aucun bloc (`visees.Instruction`). Les blocs suivent la
convention de légistique : chaque alinéa inséré ouvre un guillemet, seul le
dernier le ferme — un « après un point ou un point-virgule continue le bloc,
tout autre en ouvre un. `textes_deposes` note que suivre la profondeur des
guillemets « ne mène nulle part » dans les textes en discussion ; c'est vrai
là où le début de ligne tranche, et les dispositifs n'ont pas de lignes.

Un premier masque brutal retirait 63 arêtes et en ajoutait 59 ; le modèle de
bloc en retire 53 et en ajoute 13. Les 53 sont toutes des homonymes d'un autre
code — monétaire et financier, action sociale, construction, urbanisme,
mutualité, assurances, éducation, tourisme — rattachés par un « présent
code » ou un nom de code lu dans le texte inséré. Les 13 sont du rappel
rendu : notre code, exclu jusque-là par un « code monétaire et financier »
cité dans un alinéa inséré.

**La date du texte.** `Resolveur.du_dossier` résolvait un numéro à la date de
la loi promulguée. Pour un amendement, c'est trop tard : « L. 141-3 du code
de la consommation est complété » déposé au Sénat en novembre 2015 sous un
dossier promulgué en novembre 2016 désigne l'article de 2005, abrogé par la
recodification de juillet 2016, non le L141-3 créé en 2024 — seule lignée
ouverte à la date de la loi. Le résolveur prend une date facultative ; `vise`
lui donne celle du texte discuté, lue dans son stade (« Texte de la
commission déposé le 28 octobre 2015 »), à défaut la plus ancienne du
dossier, à défaut la loi.

**Le contenu de l'article écrit.** Un amendement qui rédige « Art. L. N. – … »
sous un numéro que la loi a bien écrit passait ; l'amendement 4495 de 2013
réécrit tout l'article 1er selon son plan, met sous « Art. L. 423-17 » la
contestation devant le juge de l'exécution, et la loi a un L. 423-17 sur la
responsabilité pour manquement au code de commerce. Jugée fausse en
`docs/47`, elle revenait dès que le nom de code cité qui l'écartait par hasard
cessait de compter. La corroboration par le contenu de `textes_deposes` —
part des trigrammes du premier alinéa écrit que la version promulguée
contient — est portée à l'amendement, et la distribution sépare trois
familles :

| famille | exemple | part sous le numéro | meilleure autre | règle |
|---|---|---:|---:|---|
| le numéro a glissé | 4384 « Art. L. 121-109 » | 0,0 | 1,0 (L121-110) | le contenu désigne un autre article de la loi : non rattachée, comptée |
| le plan propre | 4495 « Art. L. 423-17 » | 0,0 | 0,17 | article du texte réécrit en entier, rien ne corrobore : non rattachée |
| l'autre rédaction | 3146 « Art. L. 121-104 » | 0,02 | 0,14 | un amendement rejeté propose une autre rédaction sous le numéro du texte : le numéro tient |

Un seuil absolu — celui de `porte_sur` — retirait 73 arêtes, dont toutes les
rédactions alternatives ; la règle relative en retire 33, dont L. 423-17
← 4495 et 16 dont le contenu désigne l'article voisin. Parmi ces 16, les
trois de 4384 avaient été jugées justes par le contenu de l'article voisin :
« le texte proposé pour l'Art. L. 121-105 est mot pour mot l'actuel
L121-106 ». C'est exactement ce que la résolution par le contenu poserait,
mesurée 20/20 sur `porte_sur` (`docs/47` § 4) — et jamais sur `vise`. Elle
n'est pas posée : 3532 (« Art. L. 121-104 », treize mots, 0,64 vers L121-87
qui n'a rien à voir) dit le risque. Trois justes deviennent perdues, et le
harnais le dit.

Bilan `vise` : 581 arêtes sur 455 amendements avant, 508 sur 405 après ;
harnais à zéro revenue, quatre perdues nommées.

## 3. `porte_sur` — l'en-tête de la petite loi

La petite loi du Sénat marque chaque article de sa lecture d'origine et le
renumérote : « (AN1) Article 6 8 », « (CMP) Article 21 48 », « Article
31 37 ». `ENTETE` n'admettait ni la marque ni le second numéro : **2 837
en-têtes de 131 textes n'étaient pas des en-têtes**, et leur contenu tombait
sous l'article précédent — le défaut que le commentaire du code nomme comme
le pire possible, parce qu'il produit un rattachement faux plutôt qu'une
absence. La petite loi n° 211 de 2015 n'avait qu'un article reconnu sur des
dizaines.

Lequel des deux numéros est l'article du texte ? Vérifié sur la proposition
de loi n° 130 de 2010 : les amendements sont déposés sur le **premier** —
« après l'article 26 » vise « (AN1) Article 26 31 », « Article 16, alinéa 7 »
vise « (AN1) Article 16 20 ». Le second est celui du texte définitif. La
lettre peut dépasser H — « Article 6 N » de la loi du 5 mars 2007 — et aller
à trois — « Article 3 bis AAA » ; elle est en majuscules quoi qu'il en soit du
reste, sans quoi « Article 5 et 6 » se lirait « article 5 et, renuméroté
6 ». Trois ordinaux manquaient (quinvicies, sexvicies, septvicies).

Il reste 244 lignes non reconnues, et ce sont des non-en-têtes : « (Article
56 de la loi) », « Article 1609 B du code général des impôts », un glyphe
turc.

Bilan : 2 202 mentions retirées, 4 205 ajoutées — les mêmes, sous le bon
article du texte — ; les internes dérivées passent de 6 613 à 6 702, les deux
fausses sont absentes, et aucune arête jugée juste de `porte_sur` n'est
perdue qui ne l'était déjà.

## 4. `resulte_de`

**La destination.** Le critère que l'auteur avait appliqué à la main, sans
qu'il fût écrit : l'article sous lequel l'amendement écrit le passage. Elle
se lit en tête du passage — « Art. L. 116-1. – » —, un intitulé de section
pouvant précéder, ou dans l'instruction qui l'introduit, à la dernière
référence hors guillemets, qui n'est pas une ancre, suivie d'un verbe
modificatif : « À la dernière phrase du premier alinéa de l'article
L. 330-1, après le mot : « principale » sont insérés les mots : « … » ». Un
passage destiné à L. 116-1 ne peut pas avoir écrit un alinéa de L. 115-16,
même s'il le recopie mot pour mot. Quand la loi a produit l'article
destinataire, c'est lui et nul autre ; sinon — article d'un autre code, ou
numéro que la navette a changé — le passage ne se rattache que s'il est
neuf : une fenêtre que le fonds portait déjà avant la loi, ailleurs, est une
formule, pas une écriture.

La garde temporelle seule — « ce que le fonds portait avant la loi,
l'amendement ne l'a pas écrit » — était juste et insuffisante : elle perdait
vingt arêtes jugées justes, toutes des « L'article L. 312-9 est ainsi
rédigé » qui reprennent l'ancien alinéa, et n'atteignait pas L. 121-49, dont
la formule est de la loi Hamon elle-même. Elle ne joue plus que sous une
destination que la loi n'a pas produite.

**Les numéros de l'Assemblée n'étaient pas lus.** « L. 116‑1 » avec le trait
d'union insécable échappait à `ARTICLE_CITE` ; `articles_nommes` rendait
vide sur tout amendement de l'Assemblée, donc sans contrainte. Lus, la règle
« cible non déclarée » bloquait les créations renumérotées — « Art.
L. 121-42 » codifié L121-47, jugée juste — parce qu'elle prenait toute
citation pour une déclaration. Nommer sa cible, c'est la faire suivre d'une
formule modificative : `articles_nommes` ne relève plus que cela. Les
fenêtres écartées à ce titre passent de 205 à 32.

**L'hôte de l'alinéa.** L'amendement 377 dit « Substituer à l'alinéa 11 les
deux alinéas suivants » et écrit « Art. L. 731-3 » — un article d'un autre
code, sous un article du texte qui modifie cet autre code. Rien dans le
dispositif ne le dit ; l'instruction du texte le sait, et `porte_sur` la
lit. L'arête se construit donc **après** `porte_sur` et `depose_sur` : le
script a deux temps, `--noeuds` à sa place d'avant et `--aretes` après
`textes_des_amendements`, et `pipeline.sh` les appelle ainsi. Sous un alinéa
gouverné par une instruction d'un autre code, un passage sans destination
produite par la loi ne se rattache pas — 995 passages, la plupart sans
fenêtre commune de toute façon. Une mention `non_resolue` n'y est pas « hors
du code » comme dans `visees` : la question est inverse.

Bilan : 308 arêtes avant, 293 après ; 26 retirées — trois jugées fausses,
aucune jugée juste, et des insertions au code des transports, de
l'environnement, de la santé publique, à la loi Hoguet —, 11 ajoutées, des
créations renumérotées que la cible non déclarée bloquait. Sur L224-43, le
rendu d'exemple passait de quatre amendements à trois : le 70 rect. du Sénat
était apparié par « de communications électroniques, au sens du 6° de
l'article L. 32 du code des postes » — une citation.

## 5. Le harnais

Deux choses qu'il ne savait pas, et qui faisaient d'une arête réparée une
fausse revenue.

**Un numéro n'est pas un article** (`docs/38`). La clef de `vise` et de
`porte_sur` est prise sur le numéro, et deux lignées peuvent le porter. Le
juge a vu la lignée, par la date de sa première version — « L141-3
(2024-11-15) » —, et c'est celle-là qu'il a jugée. Quand la base porte
l'arête vers l'autre lignée, c'est une autre arête, **vers une autre
lignée**, non jugée, comptée à part. Quatre aujourd'hui : L141-3, et trois
`porte_sur` jugées justes sur la lignée de 1993 que la base résout mieux —
un texte de 2010 vise le L332-6 de 2003.

**Une arête `depose_sur` jugée fausse l'est par sa voie.** `juger.py` le
dit : la voie fixe ce que le juge vérifie, et un « faux » sur la voie
`article_entier` — « N réécrit aussi d'autres articles » — ne dit rien de la
même arête établie par l'alinéa que le dispositif nomme. Une fausse portée
**par une autre voie** est comptée à part ; une juste reste juste tenue
quelle que soit la voie, parce que c'est l'affirmation qui a été validée.

**L'identifiant d'un amendement n'est pas une clef.** `amendement.id` est
attribué à l'insertion, dans l'ordre des fichiers du corpus ; quand le corpus
a grossi (`docs/37`), les identifiants ont glissé, et les fiches d'avant
disaient « perdue en bloc » — 143 arêtes `resulte_de` présentes et jugées
passaient pour perdues, et un tirage « disjoint » ne pouvait plus les tirer.
L'arête est désormais reconnue aussi par ce qui ne bouge pas : (segment,
chambre, dossier, numéro) pour `resulte_de`, (chambre, texte, numéro,
article) pour `depose_sur`. Les perdues tombent de 204 à 63, les justes
tenues montent de 455 à 596 — et quatre fausses de plus apparaissent, toutes
sur L121-91-1 (§ 6).

Rejoué sur la base du jour, au terme de la tranche : **103 faux absentes,
596 justes tenues, 63 perdues, 59 rejugées ailleurs, 6 vers une autre
lignée, 3 par une autre voie, 5 revenues** — les cinq du § 6.

## 6. Les verdicts contestés

L136-2 ← amendement 624 de l'Assemblée (n° 3067, adopté, après l'article 17
de la loi Hamon), jugée fausse à la main en `docs/21`. LEGI dit L136-2
**créé** par la loi 2014-344, article 35. L'amendement écrit : « Après
l'article L. 136-1, est inséré un article L. 136-1-1 : « Les dispositions de
l'article L. 136-1 sont reproduites intégralement dans les contrats de
prestation de services auxquels elles s'appliquent. » ». Le texte adopté par
l'Assemblée en première lecture (`14-ta-ta0176`) porte : « 2° Il est ajouté un
article L. 136-2 ainsi rédigé : « Art. L. 136-2. – Les dispositions de
l'article L. 136-1 sont reproduites intégralement dans les contrats de
prestation de services auxquels elles s'appliquent. » » — l'amendement mot
pour mot, renuméroté en séance ; le Sénat le réécrit ensuite au singulier,
et c'est la rédaction promulguée. L'alinéa de L136-2 résulte de l'amendement
624.

**L121-91-1 ← 382 rect. bis, 516, 101, 167** (Sénat, loi Hamon, tous
adoptés), jugées fausses à la main en `docs/21`, révélées par la clef stable
du § 5. Les quatre écrivent mot pour mot « Art. L. 121-91-1. – Le
fournisseur d'électricité et de gaz naturel est tenu d'offrir gratuitement
à tous ses clients la possibilité de payer ses factures par mandat compte »,
et LEGI dit L121-91-1 créé par la loi 2014-344 avec ce texte. La fenêtre
montrée au juge venait de l'autre passage du même amendement — « L. 121-84-12 »,
la téléphonie, même phrase —, et c'est la preuve qui a été jugée, non
l'arête ; la preuve vient désormais du passage destiné à l'article.

Ce sont des verdicts humains, le seul genre que le dépôt n'ait presque pas ;
ils ne sont pas retouchés ici, ni par une fiche de rejugement d'agent. Le
harnais échoue de cinq arêtes tant qu'un humain ne les a pas relues. Les
pièces sont ci-dessus.

## 7. Ce qui n'est pas fait

**La résolution par le contenu sur `vise`.** Seize arêtes dont le contenu
désigne un autre article de la loi, non posées, comptées ; dont les trois de
4384 jugées justes par ce raisonnement même. Un tirage de vingt, jugé, la
poserait avec sa confiance.

**Le plan propre hors glissement** de `docs/47` § 5 est fait par le § 2 ; les
124 non résolus de `porte_sur` ne le sont pas.

**Les doublons de l'Assemblée** : un même amendement chargé deux fois, sur le
texte déposé et sur le texte de commission (798 : ids 1121 et 8178), donne
deux arêtes pour une.

## 8. Mesuré

Protocole de `docs/45` § 5 : deux agents Sonnet 5 par fiche, colonnes
séparées, sans se lire ; un arbitre (Opus 5) sur les seuls désaccords. Les
tirages sont disjoints de tout ce qui avait été jugé, par la clef stable ;
les « nouvelles » sont les arêtes que la tranche a ajoutées. Deux juges ont
vu passer, dans les avis de modification du fichier partagé, les écritures de
l'autre colonne ; ils disent les avoir ignorées, et leurs verdicts coïncident
là où ils ont rendu avant comme après.

| arête | tirage | n | A | B | accord | arbitrage | verdict | Wilson |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `vise` | 4e, disjoint | 20 | 19 | 19 | 20 | — | 19 / 20 | 0,7639 |
| `vise` | les 11 nouvelles | 11 | 11 | 10 | 10 | 1 → faux | 10 / 11 | 0,6226 |
| `vise` | 5e, disjoint, après les gardes ci-dessous | 20 | 19 | 19 | 20 | — | 19 / 20 | 0,7639 |
| `vise` | **réunis, dédoublonnés** | 50 | | | | | **47 / 50** | **0,8378** |
| `resulte_de` | 4e, disjoint | 20 | 19 | 19 | 20 | — | 19 / 20 | 0,7639 |
| `resulte_de` | les 11 nouvelles (8 déjà dans le 4e) | 11 | 10 | 10 | 11 | — | 10 / 11 | 0,6226 |
| `resulte_de` | 5e : les 14 dernières, après les gardes | 14 | 14 | 13 | 13 | 1 → juste | 14 / 14 | 0,7847 |
| `resulte_de` | **réunis, dédoublonnés** | 37 | | | | | **35 / 37** | **0,8230** |
| `porte_sur` | parmi les 161 internes rendues par l'en-tête | 20 | 20 | 20 | 20 | — | 20 / 20 | 0,8389 |
| `porte_sur` | **quatre tirages réunis** (`docs/16`, `41`, `45`, ici) | 75 | | | | | **74 / 75** | **0,9283** |
| `depose_sur` | les 5 nouvelles | 5 | 5 | 5 | 5 | — | 5 / 5 | constantes par voie inchangées |

**Ce que les fausses ont dicté**, chacune une garde, posée avant le tirage
suivant :

- *`vise`, L217-9* — une lignée dont la seule version est mort-née (2022,
  fin avant début) : `Resolveur` la tenait pour ouverte de toujours, et
  `ecrits` comptait la version mort-née comme écrite par la loi. Les 127
  lignées sans période en vigueur sont hors du résolveur ; 10 `vise`, 17
  `porte_sur`, 35 `depose_sur`, 4 `motive` pointaient dessus.
- *`vise`, 17406 « artisan restaurateur »* — l'amendement écrit une section
  entière et numérote ses articles lui-même ; la loi a mis les métaux
  précieux sous L. 121-99. Une division écrite est un plan propre au même
  titre qu'un article du texte réécrit en entier (`DIVISION_ECRITE`). Le juge
  A l'avait dite juste par le numéro ; l'arbitre a suivi le juge B.
- *`vise`, 3794* — « Rédiger ainsi le premier alinéa : « I. – L'article
  L. 115-16 est ainsi modifié : » », la formule et rien après le deux-points :
  un chapeau, pas une cible (`CHAPEAU_VIDE`).
- *`resulte_de`, L121-83 ← 65* — « le 14° de l'article 28 de la même loi est
  ainsi rédigé » : l'hôte est une loi nommée plus haut dans le texte, que
  `HOTE` ne voyait pas (`LOI_IMPLICITE`).
- *`resulte_de`, L121-20-5 ← 1012* — « la loi n° 78-17 », citation partagée,
  sur un passage sans destination : la garde temporelle du § 4 joue désormais
  aussi sans destination. Elle a coûté sept justes jugées, toutes des
  fenêtres de formule ou de citation préexistantes — « La présente section
  est applicable aux consommateurs… », « au sens du 6° de l'article L. 32 » —
  et c'est ce que la règle dit.
- En chemin, deux défauts de `passages_inseres` antérieurs à la tranche :
  `MODIFICATIF` ignorait « est complété par » et « sont insérés » — « L'article
  L. 221-10 du code de la mutualité est complété par trois alinéas » passait
  pour du texte du nôtre —, et « dans sa rédaction issue de la loi n° 2013-672 »
  faisait de cette loi l'hôte du passage suivant (`LOI_CITEE`).

**Les constantes.** `vise` 0,8712 → **0,8378** (47/50), `resulte_de` 0,8933 →
**0,8230** (35/37), `porte_sur` 0,9039 → **0,9283** (74/75). Les deux
premières descendent : moins d'arêtes tirées que les 40 et 179 d'avant, sur
une population que les gardes d'avant ne mesurent plus, et une précision
ponctuelle qui ne bouge pas (94 %, 95 %). La population d'après les gardes
de cette section n'a de tirage à elle que le cinquième ; sur les 290 arêtes
`resulte_de` présentes, 281 portent un verdict.

**Rien de ceci n'est humain**, sauf les verdicts du § 6 — que je conteste.
