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

## 4. La XIVe législature n'a pas de source d'amendements à l'Assemblée

Constat vérifié ce jour, et il conditionne tout le rappel restant.

**513 des 832 articles éligibles — 62 % — proviennent de la XIVe législature**,
loi Hamon comprise. Or :

| Législature | Articles éligibles | Amendements AN |
|---|---:|---|
| XIV | 513 | **absent** — l'open data renvoie 404, la page d'archive pointe vers un hôte `data-preprod` qui ne résout pas |
| XIII | 216 | **absent** — aucune archive publiée |
| XV | 49 | disponible (`Amendements_XV.json.zip`, 648 Mo) |
| XVI | 32 | disponible (363 Mo) |
| XVII | 22 | disponible (297 Mo) |

Les anciennes URL du site (`/14/amendements/1015/AN/liste.asp`) rendent 404 ; le
schéma actuel `/dyn/` sert les textes mais pas les listes d'amendements, et
l'API de recherche `query_amendements` rend une liste vide quels que soient les
paramètres essayés.

**Conséquence :** l'extracteur AN, présenté depuis la phase 0 comme le premier
gain de rappel, ne couvrirait que 103 articles sur 832 pour 1,3 Go de
téléchargement. Le gisement principal — les XIIIe et XIVe législatures — n'est pas
accessible par les voies ouvertes. Deux options subsistent, et le choix n'est pas
technique : écrire à l'Assemblée pour obtenir les archives, ou se contenter du
Sénat sur cette période et l'afficher comme une limite du produit.
