# Onzième tranche — les textes en discussion, et ce sur quoi ils portent

**Objet :** relier l'article du texte en discussion à l'article du code.
**Date : 23 août 2026.**
**Code :** `tools/dila/plan_textes.py`, `tools/dila/telecharger_textes.py`,
`ingestion/textes_deposes.py`. **Schéma :** `schema/006-textes-discutes.sql`.

---

## 1. Le chaînon

Le graphe savait ce qu'un **article du code** était devenu, et ce qu'un **article
du texte en discussion** avait suscité — un amendement s'y dépose, un rapport le
commente, une étude d'impact le chiffre. Il ne savait pas relier les deux.

Ce lien n'est écrit qu'à un seul endroit : le texte lui-même. « L'article
L. 121-1 du code de la consommation est ainsi modifié. » C'est la fonction
qu'assurait DuraLex, abandonné depuis février 2019 (`docs/01` § 3.2) — il fallait
donc l'écrire.

## 2. Ce que la tranche produit

| | |
|---|---:|
| Textes relevés dans DOLE, tous stades | 362 |
| récupérés | **355** |
| perdus (pages Améli supprimées) | 7 |
| Articles de texte découpés | 26 942 |
| **Rattachements retenus** | **27 412** |
| dont vers ce code (`interne`) | 2 525 |
| vers un autre code, nommé | 24 707 |
| sans code identifiable | 180 |
| **Articles en vigueur reliés à un article de texte** | **807 (37,7 %)** |
| dont par le numéro d'aujourd'hui | 204 |
| **dont par la chaîne de renumérotation** | **722** |

Le dernier chiffre est le plus important de la tranche, et c'est la même leçon
que pour `motive` (`docs/07`) : **sur un corpus recodifié, la cible nommée par le
texte n'existe presque jamais sous ce numéro aujourd'hui.** Un texte de 2014 vise
L. 121-42 ; l'article en vigueur est L. 224-43. Sans la chaîne, la tranche
n'atteindrait que 204 articles au lieu de 807.

## 3. Trois conventions légistiques, trois règles

**Le code n'est nommé qu'une fois.** Un texte nomme le code qu'il modifie, puis
dit « du même code », parfois pendant vingt articles. Le suivi se fait donc au
niveau du **texte entier**, jamais de l'article : « Le livre V du même code » à
l'article 2 renvoie au code nommé à l'article 1. Un suivi par article aurait
perdu tout ce qui suit la première mention, sans rien signaler.

**Le code se nomme après la référence autant qu'avant.** « L'article L. 121-1
**du code de la consommation** » le nomme après ; « **Dans le même code**, les
articles L. 521-1 à L. 521-5 » le nomme avant. Les deux formes cohabitent dans la
même page. Le code est donc cherché d'abord en aval dans la phrase, puis en amont.

**Aucune référence n'est attribuée par défaut.** Contrairement à `renvoie_a`, où
une référence sans code nommé vise le code courant — parce qu'on lit un article de
ce code —, un texte en discussion peut modifier n'importe quel code, et en modifie
souvent plusieurs : les 355 textes du corpus touchent le code monétaire et
financier (8 442 fois), le code de commerce (8 370) et le code de la consommation
(6 745) dans des proportions comparables. Sans code nommé, la portée reste
`non_resolue`.

## 4. Ce qui a fait passer la précision de 8/20 à 20/20

Le premier tirage de vingt rattachements en donnait **huit** de justes. Trois
défauts, mesurés puis corrigés, chacun d'une nature différente.

**Les en-têtes manqués rattachaient au mauvais article.** « Article 4 bis BB »
porte deux lettres, « Article 18 B (nouveau) » et « Article 27 quater (Non
modifié) » portent une mention de navette. Aucun des trois n'était reconnu comme
en-tête, et **leur contenu était rattaché à l'article précédent**. C'est le pire
défaut possible ici : il produit un rattachement faux, pas une absence.

**Citer n'est pas modifier.** Une référence dans le dispositif peut être la cible
— « L'article L. 217-12 est complété par… » — ou une simple mention à l'intérieur
de la règle nouvelle. La convention distingue les deux : le verbe modificatif suit
la cible. Exiger ce verbe dans la même phrase écarte 23 260 références.

**Le texte cité n'est pas le texte qui cite.** Un alinéa inséré s'ouvre par un
guillemet, et la convention le rouvre à chaque alinéa **sans jamais le refermer**
avant le dernier : suivre la profondeur des guillemets ne mène nulle part —
essayé, 42 références sur 18 070 étaient vues hors citation. C'est le début de
ligne qui tranche. Mais la citation **en incise** compte autant, et c'est elle qui
produisait les rattachements les plus trompeurs : « la référence : "L. 132-2" est
remplacée par la référence : "L. 534-1" » désigne L. 132-1 comme cible, et
L. 132-2 comme simple texte remplacé. À l'intérieur d'une ligne, les guillemets
sont appariés et l'incise se lit sans ambiguïté. 51 317 références sont ainsi
écartées.

Les trois défauts n'ont pas été trouvés d'un coup. Le deuxième tirage, après
correction des en-têtes et exigence du verbe, donnait **17 sur 20** : les trois
erreurs restantes étaient deux incises entre guillemets et une attribution de code
à travers deux codes voisins. Le troisième tirage, après la correction des
incises, donne **20 sur 20**.
Borne inférieure de Wilson à 95 % : **`CONFIANCE = 0,8389`**. Le rappel est passé
de 435 à 204 articles atteints en direct — c'est le prix, et il est conforme au
§ 5.3.

## 5. Deux pièges d'accès, deux fois le même

**L'Assemblée sert ses textes récents par une application JavaScript** : 200,
77 ko, et pas une ligne du texte. 51 textes sur 362 étaient dans ce cas. Mais la
coquille **déclare** où est le document, dans un lien vers sa version PDF. On suit
cette déclaration ; on ne devine pas l'URL, qui diffère selon le stade
(`_texte-adopte-commission`, `_texte-adopte-seance`) et ne se déduit pas de celle
de la page. C'est le même geste que pour le fichier de structure JORF (`docs/12`).

**Les caractères NUL de l'extraction PDF.** Python les compte, `length()` de
SQLite s'arrête au premier : une fenêtre de 196 caractères en valait 33 pour la
contrainte `length(fenetre) >= 60`, qui l'a refusée — à juste titre, puisque la
preuve stockée aurait été tronquée à la lecture. **La contrainte a trouvé le
défaut que le code n'avait pas vu.** Les caractères sont remplacés, non
supprimés : les retirer décalerait tous les offsets.

Un troisième, plus banal : deux défauts de découpe se lisaient dans les résultats
avant de se lire dans le code. « code de la consommation » était tronqué en
« code » — 54 123 rattachements sur 77 019 portaient ce nom vide et pas un seul ne
se résolvait — parce que la liste des coupures de reprise, recopiée de
`renvois.py`, avait reçu un « de » en trop. Et l'encodage lu dans la déclaration
`charset` plutôt que dans les octets rendait « code mon�taire et financier ».

## 6. Ce que le chaînon débloque, et ce qu'il ne débloque pas

Il devait servir trois chantiers. Il en sert un.

**Ce qu'il donne.** Pour 807 articles en vigueur, la restitution dit sous quel
article de quel texte, à quel stade et dans quelle chambre l'article a été
discuté, avec l'URL du texte — et, quand le numéro a changé, sous quel ancien
numéro il était visé.

**Ce qu'il ne donne pas : le rattachement de l'étude d'impact.** L'hypothèse était
que charger les textes déposés permettrait de relier une section d'étude
d'impact — structurée par article du projet — aux articles du code. La mesure la
dément : **aucun des 25 dossiers ayant une étude d'impact n'a de texte déposé dans
le corpus**. Les 21 textes déposés que DOLE lie sont tous des *propositions* de
loi, qui n'ont jamais d'étude d'impact ; pour les *projets* de loi, DOLE lie le
dossier de la chambre, pas le texte déposé. Le recoupement est exactement nul.
L'étude d'impact reste au grain du texte (`docs/15` § 5).

**Ce qu'il ne donne pas encore : les amendements orphelins.** `vise` relie un
amendement à sa subdivision — « Article 10 » — et `porte_sur` relie cette
subdivision au code. Les deux se joindraient, mais les identifiants de texte des
deux corpus ne se correspondent pas : `2002-2003_166.csv` côté Sénat,
`BTC1156/PO644420` côté Assemblée, `senat/leg-tas07-009.html` ici. Une table de
correspondance est nécessaire, et elle n'est pas écrite.

## 7. Ce que la tranche ne fait pas

**Elle ne qualifie pas le lien.** `porte_sur` dit que l'article du texte porte sur
l'article du code, rien de plus. Le texte dit pourtant lequel — « est ainsi
modifié », « est abrogé », « est complété » — et le verbe a été utilisé pour
*décider* qu'il s'agit d'une cible, sans être *conservé*. Le stocker demanderait de
rattacher chaque verbe à sa référence dans une phrase qui en enchaîne plusieurs
(« les articles L. 521-1 à L. 521-5 sont ainsi rédigés, l'article L. 521-6 est
ainsi rétabli »). Ce découpage n'est pas fait, donc la qualification n'est pas
prétendue.

**Les sept textes Améli perdus ne sont pas récupérés.** `ameli.senat.fr` répond
404 sur ses pages `publication_pl` ; le service a été retiré. Les mêmes textes
existent peut-être sous une autre adresse au Sénat — non cherché.

**Le code hôte pouvait dériver, et la mesure de ce § 4 ne le voyait pas.** Un
code nommé *dans une citation* gouvernait tout ce qui suivait. Le tirage de vingt
portait sur la population entière, où cette cellule pèse 6,8 % : l'erreur n'y
apparaît pas. Réparé et re-mesuré dans [`docs/34`](34-hote-du-code-cite.md).

**Les plages ne sont pas dépliées.** « Les articles L. 521-1 à L. 521-5 sont ainsi
rédigés » ne produit que L. 521-1 et L. 521-5, pas les trois du milieu.
