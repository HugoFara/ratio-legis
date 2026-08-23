# Dixième tranche — exposé des motifs, étude d'impact, avis du Conseil d'État

**Objet :** remplir les trois colonnes vides du § 4.3 — ce que le Gouvernement a
déclaré vouloir, ce qu'il a chiffré, ce que le Conseil d'État a objecté.
**Date : 23 août 2026.**
**Code :** `tools/dila/exposes_motifs.py`, `tools/dila/plan_impacts.py`,
`tools/dila/telecharger_impacts.py`, `ingestion/rapports_vers_motive.py`.

---

## 1. Ce qui manquait

Le § 4.3 impose de distinguer visuellement, dans la restitution, ce que le
**Gouvernement** a déclaré vouloir, ce que le **Parlement** a fait, ce que le
**Conseil d'État** a objecté, et ce qui vient de **Bruxelles**. Deux colonnes
étaient remplies — le Parlement depuis la deuxième tranche, Bruxelles depuis la
neuvième. Les deux autres étaient vides.

Le type `document` prévoyait pourtant `expose_des_motifs`, `etude_impact` et
`avis_conseil_etat` depuis le premier schéma. Rien ne les peuplait.

## 2. Ce que la tranche produit

| | |
|---|---:|
| Exposés des motifs, repris du XML DOLE | 39 |
| Études d'impact (PDF) | 25 |
| Avis du Conseil d'État (PDF) | 15 |
| **Documents en base, tous types** | **337** |
| PDF sans couche de texte, nécessitant une OCR | **0** |

Au grain de l'article en vigueur, par la chaîne déclarée
`version → texte → dossier → document` :

| | |
|---|---:|
| Articles atteignant un exposé des motifs | 147 |
| Articles atteignant une étude d'impact | 125 |
| Articles atteignant un avis du Conseil d'État | 125 |
| **Articles atteignant au moins un document de motivation du texte** | **1 160** |

Le dernier chiffre inclut les rapports au Président de la République de la
huitième tranche : la recodification de 2016 en porte un, et il touche à lui seul
997 articles.

## 3. Trois sources, trois chemins, aucun commun

**L'exposé des motifs n'est pas un document : c'est une balise.** Il est dans le
XML DOLE lui-même, sous `<EXPOSE_MOTIF>` — ni téléchargement, ni PDF, ni OCR, et
des offsets fiables. 39 des 93 dossiers du périmètre en portent un exploitable, de
46 000 caractères en médiane. Les autres sont des ordonnances, qui n'ont qu'un
rapport au Président, ou des lois dont l'exposé n'est resté que sur le dossier du
*projet* et n'a pas été recopié sur celui de la loi promulguée.

Il n'a pas d'adresse propre : sa citation résout sur la page du dossier. Et cette
page n'est plus sur Légifrance, qui **redirige désormais les dossiers législatifs
vers vie-publique.fr**. Construire l'URL sur `legifrance.gouv.fr/dossierlegislatif`
donne un 302 ; c'est la destination qui est stockée.

**L'étude d'impact et l'avis du Conseil d'État sont des PDF**, dont DOLE ne porte
que le lien, dans `<ARBORESCENCE>`. Ils sont servis depuis le chemin média de
Légifrance, qui — contrairement au site de consultation — n'est pas derrière un
défi JavaScript (`docs/01` § 2.6). Les 40 documents portent tous une couche de
texte : aucune OCR n'a été nécessaire.

## 4. Deux pièges, tous deux dans la requête et non dans la source

**Le libellé s'écrit avec et sans accent.** « Etude d'impact » et « Étude
d'impact » coexistent dans le même fonds, 18 contre 6 ; « Avis du Conseil d'Etat »
et « Avis du Conseil d'État », 10 contre 5. Filtrer sur la forme accentuée aurait
perdu les trois quarts des études et les deux tiers des avis, **sans rien
signaler** — la moisson aurait simplement été plus maigre. Le rapprochement se
fait sans accents.

**Légifrance refuse par 403 les requêtes sans `User-Agent`**, et `Python-urllib`
n'en pose aucun. Les 40 documents ont d'abord été comptés « en échec » alors que
`curl` les servait sans difficulté depuis la même machine, une minute plus tôt.
C'est la troisième forme du même piège : après le 404 sur une URL recopiée
(`docs/10` § 4) et le 200 sur une page de défi anti-robot (`docs/14` § 4), un
**403 sur une requête mal formée**. Aucun de ces trois échecs ne venait de la
source. L'agent annonce désormais le projet — un agent descriptif suffit, il
n'est pas nécessaire d'imiter un navigateur.

## 5. Aucune arête `motive` — et c'était prévisible

Ces trois sources n'ajoutent **aucune** arête au grain de l'article : `motive`
reste à 519.

La règle qui produit `motive` exige une citation **déclarée en en-tête**, sous la
forme conventionnelle des rapports de commission : « Article 72 bis (articles
L. 121-42 à L. 121-47 du code de la consommation) ». Aucune des trois sources ne
l'emploie.

- L'exposé des motifs porte 202 en-têtes « Article N » sur les 39 dossiers, dont
  **6 seulement** ont une parenthèse — et ce sont des intitulés de sujet, pas des
  citations d'article.
- L'étude d'impact est structurée par article du **projet**, avec un intitulé
  thématique : « Article 5 : Création d'une liste d'opposition au démarchage
  téléphonique ». Elle cite abondamment le code — 466 numéros dans celle de la loi
  consommation — mais dans son corps, jamais en en-tête.

C'est cohérent avec ce que la phase 0 avait mesuré et que rien n'est venu
démentir : l'exposé des motifs ne nomme l'article que dans **6,4 %** des cas,
l'étude d'impact dans **24,8 %**.

Le rapprochement par le numéro d'article du **projet** serait tentant : l'étude
d'impact et le rapport de commission le portent tous deux, et `motive` a déjà une
colonne `article_du_texte` pour cela. Il est faux. L'étude d'impact accompagne le
texte **déposé** ; le rapport commente le texte **d'une lecture donnée**, et les
articles sont renumérotés à chaque lecture. C'est exactement ce qui avait conduit
à retirer le contrôle de cohérence structurelle (`docs/11`). Le rapprochement
n'est pas fait.

Ces trois sources sont donc rendues **au grain du texte**, comme le rapport au
Président, avec le même avertissement à l'écran.

## 6. Ce qui est montré, et ce qui ne peut pas l'être

La restitution affiche le **début** du document, et l'annonce comme tel. Pour une
étude d'impact de 660 000 caractères, c'est une page de garde. Choisir un autre
passage supposerait de savoir lequel concerne l'article consulté — ce que rien ne
déclare, et ce qu'un appariement lexical ne trouve pas, comme la neuvième tranche
l'a mesuré sur les considérants.

Les quatre documents s'affichent dans l'ordre de la procédure et non celui de la
base : ce que le Gouvernement a voulu, ce qu'il a chiffré, ce que le Conseil
d'État a objecté, puis — pour une ordonnance — le rapport qui remplace tout cela.

## 7. Ce que la tranche ne fait pas

**Les 10 « fiches d'impact » du périmètre ne sont pas chargées.** Ce sont les
études d'impact allégées qui accompagnent ordonnances et décrets. Le type n'existe
pas dans la contrainte `CHECK` du schéma, et les ranger sous `etude_impact` les
présenterait pour ce qu'elles ne sont pas.

**Aucun découpage des PDF par article du projet.** La structure existe, elle est
lisible, et elle ne mène nulle part tant que le lien « article du projet déposé →
article du code » n'est pas établi. Ce lien passe par les textes déposés, qui ne
sont toujours pas chargés.

**Les avis du Conseil d'État antérieurs à 2015 n'existent pas** : leur publication
date de cette année-là. Les 125 articles atteints le sont par des lois récentes.
