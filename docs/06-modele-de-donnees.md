# Modèle de données — révision du § 3 au grain du segment

**Objet :** remplacer le modèle du § 3 de la feuille de route, dont l'unité est
l'article, par un modèle dont l'unité de provenance est le segment.
**Date : 22 août 2026.** **Décision de modélisation approuvée.**
**Schéma :** `schema/001-graphe-provenance.sql` — 17 tables, 3 types, 11
contraintes. Syntaxe validée par analyseur ; **aucun serveur PostgreSQL n'était
disponible dans cet environnement**, les contraintes sémantiques (`num_nonnulls`,
`gin_trgm_ops`, types énumérés) restent donc à vérifier au premier déploiement.

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

## 6. Ce qui reste ouvert

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
