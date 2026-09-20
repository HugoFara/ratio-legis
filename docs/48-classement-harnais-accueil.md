# Quarante-deuxième tranche — le classement qui sait se taire, le harnais, l'accueil

**Objet :** la première revue extérieure du dépôt public, et ce qu'elle a fait
faire. Quatre choses : réparer le classement des considérants, remonter dans
le README le chiffre qui compte, rejouer les fiches jugées contre la base,
et donner au lecteur un moyen de dire qu'une arête est fausse.
**Date : 21 septembre 2026.**
**Code :** `restitution/proximite.py`, `restitution/signalement.py`,
`restitution/index_des_exemples.py`, `tools/mesures/rejouer.py`,
`tools/mesures/rappel_classement.py`, `.github/ISSUE_TEMPLATE/`.
**Données :** `rappel-classement-considerants.tsv`.

---

## 1. Ce que la revue disait, et ce qui en est

Un relecteur extérieur a lu le site et le dépôt. Ses constats, vérifiés un à
un contre la base avant d'y toucher :

| constat | vérifié |
|---|---|
| Le classement des considérants de L112-1-1 est faux : (55), (30), (42), avec « indique, égard, pendant, exception » pour termes communs | **exact** |
| La cause est la rareté calculée dans le document ; la rareté sur le fonds corrigerait | **faux** — recalculée sur les 7 674 considérants, elle rend (42), (30), (55) : les mêmes. Aucun des 60 considérants de la directive 2019/2161 ne parle de réduction de prix ; la règle vient de son article 2, sans motif. La bonne réponse est de ne rien classer |
| Le classement est le seul composant dont la précision n'est pas mesurée | **inexact** — `docs/39` § 2 le mesure sur les rapports au Président du jeu d'annotation, rang 1 neuf fois sur 18. Mais pas sur les considérants, et 18 est petit |
| « `motive` retrouvé au passage 29/72 » est le chiffre le plus important du projet, enterré en tranche 33 | **fondé sur le fond, lu trop vite sur la forme** — 18 des 72 visent un rapport au Président servi au grain du texte par décision, 9 des documents hors corpus, 13 sont motivés par la base par un autre passage du même document. Le chiffre honnête est deux lignes plus bas : le bon document 62/67, le bon passage 29/51. Il est en tête du README désormais |
| Les agents ont remplacé le bloquant humain sans le réduire | **exact**, et dit désormais à côté des chiffres, non dans une section à part |
| Le harnais de régression n'a pas été construit, huit tranches l'auraient payé | **exact** |
| La page d'accueil est un menu sans chiffre | **exact** |

## 2. Le classement

**La pondération.** La rareté d'un terme est désormais celle du fonds — les
28 294 alinéas du code, `log(N / df)`, calculée une fois par base et gardée en
mémoire — et non celle du document interrogé. Dans le document, « prix »,
présent dans dix considérants sur soixante, pesait moins que « lesquelles »,
présent dans un seul ; rare dans le document n'est pas discriminant pour
l'article. Dans le fonds, « réduction » pèse 6,0, « annonce » 5,6,
« antérieur » 7,5, « consommateur » 2,3, « alinéa » 2,9.

**La liste d'arrêt** s'allonge du vocabulaire de rédaction juridique qui ne dit
rien du sujet — « alinéa », « égard », « exception », « lesquelles »,
« pendant », « mentionné », « prévu » — et s'applique avant et après le repli
du pluriel, qui laissait passer « lesquelle ».

**Le silence.** Un considérant n'est classé que s'il partage avec l'article
deux termes rares — `log(200)`, moins d'un alinéa du code sur deux cents. Un
seul ne suffit pas : « rapide », rare dans le code (8,9), suffisait à classer
sous L112-1-1 le considérant sur le prix personnalisé. La barre ne vaut que
pour une unité entière : sur les fenêtres de 400 signes des rapports au
Président, elle ferait passer le passage annoté de 12 à 7 fois dans les trois
montrés, parce qu'une fenêtre courte partage peu de termes, rares ou non.

**Mesuré.** Vingt couples (article, considérant attendu) constitués à la main
en lisant les considérants, plus un « aucun » attendu — L112-1-1 —, fiche
`rappel-classement-considerants.tsv`, juge `claude-opus-5`. Et les rapports au
Président du jeu d'annotation, rejoués par `tools/annotation/verifier.py`.

| | pondération locale | fonds, sans barre | fonds, un terme rare | **fonds, deux termes rares** |
|---|---:|---:|---:|---:|
| considérants, attendu dans les trois montrés (21) | 16 | 17 | 17 | **17** |
| dont L112-1-1 rend rien | non | non | non | **oui** |
| rapports au Président, passage annoté dans les trois (17) | 11 | **12** | 9 | 7 — non appliquée |

Les quatre échecs restants : L221-1 (définitions, le classement rend les
considérants sur le champ des services numériques, que la fiche n'attendait
pas), L241-2 (rend les considérants sur les sanctions, voisins de celui
attendu sur la directive 93/13), L452-5-1 (l'article dit « les mesures prévues
au paragraphe 8 de l'article 9 » sans dire « accident » — aucun chemin
lexical), et L112-1-1 hors de la règle à deux termes. Wilson 0,60 sur 21.

Le classement était déjà replié sous « lire les considérants dans l'ordre de
l'acte » ; la revue lisait un rendu d'avant.

## 3. Le harnais

`tools/mesures/rejouer.py` relit les sept cents verdicts des fiches
`precision-*.tsv` contre la base du jour, famille par famille, avec la clef du
tirage. Le dernier verdict d'une arête jugée deux fois tient — `docs/47` a
rejugé par le contenu ce que `docs/45` avait jugé par le numéro. Trois
comptes : **revenue** (jugée fausse, présente — le harnais échoue), **perdue**
(jugée juste, absente — du rappel qui s'en va), **déplacée** (juste, vers un
autre article).

Premier passage : **362 justes tenues, 194 perdues, 50 rejugées ailleurs, 10
fausses dans la base.**

| famille | arête | ce que la fiche dit |
|---|---|---|
| `vise` | L411-1 ← amendement 12394 (Sénat) | le dispositif écrit « l'article L. 411-1 **du code de la mutualité** » ; `code_nomme` ne regarde qu'en amont du numéro (`docs/46` § 4) |
| `vise` | L141-3 ← 26732 | « L. 141-3 du code de la consommation » tel qu'en vigueur en 2016 — une autre lignée sous ce numéro |
| `vise` | L522-5 ← 32859 | ratification de l'ordonnance sur la distribution d'assurances |
| `depose_sur` | L121-79-4 ← 342 | l'article 64 du texte modifie trois articles, la voie a cru à un seul |
| `porte_sur` | L224-42-2 | « Article 21 A (Suppression maintenue en C.M.P.) » : barré, lu comme modificateur |
| `porte_sur` | L141-1 | l'article 5 crée L. 14-10-10 du code de l'action sociale ; la mention de L. 141-1 est ailleurs |
| `resulte_de` | L121-49, L122-14, L136-2, L115-16 | quatre arêtes jugées fausses en `docs/21`, que les six gardes n'ont pas atteintes |

Elles ne sont pas réparées ici : le harnais est fait pour les nommer à chaque
passage, et `CONTRIBUTING.md` demande qu'une contribution n'en ajoute pas.

Les 194 perdues sont pour les deux tiers des `resulte_de` — 160 sur 296
jugées — d'avant les gardes de `docs/21` et la scission des lignées de
`docs/38` ; la fiche `precision-depose-sur.tsv` de `docs/31` en perd 14 sur 15,
sa population ayant été refaite deux fois depuis. C'est du rappel dont le
projet savait qu'il partait ; le harnais le chiffre.

## 4. Le README et l'accueil

Le README ouvre sur le chiffre que la revue demandait, dans sa formulation
juste — le bon document 65 fois sur 74, le bon passage 30 fois sur 53, rejoués
sur la base du jour — et sur qui l'a mesuré. L'instrument est nommé à côté du
tableau des arêtes, non dans « ce qu'il ne fait pas ».

La page d'accueil du site ouvre sur le verdict par partie, lu dans
`hygiene.tsv` à la génération, jamais recopié ; puis sur les 2 955
irrecevabilités. Le menu vient après.

**« Signaler cette arête. »** Chaque arête de chaque page — `motive`,
`resulte_de`, `transpose`, `porte_sur`, `vise`, `depose_sur`, `renvoie_a`, le
document du texte — porte un lien qui ouvre dans les issues du dépôt un
rapport pré-rempli : article, arête, cible, preuve montrée, et une ligne
vide pour la raison. Gabarit `.github/ISSUE_TEMPLATE/arete-fausse.md`. C'est
une URL, rien d'autre : aucune requête à l'ouverture de la page, GitHub ne voit
le lecteur que s'il clique. C'est le seul canal vers un jugement humain que le
projet n'ait pas à payer — à condition que quelqu'un lise.

## 5. Ce qui n'est pas fait

**Les dix.** Deux ont leur cause écrite depuis `docs/46` (le code nommé après
le numéro) et `docs/38` (la lignée sous un numéro réutilisé). Elles se
réparent à la source, pas à la fiche.

**La distribution.** La revue la met en cinquième ; elle est hors du code.

**Le seuil du classement a été choisi sur les vingt-et-un couples qu'il
mesure.** Quatre variantes, toutes à 17 ; celle retenue est la seule qui
rende rien sur L112-1-1. Un second jeu, constitué par quelqu'un d'autre,
dirait si le seuil tient hors de l'échantillon.
