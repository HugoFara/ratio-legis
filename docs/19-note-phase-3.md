# Phase 3 — la note « pourquoi cet article », sous contrat

**Objet :** produire une note en langue naturelle dont chaque phrase affirmative
porte sa citation, et dont aucune ne survit sans elle.
**Date : 23 août 2026.**
**Code :** `restitution/note.py`. **Exemples :** `restitution/exemples/notes/`.

---

## 1. Ce que le graphe ne faisait pas

`graphe.py` affiche ce qu'il sait, arête par arête : c'est un instrument, pas une
réponse. La phase 3 demande autre chose — une note — et l'assortit d'un contrat
que le § 4.3 énonce sans détour :

> Toute phrase affirmative produite doit porter au moins une citation au niveau
> du **span**, résolvable vers le passage exact. Une phrase sans citation
> résoluble n'est pas affichée. **Le post-traitement supprime la phrase, il ne
> l'excuse pas.**

## 2. Le contrat est un filtre exécuté

Chaque phrase est construite avec sa citation. Celles qui n'en ont pas sont
retirées avant tout rendu, et **le compte des phrases écartées est affiché en pied
de note**. S'il valait toujours zéro, le filtre ne filtrerait rien : le rendre
visible est la seule façon de savoir qu'il travaille.

Les phrases se répartissent en deux registres, et les mélanger est exactement ce
que le contrat interdit :

- les **constats** affirment quelque chose du droit, et portent tous une source ;
- l'**état du dossier** ne parle que de nos sources — « aucun passage ne motive cet
  article », « 4 alinéas sur 4 ne sont rattachés à aucun amendement » — et
  n'affirme rien du droit. *« Nous n'avons rien trouvé »* n'est pas *« il n'y a
  rien »*.

Le verdict de la treizième tranche ouvre la note, et c'est là qu'il appartient :
il dit l'état du dossier avant que la note ne dise le droit.

### Le filtre n'écarte rien, et c'est un résultat

Passé sur les 2 104 articles en vigueur, il produit **11 638 constats et écarte
zéro phrase**. Aucune note n'est vide. Un compteur qui reste à zéro est
suspect — il faut donc dire pourquoi celui-ci l'est, et le prouver.

Il l'est parce que **le contrat est déjà tenu en amont**. Le schéma interdit une
arête sans source résoluble : `document.url` est `NOT NULL`, et chaque table
d'arête porte un `CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)`. Une
phrase construite depuis le graphe ne *peut* pas manquer de citation.

`note.py --contrat` l'éprouve plutôt que de l'affirmer : le filtre est d'abord
confronté à une phrase délibérément sans source — qu'il écarte — puis passé sur le
fonds. Sans la première vérification, la seconde ne dirait rien.

## 3. Deux natures de citation, parce qu'il y en a deux

Une citation **`web`** pointe une URL publique : rapport de commission, exposé des
motifs, avis du Conseil d'État, acte de l'Union. Elle se résout d'un clic.

Une citation **`corpus`** pointe un identifiant du fonds versionné — `LEGIARTI…`,
un numéro d'amendement et son texte discuté. Elle se résout dans le miroir DILA et
son manifeste haché, pas d'un clic sur le web.

Cette distinction n'est pas un aménagement du contrat, c'en est l'application
honnête. Le site de consultation de Légifrance est derrière un défi JavaScript
(`docs/01` § 2.6) : l'URL d'un article y est la citation d'usage, mais elle **n'a
pas pu être vérifiée depuis le pipeline** — deux requêtes, l'une sur un
identifiant réel, l'autre sur un identifiant inventé, répondent toutes deux 403.
Fabriquer un lien qu'on n'a pas pu éprouver serait précisément ce que le projet
s'interdit. L'identifiant, lui, est vérifiable : il est dans le miroir.

## 4. Les quatre voix, séparées

Le § 4.3 impose de distinguer à l'écran ce que le **Gouvernement** a déclaré
vouloir, ce que le **Parlement** a fait, ce que le **Conseil d'État** a objecté,
et ce qui vient de **Bruxelles**. La note les regroupe et les colore ; le fonds
consolidé forme une cinquième voix, qui n'est celle de personne.

Deux liens très différents mènent au même acte européen : le texte français
**déclare** le transposer, ou l'article le **nomme** dans son texte. Une première
version les rendait de la même façon et faisait dire d'un article qu'il nommait
une directive qu'il ne nomme pas — L. 112-1-1 ne cite pas la directive 2019/2161,
c'est l'ordonnance qui la transpose. Les deux formulations sont désormais
distinctes.

## 5. Aucun modèle de langue

La note est composée par **assemblage de gabarits déterministes** à partir du
graphe ; les passages entre guillemets sont verbatim, avec leurs offsets.

L'article 50 du règlement (UE) 2024/1689, applicable depuis ce mois-ci, impose de
marquer le contenu synthétique produit par un système d'IA. Il ne trouve pas à
s'appliquer ici, et la note l'écrit plutôt que d'afficher une étiquette qui
laisserait croire le contraire. Dire « généré par IA » d'un texte qui ne l'est pas
serait aussi trompeur que l'inverse.

C'est aussi ce qu'impose le § 5.6 : les modèles de langue « résument, reformulent
et classent », ils ne décident jamais d'une arête. Ici, ils ne rédigent pas non
plus — parce que le contrat est si strict qu'il rend la rédaction libre inutile :
une phrase qui doit porter sa source n'a plus grand-chose à inventer.

## 6. Ce que cela donne

Trois notes, trois états du dossier :

**L. 224-43** — verdict `passage_motivant`. Trois rapports de commission le
commentent sous l'article 72 bis, trois amendements l'ont écrit, avec leur auteur,
leur sort et leur justification textuelle. Dix-huit phrases, toutes sourcées.

**L. 112-1-1** — verdict `motivation_du_texte`. Aucun passage ne l'explique, mais
l'ordonnance qui l'a produit déclare transposer la directive 2019/2161, qui porte
soixante considérants. Cinq phrases.

**L. 224-109** — verdict `raison_non_documentee`. Trois phrases, toutes de fonds :
il est en vigueur depuis 2022, il vient de la loi anti-gaspillage, cinq articles y
renvoient. Et rien d'autre. **C'est une note complète** : elle dit tout ce qu'on
sait, y compris qu'on ne sait pas pourquoi il dit ce qu'il dit.

## 7. Ce que la tranche ne fait pas

**Elle n'a pas passé l'évaluation en aveugle.** Le critère de sortie de la phase 3
est une évaluation humaine sur le golden set — « zéro affirmation non étayée
tolérée », « taux de *raison non documentée* correctement identifié > 90 % ». Elle
suppose le jeu d'annotation validé, ce qui reste ouvert depuis la phase 0. Tant
qu'elle n'a pas eu lieu, la phase 3 n'est pas close.

**La note coûte cher à produire, et ce n'est pas la note qui coûte.** La
composition prend moins d'une milliseconde ; l'interrogation du graphe prend de
0,6 à 4,2 secondes selon l'article, dominée par les remontées récursives de
chaînes. C'est le premier obstacle de la phase 4, et il est identifié.

**Les notes sont courtes, et c'est l'état du fonds.** La médiane est de quatre
phrases, le minimum de deux, le maximum de cinquante. Une note de quatre phrases
n'est pas une note tronquée : c'est tout ce que les sources françaises disent de
cet article.

**Elle ne hiérarchise pas les raisons.** Quand trois rapports commentent le même
article, les trois sont rendus dans l'ordre du graphe. Choisir lequel explique le
mieux demanderait un jugement que rien dans les données ne fonde.
