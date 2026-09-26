# Cinquantième tranche — Tisseuse contre `vise`, et legi.py

**Objet :** mesurer si l'extracteur de directives de Tisseuse (Tricoteuses),
seul successeur maintenu de DuraLex, peut tenir la fonction de `vise` ; et
clore la décision laissée ouverte par `docs/01` § 6, qui disait de legi.py
« à utiliser » alors que rien ne l'utilise.
**Date : 26 septembre 2026.**
**Code :** `tools/mesures/banc_tisseuse.py`.
**Données :** les douze fiches `precision-vise*.tsv`, 199 fiches jugées sur
195 arêtes distinctes ; sortie `data/mesures/banc-tisseuse-vise.tsv`.
**Version comparée :** `tricoteuses-juridique`, commit `bf985e5` du
9 avril 2026, lu sur un miroir GitHub tiers. La forge de Tricoteuses refuse
les robots, et le serveur MCP Moulineuse, qui expose leurs bases, demande une
authentification et n'expose pas l'extracteur.

---

## 1. La question

`extractActionDirectivesFromText` rend, pour un texte modificatif, une liste
de directives typées : `insert_after`, `insert_before`, `replace`,
`replace_portion`, `delete`, `delete_portion`, `delete_article`, chacune avec
la référence qu'elle touche. Si l'article que nous visons est la référence
d'une de ces directives, Tisseuse et `vise` disent la même chose. Le banc
passe dans l'extracteur le dispositif de chaque arête jugée, et range le
résultat en trois issues : une directive porte sur l'article visé
(`meme_article`), des directives mais aucune sur lui (`autre_cible`), aucune
directive (`aucune`).

## 2. Le résultat

| Notre verdict | même article | autre cible | aucune directive |
|---|---:|---:|---:|
| juste (163) | **47** | 37 | 79 |
| faux (34) | 3 | 4 | 27 |
| douteux (2) | 0 | 1 | 1 |

Aucune erreur d'exécution sur 199 dispositifs.

**Sur les justes, Tisseuse retrouve l'article 47 fois sur 163 (29 %).** Le
silence tient au périmètre, non à la qualité : Tisseuse modélise la
retouche de mots dans un article, et les formes les plus courantes du
corpus n'en sont pas. Parmi les 79 justes sans directive : « est ainsi
rédigé » 49 fois, « est complété par un alinéa » 11, « est ainsi modifié »
4, « sont ainsi rédigés » 4, l'insertion d'articles 5, l'abrogation 4.
Aucun type de directive ne réécrit ni ne crée un article.

**`autre_cible` (37) n'est pas une erreur démontrée.** Dans un dispositif à
plusieurs instructions, Tisseuse extrait bien des directives, sur d'autres
articles que celui du tirage ; certaines portent le numéro de l'article du
projet de loi (« 13 I », « 26 ») et non celui du code. Ces cibles ne sont pas
jugées.

**Les trois erreurs communes sont des erreurs de version.** L131-4 est un
homonyme dans un autre code ; L122-3 pointe une version de 1993 ; L217-9
pointe une version « morte-née » de 2022, jamais entrée en vigueur. Tisseuse
rend le numéro écrit, pas la version : ces trois erreurs se commettent après
l'extraction, là où `vise` choisit la version (`docs/43`, `docs/47`). Le
chargeur de liens de Tisseuse choisit la version en vigueur à la date du
texte (`links.ts`) : il ne voit pas qu'un numéro a pu glisser.

## 3. Ce que cela vaut

Tisseuse n'est pas un substitut de `vise` : il ne couvre ni la réécriture ni
la création, et il ne choisit pas la version. Ce qui se reprend est plus
étroit :

- **le grain de la retouche.** Le rang d'occurrence (« la seconde
  occurrence du signe « , » ») et la portion d'article sont plus fins que ce
  que lit `resulte_de` pour situer l'alinéa ;
- **les tests.** Tisseuse porte 538 tests unitaires sur des tournures
  modificatives ; ce dépôt n'en a aucun et ne voit ses régressions qu'au
  harnais et aux tirages. Leurs cas, sous la même licence, feraient une base
  de non-régression pour la lecture des instructions.

Ce chiffre n'est pas une précision de Tisseuse : c'est l'accord de Tisseuse
avec des verdicts d'agents, sur des arêtes tirées dans notre population.

## 4. legi.py : la décision close

`docs/01` § 6 classait legi.py « vivant, à utiliser ». La première tranche
LEGI (`ingestion/legi_vers_graphe.py`, 22 août 2026) a lu le XML elle-même,
sans que la décision soit écrite. Elle l'est ici : **legi.py n'est pas
utilisé**, pour trois raisons vérifiées dans son code.

1. **Il oriente les liens par l'attribut `sens`.** `tar2sqlite.py` inverse
   la source et la cible quand `sens="cible"`. C'est le piège 1 de
   `docs/01` § 2.3 bis : les vocabulaires ancien et récent donnent à `sens`
   des valeurs opposées pour la même relation, et filtrer sur lui perd des
   articles. Il faudrait relire les liens bruts, donc le XML.
2. **Il ne découpe pas l'alinéa.** Il garde le `BLOC_TEXTUEL` entier ; le
   modèle de ce dépôt est au grain du segment, coupé aussi aux `<br/>`
   (26,5 % des articles n'ont aucun `<p>`), et `repris_de` compare les
   alinéas d'une version à l'autre. Cette couche serait à écrire au-dessus
   de lui de toute façon.
3. **Il charge tout LEGI dans une base à lui.** Le pipeline n'extrait que le
   code de la consommation de l'archive (`pipeline.sh`, étape 1), et la base
   de ce dépôt est le dump ouvert (`docs/23`) : une seconde base de tout le
   fonds serait une dépendance sans usage.

legi.py reste la référence pour les anomalies du fonds LEGI, qu'il signale à
la DILA ; le lecteur de ce dépôt n'en tient pas de registre.

## 5. Ce qui n'est pas fait

- les 37 cibles `autre_cible` ne sont pas jugées ;
- les tests de Tisseuse ne sont pas repris ;
- la version comparée est celle d'un miroir d'avril 2026, qui peut être en
  retard sur la forge.
