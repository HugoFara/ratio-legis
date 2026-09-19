# Trente-huitième tranche — l'instruction qui gouverne l'alinéa, lue dans le texte

**Objet :** corriger ce que `docs/43` § 2 avait nommé — l'alinéa rattaché à
une instruction que `porte_sur` n'avait pas relevée, et la maille du code hôte
inconnu — puis re-mesurer sur des tirages réellement disjoints.
**Date : 20 septembre 2026.**
**Code :** `ingestion/textes_des_amendements.py`, `ingestion/visees.py`.
**Données :** `precision-depose-sur-alinea-3.tsv`, `precision-vise-3.tsv`.

---

## 1. Trois corrections

**L'instruction se lit dans le texte, à toutes ses occurrences.** `porte_sur`
retient une mention par numéro et par article de texte — la première. Pour
savoir ce qu'un alinéa réécrit, il faut la dernière instruction *avant* lui,
quelle qu'elle soit : un article que le texte écrit (« Art. L. 333-6. – »),
une instruction sur un autre code, une seconde occurrence. `Textes.instructions`
relit l'article du texte — références hors citation qui sont des cibles,
en-têtes d'articles écrits — et l'alinéa prend la dernière ; `porte_sur` ne
sert plus qu'à la résoudre. Si l'instruction gouvernante n'est pas connue de
`porte_sur`, l'alinéa est illisible, non rattaché à celle d'avant.

**Un paragraphe de tête borne l'instruction précédente.** « III. – L'article
1er de la loi du 29 mars 1944 est abrogé » ne vise aucun article de code, et
sans lui le II sur L. 113-3 gouvernait encore le III. Une borne sans numéro
rend l'alinéa illisible.

**La ligne de statut du Sénat n'est pas un alinéa.** « (Non modifié) »,
« (Supprimé) », « (Conforme) » sous le titre : la numérotation des amendements
l'exclut, et la compter décalait tout d'un cran.

Et pour `vise` : hôte inconnu — jeu d'amendements non apparié à un texte — et
code non nommé, pas de rattachement. Dix amendements, dont celui qui
complétait « L. 131-4 » du code de l'environnement.

Sur les arêtes déjà jugées, avant tout nouveau tirage : **des onze `alinea`
qu'au moins un juge avait dites fausses, six ne sont plus dans la base ;
aucune des cinquante-et-une justes n'a été retirée.**

## 2. Re-mesuré, deux juges flash, arbitre sur désaccord

Les tirages précédents étaient disjoints deux à deux, non trois à trois : le
« troisième » tirage `alinea` recouvrait le premier à 18 sur 20, parce que
`--sauf` n'excluait qu'une fiche. Corrigé par une fiche d'exclusion fusionnée ;
les deux tirages ci-dessous sont disjoints de tous les précédents.

| arête | n | deepseek | glm | accord | arbitrage | verdict | Wilson | constante |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `depose_sur` · `alinea` | 20 | 16 | 17 | 19 | 1 → juste | **17 / 20** | **0,6396** | 0,584 → 0,640 |
| `vise` | 20 | 20 | 19 | 19 | 1 → juste | **20 / 20** | **0,8389** | 0,584 → 0,839 |

`vise`, en quatre tirages : 13/15 en août, puis 9/20 (tirets lus, homonymes
avec), 16/20 (code hôte), 20/20 (hôte inconnu écarté). L'arête est passée de
318 à 1 019, puis 569 ; elle en vaut aujourd'hui 0,84 là où elle en valait
0,45 hier, avec moins d'arêtes que ce qu'elle promettait et plus que ce
qu'elle avait.

Les trois `alinea` fausses restantes ont une cause commune et nommée : la
**sous-instruction** — « a bis) » sous un 1°, « 2° » sous un I — que le
parseur ne borne pas : l'alinéa 22 relève du bloc a bis)/a ter) sur L. 223-5,
l'instruction retenue est celle du 1° sur L. 223-1. C'est le grain suivant, et
il est petit.

## 3. Ce que cela a coûté

Quatre-vingts juges flash et deux arbitrages : un peu plus de trois dollars.
Rien de ceci n'est humain ; `verdict` dit qui a tranché.
