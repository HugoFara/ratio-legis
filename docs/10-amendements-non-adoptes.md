# Cinquième tranche — ce qu'un amendement visait, adopté ou non

**Objet :** répondre à « qu'a-t-on déjà tenté sur cet article, et qu'est-ce qui l'a
fait échouer ». **Date : 23 août 2026.**
**Code :** `ingestion/visees.py`. **Schéma :** `schema/003-visee.sql`.

---

## 1. Pourquoi une arête distincte de `resulte_de`

`resulte_de` ne relie que les amendements dont le texte a survécu : 79 sur 19 078.
Elle est muette sur les 5 913 rejetés, 3 638 retirés, 795 irrecevables au titre de
l'article 40 et 597 cavaliers. C'est pourtant ce corpus que le législateur
consulte avant de rédiger.

`vise` est **déclarée**, pas inférée : aucun appariement textuel n'intervient, le
dispositif nomme l'article et la formule qui le modifie. C'est ce qui rend l'arête
possible pour un amendement qui n'a jamais produit une ligne de droit.

Ce que la vue `historique_article` rend, pour L. 311-8-1 :

```
amdt 73        Rejeté   Mme TERRADE   [loi n° 2010-737 du 1er juillet 2010]
amdt 125 rect. Rejeté   M. MÉZARD     [loi n° 2014-344 du 17 mars 2014]
amdt 45        Adopté   M. MÉZARD     [loi n° 2014-344 du 17 mars 2014]
amdt 174       Adopté   M. COINTAT    [loi n° 2014-344 du 17 mars 2014]
```

Le même sénateur a vu son amendement rejeté puis adopté sur le même article, à
quatre ans d'intervalle. C'est exactement l'information qu'aucune source publique
ne restitue aujourd'hui.

| | |
|---|---:|
| Amendements avec une cible déclarée | 146 |
| Arêtes `vise` | 162 |
| Articles du code visés · dont en vigueur | 107 · 56 |
| Adoptés · rejetés · retirés · non soutenus | 55 · 40 · 34 · 17 |

## 2. Cinq formes de la confusion de cible, toutes rencontrées ici

La leçon la plus chère de la phase 0 — neuf faux rattachements sur dix — s'est
présentée cinq fois de suite sous des habits différents. Chaque correction est
issue d'un contrôle à la main.

**Un dispositif cite le droit existant sans le modifier.** « L'article L. 121-36
est ainsi rédigé » vise ; « dans les conditions prévues à l'article L. 121-36 » ne
vise pas. Seule la cible d'une formule de modification est retenue.

**Le numéro ne dit pas le code.** L. 152-1 existe au code de l'environnement,
L. 121-1 à celui de l'urbanisme, et les deux au nôtre. Sur 865 dispositifs citant
un numéro présent dans ce code, la majorité modifiait un autre code.

**Le code est nommé « le », pas « du ».** « Le code de l'énergie est ainsi
modifié : 1° L'article L. 241-2 est ainsi rédigé ». N'accepter que « du code »
laissait passer ces cas : 5 faux sur 14 vérifiés.

**Le code gouverne tout le bloc qui suit.** Il est nommé une fois en tête et la
clause du numéro ne le contient pas. Même convention que « du même code » dans la
tranche des renvois : à défaut de code dans la clause, le dernier code nommé en
amont gouverne.

**Le suffixe appartient au numéro.** « Art. L. 222-1 B » du code de
l'environnement n'est pas L. 222-1 du nôtre, et « L. 111-6-1-3 » du code de la
construction n'est pas L. 111-6-1. Les tronquer fabriquait une identité entre
deux articles sans rapport.

Une sixième restriction est assumée avec son prix : un amendement à un projet de
loi qui n'a produit **aucun** article de ce code ne peut pas en viser un. Elle
écarte 787 amendements — et, avec eux, les « cavaliers » qui tentaient d'ajouter
une disposition de consommation à un texte étranger. C'est un cas intéressant,
sacrifié au faux rattachement (§ 5.3).

## 3. Confiance : 0,6212

Borne inférieure de Wilson à 95 % pour 13 succès sur 15 vérifiés à la main. C'est
la plus basse du graphe. L'échec résiduel est toujours le même : un amendement qui
crée un article dans un autre code sans que ce code soit nommé nulle part dans le
dispositif — le contexte est porté par l'article du projet de loi, pas par
l'amendement. Le résoudre suppose de rattacher l'amendement à l'article du texte
en discussion, donc de charger les textes déposés — déjà récupérés en phase 0.

## 4. Correction : la XIVe législature est disponible

**La conclusion précédente de cette note était fausse et est retirée.** Elle
affirmait que les amendements de l'Assemblée pour la XIVe législature étaient
inaccessibles. Ils sont servis en clair, à cette adresse :

```
/static/openData/repository/14/loi/amendements_legis_XIV/Amendements_XIV.csv.zip
```

L'erreur avait deux causes, et la seconde est la plus instructive. Le chemin
essayé — `amendements_legis/` — était faux d'un suffixe. Et la page d'archives de
l'Assemblée, seule source consultée pour le corriger, publie des URL pointant vers
un hôte `data-preprod` qui ne résout pas : **une page institutionnelle périmée a
été prise pour une preuve d'absence**. Le bon chemin a été retrouvé par l'index
CDX de la Wayback Machine, qui archive l'arborescence du dépôt.

La règle qui en sort : un 404 sur une URL recopiée prouve que l'URL est fausse,
jamais que la donnée est absente.

**Extraction réalisée** — `tools/an/extraire_amendements_an.py`, lecture en flux
du CSV de 420 Mo et 624 colonnes sans décompression sur disque :

| | |
|---|---:|
| Lignes lues | 167 420 |
| **Amendements retenus, 24 textes du périmètre** | **11 117** |
| Rejetés · adoptés | 3 280 · 2 677 |
| Non soutenus · retirés · tombés | 2 436 · 1 191 · 382 |

Le corpus d'amendements passe de 19 078 à 30 195, et il couvre enfin la chambre
de dépôt de la XIVe législature, d'où proviennent **513 des 832 articles
éligibles**.

Deux pièges de format relevés au passage. Les références de texte ont deux
formes — `L14B1015` pour le texte déposé, `L14BTC2442` pour le texte de
commission — et n'en reconnaître qu'une fait perdre la moitié du corpus : 2 195
amendements au lieu de 11 117. Et le sort n'est pas dans la colonne `sort[1]`,
vide sur toute la législature, mais dans `sort[1]/sortEnSeance[1]` ; la colonne
`etat[1]` ne porte que l'état procédural, et la prendre pour le sort ferait
disparaître 3 280 rejets derrière un « Discuté » uniforme.

## 5. Ce qui reste réellement manquant

**La XIIIe législature — 216 articles éligibles — n'a jamais été publiée en open
data.** L'index CDX confirme que le dépôt ne contient que les législatures 14 à
17. En revanche, la Wayback Machine archive les pages d'amendement individuelles
du site de l'époque, sous la forme
`assemblee-nationale.fr/13/amendements/<texte>/<texte><numéro>.asp`. La voie est
donc une reconstitution par archive, page par page, et non un fichier à charger.

**Les auteurs ne sont pas nommés** dans le fichier des amendements : les colonnes
portent des références `PA…` et `PO…`, résolues par le jeu Acteurs de
l'Assemblée. Sans ce chargement complémentaire, les 11 117 amendements ont un
sort mais pas de signataire.

**Le chargement en base reste à faire.** Cette tranche produit l'extraction et
l'outil ; l'alimentation de `amendement`, `resulte_de` et `vise` côté Assemblée
est la tranche suivante.
