# Trente-sixième tranche — `depose_sur` par l'alinéa, et trois voies mesurées à trois

**Objet :** composer `depose_sur` avec ce que le dispositif de l'amendement dit
de lui-même — l'article qu'il nomme, ou l'alinéa du texte qu'il touche — et
mesurer chaque voie à part, par trois juges.
**Date : 19 septembre 2026.**
**Code :** `ingestion/textes_des_amendements.py`, `schema/011-textes-des-amendements.sql`
(colonne `voie`), `tools/mesures/precision_depose_sur.py` (`--voie`),
`tools/mesures/juger.py` (trois colonnes).
**Données :** `data/mesures/precision-depose-sur-{alinea,visee,article-entier}.tsv`.

---

## 1. Ce que `docs/41` avait laissé

La composition seule — déposé sur l'article N du texte, N réécrit A et aucun
autre — valait 7 sur 15 quand on lui demandait ce qu'elle prétend :
« l'amendement portait sur A ». Un amendement déposé sur N peut ne toucher
qu'un paragraphe de N qui modifie un autre code. Et 1 626 amendements étaient
écartés parce que N réécrit plusieurs articles — la composition n'avait aucun
moyen de choisir.

Le dispositif, lui, dit presque toujours **où** il porte : « Alinéa 4 »,
« Après l'alinéa 13 », « Alinéas 7 à 11 ». Et l'alinéa d'un article de texte
se rattache à l'article du code que le texte réécrit à cet endroit : la
dernière instruction relevée par `porte_sur` — avec son offset de preuve —
avant la fin de l'alinéa.

## 2. Trois voies

| voie | ce que l'arête établit | arêtes |
|---|---|---:|
| `visee` | le dispositif nomme l'article du code (`vise`, chaîne de renumérotation comprise), et c'est une cible de N | 26 |
| `alinea` | le dispositif nomme l'alinéa n de N ; l'instruction qui gouverne cet alinéa réécrit A | **1 107** |
| `article_entier` | « Supprimer cet article », « Rédiger ainsi… » ; N ne réécrit que A, tous codes confondus | 22 |

Écartés, et comptés : 29 dont la cible déclarée contredit N ; 259 dont
l'alinéa relève d'une instruction sur un autre code — le cas du gaz de
`docs/41`, résolu à l'alinéa près ; 241 dont l'alinéa n'est pas lisible dans
le texte ; 74 « compléter cet article par un paragraphe », dont la cible est
par nature inconnue.

**1 155 arêtes au lieu de 246**, 31 articles en vigueur atteints au lieu de
14 — non par relâchement, mais parce que l'alinéa lève l'exclusion des
articles de texte à cibles multiples. C'est l'alinéa qui désambiguïse, pas la
garde.

## 3. Mesuré à trois

Trois tirages disjoints, un par voie, chaque arête jugée par trois modèles
qui ne se lisent pas — qwen3p8-max (colonne comptée), deepseek-v4p1-flash,
glm-5p3-flash — sur un brief qui dit, voie par voie, ce que « juste » veut
dire et demande de compter les alinéas dans le texte.

| voie | n | qwen | deepseek | glm | unanimité | Wilson |
|---|---:|---:|---:|---:|---:|---:|
| `alinea` | 20 | **18** | 18 | 18 | 19 / 20 | **0,6990** |
| `visee` | 10 | 7 | 8 | 8 | 9 / 10 | 0,3968 |
| `article_entier` | 10 | 7 | 7 | 7 | 10 / 10 | 0,3968 |

Les fausses ont toutes une cause nommée, et trois juges l'ont nommée pareil :

- `alinea` — l'instruction gouvernante s'arrête avant l'alinéa cité : les
  alinéas 7 à 11 de l'article 72 ter forment un II sur le code des postes,
  après un I sur L. 121-83-1 ; la dernière mention *interne* avant l'alinéa
  n'est pas la dernière instruction. La portée d'une instruction n'est pas
  bornée par la suivante quand celle-ci vise un autre code sans que
  `porte_sur` l'ait relevée.
- `visee` — le dispositif nomme A comme **ancre** : « après l'article
  L. 312-9, il est inséré un article L. 312-9-… ». `vise` prend une position
  pour une cible. C'est un défaut de `vise`, mesuré ici pour la première fois.
- `article_entier` — « N ne réécrit que A » repose sur `porte_sur`, qui ne
  voit ni l'article que le texte **insère** (« il est inséré un article
  L. 522-7-1 ») ni toujours l'autre code qu'il modifie. Et un « 72 terdecies »
  lu « 72 ter » : le rang composé n'avait pas de frontière de mot. Corrigé.

Les deux voies faibles portent 48 arêtes sur 1 155. La voie de l'alinéa porte
le reste, à 0,699 — au-dessus de la composition seule (0,248), au-dessous de
`porte_sur` (0,856), ce qui est l'ordre attendu d'une arête composée.

## 4. Trois juges, quatre dollars

Cent vingt juges : qwen 6,67 $, deepseek et glm moins de deux dollars
chacun. Sur 40 arêtes, 38 verdicts unanimes ; les deux désaccords opposent
qwen seul aux deux autres, et dans un cas il a raison sur pièces
(« L. 121-44 » du texte est le L. 121-48 du code — numérotation glissée), dans
l'autre il a échoué à l'appel et son second passage a rejoint la majorité.
Trois juges bon marché valent mieux qu'un juge cher : le désaccord est
l'information.

## 5. Ce que la tranche ne fait pas

Elle ne corrige pas `vise` (l'ancre prise pour une cible), ni `porte_sur` (les
articles insérés). Elle ne borne pas la portée d'une instruction par l'instruction
suivante quand celle-ci n'est pas relevée. Elle ne relit pas les 1 107 arêtes
de l'alinéa au-delà des vingt tirées. Et rien de ceci n'est humain.
