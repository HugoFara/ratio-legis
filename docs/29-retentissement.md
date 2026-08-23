# Vingt-troisième tranche — « si je modifie cet article, qu'est-ce qui bouge »

**Objet :** sortir l'arête `renvoie_a` de la fiche de provenance et en faire un
produit à part entière, pour le légiste.
**Date : 23 août 2026.**
**Code :** `restitution/retentissement.py`, points d'entrée
`/articles/{numero}/retentissement` et `/renvois/sommet`.

---

## 1. Ce qui était enterré

`docs/08` a construit `renvoie_a` en posant la bonne question : « la question du
législateur n'est pas *pourquoi cet article existe* mais *si je modifie
celui-ci, qu'est-ce qui bouge* ». Douze tranches plus tard, la réponse était
rendue sous forme d'une ligne au bas d'une fiche de provenance :

```
CE QUI CITE CET ARTICLE (10)
  L111-2, L111-3, L111-5, L131-1, L131-1-1, L216-1, …
```

Une liste de numéros, au rang 1 seulement, sans les phrases qui créent la
dépendance et sans dire dans quel état sont les articles touchés.

C'est pourtant l'objet le plus immédiatement utilisable de toute la base. Il ne
dépend d'aucune arête difficile : `renvoie_a` est dérivée du texte des articles,
chaque arête porte sa fenêtre de preuve, et elle couvre le fonds chargé, parties
réglementaire comprise — 709 articles L, 407 R et 121 D en émettent.

## 2. Ce que le module rend

**Ce qui bougerait, par onde.** Le rang 1 cite l'article. Le rang 2 cite un
article du rang 1 : il ne bougerait qu'en second, mais il bougerait. Un légiste
qui ne regarde que le rang 1 relit la moitié de ce qu'il faut relire. Sur L111-1,
au rang 3 : **69 articles**, dont 10 au rang 1, 15 au rang 2 et 44 au rang 3.

Le plus court chemin fait foi — `min(rang)` — et la borne de profondeur termine
la récursion même sur les cycles de renumérotation, que le fonds contient.

**La phrase qui crée la dépendance**, au seul rang direct. Aux rangs suivants
elle ne parle plus de l'article interrogé, et l'afficher tromperait.

**Le verdict de chaque article touché.** C'est le renseignement qui coûte : sur
les 69 articles que déplacerait une modification de L111-1, **20 n'ont aucune
raison documentée**. Les déplacer, c'est déplacer des dispositions dont aucune
source dépouillée ne dit pourquoi elles sont écrites ainsi. La répartition par
partie le montre du même coup — 48 L, 10 R, 11 D — et c'est là que les parties
réglementaires cessent d'être un complément.

**Ce dont l'article dépend**, avec l'état de résolution de chaque cible. Une
citation non résolue n'est pas une incohérence du droit : c'est une limite du
fonds chargé. `renvoie_a.portee` porte la distinction, elle est rendue telle
quelle plutôt que fondue dans un total.

## 3. La mesure de structure

`--sommet` classe les articles par nombre d'articles en vigueur qui les citent.
Ce n'est pas une mesure d'importance, et le module l'écrit : elle dit combien
d'autres articles nomment celui-ci, rien de plus.

| Article | Citants | Verdict |
|---|---:|---|
| L412-1 | 37 | un passage l'explique |
| L733-1 | 37 | un passage l'explique |
| L733-4 | 35 | un passage l'explique |
| L733-7 | 32 | un passage l'explique |
| L313-1 | 25 | un passage l'explique |
| L221-5 | 24 | origine située |

## 4. Ce qu'il ne fait pas

Aucune inférence. Les arêtes descendues sont celles de `renvoie_a`, toutes
déclarées ou munies d'une preuve. Le module ne pondère rien, ne calcule aucune
distance, et n'ordonne que par rang d'onde puis par numéro — un ordre total, donc
reproductible (§ 5.2).

Il dit **ce qu'il faudrait relire**. Il ne dit pas ce qu'il faudrait y écrire, et
il ne le dira jamais : ce serait une interprétation juridique, que le § 2 de la
feuille de route exclut du produit.

**Coût.** 38 ms pour la mesure de structure sur tout le fonds, 70 ms pour l'onde
de rang 3 d'un article très cité.
