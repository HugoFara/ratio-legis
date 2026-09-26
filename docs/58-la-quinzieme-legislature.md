# Cinquante-deuxième tranche — la XVe législature, et quatre gardes

**Objet :** mesurer ce que les amendements de la XVe législature (2017-2022),
entrés en base le 26 septembre 2026 (`docs/57` § 7), ajoutent au graphe ;
réparer ce que la mesure a montré ; re-mesurer sur des tirages disjoints.
**Date : 26 septembre 2026.**
**Code :** `ingestion/textes_deposes.py`, `ingestion/textes_des_amendements.py`,
`tools/mesures/precision_porte_sur.py`.
**Données :** `precision-vise-xve.tsv`, `precision-vise-par-le-contenu-xve.tsv`,
`precision-resulte-de-xve.tsv`, `precision-depose-sur-xve-alinea.tsv`,
`precision-depose-sur-xve-visee.tsv`, `precision-depose-sur-xve-visee-2.tsv`,
`precision-depose-sur-xve-article-entier.tsv`,
`precision-depose-sur-xve-article-entier-2.tsv`,
`precision-porte-sur-declaree-contredite.tsv` ;
`precision-depose-sur-xiiie-alinea.tsv` ré-arbitrée (§ 5).
**Juges :** deux Sonnet 5 par fiche, colonnes séparées ; arbitre Opus 5.5 sur
désaccord et sur les douteuses.

---

## 1. La XVe en base

L'archive `Amendements_XV.json.zip` (619 Mo) est passée au pipeline le
26 septembre : **42 400 amendements**, 115 671 pour l'Assemblée, 148 870 en
tout. Les amendements de la XVe n'ont pas d'adresse en base ; ils se
reconnaissent par la clef (dossier, numéro, texte discuté) de l'extrait
`amendements_15.csv` — les 42 400 s'y retrouvent. Les arêtes `depose_sur` se
reconnaissent par leur texte (`assemblee/15-…`).

**5 030 amendements de la XVe n'ont pas de dispositif**, ni d'exposé : ce
sont pour l'essentiel des irrecevables, dont l'Assemblée ne publie pas le
texte. Ils ne peuvent entrer au graphe que par la subdivision où ils ont été
déposés — la voie `article_entier` « dispositif non lu, cible unique ».

## 2. Mesuré, avant réparation

| arête | nouvelles | n | juge A | juge B | désaccords | verdict | Wilson |
|---|---:|---:|---:|---:|---:|---:|---:|
| `vise` · déclarée | 328 | 20 | 20 | 20 | — | **20 / 20** | 0,8389 |
| `vise` · par le contenu | 1 | 1 | 1 | 1 | — | 1 / 1 | 0,2065 |
| `resulte_de` | 56 | 20 | 19 | 17 | 2 → juste | **19 / 20** | 0,7639 |
| `depose_sur` · `alinea` | 159 | 20 | 20 | 20 | — | **20 / 20** | 0,8389 |
| `depose_sur` · `visee` | 34 | 20 | 18 | 18 | — | **18 / 20** | 0,6990 |
| `depose_sur` · `article_entier` | 44 | 20 | 13 (+6 douteuses) | 13 (+6) | 6 → 4 faux, 2 justes | **15 / 20** | 0,5313 |

**Les arbitrages.**

- `resulte_de` L242-16 ← 29, deux segments. L'amendement écrivait pour
  L522-6 trois alinéas sur la publication des sanctions ; la navette les a
  mis sous L242-16, « par dérogation au premier alinéa de l'article
  L. 522-6 ». La version de 2016 de L242-16 ne les a pas, celle de 2020 les
  reprend presque mot pour mot : l'alinéa descend du passage de 29. Justes.
- `depose_sur` · `article_entier`, six irrecevables sans dispositif. Deux
  sont déposées sur un article du texte qui ne réécrit que l'article du
  fonds : justes. Quatre sont déposées sur l'article 5 bis de la proposition
  2743, qui crée « Art. L. 412-10. – Le nom et l'adresse du producteur de
  bière… » ; la loi a rangé ce texte sous L412-12, et l'arête pointait le
  L412-10 du fonds, les dénominations des denrées d'origine animale. Fausses,
  indépendamment du dispositif.

## 3. Les quatre défauts

1. **Le numéro que l'instruction déclare échappait au contenu.** `porte_sur`
   lit l'article du texte en deux passes : les cibles des instructions
   (« … est complétée par un article L. 412-10 ainsi rédigé »), puis les
   articles écrits (« Art. L. 412-10. – … »), dont le contenu est comparé à
   la version que la loi a produite sous ce numéro (`docs/47`). Un numéro
   relevé par la première passe était « déjà déclaré », et la seconde ne le
   comparait pas — alors que c'est la forme la plus courante de la création
   d'un article : 21 628 articles écrits sur 21 700 le sont aussi par
   l'instruction. Quatre `article_entier` fausses.
2. **« Rédiger ainsi cet article » vers un autre article.** La garde « la
   réécriture écrit un voisin » (`docs/42`) cherche les articles que le
   dispositif nomme, hors des citations. Or la réécriture est une citation :
   « Rédiger ainsi cet article : « Au début du deuxième alinéa de l'article
   L. 413-8 du code de la consommation… » » ne nommait rien. L'article 4 de
   la proposition 1786 ne créait que L412-8 ; l'amendement 107, adopté, le
   récrit vers L413-8.
3. **La chaîne de renumérotation reliait les frères.** La fermeture de
   `renumerote_de` montait vers les anciens numéros et redescendait dans la
   même récursion : L313-31 atteignait L313-30 par L312-9, que la
   recodification de 2016 a éclaté en L313-30 à L313-33. Deux amendements
   qui insèrent une instruction sur L313-31, et ne citent L313-30 qu'en
   renvoi, étaient déposés sur L313-30, que l'article 42 bis du texte
   réécrit.
4. **« Compléter l'article 5 par l'alinéa suivant »** n'était pas un ajout
   en fin d'article ; seul « Compléter cet article » l'était. L'amendement 63
   y ajoutait un 2° sur L221-17, L224-30 et L224-54 à un article qui ne
   touchait que L131-4 — trouvé au second tirage (§ 4).

S'y ajoute un défaut de l'outil : les fiches `porte_sur` montraient le
premier état de la lignée, non la version que la loi du dossier a produite
(`etat_pour_le_juge`, écrite pour `docs/51` § 7, n'y était pas appelée), et
une colonne vide pour un article sorti des articles courants. Les deux juges
ont dû relire la base pour ne pas conclure à tort ; l'outil est corrigé.

**Les réparations.**

1. `porte_sur` compare le contenu aussi quand l'instruction déclare le
   numéro, et **résout vers l'article que le contenu désigne quand il en
   désigne un** — 79 déclarés contredits, 32 résolus. Quand le contenu n'est
   nulle part (l'article a été réécrit en navette), le numéro déclaré tient.
   La première version rendait ces 47 autres non résolues : le harnais y
   perdait des arêtes jugées justes (L113-7, L111-7-3, L313-11) ; elle a été
   retirée.
2. La garde du voisin lit aussi les articles que la réécriture désigne avec
   leur code (`NOMME_AVEC_LE_CODE`).
3. La chaîne est l'union des ancêtres et des descendants, chacun par sa
   fermeture : plus de frères.
4. `AJOUT_EN_FIN` admet « Compléter l'article 5 / premier / unique ».

## 4. Re-mesuré

Sur des tirages disjoints des premiers, dans la population réparée :

| arête | n | juge A | juge B | verdict | Wilson |
|---|---:|---:|---:|---:|---:|
| `porte_sur` · déclarée, résolue par le contenu | 20 parmi 32 | 20 | 20 | **20 / 20** | 0,8389 |
| `depose_sur` · `visee`, XVe | 13 (toutes) | 13 | 13 | **13 / 13** | 0,7719 |
| `depose_sur` · `article_entier`, XVe | 20 parmi 28 | 19 | 19 | **19 / 20** | 0,7639 |

La fausse du second tirage `article_entier` est celle du défaut 4, réparé
après. Les six irrecevables de l'article 5 bis y sont justes : elles pointent
L412-12.

**Le harnais**, sur la base finale :

| | |
|---|---:|
| justes tenues | 1 095 |
| perdues | 61 — autant qu'avant la XIIIe |
| fausses présentes | 11 : les 8 d'avant `docs/57`, et trois `resulte_de` d'une même famille, sans garde — l'incise dans un alinéa écrit ailleurs (L331-3-1 et L121-84-6 de la XIIIe, L441-3 de la XVe) |
| fausses de la XIIIe et de la XVe que les gardes visaient | toutes absentes |

## 5. Trois verdicts de la XIIIe rendus contre les juges

La réparation 1 a déplacé trois arêtes `depose_sur` · `alinea` de la XIIIe
jugées justes par les deux juges : L311-47 ← 11 et 263 rect., L121-84-3 ←
11. Le texte y écrit, sous « Art. L. 311-47 », « Le prêteur qui accorde un
crédit sans communiquer à l'emprunteur les informations précontractuelles… »,
que la loi a promulgué sous L311-48 — son L311-47 est le dépassement prolongé
d'un découvert ; et sous « Art. L. 121-84-3 » ce qui est devenu L121-84-5 —
son L121-84-3 est la durée minimale d'engagement. Les juges avaient jugé par
le numéro écrit ; on juge contre l'article du fonds (`docs/55` § 2). Les
trois sont arbitrées fausses, et la base rattache désormais ces amendements
aux articles que le contenu désigne.

La mesure `alinea` de `docs/57` § 3 se lit donc **16 / 20** (Wilson 0,5840),
non 19 / 20 : les trois fausses de plus sont celles que la réparation 1
écarte.

## 6. Ce que la XVe ajoute

Sur la base finale, XIIIe et XVe comprises, comparée à celle d'avant la
XIIIe :

| | avant la XIIIe | après la XVe |
|---|---:|---:|
| amendements, deux chambres | 97 226 | 148 870 |
| articles en vigueur portant une tentative, trois voies | 256 | 321 |
| tentatives déclarées sur un article en vigueur | 357 | 670 |
| irrecevabilités lues (dont article 40) | 11 800 (3 097) | 16 643 (4 660) |
| arêtes `vise` (par le numéro, par le contenu) | 663 (652, 11) | 1 105 (1 091, 14) |
| arêtes `depose_sur` | 1 835 | 2 405 |
| arêtes `resulte_de` | 446 | 645 |
| `porte_sur` internes (dont résolues par le contenu) | 7 494 (236) | 7 645 (268) |

## 7. Les constantes

Elles ne changent pas. Réunies à celles d'avant, les mesures de la XIIIe et
de la XVe les feraient monter pour `alinea` (112 / 118 avec les 76 / 78 d'avant,
les 20 / 20 de la XVe et les 16 / 20 de la XIIIe), `visee` et `resulte_de`, et descendre pour
`article_entier`. Mais chaque tirage mesure une population réparée à un
moment différent ; la réunion demande un tirage unique sur la base finale,
toutes législatures ensemble. C'est la prochaine mesure.

## 8. Ce qui n'est pas fait

- *(tranché en `docs/59` § 1 : la retouche compte, les trois sont justes)* la famille « incise dans un alinéa écrit ailleurs » de `resulte_de`, trois
  fausses en base, sans garde ;
- les constantes, sur un tirage unique de la base finale (§ 7) ;
- la scission des lignées arrivées d'un autre numéro (`docs/57` § 6) ;
- les 5 030 amendements sans dispositif ne se jugent que par leur
  subdivision.
