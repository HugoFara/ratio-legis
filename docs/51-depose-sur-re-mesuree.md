# Quarante-cinquième tranche — `depose_sur` re-mesurée sur les arêtes nouvelles

**Objet :** la re-mesure que `docs/50` § 7 laissait ouverte. `depose_sur`
avait gagné 141 arêtes avec les législatures XVI et XVII, la loi Hamon
complète et onze dossiers nouveaux ; ses constantes par voie dataient de
`docs/45`. Le tirage a trouvé deux défauts, un par voie : 10 justes sur 20
par l'alinéa, 3 sur 20 par l'article entier. Les deux sont réparés à la
source, et un second tirage disjoint les mesure.
**Date : 24 septembre 2026.**
**Code :** `ingestion/textes_des_amendements.py`, `tools/dila/fonds.py`.
**Données :** `precision-depose-sur-legislatures-{alinea,article-entier,visee}.tsv`,
`precision-depose-sur-legislatures-{alinea,article-entier}-2.tsv`.

---

## 1. Le tirage

Les 141 arêtes nouvelles sont celles qu'une clef stable — chambre, texte,
numéro de l'amendement, article — ne retrouve pas dans la base d'avant
`docs/50` ; aucune arête d'avant n'a disparu. `--sauf` écarte par (numéro,
article) : quatre nouvelles partagent ce couple avec une ancienne et ne
pouvaient pas être tirées.

| voie | nouvelles | tirées |
|---|---:|---:|
| `alinea` | 90 | 20 |
| `article_entier` | 43 — la voie passait de 21 à 64 | 20 |
| `visee` | 8 | 8 |

Deux juges Sonnet 5 par fiche, colonnes séparées ; un arbitre Opus 5 sur
désaccord.

| voie | juge A | juge B | accord | arbitrage | verdict |
|---|---:|---:|---:|---:|---:|
| `alinea` | 10 | 10 | 19 | 1 → faux | **10 / 20** |
| `article_entier` | 3 | 3 | 20 | — | **3 / 20** |
| `visee` | 8 | 8 | 8 | — | **8 / 8** |

## 2. `alinea` : « VI (nouveau). – » n'était pas une borne

Neuf des dix fausses ont la même cause, et les deux juges l'ont trouvée
chacun de leur côté. L'instruction qui gouverne un alinéa court jusqu'à la
borne suivante — une autre instruction, ou un paragraphe romain
(`PARAGRAPHE`, `docs/44`). Le texte de commission écrit ses paragraphes
ajoutés en navette « VI (nouveau). – », « II bis (nouveau). – », et la
mention entre le numéro et le point faisait échouer l'expression. L'article
32 bis du texte de la loi Macron réécrit L. 141-1 à son III, puis ajoute des
VI, VII et VIII sur l'aide à domicile : pour le graphe, tout cela était
encore L. 141-1. Sept fausses de ce seul article, deux de l'article 12 du
même texte (un « II bis (nouveau) » après le II sur L. 113-3).

La borne admet désormais une mention entre parenthèses. Sur toutes les
fiches `depose_sur` jugées, anciennes et nouvelles : **165 justes gardées,
aucune retirée** ; 47 arêtes `alinea` quittent la base.

**Ce qui n'a pas été fait, et pourquoi.** La dixième fausse compte « III et
III bis. – (Non modifiés) » comme un alinéa, et l'amendement cite le
suivant. Ne plus compter ces lignes réparait l'arête — et décalait 29
autres arêtes non jugées. Les ancres des amendements, qui confirment ou
contredisent le compte indépendamment de toute fiche, l'ont démenti : 89
confirmant et 19 contredisant avec la règle, 92 et 16 sans elle ; 34
articles de texte à numérotation contredite au lieu de 11. L'Assemblée
compte ces lignes. L'arbitre, relisant l'article 13, conclut de même que
l'alinéa 29 est bien numéroté, et que l'amendement vise le III de l'article
du texte, une instruction sur la loi n° 71-1130 : l'arête est fausse pour
une autre raison que celle du juge B, et elle reste dans la base.

## 3. `article_entier` : l'article qui touche une autre loi

La voie repose sur une affirmation que `porte_sur` ne sait pas vérifier :
« l'article N du texte ne réécrit que A ». `porte_sur` relève des articles
de code. L'article 13 du projet Macron réécrit la loi n° 71-1130 sur les
avocats et complète L. 141-1 en passant ; l'article 17 ter réécrit
l'ordonnance du 10 septembre 1817 ; l'article 10 d'un texte de 2025 modifie
le code monétaire et financier et le code de commerce. Pour `porte_sur`,
chacun n'avait qu'une cible. Dix-sept fausses sur vingt.

La garde : l'article du texte ne doit nommer, hors citation, aucune autre
norme — loi, ordonnance, décret, ou code qui n'est pas le nôtre. Et quand le
dispositif ne porte pas sur l'article entier, il ne doit pas en nommer une
lui-même : « Dans le III de l'article L. 863-8 du code de la sécurité
sociale créé par le I de cet article » dit où il agit. Un « Rédiger ainsi
cet article » qui récrit l'article dans une autre loi reste rattaché : il
porte sur N, donc sur A, et un tirage antérieur l'avait jugé juste (L141-6 ← 8 du Sénat).

Sur toutes les fiches `article_entier` jugées : **les 17 fausses retirées,
les 18 justes gardées**. La voie passe de 64 à 30 arêtes. La garde est
choisie sur ce tirage ; un second tirage la mesure.

## 4. Le second tirage, disjoint

Parmi les arêtes d'après les gardes, jamais jugées : 20 `alinea` nouvelles,
et les 15 `article_entier` qui restaient.

| voie | juge A | juge B | accord | arbitrage | verdict |
|---|---:|---:|---:|---:|---:|
| `alinea` | 20 | 18 | 18 | 2 → juste | **20 / 20** |
| `article_entier` | 12 | 12 | 14 | 1 → faux | **12 / 15** |

**Les deux arbitrages `alinea`.** Deux amendements au projet de loi numérique citent
« l'alinéa 5 » de l'article 22 pour un mot qui est à l'alinéa 8. Le juge B
les dit faux par la lettre de la définition — « l'alinéa cité n'est pas
celui que le texte numérote ainsi ». L'arbitre les dit justes : les neuf
alinéas de l'article 22 ne touchent que L. 111-5, aucun numéro, juste ou
faux, ne pouvait mener ailleurs, et c'est ce que la clause protège. Ce que
l'arête affirme — l'amendement portait sur L. 111-5 — est vrai.

**Les trois fausses `article_entier`.** Deux « Rédiger ainsi cet article »
qui, sous l'article 18 réécrivant L. 311-8-1, écrivent un article
L. 311-9-… sur le démarchage : les deux juges les disent fausses, ce qui
nuance `docs/42` — la réécriture entière porte sur N, mais ce qu'elle met à
la place peut dire qu'elle vise un voisin. La troisième vient de la source :
l'Assemblée range sous le texte de commission n° 434 (bisphénol A) des
amendements d'une autre proposition de loi, sur les réseaux de soins — « le
III de l'article L. 863-8 du code de la sécurité sociale », les
« médecins ». Le fichier les donne tous pour `PIONANR5L14BTC0434`, et leur
PDF est sous `/14/amendements/0434/`. Le plan dérivé de `docs/50`, qui lie
à raison le n° 434 au dossier bisphénol, les a fait entrer avec lui.

## 5. Les constantes

La convention de `depose_sur` (`docs/45`) : la constante prend les tirages
disjoints faits après les gardes, non ceux qui les ont dictées.

| voie | tirages | avant | après |
|---|---|---:|---:|
| `alinea` | 19 / 20 (`docs/45`) + 20 / 20 | 0,7639 | **0,8712** |
| `article_entier` | 6 / 7 (`docs/42`) + 12 / 15 | 0,4869 | **0,6148** |
| `visee` | 13 / 15 (`docs/43`) + 8 / 8 | 0,6212 | **0,7320** |

| `depose_sur` en base | avant | après |
|---|---:|---:|
| `alinea` | 1 063 | 1 016 |
| `article_entier` | 64 | 30 |
| `visee` | 110 | 110 |
| **total** | 1 237 | **1 156** |

Le harnais rejoue les cinq fiches de cette tranche : il échoue désormais de
douze arêtes — les huit de `docs/50`, et les quatre fausses de ces tirages
qu'aucune garde n'attrape (l'alinéa 29 de l'article 13, les deux réécritures
d'un voisin, l'amendement du lot n° 434).

## 6. En chemin : l'étape des rapports au Président ne finissait plus

La lecture des incréments DILA de `docs/50` rejouait `tar --wildcards` par
lot de 400 motifs sur chacun des 744 incréments JORF, et la reconstruction
restait des dizaines de minutes à l'étape 2. Le profil a montré que
l'essentiel n'était pas là : 295 secondes sur 332 dans `tar` sur l'archive
globale, à comparer des milliers de motifs à chacun de ses millions de
membres — un coût antérieur à `docs/50`, que les incréments ont aggravé.
`fonds.py` liste désormais l'archive globale une fois, choisit les membres
par leur nom de fichier dans un ensemble, et extrait la liste exacte ; chaque
incrément est décompressé une seule fois, en parallèle, puis appliqué dans
l'ordre. `rapports_president.py` passe de 9 minutes à 2 min 17, ses 64
rapports identiques octet pour octet ; la reconstruction complète reprend
15 min 50.

Rejoué avec l'état courant du fonds, `titres_jorf.py` rend 27 intitulés de
plus — les textes de 2025 et 2026 — et 9 que la DILA a corrigés depuis
juillet 2025 (« LOI no 98-46 » devenu « LOI n° 98-46 ») ; aucun texte perdu.
Le plan versionné `titres-jorf.tsv`, qui ne se régénère que s'il manque, est
remplacé.



## 7. Ce qui n'est pas fait

**Le lot n° 434** et ses semblables : un amendement que la source range sous
un autre texte que le sien. Six des 51 amendements du lot parlent de
réseaux de soins ; aucune garde ne les sépare, et le phénomène n'est pas
compté ailleurs.

**La réécriture entière qui vise un voisin.** Les deux fausses du second
tirage appellent une garde — le dispositif écrit « Art. L. X » avec un X
qui n'est pas A —, qui n'est pas posée : elle se choisirait sur les deux
arêtes qui la dictent.

**La version de l'article montrée au juge.** L'arbitre relève que la fiche
affiche le L. 111-5 d'aujourd'hui, non celui que le texte de 2016 écrivait
sous ce numéro. Le jugement n'en dépendait pas ici ; la question des
lignées (`docs/38`) se pose à toute fiche qui montre « l'article du fonds ».
