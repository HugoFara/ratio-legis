# Treizième tranche — le verdict, et les métriques d'hygiène

**Objet :** rendre le verdict `raison non documentée`, et compter ce que le
graphe permet enfin de compter.
**Date : 23 août 2026.**
**Code :** `ingestion/verdict.py`, `tools/mesures/hygiene.py`.
**Schéma :** `schema/007-verdict.sql`. **Données :** `data/mesures/hygiene.tsv`.

---

## 1. Se taire n'est pas dire

Le § 4.3 de la feuille de route donne au produit un verdict explicite —
**`raison non documentée`** — et en fait « un résultat de premier ordre, pas un
échec ». Douze tranches plus tard, il n'était rendu nulle part. La restitution
affichait ce qu'elle savait et se taisait sur le reste.

Ce n'est pas la même chose. Un lecteur ne peut pas distinguer « nous n'avons pas
cherché » de « nous avons cherché dans treize sources et il n'y a rien ». Le
second est une information ; le premier n'en est pas une.

## 2. Quatre verdicts, du grain le plus fin au silence

| verdict | ce qu'il dit |
|---|---|
| `passage_motivant` | un passage explique cet article — commentaire de rapport qui le nomme, ou amendement qui a écrit l'alinéa |
| `origine_situee` | aucun passage, mais on sait sous quel article de quel texte il a été discuté |
| `motivation_du_texte` | ni l'un ni l'autre, mais un document motive le texte entier, ou un acte de l'Union le commande |
| `raison_non_documentee` | rien |

**Trois chaînes, trois directions.** Le calcul n'est pas une simple réunion de
jointures : chaque voie se remonte différemment, et sur ce corpus un article en
vigueur n'est presque jamais rattaché sous son numéro d'aujourd'hui.

- `motive` remonte les **ancêtres** de l'article : un rapport de 2013 nomme
  L. 121-105, jamais L. 224-65.
- `resulte_de` remonte les **segments** dont l'alinéa est repris : l'amendement a
  écrit un alinéa d'une version antérieure.
- `porte_sur` descend vers les **descendants** de l'article visé : le texte de
  2014 vise L. 121-42, devenu L. 224-43.

En oublier une donne un taux de silence faux — et ce taux est précisément ce que
la tranche publie.

## 3. Le chiffre qu'il ne faut pas publier seul

Sur les 2 104 articles en vigueur, **699 (33,2 %) sont sans raison documentée**.
Ce chiffre ne décrit rien, et le publier tel quel serait une faute.

| partie | articles | un passage les motive | origine située | motivation du texte | **raison non documentée** |
|---|---:|---:|---:|---:|---:|
| **L** | 1 293 | 696 (53,8 %) | 177 | 415 | **5 (0,4 %)** |
| **R** | 632 | 44 (7,0 %) | 14 | 47 | **527 (83,4 %)** |
| **D** | 179 | 1 | 0 | 11 | **167 (93,3 %)** |

Un décret n'a ni exposé des motifs, ni débat, ni amendement : son silence est
**structurel**, celui d'un article de loi ne l'est pas. Séparés, les deux chiffres
disent deux choses vraies et différentes :

- **la partie législative du code de la consommation est documentée à 99,6 %** — 5
  articles sur 1 293 échappent à toute source ;
- **la partie réglementaire l'est à 14,4 %** — et c'est elle qui porte la masse des
  obligations que rencontre un consommateur.

`docs/27` a élargi le périmètre aux parties R et D et mesuré ce que
l'élargissement change à ces taux : 701 muets deviennent 699. **Le silence
réglementaire n'était pas un artefact de périmètre.**

Le § 7 de la feuille de route l'annonçait : « Documenter leur absence de
motivation est un résultat en soi. » Il est ici chiffré.

## 4. Deux autres chiffres qui mentent si on les prend bruts

**« 11,5 % des amendements du Sénat n'ont pas d'objet publié. »** Faux comme
constat de pratique. 1 515 des 2 338 objets manquants sont ceux d'amendements
« retirés avant séance », 804 d'amendements irrecevables au titre de l'article 40 :
Améli ne publie pas l'objet de ce qui n'a pas été défendu. La corrélation est
quasi parfaite — 100 % des retirés avant séance, 99,6 % des irrecevables.

Rapporté aux seuls amendements **adoptés**, le taux est de **0,3 % — 17 sur
5 070** au Sénat, **0 sur 2 677** à l'Assemblée. Là, le chiffre veut dire quelque
chose : dix-sept dispositifs sont entrés dans la loi sans justification publiée.

**« 78 % du code vient d'ordonnances. »** Vrai de l'origine *apparente* : 1 008
des 1 293 articles L en vigueur ont une ordonnance pour texte producteur, contre
276 une loi. Mais remonter la chaîne de renumérotation rétablit une loi dans
l'ascendance de **1 080 articles, soit 83,5 %**. C'est la thèse du projet, et
c'est le seul chiffre de cette liste qui ait demandé onze tranches de travail pour
devenir calculable.

Les deux premiers nombres se recouvrent de treize articles, dont la version en
vigueur porte deux textes producteurs de natures différentes. Ils ont d'ailleurs
longtemps été faux : la mesure comptait les articles ayant **une version
quelconque** produite par une ordonnance, abrogées et hors vigueur comprises, sur
un dénominateur d'articles en vigueur — 1 822 sur 1 293, soit 140,9 %. Un taux
supérieur à cent aurait dû suffire à la faire relire, et il a fallu qu'un
relecteur extérieur bute sur la phrase pour qu'on la reprenne.

## 5. Ce que les métriques disent d'autre

| | |
|---|---:|
| Amendements déposés, deux chambres | 31 457 |
| dont adoptés | 7 363 (23,4 %) |
| Durée médiane de la navette, sur 53 dossiers datés | **147 jours** |
| la plus courte | 1 jour |
| la plus longue | 693 jours |
| Articles les plus cités — L733-1 / L412-1 / L733-4 | 37 / 36 / 35 |

Les articles les plus cités sont les points de rupture d'une réforme : toucher à
L. 733-1 déplace trente-sept articles. C'est le chiffre qui parle au législateur,
et il ne demande aucune interprétation.

## 6. Ce que les métriques ne soutiennent pas

**La part de chaque chambre dans le texte final.** 98 segments viennent d'un
amendement de l'Assemblée, 147 du Sénat. Le dénominateur est trop faible — 110
articles seulement ont un alinéa tracé jusqu'à un amendement — et il reflète l'état
des corpus chargés, non le travail des chambres. Publier ce rapport serait une
erreur de lecture. Le chiffre est dans le fichier, avec sa note.

**Le taux d'adoption par groupe politique.** La donnée existe : `amendement` porte
l'auteur et son groupe. Le calcul serait facile et la lecture qu'on en ferait est
politique, pas documentaire. Le projet vend de la traçabilité, jamais de
l'interprétation (§ 8) ; la métrique n'est pas produite.

**La durée de la navette est mesurée sur les dates que DOLE écrit dans le libellé
des états du texte** — « Texte adopté en 1ère lecture par l'Assemblée nationale le
27 avril 2010 » — et non sur des dates structurées. 53 dossiers sur 93 en portent
au moins deux. La médiane vaut pour ceux-là.
