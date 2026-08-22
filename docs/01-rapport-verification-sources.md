# Rapport de vérification des sources

**Livrable § 9.2 de la feuille de route.**
**Date de vérification : 22 août 2026.** Toutes les mesures de ce document ont été
obtenues en récupérant et en analysant les données réelles, pas en lisant la
documentation. Les scripts de mesure sont dans `tools/phase0/`.

Convention : ✅ confirmé · ⚠️ confirmé avec réserve · ❌ invalidé.

---

## 1. Synthèse — les `[VÉRIFIER]` de la feuille de route

| Point de la feuille de route | Verdict | Conséquence |
|---|---|---|
| § 2.1 point d'accès DILA (`echanges.dila.gouv.fr`) | ✅ | Aucune, l'URL est bonne |
| § 2.1 « dumps globaux + incréments » | ⚠️ | Global figé au 13/07/2025, voir § 2.2 ci-dessous — risque de non-reconstructibilité |
| § 2.1 « liens typés déjà présents dans LEGI » | ✅ | Confirmé et **plus riche** que décrit |
| § 2.1 API Légifrance via PISTE, OAuth2 | ✅ | Endpoint vivant, quotas non mesurables sans compte |
| § 2.2 « tableau synoptique du Sénat » | ❌ | **N'existe pas.** La cascade `resulte_de` du § 3 doit être réécrite |
| § 2.2 amendements AN en open data | ⚠️ | **Législatures 16-17 seulement.** 13/14/15 absents |
| § 2.2 avis du Conseil d'État publiés depuis 2015 | ⚠️ | Vrai, mais 14 % des lois seulement en portent un lien dans DOLE |
| § 2.3 EUR-Lex, considérants | ✅ | Accessibles sans authentification |
| § 2.3 « détecter la transposition via DOLE » | ❌ | 1 dossier sur 3 411 porte un lien EUR-Lex |
| § 2.4 réutiliser DuraLex / Archéo Lex / law-factory | ❌ | Abandonnés depuis 2019-2022, voir § 6 |
| § 0 « ordonnances : aucun exposé des motifs » | ⚠️ | **Faux à 90 %** — il existe un rapport au Président de la République |

Deux constats renversent des hypothèses structurantes du projet : l'absence du
tableau synoptique (défavorable, § 4.2) et l'existence du rapport au Président de
la République (favorable, § 3.3).

---

## 2. Fonds DILA — LEGI, JORF, DOLE

### 2.1 Point d'accès

✅ `https://echanges.dila.gouv.fr/OPENDATA/` répond en HTTP 200, listage Apache
ouvert, sans authentification. FTPS disponible sur le même hôte. 36 fonds y sont
publiés, dont les quatre qui nous intéressent : `LEGI/`, `JORF/`, `JORFSIMPLE/`,
`DOLE/`. Les DTD sont dans `DTD_LEGIFRANCE/` (archive `.7z` de 2018, plus une note
de migration technique d'octobre 2023 — le format a changé à cette date, en tenir
compte pour les archives antérieures).

Licence : Licence Ouverte / Etalab 2.0 (`fr-lo` sur data.gouv.fr), fréquence
déclarée « quotidienne », dernière mise à jour constatée le 21/08/2026.

### 2.2 ⚠️ Le risque réel : la fenêtre de rétention

C'est le point le plus important de ce rapport et il n'est pas dans la feuille de
route.

| Fonds | Dump global | Date du global | Incréments | Le plus ancien | Le plus récent |
|---|---|---|---|---|---|
| LEGI | `Freemium_legi_global_20250713-140000.tar.gz` (1,1 Go) | **13/07/2025** | 408 | 12/07/2025 | 21/08/2026 |
| JORF | `Freemium_jorf_global_20250713-140000.tar.gz` (1,6 Go) | **13/07/2025** | 744 | 13/07/2025 | 22/08/2026 |
| DOLE | `Freemium_dole_global_20250713-140000.tar.gz` (18 Mo) | **13/07/2025** | 242 | 11/07/2025 | 20/08/2026 |

Les incréments sont quotidiens et de taille modeste (LEGI : 600 Ko à 20 Mo par
jour). Mais **le plus ancien incrément disponible coïncide avec la date du dump
global**. La DILA ne conserve donc qu'une seule chaîne reconstructible : le global
du 13/07/2025 plus tout ce qui a suivi. Il n'y a aucune redondance.

Conséquences opérationnelles, à traiter en phase 1 et non plus tard :

1. **Miroiter le dump global immédiatement** et le conserver hors du cycle de vie
   du pipeline. Si la DILA publie un nouveau global et purge les incréments
   antérieurs avant que nous ayons archivé l'ancien, toute reconstruction depuis
   zéro devient impossible et le critère de sortie de la phase 1 (« ré-exécution
   complète depuis zéro, reproductible ») devient invérifiable.
2. **Archiver chaque incrément quotidien dès sa parution**, avec hash et date de
   récupération. C'est l'application directe de la règle § 5.2 « le brut est
   sacré », mais elle a ici une échéance : un incrément manqué est un trou
   définitif dans l'historique.
3. Surveiller la publication d'un nouveau global : le passage de `20250713` à une
   date ultérieure est l'événement à détecter.

### 2.3 ✅ LEGI — les liens typés, arête n° 1

Confirmé sur données réelles. Chaque version d'article porte un bloc `<LIENS>`
dont les entrées ont la forme :

```xml
<LIEN cidtexte="LEGITEXT000006074068" datesignatexte="2999-01-01"
      id="LEGIARTI000029968055" naturetexte="CODE" nortexte="" num="L401"
      numtexte="" sens="source" typelien="MODIFIE">Code des pensions… - art. L401 (M)</LIEN>
```

Les attributs `sens` (`source` / `cible`) et `typelien` donnent l'arête et son
orientation sans aucun calcul. Typologie relevée sur un incrément quotidien
(20 897 fichiers, 18/08/2026) :

| `typelien` | Occurrences | Usage pour le graphe |
|---|---:|---|
| `CITATION` | 168 827 | Bruit, à écarter du graphe de provenance |
| `CODIFICATION` | 5 158 | **Arête `renumerote_de`** |
| `MODIFIE` | 4 286 | Arête `produite_par` |
| `CREE` | 3 057 | Arête `produite_par` |
| `CONCORDANCE` | 2 263 | **Arête `renumerote_de`** |
| `CONCORDE` | 1 409 | **Arête `renumerote_de`** |
| `TXT_SOURCE` | 763 | Rattachement au texte |
| `SPEC_APPLI` | 761 | Conditions d'application |
| `MODIFICATION` | 716 | Variante historique de `MODIFIE` |
| `ABROGE` | 408 | Arête `produite_par` |
| `CREATION` | 317 | Variante historique de `CREE` |
| `TRANSFERE` / `TRANSFERT` / `DEPLACE` | 37 / 18 / 24 | **Arête `renumerote_de`** |
| `RATIFIE` / `RATIFICATION` | 19 / 11 | Ordonnance → loi de ratification |

Deux enseignements que la feuille de route n'anticipe pas :

- Les noms réels sont `CREE`/`MODIFIE`/`ABROGE` et non `CREATION`/`MODIFICATION`
  /`ABROGATION` comme écrit au § 2.1. **Les deux séries coexistent** dans le
  fonds, avec des volumes très différents. Un parser qui ne connaîtrait que la
  série de la feuille de route perdrait 85 % des arêtes. À traiter comme un
  vocabulaire ouvert avec test de contrat (§ 8 « instabilité des formats »).
- `CODIFICATION`, `CONCORDANCE`, `CONCORDE`, `TRANSFERE`, `TRANSFERT` et `DEPLACE`
  portent la renumérotation **dans la donnée elle-même**. Le § 4 phase 2 prévoit
  de « reconstruire les chaînes de renumérotation via les tables de concordance »,
  c'est-à-dire d'extraire des PDF. C'est en grande partie inutile : l'arête est
  déclarée. Économie estimée : plusieurs jours de phase 2, et surtout passage de
  `methode: inferee` à `methode: declaree` sur cette arête.

`ETAT` (`VIGUEUR`, `VIGUEUR_DIFF`, `ABROGE`, `ABROGE_DIFF`), `DATE_DEBUT`,
`DATE_FIN` et le bloc `<VERSIONS>` (chaînage explicite des versions successives
d'un même article) sont présents et suffisent au modèle `VersionArticle` du § 3
sans calcul de diff.

### 2.3 bis ⚠️ Trois pièges de la donnée LEGI, mesurés

Ces trois points ont été découverts en construisant les mesures de la note de
cadrage. Chacun fausse silencieusement les résultats si on ne le connaît pas.

**Piège 1 — l'attribut `sens` n'est pas fiable.** La feuille de route et
l'intuition suggèrent que `sens` donne l'orientation de l'arête. C'est vrai pour le
vocabulaire récent, faux pour l'ancien. Mesure sur les articles L en vigueur du
Code de la consommation, liens vers un texte normatif :

| `typelien` | `sens` observé | N |
|---|---|---:|
| `CREE` | `cible` | 826 |
| `MODIFIE` | `cible` | 412 |
| `MODIFICATION` | **`source`** | 38 |
| `CREATION` | **`source`** | 1 |
| `RECTIFICATION` | **`source`** | 1 |

Les deux vocabulaires coexistent avec des orientations opposées pour la même
relation sémantique. Filtrer sur `sens="cible"` fait perdre 40 articles et,
surtout, produit de faux « articles sans rattachement ». **Règle à appliquer :
filtrer sur `typelien` et sur `naturetexte ∈ {LOI, ORDONNANCE, DECRET, ARRETE}`,
ignorer `sens`.** Appliquée correctement, la couverture de `produite_par` passe de
96,0 % à **99,0 %**.

**Piège 2 — le graphe de concordance n'est pas une chaîne.** Les liens
`CONCORDANCE` / `CONCORDE` forment un graphe dont la fermeture transitive diverge.
Sur l'article L311-1, la remonter jusqu'au bout atteint **266 numéros d'articles
distincts** et fait remonter l'origine à la codification de 1993. Sur l'ensemble du
périmètre, la remontée non bornée attribue 688 articles sur 1 280 à la loi 93-949,
ce qui est formellement exact et analytiquement inutile.

La remontée doit être **bornée à un saut**, qui correspond à la recodification de
2016. C'est le seul saut que le produit doit franchir, et le résultat est stable :
74,1 % d'origine législative contre 25,6 % d'origine ordonnantielle.

**Piège 3 — trois articles législatifs ont une origine réglementaire, et ce n'est
pas une anomalie.** Une première lecture concluait à une erreur de la donnée
source. Vérification faite sur les trois cas, c'est faux, et le signalement à la
DILA aurait été une erreur coûteuse auprès du seul fournisseur du projet.

Exemple de L822-2 (objet de l'Institut national de la consommation) :

| Maillon | Article | État | Texte |
|---|---|---|---|
| Actuel | L822-2 | VIGUEUR depuis 2016-07-01 | créé par l'ordonnance 2016-301 |
| Prédécesseur par `CONCORDANCE` | **R531-2** | **ABROGE** en 2016 | modifié par le décret 2010-1221 |

Le prédécesseur est un article **réglementaire**, abrogé par la recodification, dont
la substance est remontée au rang **législatif**. Les deux autres cas (L512-12 et
L512-46, issus des anciens R215-2 et R215-16) sont de même nature.

Piège de lecture à éviter : le numéro `R531-2` existe **aussi** en vigueur
aujourd'hui, et porte une disposition entièrement différente sur la vente de
marchandises non conformes. Une jointure par numéro d'article, au lieu de
l'identifiant `LEGIARTI` porté par le lien, produit un contresens complet.

Conséquence de fond, qui dépasse la qualité de la donnée : **la recodification de
2016 n'est pas à rang constant.** L'expression « codification à droit constant »
ne garantit pas la stabilité du rang normatif. Pour ces articles, la motivation
est à chercher dans un décret, qui n'a ni exposé des motifs, ni étude d'impact, ni
débat — le cas le plus défavorable du corpus.

### 2.4 ✅ DOLE — bien plus riche que décrit

3 411 dossiers dans le dump global, couvrant 1997 à 2025. Structure vérifiée :

- `<EXPOSE_MOTIF>` contient le texte de l'exposé des motifs **en XML inline**, pas
  un lien vers un PDF. Extraction directe, offsets fiables, aucun OCR.
- `<ARBORESCENCE>` contient des `<LIEN id libelle lien>` typés par leur libellé :
  étude d'impact, avis du Conseil d'État, dossier AN, dossier Sénat, rapports de
  commission, textes adoptés à chaque étape, et **comptes rendus de séance avec
  ancres de position** (`…/cri/2012-2013/20130281.asp#P4881`).
- `<ECHEANCIER>` relie les articles d'une loi aux décrets d'application attendus
  (`<CID_LOI_CIBLE>`, `<BASE_LEGALE>`, `<DECRET>`, `<OBJET>`) — utile pour
  l'extension au pouvoir réglementaire du § 7.

Couverture mesurée sur les 3 411 dossiers, par type :

| Type | N | Exposé motifs | Étude d'impact | Avis CE | Comptes rendus | Liens AN ou Sénat |
|---|---:|---:|---:|---:|---:|---:|
| `LOI_PUBLIEE` | 1 182 | 49 % | 27 % | 14 % | 92 % | 100 % |
| `ORDONNANCE_PUBLIEE` | 1 116 | **0 %** | 0 % | 0 % | 0 % | 5 % |
| `PROJET_LOI` | 662 | 96 % | 14 % | 7 % | 3 % | 99 % |
| `PROPOSITION_LOI` | 446 | 19 % | 0 % | 0 % | 42 % | 100 % |

Lecture : sur une loi publiée, le rattachement aux travaux préparatoires est
**déclaré à 100 %** et les comptes rendus à 92 %. C'est l'arête `issu_de` du § 3,
et elle est gratuite. Le critère de sortie de phase 2 « couverture `issu_de` >
90 % » est atteignable sans effort d'inférence, à condition que le périmètre soit
majoritairement composé de lois.

L'exposé des motifs n'est présent que sur 49 % des lois publiées parce qu'il est
porté par le dossier du **projet** de loi (96 %) et non systématiquement recopié
sur le dossier de la loi promulguée. Il faut donc chaîner
`LOI_PUBLIEE → PROJET_LOI` avant de conclure à une absence de motivation. Une note
« raison non documentée » émise sans avoir tenté ce chaînage serait un faux
positif — exactement le type d'erreur que le § 4.3 interdit.

### 2.5 ⚠️ Ordonnances : la feuille de route se trompe en sa défaveur

Le § 0 pose que les ordonnances de l'article 38 n'ont « aucun débat » et le § 7
que les décrets n'ont « aucun exposé des motifs ». Pour les ordonnances, c'est
inexact :

**1 011 des 1 116 ordonnances (90,6 %)** référencent, via `<ID_TEXTE_2>`, un
**Rapport au Président de la République** publié au *Journal officiel* en même
temps que l'ordonnance. Ce rapport est le document de motivation de l'ordonnance :
il expose l'habilitation, l'économie du texte et les choix opérés.

C'est une source de premier ordre, récupérable dans le fonds JORF, et elle change
l'arbitrage de périmètre : une verticale dominée par une recodification par
ordonnance n'est pas condamnée à un taux de « raison non documentée » de 100 %.

Réserve : le rapport au PR est un document du Gouvernement, à ranger dans la
catégorie « ce que le gouvernement a déclaré vouloir » du § 4.3, et non dans une
catégorie « travaux préparatoires » qui suggérerait un débat contradictoire.
La distinction visuelle exigée par le § 4.3 doit donc comporter une nuance de plus
que les quatre prévues.

### 2.6 ✅ API Légifrance via PISTE

- Endpoint OAuth2 : `https://oauth.piste.gouv.fr/api/oauth/token`, `grant_type=client_credentials`.
  Vivant : répond `invalid_client` à des identifiants factices, comportement conforme.
- API : `https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/…`, vivante.
- Inscription gratuite obligatoire sur `piste.gouv.fr/registration`. Les quotas ne
  sont consultables que depuis le compte ; ils ne sont pas documentés publiquement
  et la DILA se réserve le droit de les modifier à tout moment (CGU).
- L'environnement bêta a fermé le 06/06/2023 ; la version stable date du 04/04/2023.

**Action bloquante pour la phase 1 :** créer un compte PISTE. Sans compte, les
quotas restent une inconnue, et la feuille de route les cite comme la raison de ne
pas utiliser l'API en ingestion de masse — recommandation à conserver telle quelle.

### 2.7 ❌ Le site Légifrance n'est pas récupérable

`www.legifrance.gouv.fr` et `circulaires.legifrance.gouv.fr` répondent **HTTP 403
derrière Cloudflare** avec défi JavaScript. Le scraping du site est donc exclu,
pour la consultation d'articles comme pour les tables de concordance PDF.

Toute donnée doit venir des dumps DILA ou de l'API PISTE. C'est une contrainte
d'architecture, pas un détail : elle interdit le repli « on ira chercher la page
Légifrance » qui vient naturellement à l'esprit en cas de trou.

Les PDF d'études d'impact, eux, sont servis depuis un chemin média non protégé et
se téléchargent normalement (vérifié : étude d'impact du projet de loi
consommation, 996 Ko, HTTP 200).

---

## 3. Travaux parlementaires

### 3.1 ⚠️ Assemblée nationale — la limite de couverture

Dumps confirmés à `https://data.assemblee-nationale.fr/static/openData/repository/{legislature}/…` :

| Jeu | Chemin | Taille |
|---|---|---:|
| Amendements | `17/loi/amendements_div_legis/Amendements.json.zip` | 297 Mo |
| Dossiers législatifs | `17/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip` | 10 Mo |
| Comptes rendus (Syceron) | `17/vp/syceronbrut/syseron.xml.zip` | 56 Mo |

JSON et XML disponibles pour chaque jeu. Répertoire non indexable (403 sur les
chemins de dossier) : les URL doivent être connues, il n'y a pas de découverte
automatique. Prévoir un test de contrat qui échoue bruyamment si un chemin change.

**❌ Limite majeure :** seules les **législatures 16 et 17** sont servies. Les
législatures 13, 14 et 15 renvoient 404 sur tous les chemins testés, y compris les
variantes de nommage. Le jeu « dossiers » de la 17e contient bien quelques
dossiers antérieurs (27 de la 14e, 64 de la 15e) mais ce sont des résidus de
dossiers encore ouverts, pas une couverture rétrospective.

Conséquence directe : **tout amendement antérieur à juin 2022 est hors open data
AN.** Les pages HTML historiques restent servies
(`assemblee-nationale.fr/14/amendements/1156/AN/1.asp` répond 200), mais les
exploiter serait du scraping, avec la fragilité que cela implique et une
extraction d'exposé sommaire à écrire à la main.

Point positif : le jeu « dossiers législatifs » porte un champ `senatChemin`
donnant l'URL du dossier Sénat correspondant (présent sur 30 % des dossiers). Cela
résout partiellement la résolution d'entités inter-chambres du § 4 phase 2, qui
était identifiée comme un point dur.

### 3.2 ⚠️ Sénat — Améli est exploitable, le tableau synoptique n'existe pas

Base Améli confirmée. Format : CSV, **encodage latin-1**, séparateur tabulation,
avec une première ligne parasite `sep=` à ignorer. HTML échappé dans les champs
longs. URL par texte de commission :
`https://www.senat.fr/amendements/{session}/{numero}/jeu_complet_{session}_{numero}.csv`

Colonnes réelles, vérifiées sur le jeu du projet de loi consommation
(session 2012-2013, texte 810, 705 amendements) :

```
Nature · Numéro · Subdivision · Alinéa · Auteur · Au nom de · Date de dépôt
Dispositif · Objet · Sort · Date de saisie du sort · Url amendement · Fiche Sénateur
```

Sur ces 705 amendements : 160 adoptés, 245 rejetés, 117 non soutenus, 94 retirés,
19 tombés, 2 irrecevables au titre de l'article 40. **13 des 160 amendements
adoptés (8 %) ont un champ `Objet` de moins de 80 caractères** — c'est la mesure
directe du cas « dispositif introduit par amendement sans justification » que le
§ 4.3 désigne comme le résultat le plus intéressant du produit.

Base Dosleg confirmée : `https://data.senat.fr/data/dosleg/dosleg.zip` (16 Mo),
plus des extraits CSV (`dossiers-legislatifs.csv`, `promulguees.csv`,
`rapports.csv`, `ppl.csv`, `orgdos2sen.csv`). Format PostgreSQL. Licence ouverte
reprenant les termes de data.gouv.fr.

**❌ Le tableau synoptique n'existe pas.** Le § 2.2 le présente comme « un
raccourci majeur » reliant explicitement chaque modification du texte à
l'amendement qui l'a produite, et le § 3 en fait le premier échelon de la cascade
`resulte_de`, seul échelon classé `declaree`. Vérifications menées :

- La « petite loi Améli » (`senat.fr/petite-loi-ameli/2012-2013/810.html`,
  686 Ko) est un export Word converti en HTML. Elle contient **zéro occurrence**
  de marqueur d'amendement et aucun lien sortant vers un amendement.
- Aucun jeu de données `data.senat.fr` ne porte ce nom ni cette fonction.
- Ce qui existe réellement : le **tableau comparatif** annexé aux rapports de
  commission (par ex. `senat.fr/rap/l12-809-2/l12-809-2.html`), qui met en regard
  le texte en vigueur, le texte transmis et le texte de la commission. Il ne cite
  pas les numéros d'amendement.

**La conséquence est structurante et doit remonter au § 3.** Le champ
`Subdivision` d'Améli désigne l'article **du projet de loi** (« Article 1er »,
« art. add. après Article 4 »), jamais l'article du code. Le chaînage réel
comporte donc un maillon que la feuille de route ne mentionne pas :

```
Amendement --(déclaré, Améli)--> Article du projet de loi
Article du projet de loi --(À PRODUIRE)--> Article du code
```

Ce second maillon suppose de parser le langage modificatif (« l'article L. 121-4
du code de la consommation est ainsi modifié… ») dans le texte de l'article du
projet de loi. C'est exactement la fonction de DuraLex — qui est abandonné (§ 6).
**Le premier échelon de la cascade du § 3 est donc à supprimer, et le deuxième
devient l'échelon le plus fiable disponible, sur du code à écrire nous-mêmes.**

### 3.3 Études d'impact et avis du Conseil d'État

Confirmés comme PDF liés depuis `<ARBORESCENCE>` de DOLE, téléchargeables sans
authentification. Couverture réelle : étude d'impact sur 27 % des lois publiées,
avis du Conseil d'État sur 14 %. Ces taux plafonnent mécaniquement la couverture
de l'arête `motive_par` vers ces deux types de nœuds — un objectif supérieur
serait une erreur de conception, pas un objectif ambitieux.

L'extraction PDF avec conservation des offsets (§ 4.3) reste donc nécessaire, mais
elle porte sur un volume plus faible que ne le suggère la feuille de route.

---

## 4. Droit de l'Union

✅ EUR-Lex accessible sans authentification :
`https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32011L0083` répond
200. Les considérants sont numérotés et extractibles (67 relevés sur la directive
2011/83/UE). Réutilisation régie par la décision 2011/833/UE, attribution
obligatoire.

❌ **En revanche, la détection de la transposition depuis DOLE ne fonctionne pas.**
Le § 2.3 propose de détecter la transposition via « la mention explicite dans
l'exposé des motifs, le tableau de concordance annexé, la mention dans le titre ».
Mesure : **1 dossier DOLE sur 3 411 porte un lien vers `eur-lex.europa.eu`**.
Quelques dossiers portent bien un libellé de directive dans leur arborescence,
mais avec une URL Légifrance et sans identifiant CELEX.

L'arête `transpose` devra donc être produite par recherche de motifs dans le texte
(« directive 2011/83/UE », « directive (UE) 2015/2302 ») puis résolution du numéro
vers un CELEX via EUR-Lex. C'est faisable et déterministe — la règle § 5.6 est
respectée — mais c'est du travail non provisionné, et le résultat sera classé
`derivee` et non `declaree`.

---

## 5. Volumétrie et coût d'ingestion

| Source | Volume initial | Incrément | Remarque |
|---|---:|---|---|
| LEGI global | 1,1 Go compressé | 0,6–20 Mo/j | ~10 Go décompressés, > 200 000 fichiers XML |
| JORF global | 1,6 Go compressé | 0,1–13 Mo/j | Deux publications par jour |
| DOLE global | 18 Mo compressé | 3–500 Ko/j | 3 411 fichiers, tient en mémoire |
| AN amendements L17 | 297 Mo | quotidien | JSON, un fichier par amendement |
| AN Syceron L17 | 56 Mo | quotidien | Comptes rendus bruts |
| Sénat Dosleg | 16 Mo | quotidien | Dump PostgreSQL |
| Sénat Améli | ~1,3 Mo par texte | par texte | Pas de dump global par législature |

Le stockage brut immuable exigé au § 4 phase 1 représente donc environ **3 Go pour
l'amorçage**, plus environ **10 Mo par jour** en régime permanent, soit moins de
4 Go par an. Aucune contrainte de coût. Rien ne justifie de déroger à la règle
§ 5.2.

Avertissement pratique constaté en conditions réelles : la décompression complète
de LEGI produit un très grand nombre de petits fichiers et sature un `/tmp` de
taille modeste. Extraire par filtre (`tar --wildcards '*LEGITEXT…*'`) pour tout
travail ciblé sur un code.

---

## 6. ❌ Écosystème à réutiliser : la recommandation du § 2.4 ne tient plus

Le § 2.4 demande d'« évaluer et, si viable, intégrer plutôt que reconstruire ».
Évaluation faite, sur l'activité réelle des dépôts :

| Projet | Dernier commit | Étoiles | Verdict |
|---|---|---:|---|
| `Legilibre/legi.py` | **18/08/2026** | 60 | ✅ **Vivant.** À utiliser |
| `regardscitoyens/the-law-factory-parser` | 29/03/2022 | 46 | ⚠️ 4 ans sans commit |
| `Legilibre/Archeo-Lex` | 10/03/2019 | 104 | ❌ 7 ans sans commit |
| `Legilibre/DuraLex` | 14/02/2019 | 35 | ❌ 7 ans sans commit |
| `Legilibre/SedLex` | 14/02/2019 | 15 | ❌ 7 ans sans commit |
| `openfisca/openfisca-france` | 31/07/2026 | 309 | ✅ Vivant (extension § 7) |

Le fonds LEGI a changé de format en octobre 2023 (note de migration technique
DILA). Un parser sans commit depuis 2019 n'a pas vu cette migration. **Archéo Lex,
DuraLex et SedLex sont à considérer comme des références de conception, pas comme
des dépendances.**

C'est DuraLex qui fait le plus mal : le § 3 en fait le deuxième échelon de la
cascade `resulte_de`, et le § 2.4 le dit « directement applicable ». Comme le
premier échelon (tableau synoptique) n'existe pas et que le deuxième repose sur un
outil mort, **la totalité de l'arête critique du projet est à écrire**. C'est le
principal écart entre la feuille de route et la réalité, et il doit être
provisionné en phase 2.

État de La Fabrique de la loi, vérifié sur `lafabriquedelaloi.fr/api/` : 1 543
dossiers publiés, dernière modification du corpus le **29/07/2024**. La couverture
est hétérogène (dossiers nommés `pjlXX-…`, `pplXX-…`, `15-…`) et ne couvre ni la
16e ni la 17e législature. Le service est en ligne et reste une référence utile
pour la fonctionnalité de surlignage (§ 4 phase 4), dont le format
`viz/articles_etapes.json` donne le modèle, mais ce n'est pas une source
d'ingestion à jour.

---

## 7. Ce qu'il faut décider avant la phase 1

1. **Créer un compte PISTE** — sans quoi les quotas restent une inconnue et la
   vérification unitaire est impossible.
2. **Miroiter le dump global du 13/07/2025 et les 408 incréments LEGI dès
   maintenant** (§ 2.2). C'est urgent et irréversible si manqué.
3. **Réécrire la cascade `resulte_de` du § 3** en tenant compte de la disparition
   des deux premiers échelons (§ 3.2 et § 6). Traité dans la note de cadrage.
4. **Trancher le périmètre en connaissance de la limite AN aux législatures
   16-17** (§ 3.1), qui pèse directement sur le choix de la verticale. Traité dans
   la note de cadrage.
