# Seizième tranche — rendre la base lisible en ligne

**Objet :** lever le premier obstacle de la phase 4 — une interrogation du graphe
coûtait de 0,6 à 4,2 secondes par article.
**Date : 23 août 2026.**
**Code :** `ingestion/index_de_lecture.py`, `schema/008-index-de-lecture.sql`.

---

## 1. Le planificateur travaillait à l'aveugle

La cause n'était ni le volume — 240 Mo — ni la forme des requêtes. Sans
statistiques, SQLite suppose que toutes les tables se valent. Il choisissait donc
de **balayer les 6 131 versions d'articles, chacune portant le texte intégral,
pour chaque acte de l'Union, deux fois par requête** : environ 1,7 million de
lignes visitées pour répondre sur un article.

```
|--SCAN u USING COVERING INDEX …
`--CORRELATED SCALAR SUBQUERY 1
   |--SCAN vv                       ← 6 131 versions, une fois par acte
```

## 2. Deux remèdes, qui ne pèsent pas pareil

La mesure les sépare, parce que l'intuition se trompe sur lequel compte :

| | Quatre articles | Gain |
|---|---:|---:|
| Base telle quelle | 1,70 s | — |
| Index seul | 0,41 s | × 4 |
| **`ANALYZE` seul** | **0,047 s** | **× 36** |
| Les deux | 0,037 s | × 46 |

**C'est `ANALYZE` qui fait l'essentiel.** Le planificateur n'avait pas besoin d'un
chemin de plus, il avait besoin de savoir ce qu'il avait. On aurait pu ajouter
des index pendant des heures sans approcher ce résultat.

L'index sur `article (numero)` reste utile et justifié : la restitution part
toujours du numéro d'article, et `article` n'était indexé que par le couple
`(code, numero)` — un préfixe inutilisable pour une recherche sur le seul numéro.
Les index de l'ingestion ne sont pas ceux de la lecture, et un index inutile se
paie à chaque insertion : ils sont donc dans un fichier de schéma à part, appliqué
en dernier.

## 3. Résultat

| | Avant | Après |
|---|---:|---:|
| Médiane par article | ~425 ms | **9,4 ms** |
| 95ᵉ centile | — | 33 ms |
| Maximum | 4,2 s | 168 ms |
| Balayage des 2 139 articles | ~15 min | **32 s** |

L'API de la phase 4 n'est plus contrainte par la base.

## 4. Ce que la mesure a révélé au passage : une restitution non reproductible

En comparant les sorties avant et après, **38 articles sur 2 139 rendaient un
résultat différent**. Vérification faite, aucun contenu ne changeait : seul
l'**ordre** des listes variait — les anciens numéros d'un article sortaient dans
l'ordre où le plan d'exécution les avait rencontrés.

C'est bénin à l'écran et grave sur le fond. Une restitution dont l'ordre dépend
d'un index n'est pas reproductible, et la reproductibilité est ce que ce projet
vend (§ 5.2). Deux exports du même graphe auraient différé sans qu'aucune donnée
n'ait bougé.

Quatre requêtes n'avaient pas de tri total ; elles l'ont désormais. Le tri des
documents motivant le texte, fait en Python, était lui aussi partiel : deux
documents de même type sortaient dans l'ordre du plan.

Vérification après correction : les 2 139 articles interrogés sur **deux plans
d'exécution différents** — avec et sans l'index de lecture — rendent des sorties
identiques au caractère près, ordre compris. **Zéro écart.**

**L'accélération n'était pas censée trouver cela.** C'est le propre d'une mesure
faite sur deux états comparables : elle expose ce qui n'aurait pas dû dépendre de
l'état.
