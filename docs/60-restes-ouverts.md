# Cinquante-quatrième tranche — l'ancre, l'autre norme, le départ, les constantes restantes

**Objet :** solder `docs/59` § 4 : la garde du voisin qui confond l'ancre et
la cible, les familles de fausses `resulte_de`, les constantes de `vise` par
le contenu et de `porte_sur`. La mesure de `porte_sur` a fait apparaître un
défaut plus large : la lignée qu'un texte vide en renumérotant.
**Date : 26 septembre 2026.**
**Code :** `ingestion/textes_des_amendements.py`, `ingestion/amendements_vers_resulte_de.py`,
`ingestion/legi_vers_graphe.py`, `ingestion/lignees.py`, `ingestion/visees.py`,
`ingestion/textes_deposes.py`.
**Données :** `precision-porte-sur-declaree-constante.tsv`,
`precision-porte-sur-declaree-constante-2.tsv`, `precision-porte-sur-citation-constante.tsv`,
`precision-porte-sur-contenu-constante.tsv`, `precision-vise-par-le-contenu-constante.tsv`.
**Juges :** deux Sonnet 5 par fiche ; arbitre Opus 5.5.

---

## 1. L'ancre n'est pas nommée comme cible

« Rédiger ainsi cet article : après l'article L. 121-2, sont insérés des
articles L. 121-2-1 et L. 121-2-2 » écrit deux voisins de L121-2, qui n'est que
le repère. La garde du voisin (`docs/42`, `docs/58`) cherchait si le
dispositif nommait A ; il le nommait, en ancre, et l'arête passait.
`articles_nommes_par` retire les ancres (`ANCRE_NOMMEE`) avant de lire. La
fausse `article_entier` L121-2 ← 1838 de `docs/59` § 3 est écartée.

## 2. `resulte_de` : ce qui se sépare, et ce qui ne se sépare pas

Trois grandeurs mesurées sur les 453 arêtes jugées — la part de l'alinéa que
le dispositif de l'amendement contient, la meilleure part contenue par un
autre amendement du dossier, la meilleure part d'un autre alinéa du même
article contenue par le même amendement :

| règle | fausses retirées | justes retirées |
|---|---:|---:|
| un autre alinéa du même article mieux couvert (le segment voisin) | 1 | 2 |
| un autre amendement du dossier couvre mieux (la rédaction concurrente) | 4 | 3 |
| l'alinéa peu couvert (moins de 0,15) | 5 | 4 |
| **l'amendement n'agit que sur une autre norme** | **5** | **0** |

Les trois premières ne séparent rien, comme `docs/54` § 1 l'avait conclu sur
la moitié des verdicts. La quatrième est posée
(`agit_sur_une_autre_norme`) : un dispositif qui, hors citation, ne vise
qu'une autre loi ou un autre code — « L'article L. 631-1 du code monétaire et
financier est complété… », « Après l'article 8 de la loi n° 81-766… » — et ne
nomme aucun article du nôtre ne peut être l'origine d'un alinéa de notre code.
La mesure a été refaite sur l'amendement réellement relié au segment, non sur
le premier amendement de ce numéro : une première passe comptait à tort une
juste, un amendement homonyme du même dossier. 4 028 amendements sont écartés
à ce titre ; les cinq fausses qu'elle vise étaient déjà hors de la base par
d'autres gardes, et les quatre fausses du tirage de `docs/59` § 3 ne sont pas
de cette forme : leur dispositif est tout entier une citation (« Rédiger ainsi
l'alinéa 2 : « … » »). Elles restent, sans règle.

## 3. Le départ, et le sens du numéro

La mesure de `porte_sur` déclarée (§ 4) a donné **32 sur 40**. Cinq des huit
fausses venaient d'une même phrase de la loi Lagarde : « l'article L. 311-7
devient l'article L. 311-28 », puis un L311-7 neuf. L'ancien texte part vers
un autre numéro ; LEGI écrit une modification de L311-7 ; la coupe à
l'arrivée (`docs/59` § 2) ne voit rien, puisque le texte neuf ne vient
d'aucun numéro. L'arête « l'article 1er B renumérote L311-7 » tombait sur le
L311-7 que 1er B n'écrit pas.

**La coupe au départ**, symétrique de l'arrivée : une version close par une
modification sans rapport avec la suivante (moins de 0,2), dont le texte se
retrouve dans un autre numéro en vigueur au jour où elle se ferme — ouvert ce
jour-là ou avant : LEGI fait courir le texte de L311-7 sous L311-28 dès
septembre 2010 et ne le retire de L311-7 qu'en mai 2011. Le seuil est celui de
la même disposition (0,5), non celui de l'arrivée : le texte neuf ne partage
déjà presque rien avec l'ancien, et l'ancien, retouché au passage, n'est
repris qu'à 0,65. La destination reçoit un lien `renumerote_de` inféré. Les
lignées passent de 3 964 à 4 058 ; 232 liens inférés en tout.

**Le sens du numéro, resserré.** `docs/59` § 2 traitait comme « existant »
tout numéro que le texte ne crée pas. C'était trop : « L'article L. 121-79-4
est ainsi rédigé : les personnes physiques… » écrit la lignée de 2014, et le
résolveur l'envoyait à celle de 2010. Seul ce qui fait **quitter** l'article —
« devient », « deviennent », « est abrogé » — désigne la lignée en vigueur au
jour du texte (`lignees.quitte`) ; « est ainsi rédigé », « est modifié »,
« est complété » désignent la version qui en résulte.

**Le harnais.** 61 justes perdues, comme avant. Une seule arête jugée juste
disparaît, remplacée dans le compte par une autre : `depose_sur` L311-34 ←
321 (XIIIe), qui ne tenait que par la chaîne reliant L311-35, devenu L311-49 —
seul article que l'amendement déclare —, à L311-34 fusionné. La voie qui la
trouverait honnêtement est celle de l'alinéa (« après l'alinéa 9 »). 64
justes changent de lignée ; celles qu'on a relues vont toutes à la bonne : 27
amendements à la loi Lagarde qui écrivent « Art. L. 311-17. – … crédit
renouvelable… » vers la lignée de 2011, non l'ancien « Tant que l'opération
n'est pas définitivement conclue » ; « l'article L. 311-9 est abrogé » (2010)
vers l'ancienne lignée, « substituer au mot « vérifie » le mot « évalue » »
vers la nouvelle ; L311-13, L331-5, L733-9 vers la lignée dont l'amendement
écrit le contenu.

**Ce que la coupe retire encore.** Les articles remontant à un passage
motivant passent de 791 à 792 (787 dans la partie L), ceux motivés par un rapport au Président de 781
à 771 : l'article en vigueur n'hérite plus du rapport de la disposition qu'il
a remplacée.

## 4. Les constantes restantes

Sur un tirage unique de la base, arêtes qu'aucune fiche n'avait jugées.

| arête | n | verdict | Wilson | constante d'avant |
|---|---:|---:|---:|---:|
| `vise` · par le contenu | 14 (toutes) | **14 / 14** | **0,7847** | 0,7412 |
| `porte_sur` · article écrit | 40 | **39 / 40** | **0,8712** | 0,7218 |
| `porte_sur` · résolue par le contenu | 40 | **40 / 40** | **0,9124** | 0,8389 |
| `porte_sur` · déclarée, avant le départ | 40 | 32 / 40 | 0,6524 | 0,9094 |
| `porte_sur` · déclarée, tirage disjoint après | 40 | **37 / 40** | **0,8014** | — |

**Les arbitrages.** `vise` par le contenu : six désaccords, le second juge
tenant pour fausse la tentative dont un autre amendement, adopté, a fourni le
texte de la loi ; c'est le critère de `resulte_de`, `vise` compte la tentative
(`docs/57` § 3) — justes. `porte_sur` déclarée, premier tirage : l'abrogation
de L123-6 « dans sa rédaction antérieure » pour certains territoires abroge A —
juste ; L311-8-1, que l'article 18 réécrit et que la loi n'a pas retenu, juste :
`porte_sur` dit ce que l'article du texte fait, non ce que la loi garde. Les
arêtes que le départ a déplacées sont rejugées sur la base réparée : L311-7,
L311-17 (deux), L311-26 pointent désormais l'article que 1er B renumérote,
L121-79-4 la lignée que « ainsi rédigé » écrit, L121-20-10 celle que « devient »
quitte. Reste L311-8 : 1er B abroge l'ancien texte, qui ne part nulle part, et
un autre article en écrit un neuf sur place — aucune coupe ne le voit. Second
tirage : L112-11 créé par le texte sur l'impact environnemental de la
livraison, alors que la seule lignée L112-11 du fonds est l'origine des
denrées — fausse.

La constante de `porte_sur` déclarée, la plus nombreuse du graphe (plus de
sept mille arêtes), était surestimée : 0,91 réunissait des tirages de
populations anciennes. Elle est de **0,80**.

## 5. Ce qui n'est pas fait

- `resulte_de` : le segment voisin, la rédaction concurrente, la formule
  partagée à l'intérieur d'un alinéa cité — sans règle séparatrice ;
- la réécriture sur place d'un article abrogé (L311-8), que ni l'arrivée ni
  le départ ne voient ;
- `depose_sur` L311-34 ← 321, à retrouver par la voie de l'alinéa.

- les 40 `resulte_de` que les liens de départ ont ajoutées (653 → 693) :
  la chaîne de renumérotation atteint désormais des segments qu'elle ne
  voyait pas, et elles ne sont pas mesurées ; la constante (0,7695) l'a été
  avant elles.

Le harnais, en fin de tranche : 1 398 justes tenues, 61 perdues ; 19 fausses
présentes — les 8 d'avant `docs/57` et les 11 que les tirages de `docs/59` et
de cette tranche ont trouvées sans garde (quatre `resulte_de`, deux
`article_entier`, un `porte_sur` par l'article écrit, quatre `porte_sur`
déclarées).
