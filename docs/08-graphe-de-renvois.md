# Troisième tranche — le graphe de renvois

**Objet :** répondre à la question du législateur, qui n'est pas « pourquoi cet
article existe » mais « si je modifie celui-ci, qu'est-ce qui bouge ».
**Date : 23 août 2026.**
**Code :** `ingestion/renvois.py`. **Schéma :** `schema/002-renvois.sql`.

---

## 1. Pourquoi cette tranche avant les amendements

Les deux premières tranches servent le citoyen : elles sont rétrospectives et
répondent à « pourquoi ». Un parlementaire ne pose jamais cette question. Il
travaille sur un texte en cours et demande « et si ».

Cette tranche est le premier livrable prospectif du projet, et elle ne demande
**aucune source nouvelle** : la donnée était dans le texte des articles déjà
chargés, elle n'avait pas été extraite.

## 2. Ce que la tranche produit

| | |
|---|---:|
| Renvois relevés | **11 656** |
| dont résolus dans le fonds (`interne`) | 9 568 (82,1 %) |
| vers un autre code, nommé dans le texte | 1 812 (15,5 %) |
| **introuvables (`non_resolue`)** | **276 (2,4 %)** |
| Articles en vigueur citant un autre article | 1 220 (57,0 %) |
| **Articles en vigueur cités par un autre** | **1 064 (49,7 %)** |
| **Articles L cités par un article réglementaire** | **303 sur 1 280 (23,7 %)** |

Les plus cités : L733-1 (37 articles), L412-1 (36), L733-4 (35), L733-7 (32),
L313-1 (25). Ce sont les points de rupture d'une réforme : un amendement qui
touche L. 313-1 déplace vingt-cinq articles.

Ce que la restitution rend, pour L. 313-1 :

```
L314-24  « …l'octroi des contrats de crédit mentionnés à l'article L. 313-1, la f… »
L314-12  « Lorsqu'une opération de crédit est destinée à regrouper des crédits
           mentionnés à l'article L. 313-1, le nouvea… »
L313-53  « …relatifs aux immeubles mentionnés au a du 1° de l'article L. 313-1 sont… »
```

Chaque ligne porte l'alinéa exact et sa preuve. Le législateur ne lit pas un
compte, il lit la phrase qui casse.

## 3. Trois précautions, chacune tirée d'une erreur déjà commise

**La résolution se fait à la date de la citation.** Un numéro d'article n'est pas
une identité stable : R. 531-2 a désigné deux dispositions différentes à deux
époques. Résoudre un renvoi de 2013 contre le code d'aujourd'hui inventerait un
lien. La cible retenue est la version couvrant la date d'entrée en vigueur du
texte citant.

**Ce qu'on ne sait pas est nommé.** Un renvoi vers la partie réglementaire, vers
un autre code ou vers un numéro introuvable ne devient pas un lien interne et ne
disparaît pas : il porte sa portée. Confondre « cité hors de ce code » et « cité
et introuvable » ferait passer une limite de périmètre pour une incohérence du
droit — c'est-à-dire exactement le contraire de ce que l'outil promet.

**La précision est mesurée, pas supposée.** Contrôle à la main de vingt renvois
internes tirés au sort : **20/20**. `confiance` vaut 0,839, borne inférieure de
Wilson à 95 %.

## 4. Quatre pièges de la citation légistique

Aucun ne levait d'erreur ; chacun a coûté une part du corpus.

**Le seuil de preuve de 60 caractères était mal appliqué.** Il vise l'appariement
flou, où une fenêtre courte ne discrimine rien ; une référence explicite n'a pas
ce défaut. Appliqué au segment, il écartait 864 renvois — souvent des alinéas de
pure énumération, les plus utiles ici. Le contexte est désormais pris dans
l'article entier, qui contient le segment. Reste 3 renvois écartés.

**Le code est nommé une fois par énumération, parfois avant elle.** « aux articles
L. 131-2, L. 132-1 et L. 133-44 du code monétaire et financier » ; « du livre III
du code monétaire et financier et aux articles… ». Une fenêtre de 70 caractères en
aval ne voit ni l'un ni l'autre. La recherche se fait dans les deux sens, et
**seulement pour une référence qui ne se résout pas dans ce code** : sinon une
phrase citant un autre code puis le code courant verrait la seconde référence
réétiquetée à tort.

**Le point de « L. 131-2 » n'est pas une fin de phrase.** Le balayage arrière
s'arrêtait au milieu de l'énumération qu'il devait remonter. C'est cette seule
correction qui a fait tomber les renvois introuvables de 849 à 287.

**L'énumération traverse les alinéas.** Chercher le nom du code dans le segment
seul laissait 287 renvois introuvables ; le chercher dans l'article les ramène à
215. « Du même code », qui renvoie au dernier code nommé, est traité comme tel.

## 5. Le chiffre qui parle au législateur

**303 des 1 280 articles L en vigueur — 23,7 % — sont cités par un article
réglementaire du même code.** Les modifier déplace un décret d'application.
C'est précisément ce qu'une réforme casse sans le voir, et aucune source
publique ne le donne aujourd'hui.

Ce chiffre a failli ne pas exister. Une première version classait toute cible R
ou D en « partie réglementaire non ingérée », par supposition. Le fonds contient
en réalité 1 241 articles R et 254 D, dont 670 et 168 en vigueur : la supposition
écartait 2 133 renvois résolvables, soit 18 % du total. Vérifier le contenu de sa
propre base coûtait une requête.

## 6. La qualification du renvoi n'est pas soutenue par la donnée

Une tranche de qualification était envisagée : distinguer « par dérogation à
l'article L. 221-5 » de « dans les conditions prévues à l'article L. 221-5 »,
qui ne créent pas le même risque en cas de modification. La mesure de la formule
introductive des 9 568 renvois internes ne la soutient pas :

| Formule | Renvois |
|---|---:|
| Désignation neutre — *prévu, mentionné, visé, défini* | 3 742 (39,1 %) |
| En application de | 703 (7,3 %) |
| Dans les conditions prévues | 386 (4,0 %) |
| Sanction ou peine | 102 (1,1 %) |
| Sans préjudice | 19 (0,2 %) |
| **Par dérogation** | **7 (0,1 %)** |
| Aucune formule dans la fenêtre | 4 214 (44,0 %) |

La formule qui porterait le plus d'information — la dérogation — apparaît sept
fois. Le vocabulaire légistique est massivement neutre : il désigne, il ne
qualifie pas. Une taxonomie de risque bâtie là-dessus décrirait la rédaction, pas
le droit. **La piste est abandonnée**, et c'est la mesure qui la ferme, pas une
préférence.

## 7. Ce que la tranche ne fait pas

**Le point d'entrée reste l'article du code.** Un parlementaire part de son
amendement. Le résolveur sait déjà aller de l'amendement vers l'article ; il n'a
jamais été exécuté sur un texte non encore déposé.
