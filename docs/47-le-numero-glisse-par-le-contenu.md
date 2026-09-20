# Quarante-et-unième tranche — le numéro glissé, corroboré et résolu par le contenu

**Objet :** un texte de commission écrit « Art. L. 423-8. – Tout accord
négocié au nom du groupe… » ; la loi promulgue cette disposition sous
L. 423-16, et un autre L. 423-8. La garde de `docs/33` — la loi a-t-elle
écrit ce numéro — laissait passer. Comparer le contenu, écarter ce qui ne
concorde pas, et retrouver l'article que le contenu désigne.
**Date : 20 septembre 2026.**
**Code :** `ingestion/textes_deposes.py` (voie `article_cree`),
`ingestion/visees.py` (formule « rédigé »),
`ingestion/textes_des_amendements.py` (voie `visee`).
**Données :** `precision-porte-sur-contenu.tsv`, `precision-vise-contenu.tsv`.

---

## 1. La mesure avant la règle

Pour chaque article que le texte écrit sous un numéro (« Art. L. X. – … »,
voie `article_cree` de `porte_sur`), et que la garde du numéro tient pour
interne : la part des trigrammes de mots du premier alinéa écrit que
contient la version que la loi du dossier a produite sous ce numéro. Sur
les 1 616 articles écrits à contenu lisible — huit mots au moins ; 99
« (Non modifié) » ou intitulés ne se comparent pas :

| part contenue | 0,0–0,1 | 0,2 | 0,3–0,4 | 0,5–0,7 | 0,8–1,0 |
|---|---|---:|---:|---:|---:|
| articles écrits | 334 | 3 | 21 | 38 | 1 220 |

La distribution est bimodale et le seuil, 0,5, tombe dans le vide. En deçà,
l'article écrit sous ce numéro n'est pas celui que le code porte sous ce
numéro : « Art. L. 311-45. – Lorsque la convention de compte… » est le
L. 311-46 promulgué, « Art. L. 121-20-1. – Le consommateur qui ne souhaite
pas faire l'objet de prospection… » est L. 121-34, Bloctel. Ce sont des
décalages d'un cran, ou de sept quand la commission a inséré des articles.

**358 articles écrits contredits par le contenu** — ils étaient internes,
sous un numéro faux. Le L. 423-8 de `docs/46` § 3 en est un ; la fausse de
la voie `article_cree` dans `docs/45` § 2 aussi.

## 2. Corroborer, puis résoudre

Un article écrit contredit n'est pas un article de nulle part : c'est un
article du même code, sous un numéro que le texte ne dit pas. Parmi les
versions que la loi du dossier a produites, celle qui contient l'alinéa
écrit — à 0,6 au moins, aucune autre à 0,5 — le désigne. **234 des 358 sont
résolus** ainsi ; 124 restent `non_resolue`, cible comptée mais non
nommée : aucune version à 0,5 (l'article a été réécrit en navette, ou n'a
pas été promulgué), ou deux (un chapeau générique — « I. – Pour les
opérations mentionnées au premier alinéa… »).

C'est le troisième échelon de la cascade du § 3 de la feuille de route —
alignement textuel, méthode `inferee`, confiance calculée à part — et le
premier usage qu'en fait le graphe. Il ne repose sur rien de flou : la
version et l'alinéa sont dans la base, la fenêtre est la preuve, le seuil
est écrit.

Deux arêtes suivent :

- **`vise`, formule « rédigé »** : l'amendement qui rédige « Art. L. 423-8 »
  à l'alinéa 41 de ce texte rédige le même article mal numéroté. Il vise ce
  que `porte_sur` a résolu — L. 423-15 —, ou rien si `porte_sur` n'a rien
  résolu, et rien non plus s'il réécrit tout l'article du texte selon son
  propre plan (§ 4). 3 suivis, 21 écartés.
- **`depose_sur`, voie `visee`** : l'article déclaré lui-même passe avant
  la chaîne de renumérotation. La recodification de 2016 a tiré L. 223-1 à
  L. 223-5 d'un même article d'avant : par la chaîne ils se valent tous,
  et « L. 223-5 » déclaré sous un article de texte qui les réécrit tous
  contredisait tout. Ce défaut préexistait ; `docs/46` l'a rendu visible
  en donnant un `vise` à ces amendements.

## 3. Ce que cela fait au graphe

| | avant | après |
|---|---:|---:|
| `porte_sur` internes | 6 971 | **6 847** (− 358 contredits, + 234 résolus) |
| dont `inferee` | 0 | **234** |
| `porte_sur` non résolues | 532 | 656 |
| `vise` | 604 | 581 |
| `depose_sur` · `visee` / `alinea` | 87 / 1 001 | **107** / 970 |
| `depose_sur` | 1 104 | 1 093 |

**Sur les arêtes déjà jugées** — cinq tirages `alinea`, trois `visee`,
quatre `vise` : **neuf `alinea` jugées justes changent d'article**, et
chacune va là où l'arbitre de `docs/46` était allé par le contenu :
L. 423-9 → L. 423-16, L. 423-10 → L. 423-17, L. 423-11 → L. 423-18,
L. 121-20-1 → L. 121-34, L. 121-20-3 → L. 121-34-2, L. 423-8 → L. 423-15.
Les juges avaient jugé par le numéro que le texte écrit ; le contenu dit
sous quel numéro la loi l'a promulgué, et c'est ce numéro que la
restitution montre. Aucune des 62 `vise` justes n'a bougé ; la fausse de
`docs/46` § 3 est corrigée.

## 4. Mesuré

Deux juges Sonnet 5 par fiche, colonnes séparées, arbitre sur désaccord.

| arête | tirage | n | juge A | juge B | accord | arbitrage | verdict | Wilson | constante |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `porte_sur` · `inferee`, résolue par le contenu | parmi les 234 | 20 | 20 | 20 | 20 | — | **20 / 20** | 0,8389 | **0,8389** |
| `vise` · suivie par le contenu, avant la garde du § 5 | les 14 nouvelles du tirage | 14 | 14 | 3 | 3 | 11 → faux | **3 / 14** | 0,0757 | 0,8712, inchangée |

**`porte_sur`.** Les vingt résolutions sont justes, et les juges ont vu ce
que la mesure du § 1 laissait prévoir : le corps de la disposition
identique, seuls les renvois internes renumérotés — « L. 423-6 → L. 423-12,
même décalage que l'article voisin ». Le troisième échelon de la cascade
tient, sur ce qu'on lui demande ici.

**`vise`, 3 sur 14 — et la règle était fausse.** Suivre le glissement du
texte suppose que l'amendement numérote comme le texte. C'est vrai quand
il s'ancre sur ses alinéas — « Rédiger ainsi l'alinéa 41 : « Art. L. 423-8.
– … » » désigne la place du texte devenue L. 423-15, et les trois justes
sont de cette forme. C'est faux quand il **réécrit tout l'article du texte
selon son propre plan** : les amendements 3661 et 4495 de 2013 écrivent
L. 423-1 à L. 423-17 avec, à chaque numéro, une autre disposition que
celle du texte — leur « L. 423-11 » est le droit d'intervention de
l'association, celui du texte la prescription de cinq ans, devenu
L. 423-18. Le juge A a suivi la consigne — « la place, pas le contenu » —,
le juge B a lu les amendements, l'arbitre lui a donné raison onze fois.

La garde qui en sort : sous un article du texte dont la numérotation a
glissé, un « Rédiger ainsi cet article » ne se rattache pas — 21 arêtes
écartées, les onze fausses parmi elles, les trois justes conservées. La
constante de `vise` ne bouge pas : la population qu'elle décrit n'a gagné
que ces trois-là.

## 5. Ce qui n'est pas fait

**Le plan propre hors glissement.** La garde du § 4 ne joue que sous un
article du texte dont un numéro a glissé. Un amendement qui réécrit tout
l'article du texte avec son propre plan sous un article sans glissement
passe encore par la garde ancienne — la loi a-t-elle écrit ce numéro —,
qui ne dit rien de ce qu'il y met. La même famille, un cran plus loin.

**Les 124 non résolus.** Un article écrit que rien ne contient à 0,5 a été
réécrit en navette, ou n'a jamais été promulgué. Les deux se distinguent
par la loi elle-même — a-t-elle produit une version sous *un* numéro
voisin ? — mais pas par le contenu.

**La navette entière.** Le contenu se compare à la version que la loi a
produite ; le texte de commission de première lecture est parfois à trois
lectures de là. Là où la loi a réécrit, le seuil coupe ; ce sont les 21
articles entre 0,3 et 0,4 du § 1, tenus pour contredits et non résolus
sauf si un autre article les contient mieux.
