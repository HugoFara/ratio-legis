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
- la rediffusion d'extraits dans le dump open data du § 4 phase 4 est **suspendue**.

## Ce que l'attribution ne couvre pas

La Licence Ouverte n'autorise pas à laisser croire que le producteur cautionne la
réutilisation. Toute note générée doit donc porter la mention prévue au § 4.3 de la
feuille de route (étiquetage IA, règlement (UE) 2024/1689 art. 50) **et** une
mention distinguant clairement le texte officiel de la restitution produite par
Ratio Legis.
