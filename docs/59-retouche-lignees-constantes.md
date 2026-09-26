# Cinquante-troisième tranche — la retouche, les lignées renumérotées, les constantes

**Objet :** solder les trois restes de `docs/58` § 8 : la famille « incise »
de `resulte_de`, la scission des lignées arrivées d'un autre numéro
(`docs/57` § 6), les constantes de confiance sur un tirage unique de la base
finale.
**Date : 26 septembre 2026.**
**Code :** `tools/mesures/juger.py`, `ingestion/legi_vers_graphe.py`,
`ingestion/lignees.py`, `ingestion/visees.py`, `ingestion/textes_deposes.py`,
`ingestion/textes_des_amendements.py`, `ingestion/amendements_vers_resulte_de.py`.
**Données :** `precision-vise-constante.tsv`, `precision-resulte-de-constante.tsv`,
`precision-depose-sur-visee-constante.tsv`, `precision-depose-sur-alinea-constante.tsv`,
`precision-depose-sur-article-entier-constante.tsv` ; `precision-resulte-de-xiiie.tsv`
et `precision-resulte-de-xve.tsv` ré-arbitrées.
**Juges :** deux Sonnet 5 par fiche, colonnes séparées ; arbitre Opus 5.5.

---

## 1. La retouche compte

Les trois `resulte_de` fausses que `docs/57` et `docs/58` laissaient en base
étaient des incises : un amendement qui insère huit mots, ou retire un
plafond, dans un alinéa rédigé ailleurs. Une garde « le dispositif ne touche
que des mots » a été mesurée sur les 421 arêtes jugées :

| dispositif | justes | fausses |
|---|---:|---:|
| rédige ou insère un alinéa | 349 | 25 |
| ne touche que des mots | **31** | **6** |

Elle retirait 31 justes pour 6 fausses. La mesure a surtout montré que la
définition n'était pas fixée : les juges des tranches anciennes comptaient
juste la substitution d'un mot (« personne » → « personnes »), ceux de la
XIIIe et de la XVe, à qui `docs/57` § 3 avait donné la règle de l'incise,
la comptaient fausse — le même dispositif est juste dans une fiche et faux
dans une autre.

**Décision de l'auteur : l'alinéa résulte aussi de l'amendement qui l'a
retouché**, quand la retouche est dans l'alinéa en vigueur. La restitution
distingue déjà l'alinéa introduit de l'alinéa retouché (`docs/25`). La
définition est écrite dans `juger.py`. Les trois incises sont rejugées
justes, chacune vérifiée sur l'alinéa : l'incise de 349 rect. y est, celle
de 252 aussi, et le plafond que 236 supprimait n'y est plus. Il n'y a pas de
garde à poser.

## 2. Les lignées renumérotées, et le sens du numéro

La règle de `docs/57` § 6 est remise : une version qui succède par
modification à une version sans rapport (moins de 0,2) et reprend le texte
d'un autre numéro fermé le même jour (0,7 et plus) ouvre une lignée — 87
lignées nouvelles. Elle avait été retirée parce que `Resolveur.du_dossier`
prend la lignée qu'un texte du dossier a écrite, et que la loi qui renumérote
est souvent celle du dossier de l'amendement.

Le numéro dit lui-même laquelle il désigne. « L'article L. 311-14 devient
l'article L. 311-20 », « … est abrogé », « … est ainsi modifié » nomment
l'article tel qu'il est au jour du texte ; « il est inséré un article
L. 311-14 », « Art. L. 311-14. – … » nomment celui que la loi crée.
`du_dossier` prend un paramètre `existant` : pour l'existant, quand la lignée
en vigueur au jour du texte est close par une telle arrivée
(`closes_par_arrivee`), c'est elle. La recodification de 2016, qui clôt par
abrogation, n'est pas touchée. Le sens est lu par `vise` (`cree_par`) et par
la première passe de `porte_sur` (« un article L. X » est une création).

**La lignée arrivée descend de sa source.** LEGI ne déclare pas l'arrivée —
il écrit une modification —, et la coupe laissait la lignée nouvelle sans
ancêtre. `renumerote_de` reçoit donc, pour chacune des 87, un lien vers la
version fermée dont elle reprend le texte, méthode `inferee`, la similarité
pour confiance. Et la lignée close par une arrivée est corroborée, pour
`motive`, par la loi qui produit ce qu'elle devient (`rattachements_legi`) :
la section de rapport qui commente « l'article L. 311-14 devient l'article
L. 311-20 » n'était plus corroborée.

**Ce que la coupe retire, à raison.** L'article en vigueur n'hérite plus des
textes de la disposition qu'il a remplacée. Les articles remontant à un
passage motivant passent de 800 à 791, ceux dont un rapport au Président
motive le texte de 799 à 781 ; `motive` compte 1 721 arêtes au lieu de 1 726.
L'ordonnance n° 2005-428 sur les incapacités en matière commerciale sort de
l'historique : elle ne modifiait que la version de 2005 de L121-29, dans la
lignée que l'arrivée de 2014 a close — le L121-29 en vigueur n'en descend
pas. Un rapport de commission de moins est récolté pour la même raison.

**Le harnais.** Aucune juste perdue (61, comme avant). L311-14 ← 17 et
L311-34 ← 321, qui cassaient en `docs/57` § 6, tiennent. Douze justes
changent de lignée, toutes vers la bonne : les amendements de 2010 sur
L331-6 et L331-11 vers la lignée en vigueur depuis 1995 ; l'amendement qui
complète L224-3 sur les offres de gaz vers la lignée de 2016, non la
commission de 1993 ; les amendements à la loi J21 qui écrivent le livre VII
vers la lignée de 2018 ; celui qui rédige L121-79-4 vers la lignée de 2014,
dont il écrit le contenu. Les juges avaient jugé juste l'article fusionné.

## 3. Les constantes

Chaque constante réunissait des tirages pris sur des populations réparées à
des moments différents. Elles sont re-mesurées sur un **tirage unique de la
base finale** — Sénat et Assemblée, XIIIe à XVIIe législature, après les
gardes de `docs/57`, `docs/58` et § 2 —, 40 arêtes par arête, qu'aucune fiche
n'avait jugées, dans l'ordre de la clef.

| arête | n | juge A | juge B | arbitrées | verdict | Wilson | constante d'avant |
|---|---:|---:|---:|---:|---:|---:|---:|
| `vise` · déclarée | 40 | 40 | 40 | — | **40 / 40** | **0,9124** | 0,8621 |
| `resulte_de` | 40 | 36 | 36 | — | **36 / 40** | **0,7695** | 0,8402 |
| `depose_sur` · `visee` | 40 | 40 | 40 | — | **40 / 40** | **0,9124** | 0,8177 |
| `depose_sur` · `alinea` | 40 | 39 | 39 | — | **39 / 40** | **0,8712** | 0,9112 |
| `depose_sur` · `article_entier` | 40 | 37 | 36 (+1 douteuse) | 2 | **37 / 40** | **0,8014** | 0,6886 |

**Les arbitrages.** `article_entier` L141-6 ← 8 du Sénat : les deux juges
l'ont dite fausse, parce que « Rédiger ainsi cet article » récrit l'article
vers l'article 32 de la loi du 9 juillet 1991. Mais ce que cet article règle
— les frais de l'exécution forcée — est l'objet même de L141-6, qui met les
droits de recouvrement à la charge du professionnel : une autre rédaction du
même objet. Juste, comme le précédent que le code inscrit sur cette arête.
L215-2-4 ← 42 : le dispositif remplace « les médecins » au II de l'article 2,
qui n'a ni II ni ce mot dans aucune de ses versions ; le jeu est rattaché à un
texte qui n'est pas le sien. Fausse.

**Ce que disent les fausses.**

- `resulte_de`, quatre : deux formules partagées — un plafond en
  pourcentage du chiffre d'affaires mondial, la référence au règlement (UE)
  2022/2065 « précité » —, un segment voisin de celui que l'amendement a écrit
  (L412-9 : l'amendement écrit le segment 1, l'arête pointe le 0), une
  rédaction non retenue au profit de celle d'un autre amendement de la même
  auteure. Ce sont les familles de `docs/54` § 1, sans garde simple.
- `alinea`, une : un « I bis. – … il est inséré une section 2 bis ainsi
  rédigée » inséré après l'alinéa 142, qui écrit L121-25-1 ; l'alinéa 142
  gouvernait L121-33. `insere_une_instruction` ne cherchait qu'un article
  nommé ; il cherche aussi une division. Gardée.
- `article_entier`, trois : un « I » ajouté en tête de l'article qui supprime
  deux phrases de L621-6 ; un « Rédiger ainsi cet article » qui insère
  L121-2-1 et L121-2-2 après L121-2, que la garde du voisin laisse passer
  parce que L121-2, l'ancre, y est nommé ; le jeu rattaché au mauvais texte.

`resulte_de` descend sous 0,8 : c'est la mesure, non un recul — les tirages
d'avant, réunis, mêlaient des populations que les gardes successives avaient
nettoyées de leurs fausses après coup. `article_entier` monte de 0,69 à 0,80
par les gardes de `docs/58`.

## 4. Ce qui n'est pas fait

- les familles de fausses `resulte_de` du § 3, sans garde simple ;
- la garde du voisin ne distingue pas l'ancre (« après l'article L. 121-2,
  il est inséré… ») de la cible ;
- `vise` · par le contenu (0,7412) et les constantes de `porte_sur` ne sont
  pas re-mesurées ici ;
- les liens `inferee` d'une arrivée ne sont pas mesurés en eux-mêmes : ils
  valent ce que vaut la coupe, dont le harnais n'a relevé aucun déplacement
  faux.

Le harnais, en fin de tranche : 61 perdues ; 15 fausses présentes — les 8
d'avant `docs/57` et les 7 que les tirages du § 3 ont trouvées, sans garde.
