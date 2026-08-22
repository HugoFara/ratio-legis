# Golden set — 25 articles du Code de la consommation

**Livrable § 9.3 de la feuille de route.**
**Date : 22 août 2026. Révision 2** — la première version publiait un chiffre
d'affiche faux, corrigé au § 3.
**Données machine :** `data/golden-set/golden-set-v1.json`,
`data/golden-set/jeu-annotation-100.csv`.

---

## 1. Ce que ce livrable est, et n'est pas

Le § 1 exige un golden set « annoté **à la main par un humain** », et le § 9
précise que ce point est « le vrai test de faisabilité du projet ».

Ce document ne satisfait pas cette exigence. Il contient **25 chaînes
reconstruites automatiquement** depuis les sources primaires, chacune traçable
jusqu'à son identifiant d'origine, plus les mesures qui permettent de savoir ce
que ces chaînes valent. **La phase 0 reste ouverte** jusqu'à validation humaine.

Le protocole d'annotation et le jeu de 100 articles à annoter sont au § 6.

## 2. Composition

Les 25 articles couvrent délibérément les cas pénibles exigés au § 1.

| Catégorie | N | Cas pénible couvert |
|---|---:|---|
| Origine législative récente (16e-17e législature) | 4 | Amendements AN disponibles en open data |
| Origine 14e législature | 5 | Amendements AN **indisponibles** en open data |
| Origine 13e législature | 3 | Limite basse de l'open data parlementaire |
| Origine 15e législature | 2 | — |
| Ordonnance de transposition d'une directive | 3 | « La raison est à Bruxelles » |
| Ordonnance antérieure à la recodification | 2 | Modification par ordonnance |
| Ordonnance, création nette | 2 | Aucun prédécesseur, aucun débat |
| Origine antérieure à l'open data parlementaire | 2 | **Raison réellement introuvable** |
| Reclassement réglementaire → législatif | 1 | Origine dans un décret non motivé |
| Aucun lien producteur dans LEGI | 1 | **Chaîne rompue au premier maillon** |

## 3. Correction du chiffre d'affiche

La première version de ce document annonçait **21 / 25 chaînes aboutissant à un
document de motivation**. Ce chiffre était juste au sens littéral et trompeur au
sens utile : il mesurait **le rattachement au dossier législatif**, pas la
motivation de l'article.

Exemple, l'article L224-3 sur l'offre de fourniture d'électricité. Sa version en
vigueur vient de la loi du 16 août 2022 « portant mesures d'urgence pour la
protection du pouvoir d'achat ». On en récupère l'exposé des motifs, l'étude
d'impact et l'avis du Conseil d'État. Aucun de ces documents ne nomme cet article.
On a atteint le dossier d'une loi de circonstance, pas la raison de cet article-là.

**La mesure manquante a été faite.** Pour chaque article, on cherche son numéro —
actuel et antérieur à 2016 — dans le texte de l'exposé des motifs et dans le texte
extrait de l'étude d'impact.

| Mesure | Résultat |
|---|---:|
| Chaîne atteignant un dossier et au moins un document | 21 / 25 |
| **Article effectivement nommé dans l'un de ces documents** | **5 / 25** |
| Arête `resulte_de` confirmée sur la version en vigueur | **0 / 25** |

**Le chiffre à retenir est 5 / 25.** Les deux autres encadrent : 21/25 est le
plafond du rattachement documentaire, 0/25 est l'état réel du rattachement
d'amendements.

La même mesure sur toute la population éligible du périmètre (832 articles),
restreinte aux 493 articles dont l'exposé des motifs **et** l'étude d'impact ont
été récupérés :

| Population | Article nommé | Documents muets |
|---|---:|---:|
| 493 articles à documentation complète | **208 (42,2 %)** | 285 (57,8 %) |
| dont les 307 issus de la loi consommation de 2014 | **171 (55,7 %)** | 136 (44,3 %) |

L'écart entre les deux documents est net et exploitable : l'exposé des motifs ne
nomme l'article que dans **6,4 %** des cas, l'étude d'impact dans **24,8 %**.
L'étude d'impact est structurée article par article, l'exposé des motifs est un
texte politique. **La priorité d'ingestion doit être l'étude d'impact, pas
l'exposé des motifs** — ce que la feuille de route ne hiérarchise pas.

Réserve sur ces chiffres : la recherche porte sur la citation du numéro d'article.
Un passage peut motiver une disposition sans la nommer. C'est donc une borne
inférieure pour la motivation réelle, et une borne supérieure pour ce qu'un
système automatique peut **ancrer**. C'est cette seconde borne qui compte, puisque
le § 4.3 interdit toute phrase sans citation résoluble.

## 4. Zéro arête `resulte_de`, et la raison est structurelle

La révision 1 exhibait deux articles avec un « amendement candidat ». Les deux
étaient invalides, et le document en portait lui-même les éléments : amendements
des sessions 2012-2013 et 2013-2014 pour des versions en vigueur datant de 2022 et
2025. Le § 5 énonçait la règle — « l'arête `resulte_de` relie une `VersionArticle`,
jamais un `Article` » — et la construction la violait.

**Règle appliquée depuis :** un amendement ne peut produire la rédaction en
vigueur que si le texte producteur de cette version est la loi du dossier de
l'amendement. Les trois rattachements sont écartés, et le compte est **0 / 25**.

Ce n'est pas un accident d'échantillon. Mesure sur les 307 articles du périmètre
dont la disposition provient de la loi consommation de 2014 :

> **Aucun d'entre eux — 0 sur 307 — n'a encore cette loi comme texte producteur de
> sa version en vigueur.** 192 ont été réécrits par la recodification de 2016
> elle-même, les autres par des ordonnances et lois postérieures.

Conséquence pour le modèle de données du § 3, et elle est structurante :

- Une arête `resulte_de` attachée à la **version en vigueur** est vide par
  construction sur tout corpus recodifié. Ce n'est pas un objectif à 60 %, c'est
  un objectif à zéro.
- L'arête n'a de sens qu'attachée à la **version historique** que l'amendement a
  effectivement produite, **plus** une assertion explicite du type « repris sans
  modification de fond par la recodification du 14 mars 2016 ».
- Cette assertion de conservation du fond est un objet nouveau, absent du § 3, et
  elle est vérifiable : c'est une comparaison de textes entre la version
  pré-recodification et la version post-recodification.

Sans cet objet, le produit ne peut pas dire « cet article existe sous cette forme
à cause de cet amendement » sans mentir sur la chaîne.

## 5. Ce que coûte la précision : deux mesures

**Appariement naïf.** Chercher toute occurrence d'un numéro `L. xxx-xx` dans le
dispositif des amendements adoptés. Rendement apparent : 104 articles, 10
rattachements sur le golden set. **Faux à 90 %**, pour deux raisons systématiques :
un numéro d'article ne dit pas de quelle loi vient l'amendement, et il ne
distingue pas l'article *modifié* de l'article simplement *cité* en renvoi.

**Cible du langage modificatif.** Ne retenir que l'article désigné comme objet de
l'action (« l'article L. X est ainsi modifié », « après l'article L. X, il est
inséré »).

| Méthode | Articles ciblés | Amendements adoptés exploités | Fiabilité |
|---|---:|---:|---|
| Citation naïve d'un numéro | 104 | 74 / 228 (32 %) | ~10 % |
| Cible du langage modificatif | 9 | 9 / 228 (4 %) | exploitable |

Le rappel s'effondre de 32 % à 4 % dès qu'on exige la précision. La raison est
structurelle : la grande majorité des amendements ne nomment pas l'article du
code, ils modifient l'article *du projet de loi* par son numéro d'alinéa. **Le
composant qui résout « article du projet de loi → article du code » est la
condition d'existence de l'arête `resulte_de`**, pas une optimisation.

## 6. Protocole d'annotation humaine

Le critère de sortie de la phase 0 ne peut pas être « chaîne complète oui / non ».
La mesure du § 3 montre qu'une chaîne peut être complète et ne rien expliquer.

**Livrable attendu de l'annotateur, par article :**

| Champ | Contenu |
|---|---|
| `ANNOT_document` | Document consulté : exposé des motifs, étude d'impact, avis du CE, rapport au PR, compte rendu, amendement |
| `ANNOT_offset_debut` / `ANNOT_offset_fin` | **Offsets de caractères** du passage qui motive cet article dans ce document |
| `ANNOT_passage_cite` | Le passage lui-même, pour contrôle |
| `ANNOT_verdict` | `motive` / `dossier_seulement` / `non_documente` |
| `ANNOT_commentaire` | Notamment : le passage motive-t-il l'article, ou seulement le dispositif d'ensemble ? |

Les offsets ne sont pas un raffinement : le § 4.3 exige que toute phrase produite
porte une citation résoluble au niveau du passage. Un golden set sans offsets ne
teste pas le contrat de génération.

**Taille de l'échantillon.** 25 articles ne permettent pas de mesurer une précision
à 95 % — un seul faux positif fait 4 points. La population éligible étant de 832
articles, un jeu de 100 est proportionné et reste annotable en quelques jours.

`data/golden-set/jeu-annotation-100.csv` contient **100 articles** échantillonnés
de façon déterministe et reproductible (tri par hachage du numéro d'article, sans
choix humain), stratifiés ainsi :

| Strate | N |
|---|---:|
| Éligible `resulte_de`, 12e-15e législature | 46 |
| Origine ordonnance | 25 |
| Origine antérieure à l'open data parlementaire | 15 |
| Éligible `resulte_de`, 16e-17e législature | 10 |
| Reclassement réglementaire → législatif | 3 |
| Sans origine identifiable | 1 |

Deux colonnes d'indices pré-calculés — `indice_expose_nomme_article` et
`indice_etude_impact_nomme_article` — signalent où chercher. Elles ne préjugent
pas du verdict : l'annotateur doit pouvoir conclure « nommé mais non motivé ».

## 7. Méthode de reconstruction automatique

1. Version en vigueur dans LEGI (`ETAT = VIGUEUR`), identifiant `LEGIARTI`.
2. Texte producteur : lien `CREE` / `MODIFIE` / `CREATION` / `MODIFICATION` dont
   `naturetexte` est un texte normatif. L'attribut `sens` est ignoré, il n'est pas
   fiable (voir `01-rapport-verification-sources.md` § 2.3 bis).
3. Article prédécesseur : lien `CONCORDANCE` / `CONCORDE` / `TRANSFERE` /
   `DEPLACE`, **un seul saut**, résolu par l'identifiant `LEGIARTI` du lien et
   jamais par le numéro d'article.
4. Texte à l'origine : lien `CREE` le plus ancien porté par le prédécesseur.
5. Dossier : jointure du `cid` sur `ID_TEXTE_1` de DOLE.
6. Documents : exposé des motifs inline, liens de l'`ARBORESCENCE`, rapport au
   Président de la République via `ID_TEXTE_2`, études d'impact extraites en texte.
7. Motivation spécifique : recherche du numéro d'article dans ces textes.
8. Amendement : cible du langage modificatif, restreinte au dossier du texte
   producteur **de la version en vigueur**.

Trois avertissements à conserver en phase 2 :

**Le saut de concordance est borné à un cran, délibérément.** La fermeture
transitive diverge : sur L311-1 elle atteint 266 numéros d'articles distincts et
fait remonter l'origine à la codification de 1993 — exact et inutile.

**Résoudre par identifiant, jamais par numéro.** Un même numéro d'article peut
désigner deux dispositions sans rapport à deux époques. `R531-2` en est le cas
type : l'article abrogé en 2016 traitait de l'Institut national de la
consommation, celui en vigueur aujourd'hui traite de la vente de marchandises non
conformes.

**Le modèle est de niveau article, le produit sera de niveau segment.** Avec 19,5
textes ayant touché un article en moyenne, « le texte à l'origine de la
disposition » est une simplification : chaque alinéa a sa propre provenance.
L'étape 4 ci-dessus produit une réponse plausible et fausse dans une part
indéterminée des cas. Voir `00-note-de-cadrage.md` § 5.

---

## 8. Les 25 chaînes

### Origine législative récente, amendements AN en open data — 4 article(s)

#### 1. Article L224-3

- **Version en vigueur** : `LEGIARTI000046197680`, depuis le 2023-07-01. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « L'offre de fourniture d'électricité ou de gaz naturel précise, dans des termes clairs et compréhensibles, les informations suivantes : 1° L'identité du fournisseur, l'adresse de so… »
- **Article prédécesseur** (avant la recodification de 2016) : L121-87
- **Texte producteur de la version en vigueur** : LOI n°2022-1158 du 16 août 2022 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000046027237` — LOI n° 2022-1158 du 16 août 2022 portant mesures d'urgence pour la protection du pouvoir d'achat (16e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, avis du Conseil d'État, 3 comptes rendus
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non récupérée)
- **Amendement écarté** : Sénat n° 681 (M. FAUCONNIER), cible L121-87.
    - L'amendement appartient au dossier de la loi du 17 mars 2014 ; la version en vigueur est produite par « LOI n°2022-1158 du 16 août 2022 ». L'arête relierait une version historique, pas la version en vigueur.
- **Maillon manquant** : Un amendement du Sénat porte sur une version historique de l'article, mais la rédaction en vigueur a été produite par un texte postérieur. Aucune arête resulte_de confirmée.

#### 2. Article L224-12

- **Version en vigueur** : `LEGIARTI000051560277`, depuis le 2025-05-03. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « Les factures de fourniture d'électricité et de gaz naturel sont présentées dans les conditions fixées par un arrêté du ministre chargé de la consommation et du ministre chargé de l… »
- **Article prédécesseur** (avant la recodification de 2016) : L121-91
- **Texte producteur de la version en vigueur** : LOI n°2025-391 du 30 avril 2025 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000050427907` — LOI n° 2025-391 du 30 avril 2025 portant diverses dispositions d'adaptation au droit de l'Union européenne en  (17e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, avis du Conseil d'État
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non récupérée)
- **Amendement écarté** : Sénat n° 101 (Mme LÉTARD), cible L121-91.
    - L'amendement appartient au dossier de la loi du 17 mars 2014 ; la version en vigueur est produite par « LOI n°2025-391 du 30 avril 2025 ». L'arête relierait une version historique, pas la version en vigueur.
- **Amendement écarté** : Sénat n° 167 (M. COINTAT), cible L121-91.
    - L'amendement appartient au dossier de la loi du 17 mars 2014 ; la version en vigueur est produite par « LOI n°2025-391 du 30 avril 2025 ». L'arête relierait une version historique, pas la version en vigueur.
- **Maillon manquant** : Un amendement du Sénat porte sur une version historique de l'article, mais la rédaction en vigueur a été produite par un texte postérieur. Aucune arête resulte_de confirmée.

#### 3. Article L521-3-1

- **Version en vigueur** : `LEGIARTI000049571083`, depuis le 2024-02-17. Livre V : POUVOIRS D'ENQUÊTE ET SUITES DONNÉES AUX CONTRÔLES.
- **Extrait** : « Lorsque les agents habilités constatent, avec les pouvoirs prévus au présent livre, une infraction ou un manquement aux dispositions mentionnées aux articles L. 511-5, L. 511-6 et… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : LOI n°2024-449 du 21 mai 2024 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000047533100` — LOI n° 2024-449 du 21 mai 2024 visant à sécuriser et à réguler l'espace numérique (16e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, avis du Conseil d'État, 2 comptes rendus
- **✅ L'article est-il nommé dans ces documents ?** nommé (exposé des motifs : oui ; étude d'impact : non récupérée)
- **Maillon manquant** : Amendement non rattaché ; à chercher dans l'open data AN (16e-17e), non fait à ce stade.

#### 4. Article L132-1 A

- **Version en vigueur** : `LEGIARTI000051560139`, depuis le 2025-05-03. Livre Ier : INFORMATION DES CONSOMMATEURS ET PRATIQUES COMMERCIALES.
- **Extrait** : « Sans préjudice de l'allocation de dommages et intérêts, une amende civile peut être prononcée, à la suite d'une demande d'assistance mutuelle prévue par l'article L. 511-10 portant… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : LOI n°2025-391 du 30 avril 2025 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000050427907` — LOI n° 2025-391 du 30 avril 2025 portant diverses dispositions d'adaptation au droit de l'Union européenne en  (17e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, avis du Conseil d'État
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Amendement non rattaché ; à chercher dans l'open data AN (16e-17e), non fait à ce stade.


### Origine 14e législature, amendements AN hors open data — 5 article(s)

#### 5. Article L412-1

- **Version en vigueur** : `LEGIARTI000041985019`, depuis le 2020-06-12. Livre IV : CONFORMITÉ ET SÉCURITÉ DES PRODUITS ET SERVICES.
- **Extrait** : « I.-Des décrets en Conseil d'Etat définissent les règles auxquelles doivent satisfaire les marchandises. Ils déterminent notamment : 1° Les conditions dans lesquelles l'exportation,… »
- **Article prédécesseur** (avant la recodification de 2016) : L214-1
- **Texte producteur de la version en vigueur** : LOI n°2020-699 du 10 juin 2020 (LOI, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n°2014-344 du 17 mars 2014 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000027383756` — LOI n° 2014-344 du 17 mars 2014 relative à la consommation (14e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, 24 comptes rendus
- **✅ L'article est-il nommé dans ces documents ?** nommé (exposé des motifs : non ; étude d'impact : oui)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.

#### 6. Article L511-7

- **Version en vigueur** : `LEGIARTI000051558799`, depuis le 2025-05-03. Livre V : POUVOIRS D'ENQUÊTE ET SUITES DONNÉES AUX CONTRÔLES.
- **Extrait** : « Les agents sont habilités à rechercher et à constater les infractions ou les manquements aux dispositions : 1° Du règlement (UE) 2021/782 du Parlement européen et du Conseil du 29… »
- **Article prédécesseur** (avant la recodification de 2016) : L141-1
- **Texte producteur de la version en vigueur** : LOI n°2025-391 du 30 avril 2025 (LOI, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n°2016-41 du 26 janvier 2016 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000029589477` — LOI n° 2016-41 du 26 janvier 2016 de modernisation de notre système de santé (14e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, 35 comptes rendus
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.

#### 7. Article L221-5

- **Version en vigueur** : `LEGIARTI000044563141`, depuis le 2022-05-28. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « I.-Préalablement à la conclusion d'un contrat de vente de biens ou de fourniture de services, de contenu numérique ou de services numériques, le professionnel fournit au consommate… »
- **Article prédécesseur** (avant la recodification de 2016) : L121-17
- **Texte producteur de la version en vigueur** : Ordonnance n°2021-1734 du 22 décembre 2021 (ORDONNANCE, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n°2014-344 du 17 mars 2014 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000027383756` — LOI n° 2014-344 du 17 mars 2014 relative à la consommation (14e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, 24 comptes rendus
- **✅ L'article est-il nommé dans ces documents ?** nommé (exposé des motifs : non ; étude d'impact : oui)
- **Maillon manquant** : Aucun : un amendement candidat est identifié par citation directe du numéro d'article.

#### 8. Article L111-4

- **Version en vigueur** : `LEGIARTI000044330854`, depuis le 2022-01-01. Livre Ier : INFORMATION DES CONSOMMATEURS ET PRATIQUES COMMERCIALES.
- **Extrait** : « Le fabricant ou l'importateur de biens meubles informe le vendeur professionnel de la disponibilité ou de la non-disponibilité des pièces détachées indispensables à l'utilisation d… »
- **Article prédécesseur** (avant la recodification de 2016) : L111-3
- **Texte producteur de la version en vigueur** : LOI n°2021-1485 du 15 novembre 2021 (LOI, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n° 2014-344 du 17 mars 2014 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000027383756` — LOI n° 2014-344 du 17 mars 2014 relative à la consommation (14e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, 24 comptes rendus
- **✅ L'article est-il nommé dans ces documents ?** nommé (exposé des motifs : non ; étude d'impact : oui)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.

#### 9. Article L221-28

- **Version en vigueur** : `LEGIARTI000044563170`, depuis le 2022-05-28. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « Le droit de rétractation ne peut être exercé pour les contrats : 1° De fourniture de services pleinement exécutés avant la fin du délai de rétractation et, si le contrat soumet le… »
- **Article prédécesseur** (avant la recodification de 2016) : L121-21-8
- **Texte producteur de la version en vigueur** : Ordonnance n°2021-1734 du 22 décembre 2021 (ORDONNANCE, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n°2014-344 du 17 mars 2014 (LOI, lien `CREE`)
- **Dossier atteint** : `JORFDOLE000027383756` — LOI n° 2014-344 du 17 mars 2014 relative à la consommation (14e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, 24 comptes rendus
- **✅ L'article est-il nommé dans ces documents ?** nommé (exposé des motifs : non ; étude d'impact : oui)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.


### Origine 13e législature — 3 article(s)

#### 10. Article L121-4

- **Version en vigueur** : `LEGIARTI000044563107`, depuis le 2022-05-28. Livre Ier : INFORMATION DES CONSOMMATEURS ET PRATIQUES COMMERCIALES.
- **Extrait** : « Sont réputées trompeuses, au sens des articles L. 121-2 et L. 121-3, les pratiques commerciales qui ont pour objet : 1° Pour un professionnel, de se prétendre signataire d'un code… »
- **Article prédécesseur** (avant la recodification de 2016) : L121-1-1
- **Texte producteur de la version en vigueur** : Ordonnance n°2021-1734 du 22 décembre 2021 (ORDONNANCE, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n°2008-776 du 4 août 2008 (LOI, lien `CREE`)
- **Dossier atteint** : `JORFDOLE000018730653` — Loi n° 2008-776 du 4 août 2008 de modernisation de l'économie (13e législature)
- **Documents récupérés** : exposé des motifs, 29 comptes rendus
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.

#### 11. Article L311-1

- **Version en vigueur** : `LEGIARTI000034072668`, depuis le 2017-02-23. Livre III : CRÉDIT.
- **Extrait** : « Pour l'application des dispositions du présent titre, sont considérés comme : 1° Prêteur, toute personne qui consent ou s'engage à consentir un crédit mentionné au présent titre da… »
- **Article prédécesseur** : L311-1 — numéro inchangé, lien de concordance néanmoins présent
- **Texte producteur de la version en vigueur** : LOI n°2017-203 du 21 février 2017 (LOI, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n°2010-737 du 1er juillet 2010 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000020542090` — LOI n° 2010-737 du 1er juillet 2010 portant réforme du crédit à la consommation (13e législature)
- **Documents récupérés** : exposé des motifs, 11 comptes rendus
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.

#### 12. Article L511-22

- **Version en vigueur** : `LEGIARTI000041985451`, depuis le 2020-06-12. Livre V : POUVOIRS D'ENQUÊTE ET SUITES DONNÉES AUX CONTRÔLES.
- **Extrait** : « I-Sont habilités à rechercher et à constater, dans l'exercice de leurs fonctions, les infractions aux dispositions du livre IV et les infractions et les manquements mentionnés aux… »
- **Article prédécesseur** (avant la recodification de 2016) : L115-31
- **Texte producteur de la version en vigueur** : Ordonnance n°2020-701 du 10 juin 2020 (ORDONNANCE, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : LOI n°2011-525 du 17 mai 2011 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000021369332` — LOI n° 2011-525 du 17 mai 2011 de simplification et d'amélioration de la qualité du droit (13e législature)
- **Documents récupérés** : 10 comptes rendus
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.


### Origine 15e législature — 2 article(s)

#### 13. Article L771-2

- **Version en vigueur** : `LEGIARTI000045178745`, depuis le 2022-02-16. Livre VII : TRAITEMENT DES SITUATIONS DE SURENDETTEMENT.
- **Extrait** : « Sont applicables dans les îles Wallis et Futuna, sous réserve des adaptations prévues à l'article L. 771-3, les dispositions des articles mentionnés dans la colonne de gauche du ta… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : LOI n°2022-172 du 14 février 2022 (LOI, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000044125588` — LOI n° 2022-172 du 14 février 2022 en faveur de l'activité professionnelle indépendante (15e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, avis du Conseil d'État, 2 comptes rendus
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.

#### 14. Article L714-1

- **Version en vigueur** : `LEGIARTI000037650242`, depuis le 2019-03-01. Livre VII : TRAITEMENT DES SITUATIONS DE SURENDETTEMENT.
- **Extrait** : « I.-Lorsque le locataire a repris le paiement du loyer et des charges et que, dans le cours des délais de paiement de la dette locative accordés par une décision du juge saisi en ap… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : LOI n°2018-1021 du 23 novembre 2018 (LOI, lien `CREE`)
- **Dossier atteint** : `JORFDOLE000036769798` — LOI n° 2018-1021 du 23 novembre 2018 portant évolution du logement, de l'aménagement et du numérique (15e législature)
- **Documents récupérés** : exposé des motifs, étude d'impact, avis du Conseil d'État, 34 comptes rendus
- **❌ L'article est-il nommé dans ces documents ?** documents muets sur cet article (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Amendement non rattaché : les amendements AN de cette législature ne sont pas en open data.


### Ordonnance de transposition d'une directive — 3 article(s)

#### 15. Article L224-25-22

- **Version en vigueur** : `LEGIARTI000044133072`, depuis le 2021-10-01. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « I.-Dans les cas prévus à l'article L. 224-25-20, le consommateur informe le professionnel de sa décision de résoudre le contrat. Pour les contrats mentionnés au II de l'article L.… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : Ordonnance n°2021-1247 du 29 septembre 2021 (ORDONNANCE, lien `CREE`)
- **Dossier atteint** : `JORFDOLE000044129891` — Ordonnance n° 2021-1247 du 29 septembre 2021 relative à la garantie légale de conformité pour les biens, les c (15e législature)
- **Documents récupérés** : rapport au Président de la République
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun débat parlementaire par construction ; la motivation se limite aux documents du Gouvernement.

#### 16. Article L224-25-5

- **Version en vigueur** : `LEGIARTI000044133347`, depuis le 2021-10-01. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « Tout contrat souscrit par un consommateur pour la fourniture de contenus numériques ou de services numériques comporte au moins les informations suivantes : 1° L'identité et les co… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : Ordonnance n°2021-1247 du 29 septembre 2021 (ORDONNANCE, lien `CREE`)
- **Dossier atteint** : `JORFDOLE000044129891` — Ordonnance n° 2021-1247 du 29 septembre 2021 relative à la garantie légale de conformité pour les biens, les c (15e législature)
- **Documents récupérés** : rapport au Président de la République
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun débat parlementaire par construction ; la motivation se limite aux documents du Gouvernement.

#### 17. Article L351-3

- **Version en vigueur** : `LEGIARTI000048527384`, depuis le 2023-12-30. Livre III : CRÉDIT.
- **Extrait** : « Sont applicables dans les îles Wallis et Futuna, sous réserve des adaptations prévues à l'article L. 351-4, les dispositions des articles mentionnés dans la colonne de gauche du ta… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : Ordonnance n°2023-1139 du 6 décembre 2023 (ORDONNANCE, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000048532766` — Ordonnance n° 2023-1139 du 6 décembre 2023 relative aux gestionnaires de crédits et aux acheteurs de crédits (16e législature)
- **Documents récupérés** : rapport au Président de la République
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun débat parlementaire par construction ; la motivation se limite aux documents du Gouvernement.


### Ordonnance antérieure à la recodification — 2 article(s)

#### 18. Article L511-12

- **Version en vigueur** : `LEGIARTI000042623564`, depuis le 2020-12-05. Livre V : POUVOIRS D'ENQUÊTE ET SUITES DONNÉES AUX CONTRÔLES.
- **Extrait** : « Les agents sont habilités à rechercher et à constater : 1° Les infractions aux dispositions réglementaires prises en application du II de l'article L. 231-1, des articles L. 231-5,… »
- **Article prédécesseur** (avant la recodification de 2016) : L215-2
- **Texte producteur de la version en vigueur** : LOI n°2020-1508 du 3 décembre 2020 (LOI, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : Ordonnance n°2010-462 du 6 mai 2010 (ORDONNANCE, lien `MODIFICATION`)
- **Dossier atteint** : `JORFDOLE000022204472` — Ordonnance n° 2010-462 du 6 mai 2010 créant un livre IX du code rural relatif à la pêche maritime et à l'aquac (13e législature)
- **Documents récupérés** : rapport au Président de la République
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun débat parlementaire par construction ; la motivation se limite aux documents du Gouvernement.

#### 19. Article L217-5

- **Version en vigueur** : `LEGIARTI000044142571`, depuis le 2021-10-01. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « I.-En plus des critères de conformité au contrat, le bien est conforme s'il répond aux critères suivants : 1° Il est propre à l'usage habituellement attendu d'un bien de même type,… »
- **Article prédécesseur** (avant la recodification de 2016) : L211-5
- **Texte producteur de la version en vigueur** : Ordonnance n°2021-1247 du 29 septembre 2021 (ORDONNANCE, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : Ordonnance n°2005-136 du 17 février 2005 (ORDONNANCE, lien `CREATION`)
- **Dossier atteint** : `JORFDOLE000021979239` — Ordonnance n° 2005-136 du 17 février 2005 relative à la garantie de la conformité du bien au contrat due par l (12e législature)
- **Documents récupérés** : rapport au Président de la République
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun débat parlementaire par construction ; la motivation se limite aux documents du Gouvernement.


### Ordonnance, création nette sans prédécesseur — 2 article(s)

#### 20. Article L313-16

- **Version en vigueur** : `LEGIARTI000032315947`, depuis le 2016-07-01. Livre III : CRÉDIT.
- **Extrait** : « Le crédit n'est accordé à l'emprunteur que si le prêteur a pu vérifier que les obligations découlant du contrat de crédit seront vraisemblablement respectées conformément à ce qui… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : Ordonnance n°2016-351 du 25 mars 2016 (ORDONNANCE, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000032302646` — Ordonnance n° 2016-351 du 25 mars 2016 sur les contrats de crédit aux consommateurs relatifs aux biens immobil (14e législature)
- **Documents récupérés** : rapport au Président de la République
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun débat parlementaire par construction ; la motivation se limite aux documents du Gouvernement.

#### 21. Article L341-33

- **Version en vigueur** : `LEGIARTI000032303393`, depuis le 2016-07-01. Livre III : CRÉDIT.
- **Extrait** : « Les personnes physiques déclarées coupables des infractions punies par les dispositions des articles L. 341-29 à L. 341-32 encourent également à titre de peines complémentaires l'i… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : Ordonnance n°2016-351 du 25 mars 2016 (ORDONNANCE, lien `MODIFIE`)
- **Dossier atteint** : `JORFDOLE000032302646` — Ordonnance n° 2016-351 du 25 mars 2016 sur les contrats de crédit aux consommateurs relatifs aux biens immobil (14e législature)
- **Documents récupérés** : rapport au Président de la République
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun débat parlementaire par construction ; la motivation se limite aux documents du Gouvernement.


### Origine antérieure à l'open data parlementaire — 2 article(s)

#### 22. Article L313-2

- **Version en vigueur** : `LEGIARTI000032316056`, depuis le 2016-07-01. Livre III : CRÉDIT.
- **Extrait** : « Sont exclus du champ d'application du présent chapitre : 1° Les prêts consentis à des personnes morales de droit public ; 2° Ceux destinés, sous quelque forme que ce soit, à financ… »
- **Article prédécesseur** (avant la recodification de 2016) : L312-3
- **Texte producteur de la version en vigueur** : Ordonnance n°2016-351 du 25 mars 2016 (ORDONNANCE, lien `MODIFIE`)
- **Texte à l'origine de la disposition** : Loi 93-949 1993-07-26 annexe JORF 27 juillet 1993 (LOI, lien `CREATION`)
- **Dossier atteint** : aucun
- **Documents récupérés** : **aucun**
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Texte d'origine antérieur à la couverture DOLE : aucun dossier législatif récupérable.

#### 23. Article L823-1

- **Version en vigueur** : `LEGIARTI000032224216`, depuis le 2016-07-01. Livre VIII : ASSOCIATIONS AGRÉÉES DE DÉFENSE DES CONSOMMATEURS ET INSTITUTIONS DE LA CONSOMMATION.
- **Extrait** : « Le laboratoire de métrologie et d'essais est un établissement public national à caractère industriel et commercial. Le laboratoire est chargé de réaliser tous travaux d'étude, de r… »
- **Article prédécesseur** (avant la recodification de 2016) : L561-1
- **Texte producteur de la version en vigueur** : Ordonnance n°2016-301 du 14 mars 2016 (ORDONNANCE, lien `CREE`)
- **Texte à l'origine de la disposition** : Loi 93-949 1993-07-26 annexe JORF 27 juillet 1993 (LOI, lien `CREATION`)
- **Dossier atteint** : aucun
- **Documents récupérés** : **aucun**
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Texte d'origine antérieur à la couverture DOLE : aucun dossier législatif récupérable.


### Origine réglementaire déclarée sur un article législatif — 1 article(s)

#### 24. Article L822-2

- **Version en vigueur** : `LEGIARTI000032224241`, depuis le 2016-07-01. Livre VIII : ASSOCIATIONS AGRÉÉES DE DÉFENSE DES CONSOMMATEURS ET INSTITUTIONS DE LA CONSOMMATION.
- **Extrait** : « L'Institut national de la consommation a pour objet de : 1° Fournir un appui technique aux associations de défense des consommateurs ; 2° Regrouper, produire, analyser et diffuser… »
- **Article prédécesseur** (avant la recodification de 2016) : R531-2
- **Texte producteur de la version en vigueur** : Ordonnance n°2016-301 du 14 mars 2016 (ORDONNANCE, lien `CREE`)
- **Texte à l'origine de la disposition** : Décret n°2010-1221 du 18 octobre 2010 (DECRET, lien `MODIFIE`)
- **Dossier atteint** : aucun
- **Documents récupérés** : **aucun**
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Texte d'origine antérieur à la couverture DOLE : aucun dossier législatif récupérable.


### Aucun lien producteur dans LEGI — 1 article(s)

#### 25. Article L222-17

- **Version en vigueur** : `LEGIARTI000034072595`, depuis le 2017-02-23. Livre II : FORMATION ET ÉXECUTION DES CONTRATS.
- **Extrait** : « Des règles spécifiques relatives à la fourniture à distance d'opérations d'assurance un consommateur sont par ailleurs fixées par les dispositions : - du chapitre II du titre Ier d… »
- **Article prédécesseur** : aucun, l'article n'a jamais été renuméroté
- **Texte producteur de la version en vigueur** : **aucun lien dans LEGI**
- **Dossier atteint** : aucun
- **Documents récupérés** : **aucun**
- **❌ L'article est-il nommé dans ces documents ?** aucun document récupéré (exposé des motifs : non ; étude d'impact : non récupérée)
- **Maillon manquant** : Aucun lien producteur dans LEGI : la chaîne est interrompue dès le premier maillon.

