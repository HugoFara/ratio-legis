# Quarante-neuvième tranche — trois arbitrages

**Objet :** trancher les trois questions que les tranches précédentes
laissaient « à la relecture humaine » sans qu'aucune demande de lecture du
texte y réponde mieux qu'un arbitrage sur pièces : l'ancre d'une insertion,
le numéro contre lequel juger, les verdicts contestés de `resulte_de`. La
quatrième, la validation des 100 articles du jeu d'annotation, reste une
relecture à la main et n'est pas touchée.
**Date : 24 septembre 2026.**
**Arbitre :** Opus 5.5, à la demande de l'auteur ; chaque verdict réécrit
porte `opus-arbitre (arbitrage)` et cite le verdict qu'il remplace.
**Code :** `ingestion/textes_deposes.py`, `ingestion/amendements_vers_resulte_de.py`,
`tools/mesures/juger.py`, `restitution/api.py`, `restitution/tentatives.py`.
**Données :** `precision-porte-sur-declaree.tsv`, `precision-porte-sur-hote-derive.tsv`,
`precision-resulte-de.tsv`, `precision-resulte-de-tirage-2.tsv`,
`precision-resulte-de-tirage-3.tsv`, `precision-resulte-de-legislatures.tsv`.

---

## 1. L'ancre d'une insertion n'est pas une cible

**La question** (`docs/52` § 4). « Après l'article L. 224-54, il est inséré
un article L. 224-54-2 » : `porte_sur` relie-t-elle l'article du texte à
L. 224-54 ? Deux juges récents disaient non ; six verdicts plus anciens
disaient oui sur la même forme.

**L'arbitrage : non.** Trois raisons, dont aucune n'est nouvelle :

- la définition écrite de `porte_sur` (`juger.py`) est « l'article du texte
  **modifie** l'article du code », fausse « si le texte ne fait que citer
  A » — et l'ancre n'est modifiée en rien ;
- `vise` écarte l'ancre depuis `docs/42`, sur trois verdicts sur trois ; deux
  arêtes qui disent la même chose — l'amendement, le texte touchent cet
  article — ne peuvent pas avoir deux définitions ;
- les six « justes » ne répondaient pas à cette question. Quatre viennent de
  la fiche `hote-derive` de `docs/34` § 3, tirée pour savoir si le **code
  hôte** était le bon — consommation ou propriété intellectuelle, commerce,
  construction — : le code l'était. Deux viennent de la fiche `declaree` de
  la même tranche, sans commentaire. Aucune des six n'a été jugée sur la
  modification.

| fiche | clef | article | forme |
|---|---|---|---|
| `declaree` | `00c07db7` | L511-2 | après l'article, un article inséré |
| `declaree` | `00dab10d` | L512-20 | après l'article, un article inséré |
| `hote-derive` | `01e5b004` | L112-7 | après l'article, un article inséré |
| `hote-derive` | `03d353f7` | L121-15-3 | après l'article, un article inséré |
| `hote-derive` | `0eb94767` | L121-15-3 | après l'article, un article inséré |
| `hote-derive` | `14436faa` | L222-16 | **avant** l'article, un intitulé de section |

La sixième n'était pas nommée par `docs/52` : c'est le harnais qui l'a
trouvée, une fois la garde posée. Les six sont arbitrées fausses.

**La garde** est celle de `visees.py` : une référence précédée de « après
l'article », « avant l'article », « à la suite de l'article » n'est pas une
cible (`est_une_cible`). Elle vaut aussi pour les instructions que
`textes_des_amendements.py` lit par la même fonction.

| en base | avant | après |
|---|---:|---:|
| `porte_sur` | 128 723 | 123 862 |
| dont internes | 7 833 | **7 494** |
| `depose_sur` | 1 836 (1 660 · 42 · 134) | 1 835 (1 659 · 43 · 133) |
| `motive` | 1 733 | 1 727 |
| articles reliés à un article de texte | 964 | 964 |
| articles remontant à un passage qui les motive | 800 | 799 |

Aucun article ne perd son lien au texte : l'article inséré, qui est la vraie
cible, le porte. Les `motive` retirées passaient par l'ancre — le passage de
rapport qui commente l'article 19 quater allait à L. 121-116 et L. 121-118
parce que le texte insérait après eux.

**Une juste perdue, par construction.** L'amendement 334 (Assemblée, XVIe
législature) modifie lui-même L. 132-2 — il en double l'amende — sous
l'article 9 du texte, qui n'insère qu'après L. 132-2. La voie `visee` de
`depose_sur` exige que l'article nommé soit une cible de l'article du texte
(`docs/42`) ; il ne l'est plus. L'amendement garde son arête `vise` vers
L. 132-2, et la fiche de l'article le montre. Ce n'est pas une fausse : c'est
un trou, que la définition de `depose_sur` assume.

**La constante ne bouge pas.** Aucune des six n'appartient aux tirages réunis
de la voie déclarée (`docs/16`, `docs/41`, `docs/45`, `docs/49`, `docs/52` :
90 sur 93, Wilson 0,9094) ; la seule ancre qu'ils contenaient, L. 224-54, y
était déjà comptée fausse. La fiche `declaree` de `docs/34` passe de 20 sur 20
à 18 sur 20 ; aucune constante ne s'en sert.

## 2. Contre quel numéro juger

**La question** (`docs/52` § 4). Le texte de commission écrit un passage sous
« Art. L. 224-114 » ; la loi l'a rangé sous L. 224-115, et l'arête dit
L. 224-115. Deux juges ont dit faux parce que le numéro ne concordait pas ;
l'arbitre a dit juste parce que le contenu concordait.

**L'arbitrage : contre l'article du fonds.** Une arête désigne une lignée de
LEGI, non un numéro écrit ; c'est ce que la restitution montre, et c'est ce
que `docs/47` résout quand il suit un numéro glissé par le contenu. Le numéro
écrit est une pièce. La consigne, désormais dans `juger.py` et valable pour
toutes les fiches :

> Quand le texte en discussion, l'amendement ou le tableau écrivent un autre
> numéro que celui de l'article du fonds (renumérotation en séance, en navette
> ou par la recodification de 2016), on juge contre l'article du fonds : juste
> si le passage écrit sous l'autre numéro est celui que la loi a rangé sous
> cet article — la fiche montre la version que la loi du dossier a produite
> (`docs/54` § 2) —, faux si le contenu de l'article du fonds est sans
> rapport avec ce passage.

Les trois verdicts de `docs/52` rendus par l'arbitre y sont conformes ; aucun
verdict n'est réécrit à ce titre.

## 3. Les verdicts contestés de `resulte_de`

`resulte_de` n'avait pas de définition dans `juger.py`. Elle y est :
l'alinéa **descend** du passage que l'amendement a inséré ou réécrit — juste
même si la navette l'a retouché ensuite, faux s'il vient d'une autre
rédaction qui ne partage avec l'amendement que des mots, ou si la rédaction
de l'amendement n'a pas été retenue. C'est la ligne que `docs/21` traçait
déjà entre ses familles « rédaction non retenue » (fausse) et le reste.

**L121-91-1 ← 382 rect. bis, 516, 101, 167** (`docs/49` § 6) : **justes.**
Chacun des quatre amendements, adoptés, écrit en toutes lettres « Art.
L. 121-91-1. – Le fournisseur d'électricité et de gaz naturel est tenu
d'offrir gratuitement à tous ses clients la possibilité de payer ses factures
par mandat compte », l'alinéa jugé mot pour mot. Le verdict de `docs/21`
portait sur la fenêtre, prise alors dans le passage jumeau de la téléphonie
(L. 121-84-12) — la preuve était mal choisie, l'arête ne l'était pas ; la
preuve vient du bon passage depuis `docs/49`.

**L136-2 ← 624** : **juste.** L'amendement insère « Art. L. 136-1-1. – Les
dispositions de l'article L. 136-1 sont reproduites intégralement dans les
contrats de prestation de services auxquels elles s'appliquent » ; le texte
adopté par l'Assemblée le porte mot pour mot sous L. 136-2 ; le Sénat le met
au singulier. Un numéro renuméroté en séance (§ 2), une retouche
grammaticale : l'alinéa descend de l'amendement.

**L521-28 ← 18, « Mon Accompagnateur Rénov' »** (`docs/50` § 7) : **juste.**
L'agrément « Mon Accompagnateur Rénov' » est celui de l'article L. 232-3 du
code de l'énergie. Le tableau comparatif de la commission mixte paritaire
(rapport AN n° 1368, XVIIe législature) met en face le « II (nouveau) » de
L. 521-28 que l'amendement 18 a inséré et sa rédaction par le Sénat, qui
ajoute une durée et élargit les motifs de suspension. C'est le même
paragraphe, retouché ; les deux juges y avaient lu une formule passe-partout
partagée par deux agréments distincts, et il n'y en a qu'un.

Les cinq premiers étaient des verdicts humains ; ils sont réécrits sur demande de l'auteur, et le commentaire de chaque ligne cite
le verdict d'origine.

**La constante.** Les cinq verdicts de `docs/21` ne sont dans aucun tirage
réuni — `docs/21` a servi à concevoir les gardes. Celui de `docs/50` l'est :
les tirages réunis passent de 70 à **71 sur 77**, 92,2 % ponctuels, Wilson
**0,8402** (au lieu de 0,8240). Le seuil de 95 % n'est toujours pas atteint.

## 4. Le harnais

| | avant | après |
|---|---:|---:|
| arêtes jugées fausses dans la base | 15 | **8** |
| justes perdues, hors pertes anciennes | — | 1 (L132-2 ← 334, § 1) |

Les huit qui restent sont les quatre `depose_sur` sans garde de `docs/51` et
`docs/52`, et les quatre `resulte_de` sans garde de `docs/50` et `docs/53` —
deux formules administratives partagées par un passage destiné ailleurs, une
rédaction non retenue, un alinéa attribué au mauvais amendement du dossier —, dont `docs/54` § 1 a montré
qu'aucune règle simple ne les sépare des justes.

## 5. Ce qui n'est pas fait

**La validation des 100 articles du jeu d'annotation**, qui reste le bloquant
de la phase 0 et ne se délègue pas à un arbitre de même nature que les juges
qu'elle doit contrôler.

**Les arbitrages de cette tranche sont eux-mêmes des verdicts d'agent.** Ils
remplacent, pour cinq arêtes, des verdicts humains ; la règle des alinéas
retouchés en navette (§ 3) est une règle d'interprétation que l'arbitre a
fixée. Une relecture humaine peut les renverser : les pièces sont dans les
fiches.
