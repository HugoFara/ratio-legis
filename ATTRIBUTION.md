# Attribution des sources

Ratio Legis est un travail dérivé de données publiques. L'attribution est une
obligation de licence, pas une politesse. Elle doit apparaître dans l'interface,
dans l'API et dans tout export du graphe.

| Source | Producteur | Licence | Mention obligatoire |
|---|---|---|---|
| Fonds LEGI, JORF, DOLE | DILA (Premier ministre) | Licence Ouverte / Etalab 2.0 (`fr-lo`) | « Source : DILA — Légifrance, Licence Ouverte 2.0 » + date de récupération du dump |
| API Légifrance (PISTE) | DILA | Licence Ouverte 2.0 | idem, + mention que les données ont pu être filtrées |
| Amendements, dossiers, comptes rendus | Assemblée nationale | Licence Ouverte / Etalab | « Source : Assemblée nationale — open data » |
| Dosleg, Améli, comptes rendus | Sénat | Licence ouverte reprenant les termes data.gouv.fr | « Source : Sénat — data.senat.fr » |
| Actes de l'Union, considérants | Office des publications de l'UE (EUR-Lex) | Réutilisation autorisée, décision 2011/833/UE | « © Union européenne, https://eur-lex.europa.eu, 1998-2026 » |
| Rapports de commission | Assemblée nationale, Sénat | **À vérifier**, voir ci-dessous | « Source : rapport n° X de M./Mme Y, [assemblée] » |

## Réciprocité

Le projet dépend d'un écosystème associatif (Regards Citoyens, Legilibre,
OpenFisca). La contrepartie est prévue par la feuille de route § 4 phase 4 : dump
open data du graphe, sous la même Licence Ouverte que les données amont, et code
sous AGPL-3.0.

## Rapports parlementaires : régime à confirmer

Les rapports de commission sont la meilleure source de motivation au niveau de
l'article (`docs/04-annotation-externe.md`). Mais aucune page consultée n'affirme
qu'ils relèvent de la Licence Ouverte, contrairement aux jeux de données de
`data.senat.fr` et `data.assemblee-nationale.fr`. Ce sont des informations
publiques réutilisables au titre du régime général de la loi du 17 juillet 1978,
sans licence explicite.

En conséquence, et jusqu'à confirmation par les services des deux assemblées :

- le dépôt ne versionne **aucun texte de rapport** — seulement des offsets et un
  extrait de 400 caractères à fin de contrôle ;
- la rediffusion du **texte** des rapports dans le dump ouvert est **suspendue**.

### Précision d'août 2026, à la construction du dump

La suspension telle qu'écrite visait « la rediffusion d'extraits ». Appliquée à la
lettre, elle retirait aussi les **fenêtres de preuve**, sans lesquelles 624 arêtes
`motive` deviennent inauditables — ce qu'interdit la règle § 5.1, *provenance ou
silence*. Deux règles du projet se contredisaient ; l'arbitrage est écrit plutôt
que subi.

Le dump produit par `tools/diffusion/dump.py` :

- **ne rediffuse aucun texte de rapport** : les 221 documents gardent leur URL,
  leur hachage et leurs offsets, leur corps est remplacé par un avis ;
- **conserve les fenêtres de preuve, ramenées à soixante caractères** — le
  plancher que le schéma exige. Soixante caractères sont la preuve irréductible ;
  quatre cents sont de l'extrait. 624 fenêtres ont été tronquées ;
- offre l'arbitrage inverse sous l'option `--strict`, qui retire du dump les
  rapports **et** les 624 arêtes qui en dépendent, puis recalcule le verdict pour
  que la base reste cohérente avec elle-même.

Cette précision tombe si les assemblées confirment le régime de réutilisation :
le dump reprendra alors les textes, et l'option n'aura plus d'objet.

### Correction d'août 2026, avant publication du dépôt

La première des deux puces ci-dessus était fausse. Le dépôt versionnait **419
fichiers de rapports — 345,9 Mo de HTML intégral** — et la base de travail en
portait 112,5 Mo de plus dans la table `document`. La règle avait été appliquée
à l'artefact, `dump.py` retirant consciencieusement les corps, et oubliée sur la
source qui l'alimente.

Rien ne pouvait le signaler : aucune vérification ne confrontait la phrase au
contenu du dépôt. L'écart est apparu au moment où la publication a été
envisagée, c'est-à-dire au dernier moment où il restait réparable. Un `git push`
publie l'historique, et supprimer des fichiers dans un commit ultérieur ne les
retire pas des douze commits qui les portaient.

`travail/` a donc été retiré de l'intégralité de l'historique et ajouté au
`.gitignore`. Le répertoire est un cache de construction : `pipeline.sh` le
reconstruit en entier depuis `data/corpus/plan-rapports.tsv`, le miroir DILA et
le fonds LEGI. Aucun original n'y résidait. La puce ci-dessus est désormais
vraie, et le restera tant que `travail/` reste ignoré.

## Ce que l'attribution ne couvre pas

La Licence Ouverte n'autorise pas à laisser croire que le producteur cautionne la
réutilisation. Toute note générée doit donc porter la mention prévue au § 4.3 de la
feuille de route (étiquetage IA, règlement (UE) 2024/1689 art. 50) **et** une
mention distinguant clairement le texte officiel de la restitution produite par
Ratio Legis.
