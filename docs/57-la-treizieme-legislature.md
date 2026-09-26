# Cinquante-et-unième tranche — la XIIIe législature, et trois gardes

**Objet :** charger les amendements de séance de la XIIIe législature
(2007-2012), que l'Assemblée n'a jamais publiés en open data ; mesurer ce
qu'ils ajoutent au graphe ; réparer ce que la mesure a montré.
**Date : 24-26 septembre 2026.**
**Code :** `tools/an/moissonner_amendements_13.py`, `pipeline.sh` (étape 4),
`ingestion/an_vers_amendements.py`, `ingestion/visees.py`,
`ingestion/textes_des_amendements.py`.
**Données :** `data/corpus/plan-textes-an-13.tsv` ;
`precision-vise-xiiie.tsv`, `precision-vise-xiiie-2.tsv`,
`precision-vise-par-le-contenu-xiiie.tsv`, `precision-resulte-de-xiiie.tsv`,
`precision-depose-sur-xiiie-alinea.tsv`, `precision-depose-sur-xiiie-visee.tsv`,
`precision-depose-sur-xiiie-article-entier.tsv`.
**Juges :** deux Sonnet 5 par fiche, colonnes séparées ; arbitre Opus 5.5 sur
désaccord, colonne `verdict_ter` puis report en `verdict`, avec le verdict
remplacé cité.

---

## 1. La récolte

Le site de l'Assemblée sert encore les pages d'amendement de la XIIIe, à
l'adresse `/13/amendements/<texte>/<texte><n°>.asp` (et `…S0001` pour la
seconde délibération) : Wayback n'est pas nécessaire. Le moissonneur énumère
les numéros de chaque texte du plan jusqu'à un trou, garde les pages dans
`travail/an/13/` et laisse un témoin par texte : une reconstruction relit le
cache sans réseau, une récolte interrompue reprend où elle s'est arrêtée — ce
qui a servi, la première s'étant arrêtée au 35e texte.

| | |
|---|---:|
| textes du plan | 91 (28 dossiers) |
| dont amendés en séance | 37 |
| pages d'amendement | 9 271 |
| illisibles, écartées et comptées | 27 |
| amendements chargés | **9 244** |
| premier signataire : Gouvernement / député résolu / non résolu | 459 / 8 403 / 382 |

Le signataire est un nom, non une référence : il est résolu parmi les
députés de la XIIIe du jeu Acteurs, et le groupe est celui du mandat à la
date de dépôt. Les 382 non résolus restent sans référence. L'adresse de la
page est gardée à l'ingestion : elle répond, et le § 4.3 exige une citation
résoluble.

## 2. Ce que la XIIIe ajoute

Avant les gardes du § 5, sur la base sans la XVe :

| | avant | après |
|---|---:|---:|
| amendements de l'Assemblée | 64 027 | 73 271 |
| articles en vigueur portant une tentative, trois voies | 256 | 281 |
| tentatives déclarées sur un article en vigueur | 357 | 409 |
| segments écrits par un amendement de l'Assemblée | 212 | 325 |
| articles dont un alinéa est tracé jusqu'à un amendement | 166 | 206 |
| articles L dont un passage motive l'existence | 787 | 791 |
| jeux d'amendements appariés à leur texte | 192 / 192 | 229 / 232 |

Trois jeux de la XIIIe ne trouvent pas leur texte ; ils ne sont pas
examinés ici.

## 3. Mesuré, avant réparation

Les arêtes nouvelles sont celles dont l'amendement est de la XIIIe — son
adresse le dit. Le tirage garde l'ordre de la clef SHA-256 des outils
`precision_*.py`, filtré sur cette adresse : il est reproductible.

| arête | nouvelles | n | juge A | juge B | désaccords | verdict | Wilson |
|---|---:|---:|---:|---:|---:|---:|---:|
| `vise` · déclarée | 145 | 20 | 15 (+1 douteuse) | 16 | 1 → juste | **16 / 20** | 0,5840 |
| `vise` · par le contenu | 2 | 2 | 2 | 2 | — | 2 / 2 | 0,3424 |
| `resulte_de` | 109 | 20 | 16 | 17 (+1 douteuse) | 2 → juste | **18 / 20** | 0,6990 |
| `depose_sur` · `alinea` | 303 | 20 | 19 | 19 | — | **19 / 20** | 0,7639 |
| `depose_sur` · `visee` | 17 | 17 | 16 (+1 douteuse) | 17 | 1 → juste | **17 / 17** | 0,8157 |
| `depose_sur` · `article_entier` | 6 | 6 | 6 | 6 | — | 6 / 6 | 0,6097 |

**Les arbitrages.**

- `vise` L112-2-1 ← 6226, rejeté : il rédige un L112-2-1 sur la mention
  AOC des vins, et la loi du dossier a créé L112-2-1 sur ce sujet, avec une
  portée différente. `vise` compte la tentative, non son adoption : juste.
- `resulte_de` L121-84-8 ← 244 et L121-84-4 ← 328, deux sous-amendements. Le
  juge A a posé qu'un sous-amendement qui ne réécrit qu'un fragment n'est pas
  l'auteur de l'alinéa quand le reste vient de l'amendement parent. La règle
  vaut pour 349 rect. (§ 4), qui n'insère qu'une incise de huit mots. Elle ne
  vaut pas ici : 244 écrit la première phrase, substance de l'alinéa ; 328
  en écrit la structure (« La poursuite à titre onéreux de la fourniture de
  services… comprenant une période initiale de gratuité »), et l'alinéa en
  vigueur la suit, non celle de 183. Justes.
- `depose_sur` L311-14 ← 17 : au dépôt, L311-14 est la version de 1993, dont
  l'amendement abroge le dernier alinéa. Juste — mais la base met sous le
  même article la version de 2011, qui est l'ancien L311-17 (§ 6).

## 4. Ce que les fausses disent

**`vise`, quatre fausses d'une seule cause : l'article additionnel qui
numérote lui-même.** Trois amendements de 2008 (198, 199, 214) insèrent
chacun « Art. L. 121-84-4 » après l'article 7 du projet, avec trois
contenus ; la loi a mis sous ce numéro un quatrième texte, et les leurs sous
L121-84-7, L121-84-9, ou nulle part. L'amendement 6451 de 2010 crée
« Art. L. 112-2-1 », devenu le 7° de L115-16. Aucun n'était corroboré par
le contenu ; aucun n'était non plus résolu vers un autre article — deux
candidats trop proches (0,68 et 0,62) ou aucun au seuil. Ils tombaient dans
« l'autre rédaction » de `docs/49`, qui garde le numéro parce qu'il est
celui du plan du texte. Celui d'un article additionnel n'est que le sien.

**`depose_sur` · `alinea`, une fausse : « E (nouveau). – ».** `MARQUE_DE_TETE`
ne reconnaissait pas la mention de navette entre la lettre et le point :
la ligne qui ouvre l'instruction insérant L311-10-1 se recollait à
l'alinéa 11, qui est L311-10. `PARAGRAPHE` la reconnaissait depuis
`docs/51` pour les chiffres romains ; `MARQUE_DE_TETE`, qui décide du
recollage, ni pour les romains ni pour les lettres.

**`resulte_de`, deux fausses, sans garde.** 349 rect. n'insère qu'une incise
dans un alinéa du texte initial ; 236 supprime un plafond dans l'alinéa de
l'amendement 42, que la fiche fait résulter de 236. Ce sont les familles
« alinéa attribué au mauvais amendement du dossier » de `docs/55` § 4, dont
`docs/54` § 1 a montré qu'aucune règle simple ne les sépare des justes.

## 5. Les gardes

1. **`vise` : l'article additionnel que rien ne corrobore n'est pas
   rattaché** (`visees.py`). Quand un amendement déposé comme article
   additionnel rédige « Art. L. X. – … » en vingt mots au moins, et que la
   version que la loi a mise sous L. X ne contient pas cet alinéa, l'arête
   n'est pas posée. Sous vingt mots, l'alinéa ne suffit pas à contredire :
   L112-2-1 ← 6226, jugée juste, n'en a que neuf. 47 arêtes écartées dans
   la base finale, XVe comprise.
2. **`MARQUE_DE_TETE` admet la mention de navette**, comme `PARAGRAPHE` :
   « E (nouveau). – », « II (nouveau). – », « A bis (nouveau). – ».
3. **`ARTICLE_ADDITIONNEL` admet l'apostrophe typographique.** « Après
   l’article 7 » n'était pas un article additionnel : 45 subdivisions se
   lisaient comme l'article 7 du texte. Trouvé en vérifiant la garde 1.

**Le harnais**, sur la base reconstruite :

| fiche | avant | après |
|---|---|---|
| `vise` XIIIe | 16 justes, 4 fausses en base | 16 tenues, **4 absentes** |
| `depose_sur` · `alinea` XIIIe | 19 justes, 1 fausse en base | 19 tenues, **1 absente** |
| `depose_sur` · `visee`, `article_entier` XIIIe | 23 justes | 23 tenues |
| toutes fiches | 61 perdues | 61 perdues |
| fausses présentes | 8 | 10 : les 8 d'avant, et les 2 `resulte_de` du § 4 |

**`vise` re-mesurée sur un tirage disjoint.** La garde a été choisie sur les
quatre fausses du premier tirage ; elle ne se juge pas sur lui. Vingt arêtes
parmi les 131 que la XIIIe garde, hors des vingt premières : **20 / 20**
pour les deux juges, Wilson **0,8389**.

Les constantes du code ne changent pas. Réunies aux mesures d'avant, elles
monteraient : `resulte_de` 89 / 97, Wilson 0,8456 (0,8402 aujourd'hui) ;
`alinea` 95 / 98, 0,9138 (0,9112) ; `visee` 58 / 61, 0,8651 (0,8177). La XVe
est entrée en base pendant cette tranche (§ 7) et ses arêtes ne sont pas
mesurées : c'est sur la population qui la comprend que les constantes se
re-mesurent.

## 6. Essayé, retiré : la lignée qui arrive d'un autre numéro

LEGI enregistre « l'article L. 311-17 devient l'article L. 311-14 » comme une
version MODIFIE de L311-14 : la disposition de 1993 et celle de 2011 font
une seule lignée, alors que la scission de `docs/38` ne coupe qu'après une
abrogation. Une réécriture sur place (« est ainsi rédigé ») est aussi une
modification ; ce qui distingue l'arrivée est que le texte nouveau vient
d'un autre numéro, fermé le jour où la version s'ouvre.

Mesuré sur les 490 modifications à moins de 0,5 de la version d'avant
(Jaccard des mots de quatre lettres, `similarite`) : la similarité à une
source fermée le même jour se regroupe à 0,7 et plus, la similarité à la
version d'avant sous 0,2 ; **75 versions sont dans les deux**. La règle
— couper quand les deux tiennent — a donné 87 lignées nouvelles.

Elle a été retirée après le harnais : 19 arêtes jugées changeaient de
lignée, et deux dans le mauvais sens. `Resolveur.du_dossier` prend d'abord
la lignée qu'un texte du dossier a écrite ; quand la loi qui renumérote est
celle du dossier de l'amendement, c'est la lignée d'arrivée — l'amendement
de 2010 sur L311-14 passait à la disposition de 2011, et `depose_sur`
L311-34 ← 321, jugée juste, disparaissait. La scission demande que le
résolveur sache, pour un amendement, quelle lignée le numéro désigne à sa
date quand le dossier en a écrit une autre. C'est une tranche à part.

## 7. La XVe

Pendant la reconstruction, le serveur de l'Assemblée a servi l'archive de
la XVe en entier (619 Mo, `unzip -t` passé) : **42 400 amendements**, 115 671
pour l'Assemblée. L'échec est aléatoire, requête par requête, et non lié à
la position dans le fichier : une plage de 4 Mo à 50 Mo passait quand une
autre à 19 Mo échouait. Un téléchargement par plages courtes, chacune
reprise jusqu'à être entière, avançait régulièrement ; il n'a pas servi.

Les chiffres des §§ 2 à 5 ne comptent pas la XVe : les tirages sont filtrés
sur l'adresse des pages de la XIIIe, et le § 2 est lu avant son arrivée. Le
harnais du § 5, lui, a tourné sur la base qui la contient.

## 8. Ce qui n'est pas fait

- les arêtes de la XVe ne sont pas mesurées ;
- les trois jeux de la XIIIe sans texte apparié ne sont pas examinés ;
- la scission des lignées arrivées d'un autre numéro (§ 6) ;
- les deux `resulte_de` fausses du § 4 restent en base ;
- les constantes ne sont pas re-mesurées sur la population entière.
