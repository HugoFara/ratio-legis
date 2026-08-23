# Dix-septième tranche — le dump ouvert

**Objet :** le premier livrable du § 4.4 — republier le graphe, sous la licence
des données dont il vit.
**Date : 23 août 2026.**
**Code :** `tools/diffusion/dump.py`. **Sortie :** `data/diffusion/`.

---

## 1. Une obligation, pas une commodité

Le projet vit d'un écosystème de données publiques et d'outils associatifs —
DILA, les deux chambres, EUR-Lex, Regards Citoyens, Legilibre. Le § 4.4 en tire
la contrepartie : republier le graphe sous la même Licence Ouverte que les
données amont. Ce n'est pas une exportation de confort.

La base étant un fichier, elle **est** le dump. Ce qui manquait n'était pas un
format, c'était tout le reste : la licence, les attributions obligatoires, le
dictionnaire des tables, le manifeste haché, et — surtout — la décision de ce
qu'on n'a pas le droit de republier.

## 2. Le seul obstacle réel : les rapports de commission

Vérification faite aux sources en août 2026, le fondement invoqué jusque-là était
faux : **l'article L300-2 du CRPA exclut les documents parlementaires** du régime
général — ils relèvent de l'ordonnance n° 58-1100 — et la CADA se déclare
incompétente. Invoquer « la loi du 17 juillet 1978 » n'autorisait rien et
n'interdisait rien.

Ce que les portails publient sous Licence Ouverte, ce sont les *informations
descriptives* d'un rapport : titre, numéro, commission, rapporteur, dates, URL.
Le corps reste sur le site de la chambre, sous les conditions du site — et ces
conditions, publiées par chacune, **sont incompatibles avec la Licence Ouverte du
dump** : l'Assemblée interdit l'usage commercial, le Sénat exige la gratuité de la
diffusion, quand la Licence Ouverte autorise l'exploitation commerciale. L'écart
entre les deux chambres est désormais porté par la table
`regime_de_reutilisation` du dump. Voir `ATTRIBUTION.md`.

Toutes les autres sources — LEGI, JORF, DOLE, les amendements des deux chambres,
les considérants d'EUR-Lex — portent une licence de réutilisation explicite et ne
posent aucune question.

Les rapports pèsent **107 des 240 Mo** de la base, et ce sont eux qui portent la
meilleure motivation au grain de l'article.

## 3. Deux règles du projet se contredisaient

La suspension d'`ATTRIBUTION.md` visait « la rediffusion d'extraits ». Appliquée à
la lettre, elle retirait aussi les **fenêtres de preuve** : 624 arêtes `motive`
seraient devenues inauditables, ce qu'interdit la règle § 5.1 — *provenance ou
silence*. Une arête sans sa preuve n'est pas une arête prudente, c'est une
affirmation nue.

L'arbitrage est écrit dans `ATTRIBUTION.md` plutôt que subi :

- le **texte** des 252 rapports n'est pas rediffusé — URL, hachage et offsets
  restent, ce qui suffit à refaire le lien depuis la source ;
- les fenêtres de preuve sont **ramenées à soixante caractères**, le plancher que
  le schéma exige. Soixante caractères sont la preuve irréductible ; quatre cents
  sont de l'extrait. 624 fenêtres ont été tronquées ;
- l'option `--strict` rend l'arbitrage inverse : elle retire les rapports **et**
  les 624 arêtes qui en dépendent.

## 4. Un dump doit être cohérent avec lui-même

En mode strict, retirer 624 arêtes `motive` sans recalculer le verdict laisserait
la base affirmer qu'un passage motive un article qu'elle ne peut plus montrer. Le
verdict est donc **recalculé sur le dump** : 759 articles sans raison documentée
au lieu de 746.

Ces treize articles ne sont pas une perte d'information, c'est la même
information dite correctement : *dans cette base-là*, leur raison n'est pas
documentée. Un dump doit être cohérent avec lui-même, pas avec la base dont il
vient.

## 5. Ce qui sort

| | |
|---|---:|
| Base SQLite, compactée | **126 Mo** (source 240 Mo) |
| Tables exportées aussi en TSV | 17 |
| Documents dont le texte est retiré | 252 |
| Fenêtres de preuve tronquées | 624 |
| Violations d'intégrité | **0** |

Plus une table `diffusion` — licence, attributions, horodatage et **commit du
code qui l'a produit** : un dump dont on ne peut pas dire quel code l'a écrit
n'est pas auditable. Plus `LISEZ-MOI.md`, dictionnaire des tables et mode
d'emploi des arêtes. Plus `MANIFESTE.tsv`, taille et SHA-256 de chaque fichier.

Le dump n'est pas versionné : il se refait d'une commande, et seuls son manifeste
et sa notice le sont — comme pour les miroirs DILA et EUR-Lex.

## 6. Une citation vide est un mensonge poli

Le premier dump produit affichait, à la place des passages retirés, des
guillemets vides : « … ». La restitution affirmait qu'un rapport explique
l'article, et ne montrait rien.

C'est précisément ce que le contrat du § 4.3 interdit. `graphe.py` et `note.py`
disent désormais ce qui manque et où le retrouver :

> [texte non rediffusé dans cette base — le document reste à son URL]

Le défaut n'existait pas avant le dump, puisque la base locale a toujours son
texte. Il n'aurait été visible qu'après publication.
