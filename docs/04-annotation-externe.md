# Source d'annotation externe : les rapports de commission

**Objet :** remplacer la recherche manuelle du passage motivant par la validation
d'une proposition issue d'une source externe (`02-golden-set.md` § 6).
**Date : 22 août 2026.**
**Code :** `tools/prototype/commentaires_rapports.py`, `tools/prototype/jeu_annotation.py`.
**Sortie :** `data/golden-set/jeu-annotation-100-prerempli.csv`.

---

## 1. La source

Le **rapport de commission** est le seul document du corpus qui commente le texte
**article par article**. Chaque article y reçoit un en-tête, un titre, et un
commentaire développé qui expose la raison du dispositif et mentionne les
amendements adoptés. C'est très exactement ce que l'annotateur humain devait aller
chercher.

Comparaison des trois sources de motivation, sur la même mesure — l'article
est-il nommé dans le document ?

| Source | Articles nommés |
|---|---:|
| Exposé des motifs | 6,4 % |
| Étude d'impact | 24,8 % |
| **Rapport de commission** | **94,1 %** (loi 2014-344) |

Le rapport n'était pas dans la liste des sources du § 2.2 de la feuille de route,
qui cite les amendements, les comptes rendus et les dossiers. C'est pourtant, de
loin, la meilleure source d'ancrage au niveau de l'article.

## 2. Deux conventions de rédaction, à traiter séparément

**Assemblée nationale.** L'en-tête porte une parenthèse déclarant les dispositions
visées :

> Article 4 *(articles L. 111-1 à L. 111-6, L. 112-11, L. 112-12 [nouveau],
> L. 113-3, L. 113-3-1 et L. 113-3-2 [nouveaux], L. 113-7 [nouveau] du code de la
> consommation)* — Obligation générale d'information du consommateur

Cette parenthèse est une **déclaration éditoriale** du rapporteur, produite
indépendamment de LEGI. Elle donne un rattachement fort et sert de contrôle
croisé.

**Sénat.** L'en-tête est suivi d'un simple titre, sans parenthèse. Les références
au code figurent dans le corps du commentaire. Rattachement plus faible, à
vérifier au cas par cas.

Piège de récupération : les rapports du Sénat sont paginés, et la page d'index ne
contient pas le texte. Il faut la version `…_mono.html`, dont l'URL se déduit
mécaniquement.

## 3. Contrôle croisé : le rapporteur et LEGI ne disent pas la même chose

Sur la loi 2014-344, en comparant les articles du code déclarés par les
rapporteurs à ceux déclarés par les liens LEGI :

| | Articles |
|---|---:|
| Déclarés par les rapporteurs | 241 |
| Déclarés par LEGI | 280 |
| **Accord** | **130** |
| Vus par le rapporteur seul | 111 |
| Vus par LEGI seule | 150 |

L'écart n'est pas une erreur, il est structurel. Le rapporteur commente des
dispositions qui seront ensuite abandonnées ou renumérotées, et cite des articles
à titre de contexte ; LEGI enregistre des modifications de coordination qui n'ont
jamais fait l'objet d'un commentaire.

**Conséquence à respecter en phase 2 : la déclaration du rapporteur ne doit pas
servir à construire le graphe.** Elle est une source de *motivation*, pas de
*provenance*. Confondre les deux introduirait 111 arêtes non déclarées et en
manquerait 150 déclarées. La topologie reste produite par les liens LEGI, comme
l'exige la règle § 5.6.

## 4. Les ordonnances : la motivation existe mais pas au bon grain

Pour les 25 articles d'origine ordonnantielle de l'échantillon, il n'existe aucun
rapport de commission — il n'y a pas eu de commission. La seule motivation est le
**rapport au Président de la République**, récupéré depuis le fonds JORF (13
rapports, 8 000 à 12 000 caractères chacun).

Mesure : **ces rapports ne nomment l'article que dans 2 cas sur 25.** Ils motivent
l'ordonnance dans son ensemble, pas chacune de ses dispositions.

Le jeu d'annotation les propose donc explicitement **au grain du texte entier**,
via la colonne `grain_du_rattachement`. Laisser la case vide aurait laissé croire
qu'aucune motivation n'existe, ce qui est faux ; la proposer au grain de l'article
aurait été un faux ancrage, ce que le § 4.3 interdit.

## 5. Résultat sur le jeu d'annotation

`data/golden-set/jeu-annotation-100-prerempli.csv`, 100 articles, 62 rapports
dépouillés sur 35 dossiers.

| | Articles |
|---|---:|
| Avec un passage proposé | **66** |
| dont rattachement fort (déclaré en en-tête) | 22 |
| dont grain « article » | 43 |
| dont grain « texte entier » (rapport au PR) | 23 |
| Laissés à la recherche humaine | 34 |

Par strate :

| Strate | Couverture |
|---|---:|
| Éligible `resulte_de`, 12e-15e législature | **37 / 46 (80 %)** |
| Origine ordonnance | 25 / 25 (100 %, grain grossier) |
| Origine antérieure à l'open data | 3 / 15 (20 %) |
| Éligible, 16e-17e législature | 1 / 10 (10 %) |
| Reclassement réglementaire | 0 / 3 |
| Sans origine identifiable | 0 / 1 |

Les 80 % sur la strate 12e-15e législature sont le chiffre qui compte : c'est la
population qui porte l'arête critique.

Deux creux restent à traiter, et ils sont de nature différente :

- **16e-17e législature à 10 %.** Anomalie de récupération, pas de fond : les
  rapports récents sont publiés sous des URL différentes. À corriger.

  > **Corrigé le 19 septembre 2026 par [`docs/36`](36-jeu-d-annotation-prepare.md)
  > § 3.** Les pages téléchargées étaient des pages de garde ; le texte intégral
  > est sous `/dyn/opendata/`. La strate passe à 6 / 10, le jeu entier à 74 / 100.
- **Origine antérieure à l'open data à 20 %.** Structurel : les rapports d'avant
  2008 ne sont pas systématiquement en ligne. Ces articles resteront « raison non
  documentée », ce qui est le résultat attendu.

## 6. Ce que le pré-remplissage ne fait pas

**Il ne conclut pas.** La colonne `ANNOT_verdict` reste vide. Une proposition
fausse est plus dangereuse qu'une case vide parce qu'elle biaise l'annotateur ;
c'est pourquoi le format distingue explicitement rattachement fort, rattachement
faible et grain grossier, et pourquoi l'annotateur doit pouvoir répondre « passage
proposé hors sujet ».

**Il ne descend pas au segment.** Un commentaire porte sur l'article *du texte en
discussion*, qui peut créer ou modifier plusieurs articles du code. Le grain est
bon pour dire « pourquoi ce dispositif », pas « pourquoi cet alinéa ».

**Il ne remplace pas la validation humaine.** Le taux de justesse des 66
propositions n'est pas connu : il est précisément ce que l'annotation doit
mesurer.

## 7. Licence — point à trancher avant toute rediffusion

Les jeux de données de `data.senat.fr` sont sous licence ouverte reprenant les
termes de data.gouv.fr, et ceux de `data.assemblee-nationale.fr` sous Licence
Ouverte. **Les rapports parlementaires publiés sur les sites institutionnels ne
relèvent pas de ces licences** : les portails n'ouvrent que les informations
descriptives, le corps restant sous les conditions du site de chaque chambre. Le
régime général de la loi du 17 juillet 1978 ne s'y applique pas non plus —
l'article L300-2 du CRPA exclut les documents parlementaires.

Cela n'empêche pas l'usage interne fait ici — mesure et annotation — mais la
rediffusion des extraits reste bornée par les conditions de chaque chambre,
détaillées dans `ATTRIBUTION.md`. En
attendant, le dépôt ne versionne **aucun texte de rapport** : seulement les
offsets et un extrait de 400 caractères à fin de contrôle.
