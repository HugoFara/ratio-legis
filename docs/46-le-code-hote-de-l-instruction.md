# Quarantième tranche — le code hôte de l'instruction, pour `vise`

**Objet :** rattacher le numéro nu — « l'article L. 223-5 », sans son code —
sous un article de texte qui modifie plusieurs codes, là où `docs/43` § 2
avait posé « hôte multi-codes = pas de rattachement » et où `docs/45` § 6
avait nommé la maille.
**Date : 20 septembre 2026.**
**Code :** `ingestion/visees.py`.
**Données :** `precision-vise-instruction.tsv`.

---

## 1. La maille

Un dispositif qui nomme un article sans nommer son code hérite du code de
l'article du texte sur lequel il est déposé, et c'est `porte_sur` qui le
sait. Quand cet article du texte modifie le code de commerce au I bis et le
nôtre au II — l'article 3 de la proposition de loi 469 de 2024-2025, qui
crée L. 123-38-1 au code de commerce puis réécrit tout le démarchage
téléphonique —, l'hôte est double, et la règle de `docs/43` écartait le
numéro : 1 376 amendements, dont les sept qui complétaient « le premier
alinéa de l'article L. 223-5 » et que le cinquième tirage de `docs/45`
comptait parmi les justes perdues.

L'hôte de l'**article du texte** est double ; celui de l'**instruction** ne
l'est pas. Deux choses le disent, et les deux sont déjà dans la base :

1. **Le numéro lui-même**, quand `porte_sur` l'a relevé dans cet article du
   texte comme cible de notre code — et d'aucun autre : le texte modifie
   notre L. 223-5 là, l'amendement qui nomme L. 223-5 là parle de lui. Si le
   même numéro y est relevé aussi comme externe, homonyme d'un autre code
   modifié au même endroit, rien n'est tranché et rien n'est rattaché.
2. **Sinon, l'alinéa que le dispositif nomme** : l'instruction qui le
   gouverne est connue de `porte_sur` avec sa portée (`Textes.gouvernant`,
   `docs/44`, `docs/45`). « Après l'alinéa 23, insérer : « …° Après le
   deuxième alinéa des articles L. 332-9 … » » sous « I. – Le code de la
   consommation est ainsi modifié » s'y trouve ; sous un II sur la sécurité
   sociale, non.

Ni l'un ni l'autre → la règle de `docs/43` s'applique, inchangée.

## 2. Ce que cela fait au graphe

| | avant | après |
|---|---:|---:|
| numéros nus rattachés par l'instruction | — | 60 |
| `vise` | 564 | **604** (+40, rien de retiré) |
| `depose_sur` · `visee` | 76 | **87** |
| `depose_sur` · `alinea` | 1 015 | 1 001 |
| `depose_sur` | 1 107 | 1 104 |

Soixante numéros rattachés, quarante arêtes : le résolveur de lignées et la
garde du numéro glissé prennent le reste. Quatorze amendements quittent la
voie `alinea` — onze arrivent en `visee`, qui est la leur, dont les sept
sur L. 223-5 — et dix-neuf tombent sur « la cible déclarée contredit
l'article du texte », parce que les articles qu'ils écrivent — la section 17
sur le gaz de pétrole liquéfié, L. 121-105 à L. 121-111 — ne sont pas des
cibles que `porte_sur` connaît à cet article du texte.

## 3. Mesuré

Vingt arêtes tirées parmi les quarante créées, deux juges Sonnet 5 en
colonnes séparées, arbitre sur désaccord (`docs/45` § 5).

| arête | tirage | n | juge A | juge B | accord | arbitrage | verdict | Wilson | constante |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `vise` · par l'instruction | arêtes créées par la règle | 20 | 20 | 18 | 18 | 1 → juste, 1 → faux | **19 / 20** | 0,7639 | 0,8389 → **0,8712** (39 / 40, les deux tirages de la population d'aujourd'hui) |

Les juges ont, sur chaque arête, retrouvé l'instruction dans le texte et
compté — par la pastille où elle existe, ligne à ligne sinon — l'alinéa
nommé : les sept L. 223-x tombent sous « II. – Le code de la consommation
est ainsi modifié », L. 332-9 avant le II sur la sécurité sociale, L. 621-7
sous le XII et non le XIII sur la justice administrative. Ils notent aussi
que plusieurs de ces articles du texte sont en réalité à code unique — le
« second » code que `porte_sur` y voit est une mention externe relevée
ailleurs dans l'article —, ce qui dit que la règle de `docs/43` écartait
plus large que la maille.

**La fausse n'est pas de cette tranche.** Le texte de commission de 2013
écrit « Art. L. 423-8 » pour ce que la loi a promulgué sous L. 423-16 ;
l'amendement qui rédige « Art. L. 423-8 » ne vise donc pas le L. 423-8 du
code. La garde du numéro glissé exige que la loi ait écrit *un* article
sous ce numéro — elle l'a fait, une autre disposition — et non *cette*
disposition. L'arbitre a tranché en comparant le contenu écrit au fonds,
ce que le pipeline ne fait pas encore. Le second désaccord était une
erreur de lecture du juge B — un « (Non modifié) » qui n'existe pas dans
ce texte — et l'arbitre a rendu juste.

La constante réunit les deux tirages qui décrivent la population
d'aujourd'hui : 20 sur 20 (`docs/44`) sur ce qui existait, 19 sur 20 sur
ce que la règle ajoute.

## 4. Ce qui n'est pas fait

**Le numéro glissé par le contenu.** « Art. L. 423-8 » écrit par un texte
de commission, promulgué L. 423-16 : la garde actuelle — la loi a-t-elle
écrit ce numéro — laisse passer, parce que la loi a écrit un autre
L. 423-8. La corroboration par le contenu — le premier alinéa que le texte
écrit sous ce numéro est-il celui de la première version promulguée — la
tiendrait, et elle vaut au même titre pour la voie `article_cree` de
`porte_sur`, dont la fausse de `docs/45` § 2 est de cette famille. C'est de
la correspondance textuelle vérifiable, non de l'inférence ; c'est le
chantier suivant.

**Le code nommé dans le dispositif après le numéro.** L'amendement 4384 de
l'Assemblée écrit « le code de la consommation » dans son propre I bis,
après les vingt-cinq alinéas qu'il insère ; `code_nomme` ne regarde qu'en
amont. Il est passé par l'instruction ; il aurait pu passer par lui-même.

**La cible déclarée contredite** : dix-neuf amendements écrivent des
articles que `porte_sur` ne connaît pas à cet article du texte, parce que
le texte de commission ne les portait pas encore. C'est la voie `visee`
qui les tient, pas `depose_sur` — et c'est déjà ce que la restitution
affiche.

Rien de ceci n'est humain : deux juges Sonnet et un arbitre, `verdict` dit
qui a tranché.
