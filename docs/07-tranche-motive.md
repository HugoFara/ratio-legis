# Deuxième tranche — les rapports de commission deviennent des raisons

**Objet :** produire l'arête `motive`, qui relie un article du code au passage
d'un document qui explique pourquoi il existe sous cette forme.
**Date : 22 août 2026.**
**Code :** `ingestion/rapports_vers_motive.py`.
**Entrée :** 316 rapports, `data/corpus/plan-rapports.tsv` pour les URL d'origine.

---

## 1. Ce que la tranche produit

| | |
|---|---:|
| Documents chargés | **316** (303 rapports de commission, 13 rapports au Président de la République) |
| Dossiers · arêtes `issu_de` | 93 · 91 |
| Citations d'article relevées | 27 935 |
| dont désignant un article de ce code | 11 437 |
| **Arêtes `motive`** | **241** |
| Articles du code directement motivés | 185 (22,2 % des 832 éligibles) |
| **Articles en vigueur atteignant une raison** | **598 sur 2 139 (28,0 %)** |
| dont par un ancêtre, via `renumerote_de` | 574 |

Zéro violation de clef étrangère, zéro arête dérivée sans preuve.

Le second chiffre est celui qui compte : **574 des 598 articles n'atteignent leur
raison qu'en remontant leur ascendance.** Un rapport de 2007 nomme L. 121-84-6 ;
l'article en vigueur aujourd'hui s'appelle L. 224-28. Sans l'arête d'ascendance
correctement orientée, la raison existe dans le corpus et reste inatteignable.

Chaîne obtenue de bout en bout :

```
L224-28  (en vigueur)
  ← renumerote_de →  L121-84-6
  ← issu_de → LOI n° 2008-3 du 3 janvier 2008
  ← motive → rapport AN r0412, offsets 
      « Article additionnel après l'article 7 — Gratuité des appels depuis les
        téléphones mobiles des numéros présentés comme gratuits (article
        L. 121-84-6 [nouveau] du code de la consommation). La commission a adopté
        un amendement de M. Jean Dionis du Séjour… »
```

C'est la première fois que le graphe répond à « pourquoi ».

## 2. Seule la parenthèse d'en-tête fait foi

La décision structurante de cette tranche est un rejet. Un rapport nomme un
article de deux façons : dans la **parenthèse d'en-tête** qui déclare les
dispositions visées, ou **au fil du commentaire**. Les deux ne se valent pas.

Contrôle à la main d'arêtes tirées au sort, en trois échantillons :

| Classe | Précision mesurée |
|---|---:|
| **Déclarée dans la parenthèse d'en-tête** | **24 / 24** |
| Citée au fil du corps | 5 / 14 |

Les neuf échecs de la seconde classe ont deux causes, toutes deux instructives.

**Collision de numéros entre codes.** L. 221-3 existe au code de la route,
L. 123-6 au code de l'environnement, L. 721-5 au code de la propriété
intellectuelle. La corroboration par LEGI ne les rattrape pas : elle vérifie que
*ce numéro* provient bien de ce dossier, pas qu'il désigne le bon code. C'est
exactement la confusion de cible qui avait produit 9 faux rattachements sur 10
dans la première version du golden set. D'où la seconde condition retenue : la
parenthèse doit nommer le code de la consommation. Son effet se mesure — le taux
de corroboration des en-têtes passe de 19,7 % à **59,3 %**.

**Sections qui débordent.** Le motif d'en-tête ne reconnaissait que « Article 12 »
nu. « Article 19 septies [nouveau] », « Article 26 bis », « Article additionnel
après l'article 22 » n'ouvraient pas de section et n'en fermaient pas non plus :
une section absorbait alors tout ce qui suivait, jusqu'à 1,2 million de
caractères. Le commentaire rendu portait les offsets d'un article et le texte de
plusieurs. Le motif élargi sert d'abord de **borne de fin** ; le test
d'acceptation d'une section est inchangé, la précision n'est donc pas relâchée.

Appliquer la règle § 5.3 — précision avant rappel — coûte cher : la couverture
tombe de 50,4 % à 22,2 % des articles éligibles. C'est le prix affiché.

## 3. Correction d'un chiffre de phase 0

`05-generalisation.md` annonce **79,1 % d'ancrage par un commentaire de rapport**.
Ce chiffre comptait toute citation, y compris au fil du corps. Mesurée, cette
classe est à 36 % de précision : elle n'est pas exploitable telle quelle.

**Le chiffre honnête d'articles motivés à une précision acceptable est 22,2 %**,
et 28,0 % rapporté aux articles en vigueur. L'écart n'est pas une régression du
code : c'est la différence entre « un rapport mentionne cet article quelque part »
et « ce passage explique cet article ».

## 4. La confiance est une mesure, pas un réglage

`motive.confiance` vaut **0,862** : la borne inférieure de Wilson à 95 % de la
précision mesurée à la main, 24 succès sur 24. Écrire 1,0 surestimerait ce que
vingt-quatre vérifications établissent. La borne se resserrera d'elle-même quand
l'annotation humaine en cours élargira l'échantillon — c'est le lien direct entre
la tâche de phase 0 restée ouverte et une valeur inscrite en base.

Deux offsets distincts sont conservés, et ce n'est pas une redondance :
`motive.offset_debut/offset_fin` délimitent **le commentaire à afficher**, tandis
que la `preuve` porte la fenêtre étroite où l'article est nommé. La première sert
la restitution, la seconde le contrôle.

## 5. La topologie reste à LEGI

Une arête `motive` n'est écrite que pour un couple (article, dossier) que **LEGI
rattache déjà**. La citation d'un rapporteur apporte la raison, jamais le lien de
provenance — règle § 5.6. Ce n'est pas circulaire : la topologie n'est pas ce que
cette tranche cherche à établir.

## 6. Ce que la tranche ne fait pas

**Le cas de référence n'a pas de raison.** L224-65, l'article qui a servi de
témoin depuis la phase 0, remonte bien à L121-105, mais aucun rapport de la loi
de 2014 ne déclare L. 121-105 dans une parenthèse d'en-tête : il n'est cité qu'au
fil du commentaire de l'article 11. Sous la règle de précision retenue, il n'a
donc pas de motivation. C'est une limite réelle et elle est du bon côté : le
produit se tait plutôt que d'afficher un passage à 36 % de fiabilité.

**Le grain reste l'article, pas l'alinéa.** Un commentaire porte sur l'article du
texte en discussion, qui peut créer plusieurs articles du code. La restitution
devra dire « pourquoi ce dispositif », pas « pourquoi cet alinéa ».

**La convention du Sénat n'est pas exploitée.** Les rapports du Sénat font suivre
l'en-tête d'un titre plutôt que d'une parenthèse. Ces sections sont extraites mais
ne produisent aucune arête, faute de déclaration nommant le code. C'est la
première piste de rappel à instruire, et elle est bornée : elle ne touche que les
rapports du Sénat.
