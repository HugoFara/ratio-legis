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
| Documents chargés | **234** (221 rapports de commission, 13 rapports au Président de la République) |
| Dossiers · arêtes `issu_de` | 93 · 91 |
| Citations d'article relevées | 37 413 |
| dont désignant un article de ce code | 15 277 |
| **Arêtes `motive`** | **519** |
| Articles du code directement motivés | 225 (27,0 % des 832 éligibles) |
| **Articles en vigueur atteignant une raison** | **651 sur 2 139 (30,4 %)** |
| dont par un ancêtre, via `renumerote_de` | 625 |

Base complète : 136 Mo, le texte intégral des documents compris — sans lui les
offsets ne désignent rien.

Zéro violation de clef étrangère, zéro arête dérivée sans preuve.

Le second chiffre est celui qui compte : **625 des 651 articles n'atteignent leur
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
| **Déclarée dans la parenthèse d'en-tête** | **20 / 20** |
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
tombe de 50,4 % à 27,0 % des articles éligibles. C'est le prix affiché.

## 2 bis. Quatre défauts de découpage, tous silencieux

Le rendement de l'extraction a doublé sans qu'une ligne de la logique de
rattachement change. Tout venait du découpage en sections, et aucun de ces
défauts ne levait d'erreur.

**Le motif d'en-tête exigeait le début de ligne strict.** Les rapports du Sénat
préfixent la ligne d'une espace : 221 fichiers ne rendaient que 455 sections,
contre 7 343 pour 82 fichiers de l'Assemblée. Un rapport de 406 689 caractères en
rendait zéro. Le déséquilibre était trop grand pour une différence de convention
rédactionnelle — c'est ce qui a mis sur la piste.

**Les pages d'index du Sénat produisaient des sections.** Un rapport paginé est
chargé deux fois : sa page d'index et sa version `_mono`. L'index porte le
sommaire, dont chaque ligne a exactement la forme d'un en-tête — numéro,
parenthèse, titre. Ces sections nommaient les bons articles et n'expliquaient
rien. La règle est celle que le script de téléchargement énonçait déjà : quand la
version `_mono` existe, elle seule porte le texte.

**L'en-tête et sa parenthèse sur une même ligne n'étaient pas reconnus.**
« Article 22 ter (article 22-2 de la loi n° 89-462) » ne fermait pas la section
précédente, qui atteignait 553 330 caractères. Le suffixe admis se limite à une
parenthèse ou à un tiret de titre : « Article 22 est ainsi modifié » reste écarté,
faute de quoi toute phrase ouvrirait une section.

**Une ligne de sommaire restait indistinguable d'un commentaire.** La
distribution des tailles la trahit : 112 sections sous 400 caractères, trois
entre 400 et 800 — toutes des lignes de sommaire — et le premier commentaire
véritable à 926 caractères. Le seuil de 800 est lu dans cette bimodalité, il
n'est pas choisi. Son effet ne se voit pas dans le compte d'arêtes, qui ne perd
que six unités, mais dans la médiane de taille des passages retenus : 3 934 →
5 598 caractères. Pour 106 articles, le passage restitué était la ligne de
sommaire, qui précède le vrai commentaire dans le même document.

## 3. Correction d'un chiffre de phase 0

`05-generalisation.md` annonce **79,1 % d'ancrage par un commentaire de rapport**.
Ce chiffre comptait toute citation, y compris au fil du corps. Mesurée, cette
classe est à 36 % de précision : elle n'est pas exploitable telle quelle.

**Le chiffre honnête d'articles motivés à une précision acceptable est 27,0 %**,
et 30,4 % rapporté aux articles en vigueur. L'écart n'est pas une régression du
code : c'est la différence entre « un rapport mentionne cet article quelque part »
et « ce passage explique cet article ».

## 4. La confiance est une mesure, pas un réglage

`motive.confiance` vaut **0,839** : la borne inférieure de Wilson à 95 % de la
précision mesurée à la main sur la version courante de l'extraction, 20 succès
sur 20. Écrire 1,0 surestimerait ce que vingt vérifications établissent. La borne se resserrera d'elle-même quand
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

**Les sections à titre seul ne produisent rien.** Quand l'en-tête est suivi d'un
titre sans parenthèse, aucune déclaration ne nomme le code : la section est
extraite mais ne motive aucun article. C'est la piste de rappel restante, et elle
suppose de résoudre l'article du texte en discussion vers les articles du code
autrement que par la citation — donc par le texte déposé, déjà chargé.

**Vingt-sept sections dépassent 40 000 caractères**, jusqu'à 91 338. La médiane
est à 5 598. Ces cas restent des commentaires authentiques d'articles qui
modifient une quinzaine de dispositions, mais le passage restitué y est trop long
pour être lu tel quel. Le découpage interne du commentaire est un travail de la
couche de restitution, pas de l'ingestion.
