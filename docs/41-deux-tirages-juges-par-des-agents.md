# Trente-cinquième tranche — deux tirages jugés à deux, et ce qu'ils défont

**Objet :** juger les deux tirages de précision laissés ouverts par `docs/37`
§ 5 — `porte_sur` et `depose_sur` sur la population élargie — par deux
modèles indépendants, et reprendre les constantes de confiance.
**Date : 19 septembre 2026.**
**Code :** `tools/mesures/juger.py` (nouveau), `.opencode/agent/juge.md`,
`ingestion/textes_des_amendements.py`, `ingestion/textes_deposes.py`.
**Données :** `data/mesures/precision-porte-sur-corpus-elargi.tsv`,
`precision-depose-sur-corpus-elargi.tsv`, `precision-depose-sur-cibles-tous-codes.tsv`.

---

## 1. Le dispositif

Les fiches de `precision_*.py` portent tout ce qu'il faut pour trancher sur
la ligne : fenêtre de preuve, article du texte, article du code, subdivision
et dispositif de l'amendement. `juger.py` les expose en commandes — `montrer`,
`rendre`, deux colonnes de verdict pour deux juges qui ne se lisent pas —, et
l'agent opencode `juge` n'a que bash et le corpus local, pas de réseau.
Chaque arête est jugée par deepseek-v4p1-flash (colonne `verdict`, celle que
`--bilan` compte) et par glm-5p3-flash (`verdict_bis`). 35 arêtes, 70 juges,
puis 15 arêtes et 30 juges sur une population corrigée : une centaine
d'appels, quelques dollars.

## 2. `porte_sur` : 17 sur 20, un désaccord, et un glissement de numéro

| | deepseek | glm | accord |
|---|---:|---:|---:|
| justes / 20 | 18 | 17 | 19 / 20 |

Le désaccord est tranché contre l'arête : le texte adopté en première lecture
écrit « Art. L. 423-5 — Le professionnel procède à l'indemnisation
individuelle… », et c'est L. 423-6 qui porte cela au code promulgué ; le
L. 423-5 d'aujourd'hui est le délai d'adhésion au groupe. **La numérotation a
glissé en navette**, et la voie de la citation — qui lit le numéro que le
texte écrit — attribue au bon numéro la mauvaise disposition. `survecu`
(`docs/40`) n'y peut rien : la loi du dossier a bien écrit L. 423-5, un autre.

Par voie : déclarée 14 / 15, citation 3 / 5. Réunis aux tirages d'août
(`docs/16` 20 / 20, `docs/33` 15 / 15) : **34 / 35 → 0,8558** et **18 / 20 →
0,6996**, constantes reprises. Deux populations, deux tirages disjoints, une
seule borne : c'est la convention de `docs/21`, et elle est dite.

## 3. `depose_sur` : ce que deux juges qui se contredisent apprennent

Premier tirage, population de `docs/37` : deepseek 7 / 15, glm 11 / 15,
accord 11 / 15. **Les quatre désaccords sont du même type** : l'amendement
est déposé sur l'article 71 ter du texte, qui réécrit L. 224-3 du code de la
consommation — sa seule cible *dans ce code* — et cinq articles du code de
l'énergie ; le dispositif de l'amendement porte sur le gaz. glm juge la
composition, exacte ; deepseek juge ce que l'arête prétend, faux.

La règle « et aucun autre » de `docs/31` ne comptait que les cibles internes.
Mesuré : **304 des 550 arêtes** reposaient sur un article de texte à cibles
dans d'autres codes. Corrigé — une cible hors du code compte —, l'arête passe
à **246**, 14 articles en vigueur atteints.

Second tirage, population corrigée, disjoint du premier : deepseek **7 / 15**,
glm 10 / 15, accord 10 / 15. Les désaccords restants sont encore de nature,
non de lecture : un amendement déposé sur l'article 18, qui ne réécrit que
L. 311-8-1, mais dont le dispositif « complète cet article par un paragraphe »
modifiant le code monétaire et financier. Formellement composé, l'amendement
ne portait pas sur L. 311-8-1. Et deux fois, `cibles_de_l_article = 1` est
contredit sur pièces : `porte_sur` ne voit pas l'article que le texte
*insère* (L. 522-7-1) ni celui dont il ne change que les montants.

**La constante suit la mesure de ce que l'arête prétend : 0,2481.** Ce n'est
pas la précision de la composition — glm la met à deux tiers — c'est celle de
« l'amendement portait sur cet article », qui est ce que la restitution écrit.
Sous le seuil du § 4.2, sous tout ce que le graphe sert par ailleurs ; l'arête
reste, avec sa confiance, parce qu'une tentative à 25 % est encore une piste
et que la règle § 5.4 est de porter la mesure, pas de cacher l'arête.

Ce qui la relèverait est écrit depuis `docs/35` § 7 : composer avec `vise`,
qui lit le dispositif — 13 des 15 arêtes du second tirage sont « sans
visée », c'est-à-dire des amendements dont le dispositif ne nomme aucun
article du code. Sur eux, la composition est tout ce qu'on a, et elle ne
suffit pas.

## 4. Ce que deux juges valent

Sur les 50 arêtes, deepseek et glm s'accordent 40 fois. Les dix désaccords ne
sont pas du bruit : neuf portent sur ce que l'arête *affirme* — composition
formelle contre portée réelle —, un sur une lecture du texte. Un seul juge
aurait rendu l'une ou l'autre précision sans que rien ne dise laquelle ; deux
juges qui se contredisent systématiquement dans le même sens ont désigné une
ambiguïté de définition. C'est la seconde fois de la journée (`docs/39` § 3,
`non_documente`) qu'un désaccord entre modèles vaut mieux qu'un accord.

Rien de ceci n'est une mesure humaine ; les fiches portent le nom des juges.
