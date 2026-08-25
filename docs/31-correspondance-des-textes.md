# Vingt-cinquième tranche — la correspondance des identifiants, et son plafond

**Objet :** écrire la table de correspondance que `docs/16` § 6 posait comme le
dernier verrou, et mesurer ce qu'elle débloque. **Date : 24 août 2026.**
**Code :** `ingestion/textes_des_amendements.py`.
**Schéma :** `schema/011-textes-des-amendements.sql`.

---

## 1. Le verrou, tel qu'il était posé

> « `vise` relie un amendement à sa subdivision — "Article 10" — et `porte_sur`
> relie cette subdivision au code. Les deux se joindraient, mais les identifiants
> de texte des deux corpus ne se correspondent pas : `2002-2003_166.csv` côté
> Sénat, `BTC1156/PO644420` côté Assemblée, `senat/leg-tas07-009.html` ici. Une
> table de correspondance est nécessaire, et elle n'est pas écrite. »
> — `docs/16` § 6

Le README en faisait la condition pour que « les amendements orphelins soient
rattrapés ». Cette tranche l'écrit, et rend la réponse : **ils ne le seront
pas, et pas faute de table.**

## 2. La correspondance n'est pas un rapprochement, c'est une identité

**Sénat.** Un document du Sénat porte un numéro dans sa session : le texte n° 283
de la session 2013-2014. C'est la clef d'une URL Améli
(`/amendements/2013-2014/283/`), et c'est aussi ce que porte le nom du fichier
récupéré depuis DOLE — `leg/pjl13-283.html`, où `13` est l'année d'ouverture de
la session, ou `petite-loi-ameli/2013-2014/283.html`. Les deux identifiants
désignent le même document.

**Assemblée.** La référence d'un amendement porte la série et le numéro —
`L14B1015` pour le texte déposé, `L14BTC2442` pour le texte de commission — et
`amendement.texte_discute` en garde la forme `B1015` / `BTC2442`. Les documents
de l'Assemblée présents dans le corpus emploient la même série : `l14b2442` dans
les URL `dyn`, `r2442-a0` pour le texte annexé à son rapport.

**Les textes adoptés sont écartés des deux côtés.** `leg/tas06-135.html` est le
texte adopté n° 135, série distincte de celle des textes déposés ; `ta{N}` joue
le même rôle à l'Assemblée. Les retenir rattacherait des amendements à un
document qu'ils n'ont jamais amendé, sur la seule foi d'un numéro partagé.

## 3. Trois contrôles, dont deux rejoués à chaque exécution

**Le dossier concorde.** Le texte trouvé par le numéro doit appartenir au même
dossier DOLE que les amendements. 67 jeux sur 75 au Sénat, 26 sur 39 à
l'Assemblée. Les 21 restants n'ont aucun document de la bonne série dans le
corpus — c'est un trou de corpus, non un désaccord : à l'Assemblée, DOLE ne lie
le texte déposé que pour les propositions de loi (`docs/15` § 5).

> **Correction, 25 août 2026.** L'explication du côté Assemblée était fausse, et
> le chiffre avec. Les 13 jeux non appariés n'avaient pas de trou de corpus : leur
> document était déjà en base, apporté par DOLE. Ils échouaient sur une expression
> rationnelle — `BTC?`, qui se lit « un B, puis un T, puis un C facultatif » et ne
> reconnaît donc jamais une référence `B1247`. Corrigée en `B(?:TC)?`,
> **l'Assemblée est appariée à 39 jeux sur 39**, et le contrôle de plage y monte à
> 99,5 %. Voir [`docs/32`](32-textes-deposes-assemblee.md) § 3. Les 8 jeux du
> Sénat, eux, restent bien un trou de corpus.

**Les subdivisions tombent dans la plage.** Un amendement déposé sur l'article 12
suppose que le texte ait au moins douze articles, et `texte_discute.articles` les
compte. **3 578 subdivisions sur 3 655, soit 97,9 %.** C'est le contrôle qui
tranche : un appariement faux s'y verrait avant tout autre, et il est porté par
chaque ligne de la table plutôt que laissé dans une note.

**Le témoin au hasard.** Apparier chaque jeu à un texte tiré au sort fait tomber
la concordance des subdivisions avec `porte_sur` de 40,9 % à 15,3 % au Sénat, de
7,6 % à 2,4 % à l'Assemblée — médianes sur 200 tirages. Le signal n'est pas un
artefact de petits nombres. Ce contrôle a servi à décider ; il n'est pas rejoué à
chaque exécution, faute d'être bon marché.

## 4. Une convention qui ne supporte pas d'être composée

L'arête `depose_sur` compose deux liens : l'amendement fut déposé sur l'article X
du texte T, et l'article X de T réécrit l'article A du code. Le second est
`porte_sur`, dont `docs/16` § 4 mesure la précision à 20/20.

Un contrôle à la main sur 15 arêtes en a pourtant donné **deux fausses**, de la
même cause. L'article 23 du texte de la commission écrit :

> I. – **Le code de la propriété intellectuelle est ainsi modifié :** 1° Le 2° de
> l'article L. 411-1 … 9° L'article L. 722-1 est complété par un e ainsi rédigé

Sept citations sur huit sont correctement rendues externes. La huitième —
L. 722-1, qui existe aussi au code de la consommation — tombe dans la convention
légistique que `porte_sur` retient : *un dispositif qui ne nomme aucun code
modifie le sien*. L'hôte est déclaré une seule fois, en tête du bloc, hors de la
fenêtre de preuve du 9°.

La convention vaut pour ce qu'elle mesure. Elle ne vaut pas une seconde fois.
**La garde ne devine donc rien : elle exige que la fenêtre de preuve nomme le
code de la consommation**, au lieu de se contenter de l'avoir supposé.

Elle écarte 1 398 cibles, et elle en libère : un article de texte qui semblait en
réécrire plusieurs n'en réécrit plus qu'un une fois les cibles supposées
retirées. Les arêtes passent de 611 à **618**, et les deux fausses du premier
tirage disparaissent.

**Précision : 15 sur 15**, tirage disjoint du premier, sur le graphe d'après la
garde. Borne inférieure de Wilson à 95 % : **0,7961**. C'est la valeur portée par
chaque arête — au-dessus de `vise` (0,6212), au-dessous de `resulte_de` (0,8933),
ce qui est l'ordre attendu.

## 5. Le résultat principal est négatif, et il se compte

| Les 30 312 amendements des 93 jeux appariés | |
|---|---:|
| **portant sur un article additionnel** | **7 501** |
| subdivision sans cible interne dans le code | 20 425 |
| subdivision illisible | 1 609 |
| l'article du texte en réécrit plusieurs | 159 |
| **arêtes `depose_sur`** | **618** |

(La garde du § 4 se compte dans une autre unité : elle écarte 1 398 *cibles* de
`porte_sur`, non des amendements.)

La ligne qui compte est la deuxième. **« art. add. après Article 19 » ne vise pas
l'article 19** : l'amendement demande la création d'un article qui n'existe pas
encore, dont le numéro dans le code n'est pas fixé et ne le sera qu'à la
codification. Aucune table de correspondance ne peut lui donner une cible, parce
qu'il n'en a pas.

C'est la réponse à la question que le README posait. L'hypothèse était que les
amendements orphelins le restaient faute de pouvoir joindre deux corpus. Elle est
fausse : **ils le restent parce qu'ils créent du droit au lieu d'en modifier**, et
c'est un fait sur la fabrique de la loi, non sur l'outillage.

## 6. Ce que la voie du dépôt apporte à la restitution

Une troisième voie dans `restitution/tentatives.py`, à côté de l'alinéa écrit et
de la cible déclarée.

| | avant | après |
|---|---:|---:|
| articles en vigueur portant une tentative | 156 | **163** |
| tentatives rendues | 233 | **454** |
| dont non abouties | 88 | **257** |
| articles portant au moins un échec | 56 | **65** |

**Elle approfondit sans élargir.** Sept articles seulement lui doivent leur
première tentative ; mais elle double presque le nombre de tentatives rendues,
parce qu'elle atteint les articles que le débat a le plus travaillés — 90
amendements sur le seul L511-7, qui liste les textes dont la DGCCRF contrôle
l'application et que chaque loi de consommation vient allonger.

**Ce qu'elle dit, et rien de plus.** L'amendement a été discuté sur l'article du
texte qui a réécrit celui-ci. Elle ne dit pas qu'il visait cet article : un
amendement se dépose sur un article de projet de loi, et ce qu'il y propose peut
concerner tout autre chose. Le libellé à l'écran est une phrase de position,
jamais de cible — « déposé sur l'article du texte qui réécrit celui-ci ».

**Coût.** 12,5 ms de médiane par article, inchangé : la voie ajoute une jointure
indexée, pas un parcours.

## 7. Ce que cette tranche ne fait pas

**Elle ne corrige pas `porte_sur`.** Le défaut d'attribution d'hôte du § 4 est
réel et il est nommé ; le corriger touche 30 337 lignes et demande de re-mesurer
la précision de la onzième tranche. La garde protège l'arête nouvelle, elle ne
répare pas l'ancienne.

**Elle n'atteint pas les 21 jeux non appariés.** Il leur manque un document dans
le corpus, non une règle d'appariement. Charger les textes déposés de l'Assemblée
par le numéro de dépôt de la chambre — et non par DOLE, qui ne les lie pas — reste
le chantier ouvert, et c'est le même que celui du rapprochement des études
d'impact.

**Elle ne qualifie toujours pas le lien.** `porte_sur` sait si l'article du texte
modifie, abroge ou complète, et ne le conserve pas (`docs/16` § 7). La voie du
dépôt hérite de ce silence.
