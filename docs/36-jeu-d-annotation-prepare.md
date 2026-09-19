# Trentième tranche — le jeu d'annotation, prêt à être annoté

**Objet :** livrer à l'annotateur ce qu'il lui faut pour clore la phase 0, et
mesurer ce qui lui manquait.
**Date : 19 septembre 2026.**
**Code :** `tools/annotation/` (nouveau), `tools/prototype/telecharger_rapports.sh`,
`ingestion/rapports_vers_motive.py`.

---

## 1. Ce qui bloque la phase 0, au caractère près

Un seul livrable : la colonne `ANNOT_verdict` de
`data/golden-set/jeu-annotation-100-prerempli.csv`, vide sur 100 lignes depuis
le 22 août. Tout le reste de la phase — cadrage, vérification des sources,
golden set, jeu stratifié, pré-remplissage — est fait, et le critère de sortie
a été réécrit pour exiger **l'offset du passage** plutôt qu'un oui/non
(`docs/00` § 4, `docs/02` § 6).

Or personne n'avait regardé ce qu'il faudrait, concrètement, pour produire cet
offset. Trois choses manquaient, et deux d'entre elles se mesurent.

## 2. Les offsets proposés ne résolvaient plus — 25 sur 66

Le pré-remplissage porte, pour 66 articles, un document et deux offsets. Vérifié
ligne à ligne contre le corpus d'aujourd'hui, en recalculant `texte_brut()` du
fichier et en comparant l'extrait obtenu à `ANNOT_passage_cite` :

| | articles |
|---|---:|
| extrait retrouvé à l'offset | 41 |
| **extrait décalé** | **25** |
| document absent | 0 |

Les 25 sont les 25 rapports au Président de la République. Le fichier versionné
avait été produit sur des rapports récupérés à la main en phase 0 ; ils ont été
perdus avec `/tmp`, puis **repris du miroir JORF** par `rapports_president.py`
(`docs/12`), qui écrit le titre du texte en première ligne. Le texte a bougé
d'une ligne, les offsets ne le savaient pas.

C'est exactement le défaut que le protocole entend tester — « une citation
résoluble au niveau du passage » — et il était dans le jeu de référence
lui-même. La conséquence est une règle : **le pré-remplissage se régénère avec
le corpus** (`jeu_annotation.py`, une commande), et il est gelé au moment où
l'annotation commence, par copie dans le fichier de l'annotateur (§ 5).

Régénéré sur le corpus du jour, avant toute autre modification : 71 propositions
au lieu de 66, 27 en rattachement fort au lieu de 22. Le module de découpe des
rapports a été réparé plusieurs fois depuis août (`docs/17`, `docs/34`,
`docs/35`), et le jeu ne l'avait jamais suivi.

## 3. La XVIe et la XVIIe législature entraient en base sans corps

`docs/04` § 5 laissait un creux — 1 article sur 10 dans la strate 16e-17e — avec
un diagnostic : « anomalie de récupération, les rapports récents sont publiés
sous des URL différentes. À corriger. » Personne ne l'avait fait, et le corpus
le cachait bien : les dix fichiers existaient, à 75 ko chacun.

Depuis la XVIe législature, l'Assemblée publie ses rapports sous
`/dyn/<lég>/rapports/<commission>/l<lég>b<n°>_rapport-fond`, et cette page est
une **page de garde** — titre, auteur, lien vers le PDF — sans le corps. Le texte
intégral est ailleurs, sous `/dyn/opendata/RAPPANR5L<lég>B<n°>.html`, et l'URL
s'en déduit mécaniquement. C'est la même situation que les rapports du Sénat,
dont la page d'index ne porte pas le texte et dont `_mono.html` s'en déduit
(`telecharger_rapports.sh`, depuis la phase 0). La règle est ajoutée aux deux
endroits qui doivent la connaître : le téléchargement, et la table nom de
fichier → URL de l'ingestion, sans laquelle le document entrerait en base sans
citation résoluble et serait écarté.

| | |
|---|---:|
| rapports du plan sous `/dyn/` | 22 (XVe : 12, XVIe : 6, XVIIe : 4) |
| textes intégraux récupérés | **21** — un 404, `l15b4721` |
| documents `rapport_commission` en base | 252 → **273** |
| arêtes `motive` | 734 → **751** |
| articles L « un passage les motive » | 796 → **801** (61,6 % → 61,9 %) |
| articles en vigueur qu'un passage motive, chaîne comprise | 806 → **812** |
| propositions du jeu, strate 16e-17e | 1 / 10 → **6 / 10** |

Le découpeur lit ce format sans modification : 30 sections sur le rapport
n° 1674, en-têtes « Article 4 AC (nouveau) » compris. Les quatre articles
restants de la strate viennent tous de la loi n° 2025-594 du 30 juin 2025 ; ses
deux rapports sont désormais dans le corpus, et c'est à l'annotateur de dire
s'ils motivent ces articles ou non.

## 4. Le jeu, après

`data/golden-set/jeu-annotation-100-prerempli.csv`, régénéré :

| Strate | N | proposé | dont fort | à chercher |
|---|---:|---:|---:|---:|
| Éligible `resulte_de`, 12e-15e législature | 46 | 41 | 25 | 5 |
| Origine ordonnance | 25 | 25 (grain « texte entier ») | — | 0 |
| Origine antérieure à l'open data | 15 | 2 | 2 | 13 |
| Éligible, 16e-17e législature | 10 | 6 | 1 | 4 |
| Reclassement réglementaire → législatif | 3 | 0 | — | 3 |
| Sans origine identifiable | 1 | 0 | — | 1 |
| **Total** | **100** | **74** | **28** | **26** |

Quinze articles n'ont **aucun document pour leur dossier d'origine** : sept
portés par la loi de codification de 1993, quatre par des lois de 1992 à 2001
sans dossier DOLE, trois par des décrets, un sans origine. Mais « dossier
d'origine » est une convention du jeu — le lien `CREE` le plus ancien du
prédécesseur, un seul saut — et elle cache le reste de l'histoire : L621-3
descend de quatre articles d'avant 2016, dont L113-5 créé par la loi de
modernisation de l'économie de 2008, et le corpus a les rapports de ce dossier.
La fiche donne désormais chaque texte de l'historique, avec son dossier et ce
que le corpus en détient ; les dossiers consultés sont écrits dans le fichier
d'annotation. Sur cette base, aucun article n'est sans document — 92 dossiers
et 295 documents au lieu de 35 et 176.

## 5. Ce que l'annotateur reçoit

`tools/annotation/preparer.py` écrit un répertoire de travail, hors dépôt :

| | |
|---|---|
| `fiches/<numéro>.txt` | l'article en vigueur, ses numéros antérieurs, **l'historique complet** — chaque texte qui a produit une version, son dossier, ce que le corpus en détient —, les documents de tous ces dossiers avec **chaque mention** de l'article et 300 signes de contexte, la proposition de la machine, les verdicts et les deux règles du § 6 |
| `documents/` | le texte brut de 295 documents, celui dont les offsets comptent |
| `documents.tsv` | fichier, type, taille, empreinte SHA-256 |
| `annotations-100.csv` | le fichier à remplir : colonnes `ANNOT_*` vides, proposition gelée dans `proposition_*` |

`tools/annotation/annoter.py` fait remplir ce fichier article par article. **On
ne compte jamais un offset** : l'annotateur colle les premiers et les derniers
mots du passage, l'outil les localise — occurrence unique exigée — et calcule
les bornes. Les offsets sont ceux de `texte_brut()`, donc ceux de
`document.texte` en base : comparables aux arêtes `motive` sans conversion.
Chaque article est sauvé dès qu'il est rendu ; on s'arrête et on reprend. Un
document trouvé hors corpus — sur vie-publique, dans les archives d'une chambre,
sur Wayback — s'importe d'une commande (`e`), avec son URL ; il est converti par
la même fonction que le corpus et devient citable. `verifier.py` le compte à
part : la base ne pouvait pas le citer, et c'est un **trou du corpus**, distinct
d'un silence du fonds. C'est la donnée que la recherche exhaustive produit en
plus du verdict.

La proposition n'est jamais une réponse par défaut. L'annotateur dit ce qu'il
en fait — acceptée, corrigée, hors sujet — et c'est une colonne à part
(`proposition_jugee`), parce que le taux de justesse du pré-remplissage est
l'une des trois mesures que l'annotation doit produire (`docs/04` § 6).

`tools/annotation/verifier.py` est la mesure elle-même, écrite avant que la
première ligne ne soit annotée pour qu'elle ne s'ajuste pas au résultat. Elle
lit le fichier annoté et la base, et rend :

1. **le verdict** — parmi les `non_documente` humains, la part que la base rend
   `raison_non_documentee` (seuil § 4.3 : > 90 %), et le nombre d'articles où la
   base affirme un passage motivant alors que l'humain n'en trouve aucun — c'est
   l'affirmation non étayée, qui doit être à zéro ;
2. **le passage** — pour un article que l'humain dit motivé, la base porte-t-elle
   une arête `motive` dans le même document (retrouvé par empreinte, jamais par
   nom) dont l'intervalle recouvre le passage annoté ;
3. **la proposition** — acceptée, corrigée ou hors sujet, par strate.

Vérifié sur deux annotations d'essai, non conservées : les deux chaînes se
rejoignent, l'empreinte retrouve le document, l'intervalle recouvre.

## 6. Décisions prises, et ce qui reste ouvert

Deux décisions, prises le 19 septembre 2026 avant la première ligne annotée, et
écrites dans chaque fiche :

**Le grain des ordonnances : `dossier_seulement`.** Vingt-cinq articles n'ont
qu'un rapport au Président, qui ne nomme pas l'article. Il vaut
`dossier_seulement`, sauf si le rapport consacre un passage au dispositif de
l'article — l'outil laisse désigner ce passage, et le verdict devient alors
`motive`. C'est la lecture que le verdict de la base fait déjà
(`motivation_du_texte`), et `verifier.py` attend cette concordance.

**La recherche est exhaustive.** `non_documente` ne se rend qu'après avoir suivi
chaque texte de l'historique de l'article — pas seulement le dossier d'origine
du jeu — et cherché hors corpus ce que le corpus n'a pas. Ce qui a été consulté
s'écrit dans `ANNOT_commentaire`. Le coût est réel sur les quinze articles du
§ 4, et c'est là que le résultat est le plus intéressant : un `non_documente`
rendu après une recherche exhaustive est un fait sur le fonds documentaire
français, pas sur le corpus du projet.

Reste ouvert :

**Elle n'annote pas.** Le README l'écrit depuis la phase 3 : le critère
« suppose un jugement extérieur ». Un seul annotateur, auteur du code, ferme la
phase 0 mais pas l'évaluation en aveugle de la phase 3. Un second annotateur
sur 20 à 25 articles, pour un accord inter-annotateurs, reste à trouver.

**Elle ne recouvre pas la partie réglementaire.** Le jeu a été tiré sur le
périmètre à 1 280 articles de la partie L. Les 811 articles R et D, dont 83 %
sont « raison non documentée » (`docs/27`), n'ont aucune vérité terrain. Ce
n'est pas un obstacle à la clôture de la phase 0, qui portait sur ce périmètre ;
c'est une limite à écrire dans le verdict.
