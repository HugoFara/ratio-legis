# Trente-neuvième tranche — la pastille du Sénat, et le deux-points de l'incise

**Objet :** attaquer ce que `docs/44` § 2 avait nommé « sous-instruction » —
les trois `alinea` fausses du troisième tirage — et constater que la cause
nommée n'était pas la cause.
**Date : 20 septembre 2026.**
**Code :** `ingestion/textes_deposes.py` (`est_une_cible`),
`ingestion/textes_des_amendements.py` (`alineas_de`, `Textes`).
**Données :** `precision-porte-sur-incise.tsv`,
`precision-depose-sur-alinea-4.tsv`, `precision-depose-sur-alinea-5.tsv`.

---

## 1. Les trois fausses, relues

`docs/44` les donnait pour « des sous-instructions — "a bis)" sous un 1°,
"2°" sous un I — que le parseur ne borne pas ». Rejouées une à une sur le
texte :

| amendement | texte, article, alinéa | arête | ce que les juges lisaient | cause réelle |
|---|---|---|---|---|
| Sénat 111 rect. quater | ppl24-469, art. 3, al. 22 | L223-1 | a ter) sur L. 223-5 | l'alinéa 22 tombait sur la ligne 22, qui était la **onzième** : chaque alinéa comptait double |
| Sénat 123 | pjl19-454, art. 1er undecies, al. 9 | L511-10 | d) du 2° sur L. 512-18 | même chose |
| Sénat 350 | pjl13-283, art. 11, al. 29 | L121-101 | Art. L. 121-102 | déjà réparée par la ligne de statut de `docs/44`, la fiche avait été tirée avant |

**Chaque alinéa comptait double** parce que le Sénat numérote lui-même ses
alinéas, et que ce numéro est dans le texte : depuis 2017 environ, chaque
alinéa est précédé d'une « pastille », un `<span>` en police « Numero »,
`aria-label="pastille 22"`, dont le contenu est un glyphe de la zone privée
d'Unicode. `texte_brut` garde le glyphe et perd l'attribut ; le glyphe
faisait une ligne, et la ligne un alinéa. 113 textes du Sénat et 58 de
l'Assemblée sur 872 en portent.

Le glyphe seul suffit, parce que la police est un chiffrement régulier : de 1
à 9, une lettre de L à T ; au-delà, le chiffre des dizaines (ou des centaines)
en chiffre, puis A à J pour les dizaines et a à j pour les unités — « 1Aa »
se lit 100. Vérifié contre l'attribut sur les **873 glyphes distincts** des
126 textes qui en portent : zéro écart. La numérotation des alinéas est donc
**déclarée** là où la pastille existe, et `alineas_de` la lit : l'alinéa n
est la ligne qui suit la pastille n, rien d'autre n'est un alinéa — ni la
ligne de statut au-dessus de la première, ni le titre de chapitre après la
dernière. La lecture s'arrête au premier écart à cette forme — une pastille
qui ne suit pas la précédente, deux lignes sous une même pastille — plutôt
que de numéroter faux.

Et une fois l'alinéa 22 posé sur le bon alinéa — « a ter) Au début du
premier alinéa de l'article L. 223-5, les mots : « Les interdictions
prévues… » sont remplacés par les mots : « … » » —, l'arête restait fausse :
l'instruction n'était pas relevée, et l'alinéa remontait au « a bis) » sur
L. 223-4. Là est la « sous-instruction », et elle n'a rien d'une question de
bornage.

## 2. Le deux-points de l'incise

`est_une_cible` — la règle qui fait d'une référence une cible de `porte_sur`
depuis la onzième tranche — cherche un verbe modificatif entre la référence
et la fin de la phrase, et lit la fin de phrase au premier `.`, `;` ou `:`.
Le deux-points de « les mots : « X » sont remplacés par » est une fin de
phrase pour cette règle ; le verbe est après ; la référence n'est pas une
cible. C'est **la forme la plus courante de la légistique**.

Mesuré sur les 872 textes : **22 604 références hors citation sur 123 162**
sont suivies d'un verbe modificatif que ce deux-points cachait. « Au 3° de
l'article L. 511-5, les mots : « , II et III » sont remplacés par les mots :
« à III bis » » n'était pas une cible ; « Dans la première phrase de
l'article L. 211-16 du code de la consommation, après le mot : « consentie »,
sont insérés les mots : « … » » non plus.

La règle corrigée saute l'incise — un deux-points immédiatement suivi d'un
guillemet ouvrant, jusqu'au guillemet fermant — et cherche le verbe **hors**
de l'incise seulement : « au sens de l'article L. 223-5 : « le contrat est
ainsi modifié » » ne fait pas de L. 223-5 une cible. Le deux-points suivi
d'un retour à la ligne reste une borne : « est ainsi rédigé : » ferme
l'instruction, et le verbe la précède.

Ce que cela fait au graphe, pipeline rejoué de zéro :

| | avant | après |
|---|---:|---:|
| `porte_sur` | 77 182 | **97 676** |
| dont internes | 5 702 | **6 971** |
| articles en vigueur reliés à un article de texte | 949 | **987** |
| `vise` | 569 | 564 |
| `depose_sur` | 1 115 | **1 214** |
| dont `alinea` / `visee` / `article_entier` | 1 051 / 51 / 13 | 1 122 / 76 / 16 |
| verdict `passage_motivant` | 807 | 825 |
| verdict `origine_situee` | 124 | 135 |
| verdict `raison_non_documentee` | 770 | 769 |

`porte_sur` gagne un cinquième d'arêtes internes d'un coup, et **toutes
sont de la forme la plus simple qui soit** — une instruction qui nomme un
article et remplace, supprime ou insère des mots. Sa précision a été mesurée
sur une population qui les excluait (34/35, `docs/41`) ; celle des arêtes
nouvelles ne l'est pas encore. `precision-porte-sur-incise.tsv` en tire vingt,
parmi les arêtes que la règle a créées.

## 3. Deux gardes de plus sur la numérotation comptée

Les textes sans pastille — le Sénat avant 2017, l'Assemblée — restent
comptés : une ligne non vide vaut un alinéa. Cette règle se vérifie, parce
que les amendements la déclarent eux-mêmes : « Alinéa 67 : Rédiger ainsi cet
alinéa : « Art. L. 121-20. – … » » dit quel alinéa porte quel article écrit.
Sur ces **ancres**, prises dans les textes sans pastille :

| compte | juste | décalé de +1 | de +3 ou +4 | introuvable |
|---|---:|---:|---:|---:|
| une ligne, un alinéa | 56 | 11 | 3 | 6 |
| + intitulé coupé recollé | 63 | 4 | 3 | 6 |

Le « +1 » est un intitulé cité que le HTML coupe en deux — « IDENTIFICATION
DES IMMEUBLES » / « RELEVANT DU STATUT DE LA COPROPRIÉTÉ » : une ligne sans
marque de tête entre deux lignes citées continue la précédente. Ce qui reste
décalé a une autre cause, et elle est structurelle : **la petite loi est le
texte adopté**. Les alinéas qu'une insertion adoptée en séance a décalés ne
portent plus le numéro que les amendements leur donnaient ; l'alinéa 10 de la
petite loi 85 (2013-2014) est un « L. 141-23-1 (nouveau) » que l'amendement,
déposé avant, ne pouvait pas compter. La voie `alinea` n'est plus prise sur
une petite loi.

Et les ancres servent de garde : article de texte par article de texte, si
une seule ancre contredit le compte, aucun alinéa de cet article n'est lu.
**88 ancres confirment le compte, 18 le contredisent** ; 13 amendements sont
écartés à ce titre.

## 4. Sur les arêtes déjà jugées

Avant tout nouveau tirage, les trois fiches `alinea` rejouées sur la base
d'aujourd'hui :

- **aucune des 51 justes n'a bougé** — même amendement, même article, les
  deux arbitrées comprises ;
- des 9 fausses : **5 rendent désormais l'article que les juges nommaient**
  (L. 223-5, L. 512-18, L. 121-102, L. 218-7, L. 218-5-3), **3 sont
  retirées** (alinéa gouverné par un autre code, ou par un paragraphe sans
  numéro), 1 est inchangée : l'alinéa 110 de l'article 5 du projet de loi
  consommation, que les juges comptent deux rangs plus bas que le texte de
  2013, sans pastille, ne le permet.

Sur les fiches `visee` et `article_entier`, rien de ce qui était juste n'a
bougé, et quatre `article_entier` fausses sont retirées — l'article du texte
avait une seconde cible que le deux-points cachait.

## 5. Ce qui a été mesuré, et ce qu'on en a fait

Protocole de `docs/43` § 2, les juges changés : deux agents Sonnet 5 sur
chaque fiche, en colonnes séparées, sans se lire ; un troisième en arbitrage
sur les seuls désaccords. Chaque juge lit le texte en discussion lui-même,
pas la fenêtre de la fiche, et rend un commentaire qui dit ce qu'il a
vérifié.

| arête | tirage | n | juge A | juge B | accord | arbitrage | verdict | Wilson | constante |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `porte_sur` · incise | arêtes créées par la règle | 20 | 20 | 20 | 20 | — | **20 / 20** | 0,8389 | 0,8558 → **0,9039** (54 / 55, trois tirages réunis) |
| `depose_sur` · `alinea` | 4e, disjoint | 20 | 16 | 16 | 20 | — | **16 / 20** | 0,5840 | — |
| `depose_sur` · `alinea` | 5e, disjoint, après les gardes ci-dessous | 20 | 19 | 18 | 19 | 1 → juste | **19 / 20** | **0,7639** | 0,6396 → **0,7639** |

**`porte_sur`.** Les vingt arêtes que le deux-points cachait sont toutes
justes, et les deux juges ont remonté chaque chaîne « du même code » jusqu'à
son chapeau. La population interne a grossi d'un cinquième sans que la
précision bouge ; les trois tirages réunis donnent 54 sur 55.

**`alinea`, quatrième tirage : 16 sur 20, et les quatre fausses ont deux
causes.** Trois sont des insertions — « Après l'alinéa 9, insérer : « Art.
L. 423-1-1. – … » », « … : « III bis. – Le cinquième alinéa de l'article 2
de la loi n° 90-449 … » » : ce qu'on insère après l'alinéa N n'est pas
toujours dans l'article qui gouverne N. Un article écrit, une division, ou
une instruction qui nomme son propre article : la cible est ailleurs, et
l'arête n'est plus posée. L'Assemblée citant tout ce qu'elle insère,
instructions comprises, le guillemet ne dit rien ; c'est la forme de la tête
qui parle, et pour un numéro ou une lettre, le verbe **et** l'article
nommé — « 3° Il est complété par quatre alinéas » prolonge le bloc,
« …) Le premier alinéa de l'article L. 223-5 est complété » en ouvre un
autre. La quatrième comptait « (division et intitulé nouveaux) » comme un
alinéa : toute ligne qui n'est qu'une mention entre parenthèses est
retirée du compte — 90 formes, 1 853 lignes, aucune n'est un alinéa.

**Cinquième tirage, sur la population gardée : 19 sur 20.** La fausse
supprimait « les alinéas 22 à 26 » — la section 2 bis et L. 423-4-1 — et
l'arête ne lisait que le 22, gouverné par L. 423-4. Une plage se lit en
entier et doit relever d'une seule instruction ; une division citée et son
intitulé ne sont pas rattachés à l'instruction d'avant ; « alinéas 2 et 4 »
rend une arête par article touché. Le désaccord arbitré était un compte :
un intitulé coupé par un `<br>` dans un texte de 2013, que l'arbitre a
tranché par les autres amendements du même jeu, qui numérotent comme lui.

**Sur les cinq tirages jugés, après toutes les gardes** : les 14 fausses
sont retirées (9) ou ramenées à l'article des juges (5) ; 7 des 85 justes
sont perdues — trois insertions d'un article nouveau après le dernier
alinéa d'un autre, que les juges du quatrième tirage ont dites fausses sur
la même forme, trois sous-instructions sur L. 223-5 que `vise` devrait
tenir et ne tient pas (le numéro nu sous un article de texte multi-codes,
la maille de `docs/43` § 2), une instruction créant L. 112-12 jugée juste
pour L. 111-6, ce qui est douteux.

Ce que cela fait au graphe : `alinea` 1 122 → **1 015**, `depose_sur`
1 214 → **1 107** — moins d'arêtes, et chacune vaut 0,76 là où elle en
valait 0,58 le matin.

## 6. Ce qui n'est pas fait

**Le décalage de deux** de l'alinéa 110 (`docs/44`, texte 283 de 2013-2014)
reste inexpliqué ; le cinquième tirage a montré la même famille — un
intitulé coupé — tranchée par les ancres, et c'est probablement elle.

**`vise` sous un article multi-codes** : trois amendements qui nomment
« l'article L. 223-5 » sans nommer le code, sous un article de texte qui
modifie aussi le code de commerce, n'ont pas de `vise`. La règle qui écarte
le numéro nu là est la bonne ; c'est le code hôte de l'*instruction* qui
les tiendrait, pas celui de l'article du texte.

**Rien de ceci n'est humain.** Cinq juges Sonnet et un arbitre ; `verdict`
dit qui a tranché.
