# Trente-troisième tranche — cent verdicts d'agents, et ce qu'ils valent

**Objet :** faire annoter les 100 articles du jeu par des agents, en mesurer le
résultat contre le graphe, et dire ce que cela ne remplace pas.
**Date : 19 septembre 2026.**
**Code :** `tools/annotation/console.py`, `tools/annotation/verifier.py`,
`.opencode/agent/annotateur.md`. **Données :** `data/mesures/golden-set-100.tsv`.

---

## 1. Le dispositif

Un agent par article, sept modèles, le même protocole (`CONSIGNES.md`) et la
même interface (`console.py`) : lire la fiche, chercher, désigner un passage
par ses premiers et derniers mots, rendre. L'agent opencode est défini sans
`write` ni `edit` — il n'agit que par les commandes de la console — et se
nomme `agent:<modèle>` dans la colonne `annotateur`. Les deux premiers articles
ont été rendus par un agent Claude, la strate « origine ordonnance » par
kimi-k3, les 75 restants répartis entre cinq modèles à raison de 15 chacun,
strates mélangées — pour que la comparaison entre modèles soit lisible.

| modèle | articles | $/M entrée / sortie | coût effectif | par article |
|---|---:|---:|---:|---:|
| deepseek-v4p1-flash | 15 | 0,22 / 0,66 | 0,79 $ | **0,05 $** |
| glm-5p3-flash | 14 (+1 sans verdict) | 0,15 / 0,50 | 1,03 $ | 0,07 $ |
| minimax-m3 | 15 | 0,30 / 1,20 | 3,19 $ | 0,21 $ |
| kimi-k3 | 23 | 3 / 15 | 17,32 $ | 0,75 $ |
| nemotron-3-ultra | 16 | 0,60 / 2,40 | 24,67 $ | 1,54 $ |
| glm-5p3 | 15 | 1,40 / 4,40 | 25,28 $ | 1,69 $ |
| qwen3p7-plus | 0 | — | 0 | listé, non déployé |

72 $ pour 100 verdicts. Les deux modèles les moins chers ont tenu le protocole
aussi bien que les autres ; nemotron, à prix moyen, a coûté vingt fois plus
que deepseek en messages — 2 241 pour 16 articles.

Échecs : 15 « model not found » (qwen), 5 refus de lecture de `/tmp` avant que
l'agent n'y soit autorisé, 2 erreurs d'API au démarrage, 1 dépassement de
délai, 1 agent sorti sans rendre. Tous relancés ; aucun verdict manquant.

## 2. Ce que les cent verdicts disent du graphe

`verifier.py` confronte chaque ligne à la base scindée (`docs/38`) :

| | |
|---|---:|
| verdicts | 72 `motive`, 22 `dossier_seulement`, 6 `non_documente` |
| concordance verdict humain / verdict de la base | 68 / 100 |
| **`motive` humain retrouvé par une arête `motive` de la base, au passage** | **29 / 72** |
| dont le document est servi au grain du texte, sans arête | 18 |
| dont la base motive par un autre passage | 13 |
| dont le document a été trouvé **hors corpus** | 9 |
| dont aucune arête, document au corpus | 3 |
| **précision de `passage_motivant`, confirmée au passage** | **29 / 51 — 56,9 %**, Wilson 0,43 |
| affirmations non étayées (base : passage ; annotateur : aucun) | 3 |
| proposition de la machine : bon document | 62 / 67 |
| proposition de la machine : bon passage tel quel | 4 / 67 |

C'est la première mesure de `motive` qui ne vienne pas de l'auteur du code.
Elle dit deux choses.

**Le graphe trouve le bon document mais pas le bon passage** : 62 fois sur 67
la proposition — un commentaire de rapport nommant l'article — désigne le
document où l'annotateur a fini par citer, 4 fois le passage exact. La
section de rapport est le grain du graphe ; le passage qui explique
l'article est plus court, et il faut le lire pour le trouver. Treize fois la
base motive par un **autre** passage du même document.

**Le rapport au Président est une source que le graphe ne relie pas.** 18 des
72 `motive` désignent un passage d'un document que la base sert au grain du
texte entier — presque toujours le rapport au Président d'une ordonnance —
parce que `docs/14` § 5 a refusé d'en fabriquer une arête. Le classement
lexical de `docs/28`, qui ordonne sans affirmer, met le passage annoté au
**rang 1 neuf fois sur 18**, rang 2 ou 3 deux fois, hors des trois sept fois.
C'est la première mesure que ce classement ait jamais eue, et elle est
publiée avec ses sept échecs.

Neuf documents trouvés hors corpus — rapports du Sénat de 1991, 1993, 1994,
2003, importés en PDF par les agents — sont des **trous du corpus**, distincts
d'un silence du fonds ; deux concordances manquantes sont signalées
(L313-10 ← L312-6-2, L132-25 ← loi 92-60).

## 3. Ce que les agents disent entre eux

| modèle | n | `motive` | `dossier` | `non_doc` | concorde base | passage retrouvé | hors corpus |
|---|---:|---:|---:|---:|---:|---:|---:|
| kimi-k3 | 23 | 11 | 12 | 0 | 13 | 1 | 0 |
| deepseek-v4p1-flash | 15 | 12 | 3 | 0 | 13 | 6 | 1 |
| glm-5p3 | 15 | 14 | 1 | 0 | 10 | 4 | 4 |
| minimax-m3 | 15 | 11 | 4 | 0 | 14 | 8 | 0 |
| glm-5p3-flash | 14 | 12 | 2 | 0 | 12 | 4 | 2 |
| nemotron-3-ultra | 16 | 10 | 0 | **6** | 6 | 6 | 1 |
| claude-opus-5 | 2 | 2 | 0 | 0 | 0 | 0 | 1 |

Les strates ne sont pas les mêmes d'un modèle à l'autre (kimi n'a eu que les
ordonnances), et les colonnes ne se lisent donc pas comme un classement. Ce
qui se lit : **six `non_documente` sur cent, tous rendus par le même modèle.**
Les autres, devant un article de 1993 dont l'historique porte l'ordonnance de
recodification de 2016 et son rapport au Président, ont appliqué la règle à
la lettre — un rapport au Président qui ne nomme pas l'article vaut
`dossier_seulement` — et nemotron a jugé que ce rapport ne documentait rien de
*l'origine du dispositif*. Les deux lectures sont défendables, et c'est le
protocole qui est en défaut : **avec la recherche exhaustive, tout article a
un document quelque part dans son historique, et `non_documente` ne veut
plus rien dire tant qu'on ne dit pas de quoi.** À trancher avant de relire —
sans doute « aucun document ne motive l'origine du dispositif », ce qui
renverrait une partie des 22 `dossier_seulement` vers `non_documente`, et
rendrait au critère du § 4.3 (« raison non documentée correctement
identifiée > 90 % ») un dénominateur.

Le second désaccord est de grain : kimi cite des passages de 2 500 signes
en moyenne, deepseek de 500. Le protocole ne fixe pas la longueur d'un
passage ; la mesure par recouvrement d'intervalles est indulgente aux longs.

### Décision, le jour même

`non_documente` est redéfini : **aucun document ne motive l'origine du
dispositif** — le texte qui l'a écrit ou substantiellement réécrit, non
n'importe quel texte de l'historique. Une recodification à droit constant, une
coordination, une renumérotation ne sont pas l'origine (`CONSIGNES.md` § 2).
Neuf `dossier_seulement` sont reclassés, commentaire à l'appui ; le verdict de
la base suit la même définition (`ingestion/verdict.py`) : un document compte
si son texte a créé la racine de la chaîne de renumérotation ou modifié une
version, pas s'il a seulement créé un numéro nouveau pour un article qui a
des ancêtres. La partie L passe de 5 à **70** articles sans raison documentée
(0,4 % → 5,4 %) ; « documentée à 99,6 % » devient 94,6 %, et c'est le chiffre
honnête. Sur le jeu : 15 `non_documente`, dont 7 que la base rend tels quels,
4 qu'elle dit « origine située », 2 « motivation du texte », 2 « passage
motivant » — ces deux-là sont à relire en premier.

## 4. Ce que cela ne vaut pas, et ce qu'il reste

**Rien de ceci n'est l'évaluation humaine de la phase 3.** Cent verdicts
d'agents sont une pré-annotation à relire, pas une vérité terrain : la
colonne `annotateur` le porte, `verifier.py` l'écrit en tête de son bilan.
Ce que la relecture humaine a devant elle est bien plus court qu'une
annotation à froid : les 3 affirmations non étayées (L413-3, L462-1,
L511-17), les 13 « autre passage », les 6 `non_documente`, et un
échantillon des 29 retrouvés pour mesurer l'accord humain/agent.

**Trois décisions de protocole** avant la relecture : la définition de
`non_documente` (§ 3) ; la longueur d'un passage ; et le statut du rapport
au Président quand il consacre un passage au dispositif — 18 `motive` en
dépendent, et le graphe n'a pas d'arête pour eux.

**Le pré-remplissage a fait son travail** — bon document 62 fois sur 67 — et
il ne fera pas mieux : c'est le passage qu'il ne sait pas désigner, et
c'est ce que le jeu mesure désormais.
