# Trente-septième tranche — `vise` et `porte_sur` corrigés, et re-mesurés à deux juges

**Objet :** corriger ce que `docs/42` § 3 avait nommé — l'ancre prise pour une
cible, les articles que `porte_sur` ne voit pas —, mesurer `vise` pour la
première fois à part, et reprendre les constantes.
**Date : 19 septembre 2026.**
**Code :** `ingestion/visees.py`, `ingestion/textes_deposes.py`,
`ingestion/textes_des_amendements.py`, `tools/mesures/precision_vise.py`
(nouveau), `pipeline.sh` (ordre).
**Données :** `precision-vise.tsv`, `precision-vise-2.tsv`,
`precision-depose-sur-{alinea-2,visee-2,visee-3,article-entier-2}.tsv`.

---

## 1. Ce qui est corrigé, et ce que chaque correction a fait au graphe

**`porte_sur` — les numéros à quatre chiffres.** Le code de la santé publique
numérote L. 2133-1, le code des transports L. 6761-1 ; le parseur exigeait
trois chiffres et ne voyait pas ces références — ni internes, ni externes.
Un article de texte qui modifiait deux articles de la santé publique et un du
nôtre passait pour n'en réécrire qu'un. Externes : 52 882 → **70 963**.
Internes inchangées.

**`depose_sur` — une cible non résolue est une cible.** « Il est inséré un
article L. 522-7-1 » que la loi promulguée n'a jamais porté reste, dans le
texte, un second article réécrit.

**`vise` — l'ancre.** « Après l'article L. 312-9, il est inséré… » ne vise
plus L. 312-9 : il le nomme pour placer autre chose. « Au début de / à la fin
de l'article » restent des modifications.

**`vise` — les tirets insécables.** Les dispositifs de l'Assemblée écrivent
« L. 223‑1 » avec U+2011 ; l'arête ne lisait donc qu'un dispositif sur trois.
Normalisé : **318 → 1 019** arêtes. Une arête qui triple se mesure avant de se
servir — et la mesure a dit que la moitié du gain était faux (§ 2).

**`vise` — le code hôte.** « L. 122-3 » dans un amendement à un article du
texte qui modifie le code forestier : le dispositif ne nomme pas son code
parce que l'article du texte le dit pour lui. Un numéro nu hérite désormais
du code hôte de l'article du texte, que `porte_sur` connaît ; s'il n'est pas
le nôtre, ou si l'article en modifie plusieurs, pas de rattachement. 1 293
mentions écartées. `visees.py` passe donc après `textes_deposes.py` dans le
pipeline — `ingere` l'a signalé en s'arrêtant, comme prévu.

**`vise` — le numéro qui glisse.** « Art. L. 121-105. – » créé par un projet,
promulgué sous un autre numéro : un article que le dispositif *crée* n'est le
nôtre que si la loi du dossier a bien écrit ce numéro. 160 écartés.

**Les deux parseurs — « L. 312-9-… ».** L'article nouveau au numéro non fixé
était lu L. 312-9. Le tiret suivi d'autre chose qu'un blanc ferme la lecture.

`vise` : 318 → 1 019 → **594**. `depose_sur` : `visee` 51, `alinea` 1 083,
`article_entier` 13 — **1 147**.

## 2. Mesuré, à deux juges et un arbitre

Protocole resserré, sur remarque de l'auteur : deux juges flash sur tout
(deepseek-v4p1-flash, glm-5p3-flash, ~0,05 $ l'arête), qwen3p8-max
**seulement sur les désaccords**. Sur 82 arêtes, 74 accords ; 8 arbitrages.
Le verdict retenu est l'accord des deux, sinon l'arbitre.

| arête | tirage | juste | faux | douteux | Wilson | constante |
|---|---:|---:|---:|---:|---:|---:|
| `vise`, avant gardes | 20 | 9 | 11 | 0 | — | — |
| **`vise`, après gardes** | 20 | **16** | 2 | 2 | **0,5840** | 0,6212 → 0,5840 |
| `depose_sur` · `alinea` | 20 | 16 | 4 | 0 | 0,5840 | 0,6990 → 0,5840 |
| `depose_sur` · `visee` | 15 | 13 | 2 | 0 | 0,6212 | 0,3968 → 0,6212 |
| `depose_sur` · `article_entier` | 7 | 6 | 1 | 0 | 0,4869 | 0,3968 → 0,4869 |

Sur `vise`, la moitié du premier tirage était fausse, et neuf fausses sur
onze avaient la même cause — le code implicite. Le second tirage, disjoint,
après les gardes : deux fausses, dont une encore un homonyme (le
dispositif dit « L'article L. 131-4 » sous un article du texte qui ouvre par
« Le code de l'environnement est ainsi modifié » — l'hôte est connu de
`porte_sur` comme *externe*, mais l'article du texte a aussi une cible
interne, et la règle « multi-codes → écarter » ne s'applique qu'aux numéros
nus… qui l'était). La garde a une maille ; elle est nommée.

Sur `alinea`, le tirage baisse de 18 à 16 sur 20, et les quatre fausses ont
la même nature : l'alinéa cité relève d'une instruction que `porte_sur` n'a
pas relevée — un article inséré « Art. L. 333-6 » que le texte écrit, une
instruction X sur L. 218-7 sautée. La dernière mention avant l'alinéa n'est
alors pas la dernière instruction. **La portée d'une instruction n'est pas
bornée par la suivante quand celle-ci n'est pas vue** ; c'est le prochain
chantier, et il est du côté de `porte_sur`.

Deux des `visee` fausses du tirage 3 — les ancres « L. 312-9-… » — ne sont
plus dans la base : la dernière correction les a retirées après le jugement.
La constante ne les recompte pas : 13 sur 15 est ce qui a été mesuré.

## 3. Ce que cela a coûté, et ce que cela vaut

Cent quatre-vingts appels de juges pour cette tranche : 3,2 $ deepseek,
4,7 $ glm, 2,6 $ qwen en arbitrage. Un juge cher sur tout aurait coûté dix
fois plus pour les mêmes 74 accords ; c'est le désaccord qui vaut l'arbitre,
pas l'arête.

Rien de ceci n'est humain. Les fiches portent le nom des juges, et
`verdict` dit lequel a tranché.
