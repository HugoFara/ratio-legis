# Vingt-quatrième tranche — le sort des amendements

**Objet :** répondre à « qu'a-t-on tenté sur cet article, et qu'est-ce qui l'a
fait échouer ». **Date : 24 août 2026.**
**Code :** `ingestion/sort_des_amendements.py`, `restitution/tentatives.py`.
**Schéma :** `schema/010-sort.sql`.

---

## 1. Le sort était rendu, et il était rendu faux

`docs/11` § 5 posait le reste à faire ainsi : « le sort n'est pas exploité en
restitution ; c'est le produit législateur qui reste à écrire, pas la donnée qui
manque ». La première moitié était inexacte, et il faut le dire avant tout le
reste : la fiche de `graphe.py` portait bien une section « CE QUI A ÉTÉ TENTÉ ».

Elle portait aussi ses défauts, qui sont ceux qu'on obtient en affichant une
colonne sans la lire :

| Ce que la fiche faisait | Ce que ça valait |
|---|---|
| tri `CASE sort WHEN 'Adopté' THEN 0 ELSE 1` | « Adopté - vote unique » rangé parmi les échecs |
| libellé rendu brut | « Irrecevable art. 45, al. 1 C (cavalier) » n'apprend rien à qui ignore ce qu'interdit l'article 45 |
| sort vide affiché « ? » | 1 141 amendements de l'Assemblée dont le sort est écrit dans la colonne voisine |
| cinq colonnes, sans l'objet ni l'adresse | on lit qu'un amendement a été rejeté, jamais ce qu'il proposait |
| source `vise` seule | un amendement qui a écrit un alinéa sans nommer l'article n'y figure pas |

Le vrai reste à faire n'était donc pas d'écrire un produit à partir d'une donnée
saine : c'était de rendre la donnée lisible, puis d'en tirer un produit. Trois
défauts se tenaient devant, et deux d'entre eux rendaient le sort **faux**, pas
seulement pauvre.

## 2. Le premier défaut est une conclusion fausse qu'on aurait publiée

L'Assemblée publie deux colonnes voisines : le sort en séance
(`sort[1]/sortEnSeance[1]`) et l'état procédural (`etat[1]`). `docs/10` § 4 avait
tranché en faveur de la première, et avait raison : `etat` vaut « Discuté » sur
les 9 966 amendements qui ont un sort, et le prendre pour le sort aurait effacé
3 280 rejets derrière un mot uniforme.

La réciproque n'avait pas été regardée. Sur les **1 149 amendements sans sort
publié**, `etat` n'est pas vide :

| `etat`, quand `sort` est vide | |
|---|---:|
| Retiré | 694 |
| **Irrecevable** | **447** |
| A discuter | 8 |

Huit amendements sur 11 115 sont réellement en attente. Les 1 141 autres ont un
sort, écrit dans l'autre colonne.

Ce que cela produisait à l'écran est pire que l'absence : le Sénat affichait
1 735 irrecevabilités, l'Assemblée **zéro**. Un lecteur en aurait tiré la
conclusion qu'une chambre écarte des amendements sans les discuter et que l'autre
ne le fait jamais. C'est faux, et c'est le genre de chiffre qu'un produit
d'hygiène législative n'a pas le droit de publier de travers.

## 3. Le deuxième défaut est un bloc de style Word

Soixante-trois amendements du Sénat portaient un sort illisible :

```
sort = '{font-family:"Cambria Math"; '
sort = '{mso-style-parent:""; '
sort = 'margin:0cm; '
```

Un objet rédigé sous Word et collé dans Améli emporte son bloc `<style>`, dont
les déclarations sont **indentées par des tabulations**. Le jeu Améli étant
séparé par des tabulations, le champ se scinde en autant de colonnes : tout ce
qui suit l'objet glisse vers la droite, et le sort reçoit un fragment de feuille
de style. Les colonnes situées avant — numéro, auteur, subdivision — étaient
intactes, ce qui rendait l'enregistrement crédible.

La réparation n'interpole rien et se fait dans `lire_ameli` :

- les **sept champs de tête** et les **quatre de queue** sont pris à leurs deux
  extrémités, où aucun décalage n'est possible ;
- ce qui reste au milieu est le couple Dispositif / Objet, recoupé sur la marque
  `<body` — les deux champs commencent par elle, sans exception sur les 19 534
  dispositifs et 19 533 objets non vides du corpus, et un dispositif non vide
  n'en porte jamais deux.

Vérification : les 63 enregistrements rendent une URL d'amendement du Sénat
bien formée, et les **22 039 autres sont rendus à l'identique** de la lecture
précédente — la réparation ne touche que ce qui était cassé.

C'est le troisième défaut de cette famille dans le projet, après le chemin
d'archive de `docs/10` § 4 et l'attribut de balise de `docs/14`. La règle qui s'en
dégage : **un format tabulaire dont un champ contient du HTML n'est pas un format
tabulaire**, et il faut le lire par ses bords.

## 4. Le troisième défaut est un libellé qu'on ne peut pas additionner

« Adopté » et « Adopté - vote unique » sont le même sort — le vote unique est une
modalité de scrutin, pas un résultat. Le second n'était compté nulle part, et
surtout : la construction de `resulte_de` sélectionnait ses candidats par
`sort = 'Adopté'`, comparaison littérale qui écartait 22 amendements adoptés du
périmètre. `est_adopte()` est désormais le seul endroit du dépôt qui répond à la
question, sur le modèle de `citation.py` — une règle, un endroit.

À l'inverse, « Irrecevable art. 40 C » et « Irrecevable art. 45, al. 1 C
(cavalier) » ne sont pas le même fait : le premier dit que l'amendement aggravait
une charge publique, le second qu'il était hors sujet. La famille sert à compter,
le **libellé source est conservé verbatim** pour citer, et le motif est extrait à
part.

Huit familles, et pas une de plus : `adopte`, `rejete`, `retire`, `non_soutenu`,
`tombe`, `irrecevable`, `non_statue`, `inconnu`. La table porte aussi `source`,
qui dit **dans quelle colonne le sort a été lu** — un sort déduit de l'état
procédural ne vaut pas un sort publié comme tel, et la restitution le dit à
l'écran.

## 5. Ce que la restitution rend

`restitution/tentatives.py`, et `GET /articles/{numero}/tentatives`.

Deux voies de rattachement, distinguées à l'écran comme l'exige la règle § 5.4 :

| Voie | Ce qu'elle établit | Confiance |
|---|---|---:|
| `alinéa écrit` | l'amendement a écrit un alinéa qui subsiste — `resulte_de` puis `repris_de` | 0,893 |
| `cible déclarée` | le dispositif nomme l'article et la formule qui le modifie — `vise` | 0,621 |

La seconde est la seule ouverte à un amendement rejeté, qui par construction n'a
écrit aucun texte. C'est aussi la plus faible confiance du graphe, et elle est
affichée telle quelle sur chaque tentative.

**Le module ne juge pas.** « Retiré » est un fait ; savoir si l'auteur a cédé ou
obtenu satisfaction se lit dans le compte rendu de séance, que le graphe ne
contient pas. Le sort est nommé, jamais interprété — c'est la même règle que pour
le classement de `docs/28`.

**Un fait s'y lit pourtant sans commentaire.** L'irrecevabilité au titre de
l'article 40 de la Constitution est le seul motif d'échec dont la cause soit
publiée : l'amendement coûtait de l'argent et n'a jamais été discuté. Le rendre
visible, avec son auteur, est exactement ce que le § 4.3 de la feuille de route
appelle « un résultat de premier ordre ».

## 6. Ce que ça donne, mesuré

**Le sort, sur les 33 217 amendements du corpus.** Aucun libellé n'échappe plus
aux huit familles — le test de contrat de `sort_des_amendements.py` en compte
zéro, contre 63 avant la réparation d'Améli.

| | Assemblée | Sénat |
|---|---:|---:|
| adopté | 2 677 | 5 112 |
| rejeté | 3 280 | 6 655 |
| retiré | **1 885** (dont 694 lus dans l'état) | 5 810 |
| non soutenu | 2 436 | 1 912 |
| tombé | 382 | 877 |
| **déclaré irrecevable** | **447** (tous lus dans l'état) | **1 735** |
| non examiné | 8 | 1 |
| sort illisible | 0 | 0 *(63 avant)* |

Les 447 irrecevabilités de l'Assemblée n'étaient visibles nulle part. Les
retraits passent de 1 191 à 1 885.

**Le fondement de l'irrecevabilité**, sur les 2 182 amendements écartés :

| Fondement | | |
|---|---:|---|
| article 40 de la Constitution | 905 | aggravait une charge publique |
| article 45 de la Constitution | 603 | cavalier, sans lien avec le texte |
| non précisé | 449 | l'Assemblée écrit « Irrecevable » sans motif |
| article 44 bis du règlement du Sénat | 117 | règle de l'entonnoir |
| article 41 de la Constitution | 93 | relevait du domaine réglementaire |
| LOLF · LOLFSS | 9 · 6 | contraire à une loi organique |

**Ce que le produit rend, au grain de l'article en vigueur.** 156 articles sur
2 104 — **7,4 %** — portent au moins une tentative : 83 par la cible déclarée,
83 par l'alinéa écrit, 10 par les deux. Réunir les deux voies double donc la
couverture de la table que la fiche affichait, qui n'en connaissait qu'une.

| | |
|---|---:|
| tentatives rendues | 233 |
| dont abouties | 145 |
| dont non abouties | 88 |
| articles portant au moins un échec | 56 |
| irrecevabilités atteignant un article en vigueur | 5 |

> **Chiffres de cette tranche seule.** La suivante ajoute une troisième voie de
> rattachement — la subdivision déposée — et les porte à 163 articles, 454
> tentatives, 257 non abouties, 65 articles portant un échec. Voir
> [`docs/31`](31-correspondance-des-textes.md) § 6.

Les 5 sont toutes du Sénat et toutes au titre de l'article 45. Les 447 de
l'Assemblée sont désormais **comptées**, mais aucune n'atteint encore un article
en vigueur : la couverture de `vise` du côté Assemblée est trop mince pour cela,
et le dire est plus utile que de laisser croire au contraire.

**Coût.** 12,6 ms de médiane par article, 15,7 ms au 95<sup>e</sup> centile ;
15,5 ms pour le classement des articles les plus disputés sur tout le fonds.

**Ce qui n'a pas bougé.** `resulte_de` reste à **279 arêtes** et `vise` à **276**.
Le passage de la comparaison littérale à `est_adopte()` élargissait la population
candidate de 22 amendements ; aucun n'a produit d'arête. Les 168 justes sur 179
de `docs/21` portent donc toujours sur le même graphe, et la précision publiée
n'est pas à re-mesurer.

## 7. Un effet de bord : la restitution devient un détecteur

En choisissant les exemples à versionner, L112-1-1 — la règle du prix antérieur
sur trente jours — s'est présentée avec une tentative unique, adoptée, du
Gouvernement, portant sur *« une commission territoriale de la préservation des
espaces naturels, agricoles et forestiers »* en Corse.

L'arête est fausse. Le dispositif dit « Après l'article L. 112-1-1, il est inséré
un article L. 112-1-… » sans nommer son code, qui est le code rural ; la
convention légistique de `visees.py` — l'absence de mention vaut « le même
code » — la rattache donc au nôtre, et le dossier passe le filtre parce que la
loi d'avenir agricole a bien produit, par ailleurs, des articles du code de la
consommation. C'est mot pour mot le mode d'échec résiduel que `docs/10` § 3
décrit et que la confiance de 0,6212 chiffre.

Ce qui est neuf n'est pas le défaut : c'est qu'on le voie. La fiche affichait
`amdt 816 | Adopté | LE GOUVERNEMENT | inséré` — quatre colonnes où rien ne
détonne. **Afficher l'objet rend l'erreur évidente à la lecture**, sans requête
ni échantillonnage. La correction relève de `visees.py`, non de cette tranche, et
elle demande de rattacher l'amendement à l'article du texte en discussion — donc
les textes déposés, qui restent le chaînon manquant du projet.

## 8. Ce que cette tranche ne fait pas

**Elle n'ajoute aucune arête.** `vise` et `resulte_de` sont celles des cinquième
et quatrième tranches, inchangées dans leur méthode. La couverture de `vise`
reste ce qu'elle est, et le silence d'un article n'est pas un silence du
Parlement : c'est l'absence des amendements de la XIII<sup>e</sup> législature de
l'open data (`docs/10` § 5) et celle des législatures XV à XVII, non chargées.

**Elle ne rend pas les amendements de l'Assemblée citables.** Le jeu open data ne
publie pas d'adresse par amendement, les anciennes rendent 404, et le schéma
`/dyn/` ne les sert pas. La règle de `docs/10` § 4 s'applique — un 404 sur une URL
recopiée prouve que l'URL est fausse, jamais que la donnée est absente : rien
n'est fabriqué, et la fiche affiche « pas d'adresse publiée dans le jeu open data
de la chambre » plutôt qu'un lien mort.

**Elle ne touche pas à la note « pourquoi cet article ».** Un amendement rejeté
n'explique pas l'article : il n'est pas de la provenance, et n'a rien à faire
sous le contrat du § 4.3. C'est le raisonnement de `docs/10` § 1, appliqué à la
restitution comme il l'avait été au modèle de données.
