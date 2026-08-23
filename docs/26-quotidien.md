# Vingtième tranche — la réincrémentation quotidienne

**Objet :** le point du § 4.1 resté en suspens depuis la phase 1 — orchestration
et réincrémentation quotidienne.
**Date : 23 août 2026.**
**Code :** `quotidien.sh`, `tools/dila/increments.py`,
`tools/mesures/quoi_de_neuf.py`, `deploiement/`.

---

## 1. Le fonds avait un an de retard, et rien ne le disait

`pipeline.sh` extrayait le code de l'archive **globale** de la DILA. Celle du
miroir date du 13 juillet 2025. La DILA publie pourtant un incrément par jour
ouvré, et `miroir_dila.sh` les récupérait fidèlement depuis le début : **406
incréments dormaient dans le miroir sans que rien ne les lise.**

**Deux cents d'entre eux touchent le code de la consommation.**

C'est le genre de défaut qu'aucun test ne trouve : le pipeline s'exécutait, les
compteurs étaient cohérents, l'intégrité était bonne. Il répondait simplement à
une question plus ancienne que celle qu'on croyait poser. Il aura fallu se
demander *comment* servir la donnée quotidiennement pour découvrir qu'on ne la
servait pas fraîche.

| | |
|---|---:|
| Incréments en attente | 406 |
| Dont touchant ce code | **200** |
| Fichiers du fonds écrits | 5 555 |
| Fichiers XML avant / après | 7 793 → **8 052** |

## 2. Ce qu'est un incrément, et comment il s'applique

La même arborescence que l'archive globale, précédée d'un répertoire horodaté,
plus un `liste_suppression_legi.dat` énumérant les chemins à retirer. Appliquer,
c'est recouvrir puis supprimer, dans cet ordre.

```
global      legi/global/…/LEGI/TEXT/00/00/06/06/95/LEGITEXT…/…   → strip 9
incrément   20260819-222711/legi/global/…                        → strip 10
```

Chaque incrément appliqué est inscrit avec son empreinte dans
`data/corpus/increments-appliques.tsv`. Sans ce journal, on ne peut dire ni de
quand date le fonds, ni rejouer la même séquence — et le § 5.2 demande un
pipeline rejouable, pas rejouable une fois.

## 3. L'incrément porte sur la source, pas sur le graphe

La reconstruction quotidienne est **complète, et c'est délibéré**. Presque toutes
les arêtes dépendent de LEGI : segments, `repris_de`, `renumerote_de`, et par
ricochet `motive`, `resulte_de`, `porte_sur`, le verdict. Reconstruire coûte
quelques minutes ; patcher le graphe coûterait une classe entière de bogues
d'incohérence, pour un gain que personne n'attend sur un rythme quotidien.

Dire « réincrémentation » de la source et « reconstruction » du graphe n'est pas
un détail de vocabulaire : c'est ce qui garantit qu'une base servie un mardi est
exactement celle qu'on obtiendrait en repartant de zéro.

## 4. Pas de Dagster, et la raison est écrite

Le § 6 recommandait Dagster ou Prefect. Le pipeline est une **séquence linéaire
de huit étapes**, sans branchement ni parallélisme. Ce qu'il lui faut est un
déclencheur, un journal et l'idempotence ; ce qu'un ordonnanceur distribué
apporte — reprises, backfills, interface web, démon — ne répond à aucune question
qu'on se pose ici, au prix d'une centaine de paquets.

Le déclencheur est un **minuteur systemd utilisateur** : aucune installation à la
racine, aucun démon, `Persistent=true` pour rattraper les jours où la machine
était éteinte. Sans quoi un fonds « quotidien » se retrouve avec un trou muet,
c'est-à-dire le défaut qu'on vient de corriger.

L'écart est inscrit au § 6 bis de la feuille de route, comme les quatre autres.

## 5. Une course muette ne vaut rien

`quoi_de_neuf.py` compare l'état du fonds à celui de la course précédente et
énonce la différence : articles entrés en vigueur, articles sortis, verdicts qui
basculent, comptes d'arêtes qui bougent. C'est le seul endroit du projet où l'on
regarde le graphe **dans le temps**.

Un article qui passe de `raison non documentée` à `un passage l'explique` n'est
pas un détail d'exécution : c'est le produit qui progresse, ou une source qui
s'ouvre. L'inverse est un signal d'alerte.

L'état est versionné dans `data/mesures/etat-du-fonds.json` : son historique git
est, littéralement, la chronique du corpus.

## 6. La première course a trouvé un défaut de fond

Le rapport de la première course annonçait **243 articles sortis du corpus** et 21
entrés. Vérification faite dans le fonds : rien n'avait été supprimé — l'applicateur
n'a effacé aucun fichier. Les articles n'étaient pas partis, ils avaient changé
d'état.

LEGI publie les abrogations **à l'avance**, sous des états différés que le fonds
de juillet 2025 ne portait pas encore :

| état | ce qu'il dit | en vigueur aujourd'hui ? |
|---|---|---|
| `ABROGE_DIFF` | sera abrogée à `date_fin` | **oui**, jusqu'à cette date |
| `VIGUEUR_DIFF` | entrera en vigueur à `date_debut` | non, pas encore |
| `MODIFIE_MORT_NE`, `ANNULE` | n'a jamais pris effet | non |

Le test employé partout — `etat = 'VIGUEUR'` — écartait donc **187 articles
abrogés au 20 novembre 2026, c'est-à-dire parfaitement applicables aujourd'hui**.
Le produit dont l'objet est « un article de code en vigueur aujourd'hui » en
perdait un sur onze, silencieusement.

**L'état dit ce qui arrivera, les dates disent quand.** C'est donc aux dates qu'il
faut poser la question, et à l'état seulement d'écarter ce qui n'a jamais eu
d'existence. `schema/009-en-vigueur.sql` en fait une vue unique, `version_en_vigueur`,
qui remplace dix-sept tests éparpillés — et garantit au passage une seule version
par article, ce que le fonds ne garantissait pas.

La vue est évaluée à la lecture (`date('now')`), non à la construction. C'est
voulu : un dump relu après le 20 novembre 2026 cessera de lui-même de compter ces
187 articles, et il aura raison.

**Ce défaut ne pouvait pas être trouvé autrement.** Il ne se voit ni dans le code,
qui est cohérent, ni dans les compteurs d'une exécution isolée, qui le sont aussi.
Il n'apparaît qu'en comparant deux états du même fonds — c'est-à-dire en faisant
précisément ce pour quoi la réincrémentation quotidienne a été écrite.

## 7. Le journal de course

Chaque étape écrit une ligne dans `data/mesures/journal-quotidien.tsv` — course,
étape, état, durée, résumé. Une étape en échec arrête la course et laisse sa
trace ; une course sans nouveauté s'arrête après les incréments et le dit, plutôt
que de reconstruire pour rien.

```
course              etape          etat      secondes  detail
20260823T181224Z    miroir         OK        14        1398
20260823T181224Z    increments     OK        1         fonds à jour au 20260822-211810
20260823T181224Z    reconstruction OK        …         …
```
