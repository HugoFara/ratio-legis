# Attribution des sources

Ratio Legis est un travail dérivé de données publiques. L'attribution est une
obligation de licence, pas une politesse. Elle doit apparaître dans l'interface,
dans l'API et dans tout export du graphe.

| Source | Producteur | Licence | Mention obligatoire |
|---|---|---|---|
| Fonds LEGI, JORF, DOLE | DILA (Premier ministre) | Licence Ouverte / Etalab 2.0 (`fr-lo`) | « Source : DILA — Légifrance, Licence Ouverte 2.0 » + date de récupération du dump |
| API Légifrance (PISTE) | DILA | Licence Ouverte 2.0 | idem, + mention que les données ont pu être filtrées |
| Amendements, dossiers, comptes rendus | Assemblée nationale | Licence Ouverte / Etalab (`data.assemblee-nationale.fr`) | « Source : Assemblée nationale — open data » |
| Dosleg, Améli, comptes rendus | Sénat | Licence Ouverte Etalab 2.0 (`data.senat.fr`) | « Source : Sénat — data.senat.fr » |
| Actes de l'Union, considérants | Office des publications de l'UE (EUR-Lex) | Réutilisation autorisée, décision 2011/833/UE | « © Union européenne, https://eur-lex.europa.eu, 1998-2026 » |
| **Corps des rapports de commission** | Assemblée nationale, Sénat | **Régime propre à chaque chambre**, voir ci-dessous | « Source : rapport n° X de M./Mme Y, [assemblée] » + lien vers le document |

## Les travaux parlementaires ne relèvent pas du régime général

Le point a été vérifié aux sources en août 2026, et il corrige une erreur de ce
fichier — voir l'historique en fin de page.

**L'article L300-2 du CRPA exclut les documents parlementaires** du droit d'accès
comme de la réutilisation : « Les actes et documents produits ou reçus par les
assemblées parlementaires sont régis par l'ordonnance n° 58-1100 du 17 novembre
1958. » Séparation des pouvoirs : la CADA se déclare incompétente. Invoquer « le
régime général de la loi du 17 juillet 1978 » — ce que faisait ce fichier — est
donc faux, dans les deux sens : ce régime n'autorise rien et n'interdit rien ici.

**Le portail open data ne couvre pas le corps des rapports.**
`data.assemblee-nationale.fr` et `data.senat.fr` publient sous Licence Ouverte
les *informations descriptives* d'un rapport — titre, numéro de dépôt, commission,
rapporteur, dates, URL. Le texte intégral reste en HTML et PDF sur le site de la
chambre, sous les conditions du site. La conséquence est nette :

- les **métadonnées** de rapport sont librement rediffusables, y compris à titre
  commercial, sous Licence Ouverte ;
- le **corps** ne l'est pas, et relève des conditions ci-dessous.

## La distinction par chambre

Les deux chambres affirment la même chose sur le fond — les travaux
parlementaires ne sont couverts par aucun droit d'auteur — et posent des
conditions différentes. Ce n'est pas un détail : c'est ce qui décide de ce que
le projet peut republier.

| | Sénat | Assemblée nationale |
|---|---|---|
| Principe | « Les travaux parlementaires ne sont couverts par aucun droit d'auteur » | « Les documents "publics" ou "officiels" ne sont couverts par aucun droit d'auteur » |
| Diffusion gratuite | exigée | exigée |
| Attribution + lien vers l'original | exigés | exigés |
| Intégrité du document | **exigée** — ni modification ni altération | non exigée |
| Usage commercial ou publicitaire | non mentionné | **interdit** |
| Source | [senat.fr/mentions-legales.html](https://www.senat.fr/mentions-legales.html) | [assemblee-nationale.fr/dyn/info-site](https://www.assemblee-nationale.fr/dyn/info-site) |

**Aucune des deux ne permet de replacer le corps d'un rapport sous Licence
Ouverte.** Celle-ci autorise expressément l'exploitation commerciale ; l'Assemblée
l'interdit, et le Sénat exige la gratuité de la diffusion. Une rediffusion sous
Licence Ouverte transmettrait à l'aval des droits que l'amont n'accorde pas.

L'écart entre les deux chambres est réel et il est porté dans la donnée, non dans
une note de bas de page : `tools/diffusion/dump.py` détermine la chambre par l'URL
du document et le dump expose une table `regime_de_reutilisation` qui dit, pour
chaque régime, ce qu'un réutilisateur peut faire et à quelles conditions.

## Ce que le projet publie, et ce qu'il retient

**Le dépôt** ne versionne aucun corps de rapport. Il conserve l'URL, le hachage,
les offsets, et des extraits plafonnés à **400 caractères** — constante
`PLAFOND_EXTRAIT` dans `restitution/graphe.py`, respectée aussi par
`restitution/note.py`. Un extrait attribué, daté, résolvable vers sa source par
ses offsets est une citation, non une rediffusion.

**Le dump ouvert** (`tools/diffusion/dump.py`) :

- porte le graphe sous **Licence Ouverte / Etalab 2.0**, et le code sous
  **AGPL-3.0-or-later** ;
- **ne rediffuse aucun corps de rapport** : les 221 documents gardent leur URL,
  leur hachage et leurs offsets, leur texte est remplacé par un avis **qui nomme
  le régime de la chambre concernée** ;
- **conserve les fenêtres de preuve, ramenées à soixante caractères** — le
  plancher que le schéma exige. Sans elles, 624 arêtes `motive` deviennent
  inauditables, ce qu'interdit la règle § 5.1, *provenance ou silence*. Soixante
  caractères sont la preuve irréductible ; quatre cents seraient de l'extrait ;
- offre l'arbitrage inverse sous l'option `--strict`, qui retire du dump les
  rapports **et** les 624 arêtes qui en dépendent, puis recalcule le verdict pour
  que la base reste cohérente avec elle-même.

Cette position est plus prudente que ce que le Sénat exige et conforme à ce que
l'Assemblée impose. Elle a l'avantage d'être la même des deux côtés, donc
vérifiable d'une seule règle.

## Réciprocité

Le projet dépend d'un écosystème associatif — Regards Citoyens, Legilibre,
OpenFisca. La contrepartie est prévue par la feuille de route § 4 phase 4 : dump
ouvert du graphe sous Licence Ouverte, code sous AGPL-3.0.

Les projets voisins tiennent la même ligne : **La Fabrique de la Loi** (Regards
Citoyens et médialab de Sciences Po) publie ses données dérivées sous ODbL et
rediffuse les textes de loi, articles et amendements — non le corps des rapports ;
**NosDéputés.fr / NosSénateurs.fr** publient leurs contenus sous CC-BY-SA et leurs
données sous ODbL, avec une formule d'attribution imposée ; **Archéo Lex**
(Legilibre) republie les codes LEGI en dépôts git en avertissant que le résultat
n'a aucun caractère officiel. Licencier sa donnée dérivée, attribuer l'amont
nommément, et ne pas rediffuser ce que l'amont ne permet pas de rediffuser : c'est
la pratique de l'écosystème, et c'est celle qu'on suit.

## Ce que l'attribution ne couvre pas

La Licence Ouverte n'autorise pas à laisser croire que le producteur cautionne la
réutilisation ; les mentions légales des deux chambres le disent également. Toute
note générée doit donc porter la mention prévue au § 4.3 de la feuille de route
(étiquetage IA, règlement (UE) 2024/1689 art. 50) **et** une mention distinguant
clairement le texte officiel de la restitution produite par Ratio Legis.

## Historique des arbitrages

Le projet écrit ses arbitrages plutôt que de les subir. Les trois qui suivent ont
porté sur ce fichier.

### Août 2026 — à la construction du dump

La suspension telle qu'écrite visait « la rediffusion d'extraits ». Appliquée à la
lettre, elle retirait aussi les fenêtres de preuve, sans lesquelles 624 arêtes
`motive` deviennent inauditables — ce qu'interdit la règle § 5.1. Deux règles du
projet se contredisaient ; l'arbitrage retenu est celui décrit plus haut :
fenêtres conservées à 60 caractères, corps retirés, `--strict` pour l'inverse.

### Août 2026 — avant publication du dépôt

Ce fichier affirmait que « le dépôt ne versionne aucun texte de rapport ». C'était
faux : **419 fichiers de rapports, 345,9 Mo de HTML intégral**, plus 112,5 Mo de
corps dans la base de travail. La règle avait été appliquée à l'artefact et
oubliée sur la source. `travail/` a été retiré de l'intégralité de l'historique
git et ajouté au `.gitignore` — c'est un cache reconstructible par `pipeline.sh`.

Un second foyer du même oubli a suivi : `note.py` plafonnait ses citations à 400
caractères, `graphe.py` en citait 700, et les exemples versionnés les portaient.
Le plafond est devenu une constante nommée, `PLAFOND_EXTRAIT`. La règle valait
pour trois modules ; elle n'était écrite dans aucun.

### Août 2026 — vérification du régime, et correction du fondement

Ce fichier tenait le régime des rapports pour « à confirmer auprès des deux
assemblées », et le rattachait à la loi du 17 juillet 1978. Vérification faite aux
sources : **le fondement était faux** — le CRPA exclut les documents parlementaires
— et **la confirmation était déjà publique**, chaque chambre ayant publié ses
conditions dans ses mentions légales.

La conclusion pratique ne change pas — le corps des rapports ne peut pas passer
sous Licence Ouverte, il reste hors du dépôt et hors du dump — mais elle repose
désormais sur le bon texte, et l'écart entre les deux chambres est enfin porté
dans la donnée. Écrire aux assemblées reste utile pour lever le doute sur le
statut des **extraits de 400 caractères**, notamment au regard de la condition
d'intégrité du Sénat. Ce n'est plus un préalable au projet.
