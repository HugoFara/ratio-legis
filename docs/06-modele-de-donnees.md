# Modèle de données — révision du § 3 au grain du segment

**Objet :** remplacer le modèle du § 3 de la feuille de route, dont l'unité est
l'article, par un modèle dont l'unité de provenance est le segment.
**Date : 22 août 2026.** **Décision de modélisation approuvée.**
**Schéma :** `schema/001-graphe-provenance.sql` — 17 tables en mode `STRICT`,
appliqué et vérifié sur SQLite ; chaque contrainte a été testée en essayant de la
violer.

**SQLite plutôt que PostgreSQL.** Le § 6 de la feuille de route recommandait
PostgreSQL 16 avec `pg_trgm` et `pgvector`. Le volume ne le justifie pas : le
périmètre complet tient en 26 Mo et se construit en 3,5 secondes. La contrepartie
est réelle et doit être tranchée avant la phase 3 — l'alignement par trigrammes
passe par FTS5, et le rappel vectoriel du § 4.3 devra s'appuyer sur un index
externe. Les tables `STRICT` ne sont pas un détail : sans elles SQLite accepte
n'importe quel type dans n'importe quelle colonne et toutes les contraintes de ce
fichier deviennent décoratives.

---

## 1. Ce que la mesure impose

Le § 3 attache la provenance à l'article. Trois mesures de phase 0 disent que
c'est le mauvais grain.

**Un article a en moyenne 19,5 textes modificateurs.** « Le texte à l'origine de
l'article » n'a donc pas de référent unique.

**Au grain de l'article, la partition gouvernement / navette n'est pas définie.**
Selon la finesse d'échantillonnage, la même mesure a donné 68 %, 82,7 % puis
40,8 % sans qu'aucune donnée ne change (`05-generalisation.md` § 3). Ce n'était
pas une mesure.

**Au grain du segment, elle le devient.** Sur les 1 815 segments des versions en
vigueur rattachées à un texte déposé :

| Classe | Segments | Lecture |
|---|---:|---|
| Repris à plus de 90 % | 305 (16,8 %) | l'alinéa vient du texte déposé |
| **Retouché, de 10 à 90 %** | **379 (20,9 %)** | l'alinéa a été amendé dans sa rédaction |
| Nouveau, moins de 10 % | 1 131 (62,3 %) | l'alinéa ne figurait pas au dépôt |

L'ambiguïté ne disparaît pas — elle passe de 39,8 % à 20,9 % — mais elle **change
de nature**. « Ni gouvernemental ni parlementaire » n'était pas exploitable ;
« alinéa retouché » est une catégorie nommable, qui appelle un traitement propre
et une phrase de restitution propre.

Ramenée à l'article, la part ambiguë tombe de 39,8 % à **12,6 %** dès lors qu'on
la calcule sur des segments plutôt que sur des fenêtres.

## 2. Le segment, défini

**Un segment est un alinéa d'une version d'article.**

Le découpage ne peut pas se fier aux balises `<p>` du fonds LEGI : **26,5 % des
articles n'en portent aucune**, et le fonds compte deux fois plus de `<br/>` que
de `<p>`. L'alinéa est porté par les deux. Découpage retenu : coupure sur `</p>`
et sur `<br/>`, segments de moins de 15 caractères écartés.

Mesuré sur les 6 131 versions d'articles du code :

| | |
|---|---:|
| Versions sans aucun segment exploitable | **0** |
| Segments par version, médiane | 2 |
| Longueur d'un segment, médiane | 165 caractères |
| Segments de moins de 60 caractères | 16,7 % |

Les segments courts sont une limite connue : sous 60 caractères, l'appariement
textuel qui fonde les arêtes dérivées n'a pas de pouvoir discriminant. Ils sont
stockés comme les autres et restitués comme les autres, mais ne peuvent pas
porter d'arête `resulte_de` dérivée. La vue `segment_non_appariable` les isole,
de sorte que la restitution puisse dire « provenance non déterminable par la
méthode » plutôt que de laisser lire une absence de motivation.

**Le segment n'a pas d'identité stable entre versions.** Un alinéa inséré décale
tous les suivants. L'identité est donc `(version_article, ordre)`, et la
continuité entre versions est portée par une arête `repris_de` explicite, établie
par comparaison textuelle et porteuse de sa preuve.

## 3. Nœuds

Par rapport au § 3, trois nœuds sont ajoutés et un est généralisé.

```
Article            (id, code, numero)                        identité inter-versions
VersionArticle     (id_legi, article_id, date_debut, date_fin, etat, hash)
Segment            (id, version_id, ordre, texte, offset_debut, offset_fin, hash)   ← NOUVEAU
TexteNormatif      (id_jorf, nature, date, titre, celex_source?)
Dossier            (id_dole, id_an?, id_senat?, titre, legislature)
Document           (id, dossier_id, type, url, texte, hash, date_recuperation)      ← GÉNÉRALISÉ
Amendement         (id, chambre, numero, auteur_id, sort, objet, dispositif, subdivision)
Intervention       (id, seance_id, orateur_id, texte, horodatage)
Acteur             (id, nom, groupe, mandat)
ActeUE             (celex, type, considerants[])
Preuve             (id, methode, fenetre, offsets_source, offsets_cible)            ← NOUVEAU
```

**`Document` remplace `ExposeDesMotifs`, `EtudeImpact` et `AvisConseilEtat`** du
§ 3, qui étaient trois nœuds pour un même objet. Le champ `type` prend les
valeurs `expose_des_motifs`, `etude_impact`, `avis_conseil_etat`,
`rapport_commission`, `rapport_president_republique`, `compte_rendu`. Deux de ces
types manquaient au § 3 et ce sont les plus utiles :

| Type de document | Nomme l'article dans |
|---|---:|
| Exposé des motifs | 6,4 % des cas |
| Étude d'impact | 24,8 % |
| **Rapport de commission** | **79,1 %** |
| Rapport au Président de la République | 8 % (grain du texte entier) |

**`Preuve` est le nœud qui rend la confiance vérifiable.** Le § 5.4 pose que « la
confiance est une donnée, pas un ressenti ». Un score seul ne le garantit pas :
il faut pouvoir rejouer la décision. Chaque arête dérivée porte donc la fenêtre
de texte qui l'a produite et les offsets des deux côtés.

## 4. Arêtes

Toutes portent `confiance ∈ [0,1]`, `methode ∈ {declaree, derivee, inferee}` et,
pour les deux dernières, une `preuve_id`.

```
VersionArticle --produite_par-->  TexteNormatif    declaree   99,0 % du périmètre
Article        --renumerote_de--> Article          declaree   76,4 %
TexteNormatif  --issu_de-->       Dossier          declaree   100 % des lois
Dossier        --documente_par--> Document         declaree
Document       --motive-->        Segment|Article  derivee    offsets obligatoires
Segment        --resulte_de-->    Amendement       derivee    ← ARÊTE CRITIQUE
Segment        --repris_de-->     Segment          derivee    continuité inter-versions
Amendement     --defendu_dans-->  Intervention     declaree
TexteNormatif  --transpose-->     ActeUE           derivee    non déclaré dans DOLE
```

Trois changements par rapport au § 3, tous imposés par une mesure.

**`resulte_de` part du segment, pas de la version d'article.** Sans cela l'arête
est vide par construction sur un corpus recodifié : sur les 307 articles issus de
la loi de 2014, aucun n'a plus cette loi comme texte producteur de sa version en
vigueur (`03-prototype-resolveur.md` § 4).

**`repris_de` est nouvelle et indispensable.** C'est elle qui permet de dire « cet
alinéa vient de cet amendement de 2013, repris sans modification de fond par la
recodification de 2016 ». Sans elle, le produit ne peut relier un article en
vigueur à l'amendement qui l'a écrit sans mentir sur la chaîne. Elle est
vérifiable : c'est une comparaison de textes, et elle porte sa preuve.

**`motive` porte des offsets obligatoires**, et peut viser un segment ou un
article selon le grain de la source. Le rapport au Président de la République ne
nomme l'article que dans 2 cas sur 25 : il vise le `TexteNormatif`, et la
restitution doit dire que la motivation disponible porte sur l'ordonnance entière.

## 5. Ce que le modèle interdit

**Aucune arête sans source résoluble.** `methode = declaree` exige un identifiant
de lien LEGI ou DOLE ; `derivee` exige une `preuve_id` non nulle. Une arête sans
l'un ni l'autre est rejetée à l'écriture, pas signalée à la lecture.

**La déclaration éditoriale d'un rapporteur ne crée pas d'arête de provenance.**
Sur la loi de 2014, rapporteurs et LEGI ne déclarent que 130 articles en commun,
sur 241 et 280 respectivement (`04-annotation-externe.md` § 3). Les commentaires
alimentent `motive`, jamais `produite_par`. La topologie reste produite par LEGI,
conformément à la règle § 5.6.

**Un appariement non discriminant ne crée pas d'arête.** Une fenêtre retrouvée
dans plus de deux numéros d'articles est du texte type. Le seuil de deux n'est pas
arbitraire : 84 % des fenêtres à deux numéros désignent le même article sous ses
numérotations d'avant et d'après 2016.

## 6. Première tranche chargée

`ingestion/legi_vers_graphe.py` peuple le schéma depuis le fonds LEGI et
construit l'arête `repris_de`. Sur le Code de la consommation, 3,5 secondes :

| | |
|---|---:|
| Versions d'articles | 6 131 |
| Articles distincts | 3 428 |
| Segments | 26 524 (4,3 par version) |
| dont non appariables, moins de 60 caractères | 4 429 |
| Arêtes `produite_par` | 7 809 |
| Arêtes `renumerote_de` | 1 877 |
| **Arêtes `repris_de`** | **5 775** |
| dont reprises intégrales (≥ 0,9) | 2 814 |
| dont retouchées (0,1–0,9) | 2 712 |

Zéro violation de clef étrangère, zéro arête dérivée sans preuve.

Le cas de référence vérifié à la main en phase 0 se retrouve tel quel :

```
L224-65 (en vigueur depuis le 01/07/2016)
  --repris_de (part 0,745, preuve textuelle)--> L121-105
  --produite_par (CREE)--> ordonnance n° 2016-301
```

La part de 0,745 classe l'alinéa en « retouché », ce qui est exact : la version en
vigueur ajoute « qui éteint toute action contre le voiturier » au texte issu de
l'amendement. Un modèle au grain de l'article aurait rendu « repris » ou
« nouveau », les deux étant faux.

Ce cas a servi trois fois. La troisième a révélé que **le graphe n'était pas
orientable** : remonter l'ascendance de L224-65 bouclait indéfiniment entre cet
article et L121-105. LEGI déclare le lien de renumérotation sur les *deux*
versions concernées, et `sens`, qui devrait les départager, est inexploitable.
Ignorer `sens` — décision correcte — laissait donc une relation symétrique là où
le modèle suppose une ascendance : 3 848 des 3 849 arêtes `renumerote_de` avaient
leur réciproque, et 36 % des arêtes `repris_de` désignaient comme source une
version *postérieure* à leur cible.

Le sens est rétabli par la chronologie, qui est un fait observable dans le fonds
et non une déclaration. Les 48 paires à date de début identique sont abandonnées
plutôt que devinées. Après correction : plus aucune arête `repris_de` symétrique,
ascendance de profondeur 3 au maximum, et acyclicité garantie par construction
puisque chaque arête décroît strictement en date. Les compteurs ci-dessus sont
ceux d'après correction ; ils sont environ deux fois plus bas parce que chaque
arête n'était comptée qu'une fois de trop.

Ce cas a aussi servi deux fois auparavant. À la première exécution, l'ingestion ne trouvait que 40
reprises intégrales pour 4 017 retouchées — incompatible avec une codification à
droit constant. La cause était le piège d'offsets déjà rencontré en phase 0 :
indexer le prédécesseur par échantillonnage et l'interroger à toutes les
positions fait ressortir un alinéa identique à 10 % de reprise. Sans cas de
référence, le chiffre serait passé.

## 7. Ce qui reste ouvert

**La granularité de `motive` pour les documents non découpés.** Un commentaire de
rapport porte sur l'article du texte en discussion, qui peut créer plusieurs
articles du code. Le grain est bon pour « pourquoi ce dispositif », insuffisant
pour « pourquoi cet alinéa ». Le schéma l'accepte via la double cible
`Segment|Article` ; la restitution devra distinguer les deux cas explicitement.

**La date de référence de la comparaison.** La mesure du § 1 compare le segment
en vigueur au texte déposé. Or entre les deux s'intercalent la navette *et* tous
les textes postérieurs, y compris la recodification. Les 62,3 % de segments
« nouveaux » mélangent donc travail parlementaire et réécritures ultérieures. La
comparaison juste se fait contre la version de l'article à la date de la loi, ce
qui suppose la résolution version-à-date — travail de phase 1.
