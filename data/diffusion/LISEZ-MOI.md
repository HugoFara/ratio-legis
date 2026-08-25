# Ratio Legis — dump ouvert du graphe de provenance

Graphe de provenance normative du **code de la consommation** en vigueur : pour un article, les matériaux qui expliquent pourquoi il existe sous cette forme.

**Ce dump ne fait pas foi.** Le droit en vigueur est celui publié par Légifrance. Le graphe documente la provenance des textes ; il ne produit ni interprétation juridique, ni conseil.

## Licence

Données sous **Licence Ouverte / Etalab 2.0**, code sous **AGPL-3.0-or-later**. Les mentions ci-dessous sont obligatoires en cas de réutilisation.

- Source : DILA — Légifrance (fonds LEGI, JORF, DOLE), Licence Ouverte / Etalab 2.0
- Source : Assemblée nationale — open data, Licence Ouverte / Etalab
- Source : Sénat — data.senat.fr, licence ouverte reprenant les termes de data.gouv.fr
- © Union européenne, https://eur-lex.europa.eu, 1998-2026 — réutilisation autorisée, décision 2011/833/UE
- Rapports de commission : hors du régime du CRPA (art. L300-2, assemblées régies par l'ordonnance n° 58-1100). Métadonnées sous Licence Ouverte ; corps soumis aux conditions propres à chaque chambre — texte non rediffusé, voir la table regime_de_reutilisation

## Ce que ce dump ne contient pas

Le **texte** des rapports de commission n'est pas rediffusé : les conditions publiées par chaque chambre sont incompatibles avec la Licence Ouverte de ce dump, qui autorise l'exploitation commerciale — voir la table `regime_de_reutilisation`, qui porte l'écart entre les deux. Leur URL, leur hachage et les offsets des passages restent présents, ce qui suffit à refaire le lien depuis la source. Les fenêtres de preuve qui en viennent sont ramenées aux soixante caractères que le schéma exige au minimum.

- `documents_dont_le_texte_est_retire_senat` : 122
- `documents_dont_le_texte_est_retire_assemblee` : 130
- `documents_dont_le_texte_est_retire` : 252
- `fenetres_de_preuve_ramenees_a_60_caracteres` : 634

## Tables

| Table | Lignes | Contenu |
|---|---:|---|
| `article` | 3464 | un article de code, identifié par son numéro |
| `version_article` | 6362 | une rédaction datée d'un article, telle que LEGI la publie |
| `segment` | 28294 | un alinéa d'une version, avec ses offsets dans le texte |
| `texte_normatif` | 469 | une loi, une ordonnance, un décret ou un arrêté |
| `dossier` | 199 | un dossier législatif (DOLE) |
| `document` | 372 | un document de motivation : exposé des motifs, étude d'impact, avis du Conseil d'État, rapport de commission, rapport au Président |
| `amendement` | 33217 | un amendement déposé, adopté ou non, avec son auteur et son sort |
| `acteur` | 1478 | un parlementaire ou un groupe, tel que les chambres le nomment |
| `acte_ue` | 284 | un acte de l'Union identifié par son CELEX |
| `considerant` | 7674 | un considérant d'un acte de l'Union, dans l'ordre de publication |
| `texte_discute` | 424 | un texte déposé ou transmis, à un stade de la navette |
| `preuve` | 54945 | la fenêtre textuelle qui fonde une arête dérivée |
| `produite_par` | 8145 | version d'article → texte qui l'a produite (LEGI, déclarée) |
| `issu_de` | 200 | texte → dossier législatif (DOLE, déclarée) |
| `renumerote_de` | 1882 | article → article dont il reprend la disposition |
| `repris_de` | 6137 | segment → segment antérieur dont il reprend le texte |
| `resulte_de` | 279 | segment → amendement qui l'a écrit — l'arête critique du projet |
| `motive` | 634 | document → article ou segment que l'un de ses passages explique |
| `porte_sur` | 33772 | article d'un texte discuté → article du code qu'il modifie |
| `vise` | 276 | amendement → article du code que son dispositif désigne |
| `depose_sur` | 637 | amendement → article du code réécrit par l'article du texte sur lequel il fut déposé, quand cet article du texte n'en réécrit qu'un |
| `texte_des_amendements` | 106 | la correspondance entre l'identifiant de texte du corpus d'amendements et celui du texte en discussion |
| `sort_amendement` | 33217 | le sort d'un amendement, ramené à huit familles comparables, avec le libellé publié et la colonne d'où il est lu |
| `renvoie_a` | 12534 | segment → article cité, interne ou externe au code |
| `cite_acte_ue` | 1572 | segment → acte de l'Union qu'il nomme |
| `transpose` | 8 | texte → acte de l'Union dont il déclare la transposition |
| `verdict` | 2104 | pour chaque article en vigueur, ce que le graphe sait en dire |
| `diffusion` | 18 | licence, attributions et provenance de ce dump |
| `regime_de_reutilisation` | 2 | ce qu'une chambre autorise sur le corps de ses rapports, et à quelles conditions |

## Comment lire une arête

Chaque arête dérivée porte une `methode` (`declaree`, `derivee`, `inferee`), une `confiance` — borne inférieure de Wilson à 95 % de la précision mesurée à la main — et un `preuve_id` qui pointe la fenêtre textuelle qui la fonde. Une arête dérivée sans preuve est refusée à l'écriture, pas signalée à la lecture.

Les précisions mesurées et leurs échantillons sont publiés avec le code, dans `data/mesures/`.

