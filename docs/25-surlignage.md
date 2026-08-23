# Dix-neuvième tranche — le surlignage par étape

**Objet :** le dernier livrable du § 4.4 — sur le texte d'un article, colorer
chaque alinéa selon l'étape qui l'a introduit.
**Date : 23 août 2026.**
**Code :** `restitution/surlignage.py`. **Exemples :** `restitution/exemples/surlignage/`.

---

## 1. La même idée, sur une chaîne plus longue

La Fabrique de la loi a éprouvé le surlignage sur la navette : d'un dépôt à une
promulgation. Ici la question traverse en plus la **recodification**, et c'est ce
qui la rend difficile — l'alinéa que vous lisez sous L. 224-43 a été écrit en
2014 sous L. 121-42.

Rien n'a eu besoin d'être ajouté au graphe. `repris_de` relie un alinéa à celui
dont il reprend le texte, d'une version à l'autre ; `produite_par` dit quel texte
a produit une version. Remonter la première, puis lire la seconde sur le plus
ancien ancêtre, donne le texte introducteur. Les deux arêtes sont déclarées par
LEGI, et `repris_de` porte sa fenêtre de preuve : **rien n'est inféré**.

## 2. Le piège : le texte qui abroge n'a rien écrit

La première version attribuait chaque alinéa de L. 224-43 à **deux** textes — la
loi de 2014 *et* l'ordonnance de recodification de 2016.

`produite_par` porte un `type_lien`, et l'ordonnance figurait sur la version
ancienne au titre de `ABROGE`. Sans filtre, l'ordonnance de 2016 devenait
introductrice de tout ce qu'elle avait abrogé — c'est-à-dire de l'essentiel du
code, et l'**inverse exact** de ce que le surlignage sert à montrer. Un
surlignage qui attribue tout à la recodification ne dit rien de plus que le
numéro d'article.

Les liens d'abrogation sont donc exclus. L. 224-43 est alors rendu à la loi du
17 mars 2014, comme il se doit.

## 3. Trois plans, parce que trois choses différentes

| Plan | Ce qu'il dit |
|---|---|
| **la couleur** | quel texte a introduit l'alinéa |
| **la trame** | l'alinéa a été retouché depuis son introduction (`part_reprise` < 1) |
| **la marque** | l'amendement qui l'a écrit, avec son auteur et son sort |

**La couleur ne dit pas qui a voulu l'alinéa.** 145 alinéas sur 7 504 seulement
remontent à un amendement nommé. Confondre les deux ferait passer une ordonnance
de recodification pour un auteur, ce qui serait faux et flatteur. Les trois plans
sont distincts à l'écran comme dans les données.

## 4. Couverture

Sur les 2 104 articles en vigueur et leurs 7 504 alinéas :

| | |
|---|---:|
| Alinéas avec un texte introducteur | **7 437 (99,1 %)** |
| Alinéas sans origine documentée | 67 (0,9 %) |
| Alinéas retouchés depuis leur introduction | 1 766 (23,5 %) |
| Alinéas remontant à un amendement | 145 |
| Articles composites (deux textes introducteurs ou plus) | 357 (17,0 %) |

Médiane 8,7 ms par article, 95ᵉ centile 11 ms.

**Un article sur six est composite** — écrit par deux textes ou davantage. C'est
précisément ce que le numéro d'article seul ne peut pas montrer, et ce que la
question « pourquoi cet article est-il ainsi ? » a besoin de savoir.

## 5. Ce que cela donne

L. 111-1, information précontractuelle : huit alinéas viennent de la loi
Hamon de 2014, et **le 2° — « Le prix ou tout autre avantage procuré au lieu ou
en complément du paiement d'un prix » — vient de l'ordonnance du 29 septembre
2021**, celle qui transpose les directives sur les contenus numériques. La
disposition sur le paiement par la donnée personnelle n'a pas l'âge du reste de
l'article ; le surlignage le montre d'un coup d'œil.

Les alinéas sans origine documentée gardent une couleur neutre et le disent en
toutes lettres. C'est le même principe que le verdict `raison non documentée` :
se taire n'est pas dire.
