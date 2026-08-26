# Vingt-septième tranche — l'article écrit dans la citation

**Objet :** amener l'étude d'impact au grain de l'article. **Date : 26 août 2026.**
**Code :** `ingestion/textes_deposes.py`, `ingestion/sections_vers_motive.py`.

---

## 1. Ce qu'on cherchait, et ce qu'on a trouvé à la place

`docs/32` § 5 concluait qu'il fallait écrire un découpeur d'étude d'impact, la
structure de ces documents n'ayant rien de commun avec celle d'un rapport de
commission. Le découpeur a été écrit ; il rend **3 articles en vigueur**.

Ce n'était donc pas le chaînon. Il était en amont, et il est plus large.

## 2. `porte_sur` était aveugle aux réécritures de section

L'article 5 du projet de loi consommation ne nomme aucune cible dans son
instruction. Il dit :

> La section 2 « Ventes de biens et fournitures de prestations de services à
> distance » et la section 3 « Démarchage » du chapitre I<sup>er</sup> du titre II
> du livre I<sup>er</sup> du même code **sont remplacées par les dispositions
> suivantes** : « Section 2 « Contrats conclus à distance et hors établissement
> « **Art. L. 121-16.** – Au sens de la présente section…

Vingt-huit articles du code y sont réécrits, et `porte_sur` n'en voyait aucun :
sur les treize articles du texte déposé ayant une cible interne, ni l'article 5,
ni l'article 13, ni l'article 21 — c'est-à-dire précisément ceux dont l'étude
d'impact parle.

La cause est une règle juste, appliquée trop largement. `docs/16` pose qu'une
référence **citée** n'est jamais une cible : entre guillemets, `L. 121-1` est un
morceau de la règle nouvelle ou de l'ancienne, pas ce que le texte modifie. C'est
vrai — sauf pour une forme, et une seule.

**L'en-tête d'un alinéa cité n'est pas une référence à du droit existant.** C'est
la désignation de l'article qu'on écrit, et c'est la seule chose que le texte en
dise. La forme est exacte : un guillemet ouvrant, `Art.`, le numéro. `visees.py`
la retient depuis la cinquième tranche pour la même raison.

**10 014 relevés**, dont 8 895 déjà déclarés par l'instruction — ceux-là ne sont
pas comptés deux fois, la voie déclarée étant la mieux établie.

## 3. Le code hôte y est implicite, et il dérive

Premier contrôle à la main sur quinze arêtes internes : **sept justes**. Les huit
autres rattachaient au code de la consommation des articles du code du tourisme
(« Constitue un forfait touristique »), de la propriété intellectuelle
(« l'atteinte à une indication géographique ») ou monétaire et financier
(« la personne démarchée dispose d'un délai »).

La cause n'est pas la règle mais l'hôte. Dans l'instruction, le code est nommé
dans la même phrase que la référence. Dans la citation, il ne l'est pas : il a été
nommé une fois, loin en amont, en tête du bloc modificateur — et un texte qui
modifie plusieurs codes à la suite fait dériver la dernière mention.

## 4. La garde ne devine pas le bon code : elle demande à LEGI

Chercher mieux l'hôte, c'eût été raffiner une heuristique. La garde retenue
interroge une **source indépendante du texte en discussion** : *la loi issue de ce
dossier a-t-elle produit une version de cet article ?* `produite_par` et
`issu_de` le disent, et elles viennent de LEGI.

Si la loi ne l'a pas produit, l'article du texte ne l'écrivait pas.

Les huit fausses de l'échantillon y tombent toutes. **179 arêtes internes sont
écartées sur 753.** Second tirage, disjoint du premier et postérieur à la garde :
**15 justes sur 15**, borne inférieure de Wilson à 95 % **0,7961**. C'est la
valeur portée par les arêtes de cette voie, distincte des 0,8389 de la voie
déclarée — deux voies, deux confiances, comme l'exige le § 5.4.

La voie déclarée n'est pas soumise à la garde : son code est nommé dans la même
phrase, et `docs/16` § 4 en mesure la précision à 20/20. Une garde utile à l'une
n'est pas gratuite pour l'autre.

## 5. Le découpeur d'étude d'impact, une fois qu'il sert à quelque chose

La loi organique du 15 avril 2009 impose à l'étude d'impact un gabarit : un
en-tête `Article N : titre`, puis diagnostic, état des lieux, objectifs
poursuivis, options, impacts, consultations. C'est cette convention qui découpe,
et trois pièges l'entourent, tous rencontrés :

| Piège | Marque qui le trahit |
|---|---|
| le sommaire | les points de conduite, `Article 5 : … .......... 11` |
| l'annexe reproduisant une directive | la parenthèse, non le deux-points : `Article 2 (définitions)` |
| l'en-tête de page répété | le même numéro rouvert à chaque saut de page — quatre fois « Article 13 » |

**436 sections** sur 21 des 27 études d'impact. Les six autres n'ont pas la
convention : deux sont antérieures à sa généralisation, quatre ne portent aucun
en-tête d'article.

**La cible n'est pas cherchée par recoupement entre états.** Une étude d'impact
accompagne le texte déposé — la loi organique l'y attache —, et ses numéros
d'articles sont les siens. Quand le texte déposé est identifié (`docs/32`), il
tranche seul ; sinon seulement, la règle des deux états de `docs/17` s'applique.

## 6. Deux défauts silencieux, encore

**Un nom non importé, et une exception avalée.** Le découpage tournait dans un
`try / except Exception: continue`. `texte_brut` n'était pas importé dans ce
module ; les 27 études d'impact levaient donc un `NameError` par document, et le
compteur les affichait comme « examinées, sans section ». Le message d'échec
existe désormais, et il est une alerte.

**Les offsets portaient sur le mauvais texte.** La première rédaction découpait le
fichier ré-extrait du PDF, quand `motive` enregistre des offsets que la
restitution rouvrira dans le **texte stocké en base**. Deux extractions ne donnent
pas la même chaîne : la citation serait tombée à côté, sans que rien ne le dise.
C'est le texte stocké qui est découpé.

## 6 bis. Trois défauts de rendu, que la voix nouvelle a révélés

Aucun n'était visible tant qu'un seul type de document produisait une arête
`motive`.

**La voix était écrite en dur.** La note rangeait tout passage rattaché sous
« LE PARLEMENT », ce qui était juste tant que seuls les rapports de commission en
produisaient. La première étude d'impact rattachée est donc apparue sous la voix
du Parlement — l'exact contraire de ce que le § 4.3 demande de distinguer. La voix
vient désormais du **type de document**, comme partout ailleurs dans le module.

**« Un étude d'impact ».** Le genre du libellé n'était nommé nulle part, faute
d'en avoir jamais eu besoin : « rapport » est masculin. Il l'est maintenant, à un
seul endroit.

**Le même document, deux fois et en se contredisant.** La fiche affichait l'étude
d'impact comme passage qui explique l'article, puis, quelques lignes plus bas,
comme document « qui porte sur le texte entier, non sur cet article ». Les deux
phrases ne peuvent pas être vraies ensemble, et c'est la seconde qui est fausse :
un document déjà rattaché à cet article est exclu de la liste des documents qui ne
le sont pas.

## 7. Ce que la tranche rapporte, mesuré

| | avant | après |
|---|---:|---:|
| arêtes `porte_sur` | 33 772 | **43 786** |
| dont internes au code | 2 860 | **3 434** |
| articles en vigueur reliés à un article de texte | 819 | **964** (45,8 %) |
| arêtes `motive` | 634 | **686** |
| **dont issues d'une étude d'impact** | **0** | **15** |
| arêtes `depose_sur` | 637 | **874** |
| tentatives rendues | 454 | **689** |

**Le verdict de la partie législative, où cela se voit le mieux :**

| partie L | avant | après |
|---|---:|---:|
| un passage les motive | 708 | **756** |
| origine située seulement | 168 | 199 |
| motivation du texte seule | 412 | 333 |
| raison non documentée | 5 | 5 |

Soixante-dix-neuf articles montent d'un rang. Les cinq muets restent cinq : cette
tranche n'a pas trouvé de motivation là où il n'y en a pas.

**Et la voix du Gouvernement existe enfin au grain de l'article.** Le § 4.3 de la
feuille de route demande de distinguer à l'écran ce que le **gouvernement** a
déclaré vouloir de ce que le **parlement** a fait. Jusqu'ici, `motive` ne venait
que des rapports de commission : la colonne du Gouvernement était structurellement
vide. Quinze articles la portent désormais, avec les offsets de l'étude d'impact
qui les chiffre.

## 8. Ce que la tranche ne fait pas

**Quinze articles, ce n'est pas beaucoup, et le plafond est mesuré.** Sur les
2 016 articles de texte des dossiers ayant une étude d'impact, **220 seulement ont
une cible interne** — 10,9 %. Le code de la consommation est une mince tranche de
ces grandes lois, et aucun découpeur n'y changera rien.

**Les 179 arêtes écartées ne sont pas toutes fausses.** La garde demande à LEGI
d'avoir produit l'article ; un article créé puis abrogé avant la promulgation, ou
renuméroté entre-temps, y échoue sans être faux. C'est le prix de la règle § 5.3,
et il est chiffré plutôt que supposé.

**La règle du code hôte n'est pas corrigée.** Elle reste ce qu'elle est, et la
garde protège la voie nouvelle sans réparer l'ancienne — même constat que
`docs/31` § 7. Le corriger demande de re-mesurer la onzième tranche.
