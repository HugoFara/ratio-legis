# Le but déclaré, et un contrôle qui ne tient pas

**Objet :** restituer le *pourquoi* au sens propre — le désordre auquel une
disposition répond — et rendre compte d'un contrôle de cohérence essayé puis
retiré. **Date : 23 août 2026.**

---

## 1. Le but existe à deux grains, et ils ne disent pas la même chose

Sur L224-43, le rapport de commission donne le but du **dispositif** :

> « Cet article tend à introduire plus de transparence dans le recours à des
> numéros à valeur ajoutée, en contraignant les professionnels les proposant à
> informer les consommateurs et en permettant à ces derniers de limiter leur
> utilisation. »

L'exposé sommaire de l'amendement donne le but du **changement**, dans les mots de
son auteur, et il nomme le problème — ce que le rapport ne fait pas :

> **amdt 641, M. Razzy Hammadi** — « permettre aux consommateurs et aux services
> d'enquêtes de la DGCCRF de pouvoir identifier rapidement le fournisseur d'un
> service à valeur ajoutée. De nombreuses réclamations concernent des pratiques de
> fournisseurs de SVA, dont certaines sont parfois frauduleuses. […] Cette opacité
> nuit également à l'efficacité de l'action de la DGCCRF. »

C'est le *ratio legis* au sens propre : non pas ce que la loi dit, mais ce à quoi
elle répond. **La donnée était en base depuis le chargement des amendements —
`amendement.objet`, 31 457 lignes — et n'était pas restituée.** Elle l'est
désormais, sous chaque arête `resulte_de`.

## 2. Ce que sa lecture a permis de voir

L'amendement 70 rect. de M. SIDO, rattaché à L224-43, a pour objet le commerce
électronique, la preuve et l'article 1316-1 du code civil. Rien à voir avec les
numéros surtaxés. **C'est une arête fausse, et seul l'affichage du but l'a rendue
visible** — la fenêtre de preuve, elle, correspondait bien.

La leçon de méthode : le contrôle utile n'a pas été automatique. Il a été fait par
un lecteur, à qui la restitution donnait l'élément nécessaire. C'est exactement la
position du § 5.6 — la machine produit l'arête et sa preuve, elle ne prononce pas
le jugement.

## 3. Le contrôle structurel a été essayé, et retiré

L'échec ci-dessus suggérait un contrôle : l'article du **projet de loi** visé par
l'amendement devrait être celui que commente le rapport. C'est la seule clef
structurelle commune aux deux sources. `motive.article_du_texte` a été ajouté au
schéma pour la porter.

Mesuré sur l'ensemble : **89 arêtes sur 328 confrontables, soit 27,1 %, seraient
« incohérentes »** — pour une précision mesurée à 23/26. Le contrôle accuse dix
fois plus que la précision réelle. Il est donc faux.

La cause est structurelle et elle est visible dans l'échantillon : **l'article du
projet de loi est renuméroté à chaque lecture.**

| Article | Amendement | Texte discuté | Vise | Commentaire |
|---|---|---|---:|---:|
| L121-83-1 | amdt 639 | BTC1156, Assemblée | art. 55 | art. 72 (rapport du Sénat) |
| L111-5 | amdt 408 | BTC1574, Assemblée | art. 72 | art. 4 |

L'amendement 639 vise l'article 55 du texte de commission de l'Assemblée ; le
rapport du Sénat commente la même disposition sous l'article 72. Le désaccord ne
dit rien tant que les deux côtés ne sont pas ramenés à **la même lecture du même
texte**, ce que la base ne sait pas encore faire : il faudrait savoir quel texte
chaque rapport examine.

Le verdict a donc été retiré de la restitution. Ce qui reste affiché est le fait
brut et vérifiable — « déposé sur l'article 5 du texte 2012-2013_810 » — que le
lecteur confronte lui-même au commentaire. `motive.article_du_texte` est conservé :
la donnée est juste, c'est l'inférence qui ne l'était pas.

## 4. Reconstruction complète du corpus

Le répertoire de travail était dans `/tmp`, un tmpfs : **tous les corpus dérivés
ont été perdus** — extraction LEGI, 316 rapports, jeux Améli, archives de
l'Assemblée, base. Le miroir DILA a survécu parce qu'il est dans l'arbre du dépôt.

La règle § 5.2 « la donnée brute est sacrée » ne valait qu'à moitié : la donnée
était sauve, le chemin pour la retrouver ne l'était pas. Le plan de récupération
des jeux Améli, en particulier, n'était versionné nulle part.

Deux réponses, toutes deux vérifiées par une reconstruction complète :

**`tools/senat/plan_ameli.py`** reconstruit ce plan depuis le seul miroir DILA. Les
liens « petite loi » de DOLE portent le couple (session, texte) dont l'URL Améli se
déduit ; les liens `senat.fr/leg/pjl12-810` le portent aussi, sous une forme où
l'année de session est sur deux chiffres. La première forme seule ne couvrait que
25 dossiers sur 93 ; les deux en couvrent 55, soit **263 couples**, plus large que
le corpus perdu.

**`pipeline.sh`** rebâtit l'ensemble en une commande, depuis le miroir et les plans
versionnés. Il inscrit dans le script les pièges déjà payés : extraction ciblée du
code pour ne pas saturer le disque, `--http1.1` sur les gros fichiers de
l'Assemblée, chemin `amendements_legis_XIV`.

Résultat de la reconstruction, à comparer à l'état perdu :

| | Perdu | Reconstruit |
|---|---:|---:|
| Rapports chargés | 234 | **221** |
| Jeux Améli | 61 | **71** |
| Amendements | 30 193 | **31 457** |
| Arêtes `motive` · articles motivés | 519 · 225 | 519 · 225 |
| Arêtes `renvoie_a` | 11 656 | 11 656 |
| Arêtes `resulte_de` | 293 | 286 |
| Articles en vigueur remontant à un amendement | 90 | 82 |

**Les 13 documents manquants sont les rapports au Président de la République**,
seule motivation des ordonnances. Ils avaient été récupérés à la main en phase 0 et
leur plan n'est pas versionné. Ils sont publiés au Journal officiel, donc présents
dans le miroir JORF : les retrouver hors ligne est le premier correctif à apporter
au pipeline.

L'écart sur `resulte_de` — 286 contre 293 — vient du corpus Améli, plus large mais
non identique. Il rappelle que ces compteurs dépendent du corpus récupéré, et non
seulement du code.
