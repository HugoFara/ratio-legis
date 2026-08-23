# Neuvième tranche — les considérants des actes de l'Union

**Objet :** charger la seule motivation systématiquement publiée que le corpus
rencontre.
**Date : 23 août 2026.**
**Code :** `ingestion/considerants.py`, `tools/ue/recuperer_actes.py`.
**Schéma :** `schema/005-considerants.sql`.

---

## 1. Pourquoi c'est la meilleure source du projet

La huitième tranche avait rattaché 284 actes de l'Union aux articles du code,
mais par leur seul identifiant : le graphe savait *qu'*un règlement commande un
article, jamais *pourquoi il a été écrit*.

Le contraste avec le corpus français est brutal, et il est mesuré depuis la
phase 0 : l'exposé des motifs d'un projet de loi ne nomme l'article que dans
**6,4 %** des cas, l'étude d'impact dans **24,8 %**. Un acte de l'Union, lui,
**motive toujours ce qu'il édicte**, en tête de son propre texte, article par
article de son dispositif — et le publie dans les 24 langues.

## 2. Ce que la tranche produit

| | |
|---|---:|
| Actes miroités depuis EUR-Lex | 281 sur 284 |
| **Considérants chargés** | **7 674** |
| dont au numéro imprimé | 7 385 |
| sans numéro dans l'original | 289 |
| Actes sans aucun considérant récupéré | **0** |
| Articles d'actes déclarés (numéro, intitulé, ancre) | 6 237 |
| Citations résolues jusqu'à l'article de l'acte | 150 |
| **Articles en vigueur atteignant un considérant** | **113** |

## 3. La segmentation n'est pas à faire — pour la moitié du fonds

EUR-Lex publie les actes récents en HTML structuré selon **ELI** : chaque
considérant porte `id="rct_N"`, chaque article `id="art_N"`, et N est le numéro
imprimé. C'est une structure **déclarée**, pas une heuristique — l'inverse exact
du découpage des rapports parlementaires, qui avait coûté quatre défauts
silencieux (`docs/07` § 4).

Elle ne couvre que la moitié des actes. EUR-Lex a converti son fonds selon
**quatre générations de gabarit**, et chacune a été découverte en constatant que
la précédente rendait des actes « sans aucun considérant » :

| Gabarit | Numérotation | Actes concernés |
|---|---|---|
| `id="rct_N"` (ELI) | déclarée | les plus récents |
| `<p class="normal">considérant que …` | absente | années 1980 |
| `<p>considérant que …`, sans classe | absente | les plus anciens |
| `<p>(1) considérant que …` | imprimée, avant le mot | années 1990 |

Les 95 actes que la première version rendait vides venaient du troisième
gabarit : un `<p>` sans aucun attribut. Rien ne le signalait — les compteurs
affichaient simplement un grand nombre d'actes « sans considérant », ce qui est
invraisemblable pour du droit de l'Union et n'aurait pas dû être accepté.

**Le numéro n'est jamais recalculé.** Pour les actes qui ne numérotent pas leurs
considérants — 289 sur 7 674 — `numero` reste nul et seul le rang de lecture est
enregistré. Combler ce nul par le rang donnerait un numéro d'apparence officielle
qui ne figure nulle part dans l'original.

## 4. Un code 200 n'est pas une preuve qu'on tient le document

À cadence soutenue, EUR-Lex rend une **page de défi anti-robot d'AWS** : 2 035
octets, code 200, aucun message d'erreur. Il rend aussi, pour certains actes, la
coquille JavaScript de son interface — 85 ko sans une ligne du texte.

La première version contrôlait la taille (« au moins 2 000 octets ») et a stocké
**37 de ces pages sur 284 comme si c'étaient des actes**, dont le règlement (CE)
n° 1008/2008 — celui-là même qui avait servi à valider la méthode des ancres une
heure plus tôt. Le défaut ne s'est vu qu'en constatant un nombre absurde d'actes
sans considérant.

Le contrôle porte désormais sur le **contenu** : un acte porte forcément soit des
considérants, soit sa formule d'adoption. Ce qui n'en porte pas est refusé et
retenté avec une pause qui double à chaque échec. C'est la même leçon que le 404
de la XIVe législature (`docs/10` § 4), sous une autre forme : **ni le code de
retour ni la taille ne disent qu'on tient la bonne chose.**

Trois actes résistent — 32008R0149, 32008R1272, 32011R0142 — pour lesquels
EUR-Lex ne publie aucun rendu HTML français. Ils touchent 3 articles en vigueur.
Le trou est déclaré, non comblé.

## 5. Ce qu'on ne peut pas dire, et qui a été essayé

**Rien ne relie un considérant à un article français.** Le lien passe par l'acte,
et l'acte lui-même n'apparie pas ses considérants à ses articles. Deux méthodes
ont été essayées pour deviner, mesurées, et écartées.

**L'appariement lexical.** Un considérant est proposé s'il partage avec l'article
au moins deux mots longs et rares dans l'acte. Sur L. 112-1-1, qui impose
d'afficher le prix antérieur lors d'une annonce de réduction, la méthode retient
le considérant (30) — *les définitions des notions de contenus numériques* — sur
la foi de « pendant » et « période ». Sur L. 511-7, elle retient trois
considérants de procédure sur la protection des données. Le taux de bruit rend la
méthode inutilisable, et surtout **activement nuisible** : afficher un considérant
à côté d'un article suggère un lien que rien n'établit.

**La convention rédactionnelle du dernier considérant.** Le guide pratique commun
veut que le dernier considérant énonce l'objectif et la subsidiarité. C'est vrai
de la directive 2019/2161 ; c'est faux du règlement 2017/2394, dont le dernier
considérant abroge un texte antérieur, et de la directive 2011/83, dont le dernier
renvoie à un accord interinstitutionnel. La convention n'est pas une règle.

La restitution rend donc les considérants **au grain de l'acte**, avec leur
nombre, leur texte et leur ancre, et écrit noir sur blanc que rien ne désigne
celui qui motive l'article consulté.

## 6. Ce que la tranche apporte quand même à l'article

Un gain de grain, lui, est déclaré : **150 citations nomment un article précis de
l'acte** — « De l'article 23 du règlement (CE) n° 1008/2008 ». Croisé avec les
6 237 articles d'actes chargés, cela donne son intitulé et un lien profond :

```
  [2] 2° De l'article 23 du règlement (CE) n° 1008/2008 du Parlement européen…
        cite règlement (CE) n° 1008/2008, article 23 — Information et non-discrimination
          https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32008R1008#art_23
```

130 des 150 sont confirmées contre les articles que l'acte déclare ; les 20 autres
portent sur des actes au gabarit ancien, qui ne déclarent pas leurs articles — le
numéro est conservé, puisque c'est le texte français qui l'écrit, mais aucun lien
profond n'est fabriqué.

Le champ n'est renseigné que lorsque la fenêtre qui précède l'acte nomme **un
seul** article. Une première version tentait de découper les énumérations
— « des articles 5 ter, 8, 9 et 16 » — et attribuait à un acte les articles de
celui cité juste avant, en perdant les suffixes (« 5 ter » lu « 5 »). Sur les
1 328 citations sans article, **877 n'en nomment aucun** et **451 en nomment
plusieurs ou de façon ambiguë** : ces dernières sont ce que la tranche renonce à
découper, et le champ reste nul plutôt que faux.

## 7. Ce que la tranche ne fait pas

**Le texte des articles de l'acte n'est pas chargé**, seulement leur numéro, leur
intitulé et leur ancre. Le produit trace la provenance ; il ne recopie pas la
norme étrangère.

**Les tableaux de concordance ne sont pas ingérés.** Ils existent, en annexe des
textes de transposition, et sont la seule source qui apparie un article de
directive à un article du code français. C'est le seul chemin connu vers un lien
européen au grain de l'article, et il reste ouvert.

**La jurisprudence de la Cour de justice est hors périmètre.**
