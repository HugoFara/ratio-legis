# Contribuer à Ratio Legis

Le projet chaîne un article de code **en vigueur aujourd'hui** aux matériaux qui
expliquent pourquoi il existe sous cette forme. Il ne cherche pas de texte, il ne
l'interprète pas, il ne conseille pas. Une contribution qui produirait une phrase
juridique nouvelle est hors sujet, quelle que soit sa qualité.

La spécification est [`ratio-legis-feuille-de-route.md`](ratio-legis-feuille-de-route.md).
Lisez-en au moins le § 5 : il tient en six règles, et elles décident du sort de la
plupart des propositions.

## Les six règles, et ce qu'elles impliquent

1. **Provenance ou silence.** Aucune sortie sans source résoluble. Une
   fonctionnalité qui affiche quelque chose que l'on ne peut pas rouvrir à sa
   source ne sera pas fusionnée, même exacte.
2. **Le brut est sacré.** Les sources sont stockées telles quelles, horodatées,
   hachées. Ne corrigez jamais une source en amont : corrigez la lecture qu'on en
   fait, et écrivez pourquoi.
3. **Précision > rappel.** Un lien faux détruit la confiance dans l'ensemble ; un
   lien manquant est un trou honnête. Une arête qui gagne du rappel en perdant de
   la précision est un recul, même si le compteur monte.
4. **La confiance est une donnée.** Chaque arête porte son score et sa méthode, et
   les expose. Un score n'est pas choisi : il est mesuré (voir ci-dessous).
5. **Pas d'embeddings seuls.** Les vecteurs proposent des candidats ; la validation
   repose sur une correspondance textuelle ou structurelle vérifiable.
6. **Les LLM ne décident jamais d'une arête.** Ils résument, reformulent, classent.
   La topologie du graphe est produite par du code déterministe et des règles.

## Ajouter une arête au graphe

C'est la contribution la plus utile et la plus exigeante. Une arête est
**déclarée** — une source dit le lien — ou **dérivée** — une correspondance
vérifiable l'établit. Il n'y a pas de troisième cas.

Une arête dérivée doit porter une **preuve** : la fenêtre de texte qui l'a
produite, ses offsets dans le document, la méthode, et une confiance. Le schéma
l'impose (`CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)`) ; ce n'est pas
une convention qu'on peut contourner.

**La confiance se mesure, elle ne s'estime pas.** Le protocole employé pour
`resulte_de` est le modèle à suivre :

1. tirage reproductible d'un échantillon — le rang est une fonction du couple, pas
   un aléa (`hashlib.sha256(f"{a}|{b}".encode())`), pour que le tirage se rejoue ;
2. examen **à la main**, arête par arête, verdict écrit dans un fichier de mesure
   versionné ;
3. tranches disjointes (`--sauf <fiche>`) pour élargir sans réexaminer ;
4. **borne inférieure de Wilson à 95 %** comme confiance publiée, jamais la
   proportion brute (`--bilan`).

Voir [`tools/mesures/precision_resulte_de.py`](tools/mesures/precision_resulte_de.py)
et [`docs/21-precision-resulte-de.md`](docs/21-precision-resulte-de.md).

Si la mesure passe sous le seuil de la feuille de route, l'arête ne part pas — ou
elle part avec une **dérogation écrite**, datée, qui dit ce qui manque et pourquoi
on l'accepte. Le projet préfère une dérogation lisible à un seuil silencieusement
abaissé.

Une table nouvelle est un fichier `schema/NNN-description.sql`, en `STRICT`, avec
ses `CHECK`. Les contraintes sont la documentation qui ne ment pas.

## Le code

- **Python ≥ 3.14**, bibliothèque standard. La seule dépendance du pipeline est
  `pymupdf`, parce que les études d'impact n'existent qu'en PDF. Toute dépendance
  nouvelle doit être argumentée dans le commit : ce qu'elle apporte, et pourquoi
  la bibliothèque standard n'y suffit pas.
- `sqlite3`, pas d'ORM. Les requêtes sont lisibles et le plan d'exécution
  observable.
- **Français** pour les noms, les commentaires et la documentation.
- Les commentaires disent **pourquoi**, pas quoi — le code dit déjà quoi. Le
  commentaire qui a le plus de valeur ici est celui qui explique une décision
  contre-intuitive, ou ce qu'on a essayé et qui n'a pas marché.
- Les scripts se lancent par chemin et sont **idempotents** : les relancer ne
  refait que ce qui manque.
- **Un ordre de tri total** sur toute requête dont la sortie est comparée ou
  versionnée. Un `ORDER BY` partiel rend la sortie dépendante du plan
  d'exécution ; le piège a déjà coûté 38 articles de faux écarts.

## Ce qui doit tenir avant de proposer

```bash
./pipeline.sh                                            # rejoue de bout en bout
python3 restitution/note.py travail/ratio-legis.sqlite --contrat
python3 ingestion/verdict.py travail/ratio-legis.sqlite
python3 tools/mesures/hygiene.py travail/ratio-legis.sqlite \
        data/perimetre-v2.csv data/mesures/hygiene.tsv
```

Le contrat du § 4.3 doit rester à **zéro phrase écartée faute de citation**, et
`PRAGMA foreign_key_check` doit rester vide. Si votre changement fait bouger un
chiffre publié dans le README ou dans `docs/`, mettez-le à jour dans le même
commit : un chiffre périmé est un bug.

## Les sources, et ce qu'on n'a pas le droit de republier

Les données amont sont sous Licence Ouverte / Etalab 2.0 et **leur attribution est
obligatoire**, dans l'interface, dans l'API et dans tout export — voir
[`ATTRIBUTION.md`](ATTRIBUTION.md).

Deux interdits, qui ont déjà été enfreints par inadvertance :

- **`travail/` n'est jamais versionné.** C'est un cache reconstructible ; il a
  porté 775 Mo dans l'historique, dont le texte intégral de 419 rapports.
- **Aucun corps de rapport de commission dans le dépôt**, et aucun extrait
  au-delà de `PLAFOND_EXTRAIT` (400 caractères). Les deux chambres autorisent la
  reproduction de leurs travaux, mais à des conditions — gratuité, attribution,
  intégrité côté Sénat, interdiction de l'usage commercial côté Assemblée — qui
  ne se transmettent pas sous Licence Ouverte. Le plafond est une constante nommée
  dans [`restitution/citation.py`](restitution/citation.py) — utilisez-la plutôt
  que d'écrire le nombre.

## Les commits

Format *conventional commits*, en français, avec le périmètre existant
(`feat(dila)`, `fix(restitution)`, `docs(…)`). Le corps du message dit **pourquoi**,
et ce que la modification révèle : les meilleurs commits de ce dépôt sont ceux qui
expliquent le défaut trouvé en chemin.

## Par où commencer

Par ordre croissant de difficulté :

| Tâche | Nature |
|---|---|
| Amendements de l'Assemblée, législatures XV à XVII | mécanique, 103 articles éligibles |
| Les 172 couples à état unique de `sections_vers_motive` ([`docs/17`](docs/17-sections-appariees.md)) | charger d'autres états du texte |
| Les huit textes récents sans dossier DOLE, entrés par les incréments quotidiens | le critère `issu_de` du § 4.2 est repassé sous son seuil |
| Tableaux de concordance des textes de transposition | seul chemin connu vers un lien européen au grain de l'article |
| XIIIe législature, reconstructible page par page depuis Wayback | arbitrage coût / trou déclaré à rendre |

**La contribution la plus bloquante n'est pas du code** : la validation à la main
des 100 articles du jeu d'annotation. Tant qu'elle n'est pas faite, aucune mesure
de précision du projet n'est autre chose qu'une auto-évaluation. La marche à
suivre est dans [`docs/36`](docs/36-jeu-d-annotation-prepare.md) § 5 :

```
python3 tools/prototype/jeu_annotation.py data/golden-set/jeu-annotation-100.csv \
        travail/corpus/rapports data/golden-set/jeu-annotation-100-prerempli.csv
python3 tools/annotation/preparer.py data/golden-set/jeu-annotation-100-prerempli.csv \
        travail/ratio-legis.sqlite travail/corpus/rapports travail/annotation
python3 tools/annotation/annoter.py travail/annotation --annotateur <vos initiales>
# ou, commande par commande, sans clavier — consignes dans tools/annotation/CONSIGNES.md :
python3 tools/annotation/console.py travail/annotation etat --a-faire
python3 tools/annotation/verifier.py travail/annotation/annotations-100.csv \
        travail/ratio-legis.sqlite travail/corpus/rapports data/mesures/golden-set-100.tsv
```

## Signaler un lien faux

C'est un rapport de bug de première importance, et il est plus utile qu'un
correctif : donnez le numéro d'article, l'arête, et ce qui vous fait dire qu'elle
est fausse. La règle § 5.3 dit qu'un lien faux coûte plus que dix liens manquants.

## Licence

Le code est sous [AGPL-3.0-or-later](LICENSE). Proposer une contribution, c'est
accepter qu'elle le soit aussi.
