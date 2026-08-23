# L'Esprit des Lois — Feuille de route d'implémentation

**Destinataire :** agent d'implémentation autonome.
**Date :** août 2026.
**Statut :** spécification initiale. Toute URL, tout endpoint et tout schéma de données externe marqué `[VÉRIFIER]` doit être confirmé par l'agent avant d'être codé en dur.

---

## 0. Énoncé du problème

Pour un article de code français **en vigueur aujourd'hui**, il est actuellement très coûteux de répondre à la question : *pourquoi cet article existe-t-il sous cette forme ?*

Les matériaux existent et sont publics (exposés des motifs, études d'impact, avis du Conseil d'État, amendements, comptes rendus de séance). Ce qui manque est le **chaînage** entre le texte consolidé actuel et ces matériaux. La chaîne est rompue en aval de la promulgation par : la codification à droit constant avec renumérotation, les modifications successives par des lois sans rapport thématique, les amendements dont la justification est absente ou lapidaire, la transposition de directives (la raison est dans les considérants européens), les ordonnances de l'article 38 (aucun débat) et le pouvoir réglementaire (aucun exposé des motifs).

**Le produit n'est pas un moteur de recherche juridique. C'est un graphe de provenance normative, avec une couche de restitution en langue naturelle strictement ancrée.**

### Non-objectifs

- Ne pas reconstruire un Légifrance. La consultation du droit positif est un problème résolu.
- Ne pas produire d'interprétation juridique, de conseil, ni d'opinion sur le sens d'une norme.
- Ne pas viser l'exhaustivité du corpus en V1 (voir § 1).
- Ne pas dupliquer *La Fabrique de la loi* (médialab Sciences Po / Regards Citoyens), qui couvre déjà la navette parlementaire et s'arrête à la promulgation. Réutiliser leur parser plutôt que le réécrire.

---

## 1. Décision de périmètre (bloquant, phase 0)

Le projet échoue s'il attaque tout le droit français. L'agent doit produire, avant tout développement, une note de cadrage de 2 pages tranchant :

**Verticale par défaut recommandée :** le **Code de la consommation** dans sa recodification de 2016 (ordonnance n° 2016-301 du 14 mars 2016), ou à défaut les parties du **Code du travail** issues de la loi du 8 août 2016 et postérieures.

Critères ayant conduit à cette recommandation, à réévaluer :

| Critère | Pourquoi |
|---|---|
| Corpus récent | L'open data parlementaire est fiable à partir de 2008 seulement |
| Renumérotation unique et documentée | Table de concordance existante, un seul saut à franchir |
| Forte proportion de transposition UE | Force à traiter tôt le cas « la raison est à Bruxelles », qui est structurant |
| Demande professionnelle réelle | Juristes d'entreprise, DGCCRF, associations de consommateurs |

**Livrable de sortie de phase 0 :** liste figée de N articles cibles (N ≈ 2 000–5 000), plus un **golden set de 25 articles** annotés à la main par un humain, servant de vérité terrain pour toutes les phases suivantes. Le golden set doit inclure délibérément des cas pénibles : article issu d'un amendement sans exposé sommaire, article issu d'une transposition, article modifié par ordonnance, article dont la raison est réellement introuvable.

---

## 2. Sources de données

Toutes sous Licence Ouverte / Etalab 2.0 sauf mention contraire. L'attribution est obligatoire et doit être implémentée dès la V1.

### 2.1 Droit consolidé et Journal officiel

- **Fonds LEGI** (codes et textes consolidés, XML) — dumps DILA, disponibles en téléchargement global + incréments. `[VÉRIFIER]` le point d'accès courant (historiquement FTP `echanges.dila.gouv.fr`, également miroirs sur data.gouv.fr).
- **Fonds JORF** (textes publiés au Journal officiel).
- **Fonds DOLE** (dossiers législatifs : exposés des motifs, étapes, liens vers les travaux préparatoires).
- **API Légifrance via PISTE** (`api.piste.gouv.fr`), OAuth2 client credentials. Utile pour le ciblage unitaire et la vérification ; **ne pas** l'utiliser comme source d'ingestion de masse (quotas). `[VÉRIFIER]` quotas et endpoints actuels.

Point technique central : dans LEGI, chaque **version d'article** porte des liens typés (`CREATION`, `MODIFICATION`, `ABROGATION`, `SPEC_APPLI`, `CITATION`…) pointant vers le texte modificateur. C'est l'arête n° 1 du graphe et elle est déjà présente dans la donnée. Ne pas la recalculer par diff.

### 2.2 Travaux parlementaires

- **Assemblée nationale** : `data.assemblee-nationale.fr`. Jeux à ingérer : amendements (avec exposé sommaire et sort), comptes rendus de séance et de commission, dossiers législatifs, acteurs et organes (AMO), scrutins.
- **Sénat** : `data.senat.fr`. Dumps relationnels (dossiers législatifs, amendements type « Améli », débats). Le **tableau synoptique** du Sénat relie explicitement chaque modification du texte à l'amendement qui l'a produite — c'est un raccourci majeur, l'exploiter en priorité là où il existe.
- **Études d'impact** et **avis du Conseil d'État** : PDF rattachés aux dossiers. Les avis du CE sur les projets de loi sont publiés depuis 2015. Extraction PDF → texte avec conservation des offsets (voir § 4.3).

### 2.3 Droit de l'Union

- **EUR-Lex / Cellar** : identifiants CELEX, SPARQL ou API REST. Nécessaire pour récupérer les **considérants** d'une directive transposée, qui constituent la motivation réelle d'une part importante du corpus.
- Détecter la transposition via : mention explicite dans l'exposé des motifs, tableau de concordance annexé au projet de loi, mention dans le titre de la loi.

### 2.4 Écosystème à réutiliser, pas à réécrire

L'agent doit évaluer et, si viable, intégrer plutôt que reconstruire :

- **Legilibre / Archéo Lex** — historique git des codes, article par article. Résout une grande partie du problème de versionnement.
- **duraLex** — parse le langage modificatif français (« à l'article L. 123-4, les mots “X” sont remplacés par “Y” ») en opérations structurées. Directement applicable pour relier un amendement à l'article qu'il modifie.
- **the-law-factory-parser** (Regards Citoyens) — parsing de la navette et rattachement amendement ↔ article.
- **OpenFisca-France** — ses fichiers de paramètres portent des références législatives explicites vers Légifrance. Croisement à fort potentiel : relier une variable socio-fiscale à l'amendement qui l'a produite (voir § 7).

---

## 3. Modèle de données

Graphe de provenance persisté en relationnel (PostgreSQL), exposé comme graphe en lecture.

### Nœuds

```
Article            (id_legi, code, numero, date_debut, date_fin, texte, hash)
VersionArticle     (id, article_id, ordre, texte, diff_precedent)
TexteNormatif      (id_jorf, nature{loi|ordonnance|decret|arrete}, date, titre, celex_source?)
Dossier            (id_dole, id_an?, id_senat?, titre, legislature)
ExposeDesMotifs    (dossier_id, texte, offsets)
EtudeImpact        (dossier_id, texte, sections[], offsets)
AvisConseilEtat    (dossier_id, texte, offsets)
Amendement         (id, chambre, numero, auteur_id, sort, expose_sommaire, texte_dispositif)
Intervention       (id, seance_id, orateur_id, texte, horodatage, offsets)
Acteur             (id, nom, groupe, mandat)
ActeUE             (celex, type, considerants[])
```

### Arêtes (typées, chacune avec un champ `confiance` ∈ [0,1] et `methode` ∈ {`declaree`, `derivee`, `inferee`})

```
VersionArticle --produite_par--> TexteNormatif        (methode: declaree, source LEGI)
TexteNormatif  --issu_de-->      Dossier              (methode: declaree, source DOLE)
VersionArticle --resulte_de-->   Amendement           (methode: derivee | inferee)  ← ARÊTE CRITIQUE
Amendement     --defendu_dans--> Intervention
Dossier        --motive_par-->   ExposeDesMotifs | EtudeImpact | AvisConseilEtat
TexteNormatif  --transpose-->    ActeUE
Article        --renumerote_de-->Article               (tables de concordance)
```

**L'arête `resulte_de` est le cœur du projet et la seule qui n'existe nulle part.** Stratégie en cascade, du plus fiable au moins fiable :

1. Tableau synoptique du Sénat, quand disponible → `declaree`.
2. Parsing duraLex de l'amendement + application sur le texte de l'étape précédente, comparaison au texte de l'étape suivante → `derivee`, confiance élevée si le diff correspond exactement.
3. Alignement textuel (similarité sur n-grammes, pas d'embeddings seuls) entre le dispositif de l'amendement et le diff constaté → `inferee`, confiance calculée.
4. Aucun rattachement → arête absente. **Ne jamais fabriquer une arête pour combler un trou.**

---

## 4. Phases

### Phase 0 — Cadrage et validation manuelle (2 semaines)

- Note de cadrage, périmètre figé.
- Golden set de 25 articles annotés à la main, chaîne complète reconstituée manuellement.
- **Critère de sortie :** l'humain a pu remonter la chaîne pour au moins 18 des 25. Si moins, le périmètre est mauvais, retourner au choix de la verticale.

### Phase 1 — Ingestion (4 semaines)

- Pipeline d'ingestion LEGI / JORF / DOLE / AN / Sénat / EUR-Lex.
- **Stockage immuable des sources brutes** (XML, JSON, PDF) avec hash et date de récupération. Toute donnée dérivée doit être reconstructible depuis le brut. Non négociable : c'est ce qui rend la provenance auditable.
- Orchestration (Dagster ou Prefect), réincrémentation quotidienne.
- **Critère de sortie :** ré-exécution complète du pipeline depuis zéro, reproductible, sur le périmètre figé.

### Phase 2 — Construction du graphe (6 semaines)

- Résolution d'entités : acteurs, textes, dossiers (identifiants instables entre chambres — prévoir une table de correspondance manuelle pour les cas résiduels).
- Reconstruction des chaînes de renumérotation via les tables de concordance.
- Implémentation de la cascade de l'arête `resulte_de` (§ 3).
- **Critères de sortie, mesurés sur le golden set :**
  - couverture `produite_par` : > 95 %
  - couverture `issu_de` : > 90 %
  - couverture `resulte_de` : > 60 % (seuil réaliste, ne pas le gonfler)
  - **précision de `resulte_de` : > 95 %** — un mauvais rattachement est bien pire qu'une absence de rattachement. Cette métrique prime sur toutes les autres.

### Phase 3 — Couche de restitution (4 semaines)

Génération, pour un article donné, d'une note « pourquoi cet article ». **Contrat de génération strict :**

- Toute phrase affirmative produite doit porter au moins une citation au niveau du **span** (document source + offsets de caractères), résolvable en un clic vers le passage exact.
- Une phrase sans citation résoluble n'est pas affichée. Le post-traitement supprime la phrase, il ne l'excuse pas.
- Le système dispose d'un verdict explicite **`raison non documentée`**, et doit le rendre lorsque c'est le cas. C'est un résultat de premier ordre, pas un échec : le constat qu'un dispositif a été introduit par amendement sans étude d'impact ni justification est en soi l'information la plus intéressante que le produit puisse produire.
- Distinguer visuellement, dans la restitution : ce que le **gouvernement** a déclaré vouloir (exposé des motifs, étude d'impact), ce que le **parlement** a fait (amendements, débats), ce que le **Conseil d'État** a objecté, ce qui vient de **Bruxelles**.
- Étiquetage du contenu généré par IA conformément à l'article 50 du règlement (UE) 2024/1689, applicable depuis août 2026.

**Critère de sortie :** évaluation humaine en aveugle sur le golden set. Zéro affirmation non étayée tolérée. Taux de « raison non documentée » correctement identifié > 90 %.

### Phase 4 — Exposition (3 semaines)

- API REST + dump open data du graphe (réciprocité vis-à-vis de l'écosystème dont on dépend).
- Interface de consultation : entrée par numéro d'article, sortie = fiche de provenance + timeline des versions + note générée sourcée.
- Widget « surlignage » : sur le texte de l'article, colorer les segments selon l'étape qui les a introduits (fonctionnalité déjà éprouvée par La Fabrique de la loi, à reprendre).

---

## 5. Règles d'ingénierie non négociables

1. **Provenance ou silence.** Aucune sortie sans source résoluble.
2. **Le brut est sacré.** Les sources sont stockées telles quelles, horodatées, hachées. Le pipeline est rejouable.
3. **Précision > rappel** sur toutes les arêtes du graphe. Un lien faux détruit la confiance dans l'ensemble ; un lien manquant est un trou honnête.
4. **La confiance est une donnée**, pas un ressenti. Chaque arête porte son score et sa méthode, exposés à l'utilisateur.
5. **Pas d'embeddings seuls** pour établir un fait. Les vecteurs servent à la recherche et au rappel de candidats ; la validation d'une arête doit reposer sur une correspondance textuelle ou structurelle vérifiable.
6. **Les LLM ne décident jamais d'une arête.** Ils résument, reformulent et classent. La topologie du graphe est produite par du code déterministe et des règles.

---

## 6. Stack recommandée

- Python 3.12, PostgreSQL 16 (+ `pg_trgm` pour l'alignement textuel, `pgvector` pour la recherche uniquement).
- Dagster pour l'orchestration ; lxml pour LEGI ; pdfplumber ou équivalent avec conservation des offsets pour les études d'impact.
- FastAPI ; front Svelte ou React.
- Licence : AGPL-3.0, cohérente avec l'écosystème (LexImpact, OpenFisca) et protectrice contre l'aspiration du corpus sans réciprocité.

### 6 bis. Écarts effectivement pris, et pourquoi

Cette section est recommandée, non prescriptive. Les écarts sont écrits ici pour
qu'ils soient des décisions et non des dérives.

| Recommandé | Retenu | Raison |
|---|---|---|
| Python 3.12 | **Python 3.14**, déclaré dans `pyproject.toml` et vérifié par `pipeline.sh` | 3.12 n'est plus en support actif ; le pipeline tourne sur 3.14 sans adaptation |
| PostgreSQL 16 | **SQLite**, en tables `STRICT` | portabilité : la base est un fichier, donc le dump open data du § 4.4 *est* la base. `pg_trgm` n'a pas servi — aucune arête ne repose sur une similarité floue (§ 5.5) |
| Dagster ou Prefect | **`pipeline.sh`** | l'orchestration n'est pas un critère de sortie ; la réincrémentation quotidienne du § 4.1 reste à faire et sera reposée en phase 4 |
| lxml pour LEGI | expressions régulières sur le XML | les fonds DILA sont volumineux et de forme stable ; aucun besoin d'arbre |
| pdfplumber | **pymupdf** | conserve les offsets exigés par le § 4.3, sans OCR sur ce corpus |

---

## 7. Extensions, après V1 seulement

- **Croisement OpenFisca.** Les paramètres d'OpenFisca-France référencent des articles de Légifrance. Relier chaque paramètre à l'amendement et au débat qui l'ont produit crée un objet qui n'existe nulle part : *ce que la règle fait* (OpenFisca) joint à *pourquoi elle a été écrite ainsi* (ce projet).
- **Métriques d'hygiène législative** publiables : part des dispositifs introduits par amendement sans exposé sommaire, délai entre dépôt et adoption, part du texte final issue du Sénat vs de l'Assemblée, taux d'articles sans aucune motivation traçable. Ces chiffres sont le meilleur produit d'appel médiatique du projet.
- **Extension au pouvoir réglementaire.** Les décrets constituent la masse normative réelle et n'ont aucun exposé des motifs. Documenter leur absence de motivation est un résultat en soi.
- **Corpus RAG sous licence** pour outils juridiques tiers — le débouché commercial le plus probable, où la valeur tient à la couverture et à la fraîcheur, pas à l'interface.

---

## 8. Risques

| Risque | Gravité | Mitigation |
|---|---|---|
| Arête `resulte_de` sous les 40 % de couverture | Critique — le produit perd sa raison d'être | Décision go/no-go explicite en fin de phase 2 ; repli possible sur un produit centré dossier plutôt qu'article |
| Hallucination d'intention législative | Critique — produit activement nuisible | Contrat de génération § 4.3, éval humaine bloquante |
| Instabilité des formats DILA / AN / Sénat | Élevée | Tests de contrat sur les schémas, alerte à la dérive, stockage du brut |
| Sur-extension du périmètre | Élevée | Périmètre figé en phase 0, tout élargissement passe par une nouvelle note de cadrage |
| Contresens de positionnement | Moyenne | Vendre de la **traçabilité documentée**, jamais de l'**interprétation** ; l'usage des travaux préparatoires en interprétation est juridiquement contesté et ce n'est pas la bataille du projet |

---

## 9. Première tâche de l'agent

Ne pas écrire de code. Produire d'abord :

1. La note de cadrage de la phase 0, avec la verticale retenue et sa justification.
2. Un rapport de vérification des sources : pour chacune des sources du § 2, confirmer le point d'accès actuel, le format, le volume, la licence, la fréquence de mise à jour. Signaler tout `[VÉRIFIER]` invalidé.
3. Le golden set de 25 articles, avec la chaîne reconstituée manuellement pour chacun et, pour ceux dont la chaîne est incomplète, l'identification précise du maillon manquant.

Le point 3 est le vrai test de faisabilité du projet. S'il échoue, aucune quantité d'ingénierie ne le sauvera.
