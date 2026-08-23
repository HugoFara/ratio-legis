# Vingt-deuxième tranche — classer ce qu'on ne peut pas rattacher

**Objet :** rendre utiles les documents qui motivent le texte entier, sans créer
aucune arête ; et corriger trois défauts de rendu qui disqualifiaient la fiche
auprès du seul public qui compte.
**Date : 23 août 2026.**
**Code :** `restitution/proximite.py`, `restitution/citation.py`,
`restitution/graphe.py`, `restitution/note.py`, `restitution/surlignage.py`,
`ingestion/considerants.py`.

---

## 1. Ce que la vitrine montrait, et ce qu'elle ne répondait pas

L'article L112-1-1 est la règle du prix antérieur sur trente jours. La question
que son lecteur pose est : *pourquoi trente jours ?* Voici ce que la fiche
rendait avant cette tranche.

| Ce qui était affiché | Ce que ça valait |
|---|---|
| Le rapport au Président, sur ses 400 premiers caractères | « Monsieur le Président de la République, La présente ordonnance est prise sur le fondement… » — la formule d'adresse |
| 25 considérants sur 60, dans l'ordre du document | aucun des 25 ne parle d'annonce de réduction de prix |
| 5 alinéas, tous « aucun amendement rattaché » | exact, et sans intérêt ici |

Plusieurs milliers de mots hors sujet, et pas la réponse — alors que **le passage
qui répond était dans le corpus chargé**, à l'offset 3 514 du même document :

> L'article 2 définit les conditions dans lesquelles les professionnels peuvent
> avoir recours à des annonces de réductions de prix et assimile le non-respect
> de ces règles à une pratique commerciale trompeuse.

## 2. La cause : avoir confondu ne rien affirmer et ne rien aider

Le § 5.1 interdit d'affirmer sans source. Le § 5.6 interdit qu'un modèle décide
d'une arête. Ni l'un ni l'autre n'interdit de **classer**, et c'est la confusion
qui a coûté cet écran : puisqu'aucune arête ne désigne le passage motivant, la
restitution avait conclu qu'il ne fallait rien choisir, et affichait le document
**depuis l'offset 0**.

Or afficher un document depuis son début n'est pas s'abstenir de choisir : c'est
choisir l'ordre du document. C'est même le pire des ordres possibles pour la
question posée, puisqu'il est sans rapport avec elle — et il était présenté sans
étiquette, donc le lecteur le prenait pour un choix motivé.

La rigueur avait été appliquée aux arêtes, et pas à la présentation. C'est dans
la présentation que vit l'utilité.

## 3. Ce qui est calculé, et ce qui ne l'est pas

`restitution/proximite.py` classe les passages d'un document par recouvrement
lexical avec le texte de l'article, chaque terme pesé par sa rareté **dans ce
document-là** : `log(N / df)`, sur les N fenêtres du document lui-même.

La pondération locale n'est pas un raffinement. Sans elle, « consommateur » dans
un rapport sur le droit de la consommation ferait remonter n'importe quoi. Un
terme présent dans toutes les fenêtres pèse exactement zéro.

Aucun corpus extérieur, aucun apprentissage, aucun vecteur. Le classement se
rejoue à l'identique, et il **s'explique en montrant les termes qui l'ont
produit** — ce que la restitution affiche à côté de chaque passage. C'est cette
auditabilité qui rend le geste acceptable : le lecteur juge le classement, il ne
le subit pas.

**Le plancher.** Sous deux termes communs, rien n'est classé, et la restitution
le dit. Départager des passages qui n'ont rien en commun avec l'article
donnerait au premier une autorité qu'aucune mesure ne soutient — précision >
rappel (§ 5.3).

**La fenêtre de classement est la fenêtre d'affichage**, `PLAFOND_EXTRAIT`
caractères. Classer sur plus large que ce qu'on montre ferait juger un extrait
sur les mérites d'un texte qu'on ne voit pas. Les fenêtres se recouvrent d'une
moitié, pour qu'une phrase coupée en deux ne perde pas ses deux moitiés, et
chaque borne est recalée sur une frontière de phrase quand il y en a une à
portée ; sinon la coupe est signalée par des points de suspension.

**Aucune arête n'est créée.** L'étiquette portée à l'écran le dit dans les mêmes
mots à chaque fois :

> classé par proximité lexicale avec le texte de l'article — aucun lien déclaré,
> aucune arête créée

## 4. Ce que ça donne, et ce que ça ne donne pas

Sur L112-1-1, le premier passage classé du rapport au Président est celui cité au
§ 1, avec pour termes communs *annonce, réduction, prix, professionnel,
consommateur*. La question « pourquoi cet article existe » est répondue par le
document, et la page le montre en trois passages au lieu d'un mur.

Sur les considérants de la directive 2019/2161, **le classement ne trouve rien de
probant, et c'est un résultat exact** : cette directive ne motive pas la règle des
trente jours dans ses considérants — elle l'édicte à son article 2, qui modifie
la directive 98/6/CE. Les trois considérants remontés partagent *exception,
pendant, produit* : le lecteur voit ces termes et conclut lui-même. C'est
précisément pour ce cas que les termes communs sont affichés.

Le classement ne prétend donc pas identifier le considérant motivant. `docs/14`
§ 5 a mesuré deux méthodes qui le prétendaient et les a écartées ; rien n'est
revenu sur cette conclusion. Ce qui change est qu'un ordre sans rapport avec la
question a été remplacé par un ordre qui en a un, sous étiquette.

**Coût, mesuré.** Une passe par document, et le classement n'ajoute rien de
sensible au cas ordinaire : 50 ms pour L112-1-1 comme avant, 62 ms pour L224-43.
Il coûte là où il y a beaucoup à lire — 135 ms sur L111-1 (1,1 Mo de documents,
contre 77 ms sans classement) et **705 ms sur L511-7**, que le droit de l'Union
sature de 26 documents et 7,4 Mo, contre 222 ms sans. C'est le pire cas du corpus,
et il est cité tel quel plutôt que moyenné.

La forme naïve coûtait davantage. Découper 7,4 Mo en 562 000 jetons pour en garder
120 000 prend 422 ms ; une table des formes construite une fois, puis un accès de
dictionnaire par jeton, en prend 185. Une alternation compilée sur les 198 termes
de l'article a aussi été essayée : **741 ms**, plus lente que les deux — le moteur
d'expressions régulières ne factorise pas les grandes alternances. Les trois
chiffres sont dans le code, parce qu'une optimisation qu'on ne peut pas
contredire se re-tente.

Seuls les documents de `motivation_du_texte` sont classés — exposé des motifs,
étude d'impact, avis du Conseil d'État, rapport au Président — jamais les rapports
de commission, qui portent déjà des arêtes déclarées.

## 5. Trois défauts de rendu, corrigés

**`alinéa 0`.** Les alinéas se comptent à partir de 1 en droit français. Pire :
sur L112-1-1, le texte affiché en position 2 dit « par exception au **deuxième**
alinéa », qui portait le numéro 1. Sur un produit dont l'argument est l'ancrage
exact, un décalage d'indice visible à l'écran disqualifie. `segment.ordre` reste
compté depuis zéro — il sert de clef, `<id_legi>:<ordre>` — et un champ `rang`
porte désormais le numéro au sens du droit. `note.py` faisait déjà `+ 1` de son
côté ; la règle est maintenant écrite une fois.

**Fuite de balisage dans les citations.** 7 111 des 7 674 considérants portaient
`<div class="eli-subdivision"` en queue de texte. La borne d'un considérant était
prise au début de l'**attribut** `id="rct_N"` du suivant, et non au début de la
balise qui le porte : le fragment se terminait donc par une balise ouverte, que
`<[^>]+>` ne reconnaît pas comme une balise. Deux corrections, la seconde
défensive : la borne recule jusqu'au `<` ouvrant, et `en_texte` retire d'abord
toute balise non refermée aux deux bouts. Après réingestion : **0 sur 7 674**.

Les considérants étaient en outre coupés à 1 200 caractères sans le dire. La
coupe est désormais marquée. Le repli reste borné à 25 par acte — sans borne, la
fiche de L511-7, que le droit de l'Union sature de 997 considérants, pèse 1,1 Mo
que personne ne lira —, mais la borne ne coûte plus la pertinence : **les mieux
classés sont hors du repli**, donc toujours visibles, et le compte affiché dit
combien manquent.

**`confiance 1.000` sur la transposition.** La mesure porte sur la proposition
« ce texte transpose cet acte », déclarée par l'intitulé au Journal officiel. Elle
était affichée nue, à côté d'un avertissement disant que le lien porte sur le
texte entier et non sur l'article : le nombre d'une proposition se lisait donc
comme celui d'une autre. La confiance porte désormais sa proposition dans la même
phrase, et elle est lue dans `transpose.confiance` plutôt qu'écrite en dur.

## 6. Une règle, un endroit

`restitution/citation.py` porte `PLAFOND_EXTRAIT`, `cite()` et `extrait()`. Le
plafond de 400 caractères d'`ATTRIBUTION.md` était tenu à trois endroits, et il
avait déjà divergé une fois — 772 caractères de rapport dans les exemples
versionnés. Il commande maintenant aussi la fenêtre de `proximite.py`, ce qui
n'était pas prévu et qui est la meilleure raison de l'avoir sorti là.
