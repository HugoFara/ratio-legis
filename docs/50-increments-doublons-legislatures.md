# Quarante-quatrième tranche — les incréments DOLE, les doublons de l'Assemblée, les législatures XV à XVII

**Objet :** les trois chantiers mécaniques que le README laissait ouverts —
`issu_de` repassé sous son seuil, un même amendement de l'Assemblée chargé
deux fois, les législatures XV à XVII jamais chargées — et un quatrième,
qui ne l'était pas : `vise` résolue par le contenu, que `docs/49` § 7 avait
comptée sans la poser. En chemin, un plan versionné qui perdait en silence le
projet de loi Hamon.
**Date : 24 septembre 2026.**
**Code :** `tools/dila/fonds.py` (nouveau), les sept lecteurs de DOLE et de
JORF, `tools/an/plan_textes_an.py` (nouveau),
`tools/an/extraire_amendements_an.py`, `ingestion/visees.py`,
`ingestion/textes_des_amendements.py`, `ingestion/sort_des_amendements.py`,
`tools/mesures/rejouer.py`, `tools/mesures/precision_vise.py`, `pipeline.sh`.
**Données :** `precision-vise-par-le-contenu.tsv`,
`precision-vise-legislatures.tsv`, `precision-resulte-de-legislatures.tsv`,
`plan-textes-an-{14,16,17}.tsv`.

---

## 1. Les incréments DOLE n'étaient pas lus

`docs/26` avait appliqué les incréments quotidiens au fonds LEGI : la base
n'avait plus un an de retard sur la source. Il ne l'avait fait que pour LEGI.
Sept scripts lisaient DOLE, deux lisaient JORF, et tous n'ouvraient que
l'archive **globale** du 13 juillet 2025. Les textes de 2025 et 2026 entraient
en base par LEGI, à jour, et cherchaient leur dossier dans un DOLE figé un an
plus tôt.

Onze lois et ordonnances qui produisent une version en vigueur étaient sans
dossier ; le README en comptait huit, par une autre définition. Les onze sont
listées par un dossier DOLE — dans un incrément. Il n'en manquait aucune à la
source.

`tools/dila/fonds.py` fait pour DOLE et JORF ce que `increments.py` fait pour
LEGI : l'archive globale, puis chaque incrément postérieur au socle, dans
l'ordre, en recouvrant puis en supprimant ce que `liste_suppression_*.dat`
énumère — les incréments JORF en portent, ceux de DOLE non. Le préfixe
horodaté des incréments est retiré à l'extraction, de sorte que les `rglob` des
appelants retrouvent le même arbre : aucun n'a changé de logique.

| | avant | après |
|---|---:|---:|
| lois et ordonnances utiles avec dossier | 59 / 70 | **70 / 70** |
| arêtes `issu_de` | 200 | 211 |
| recoupement avec les arêtes existantes | — | 200 / 200 d'accord |
| dossiers de l'historique du périmètre | 184 | 195 |

Le critère de sortie de la phase 2 sur `issu_de` est de nouveau atteint.
Les onze dossiers nouveaux ont régénéré les plans de rapports, d'études
d'impact, de textes et d'Améli : les lois de 2026 ont désormais leur exposé
des motifs, leurs rapports et leurs amendements.

## 2. Un même amendement, publié deux fois

`docs/49` § 7 le signalait sur un exemple : l'amendement 798 de l'Assemblée
était en base sous deux identifiants, 1121 et 8178, avec deux arêtes pour une.

Le fichier de l'Assemblée publie le même amendement sous le texte déposé
(`B2736`) et sous le texte de commission (`BTC2736`) : même numéro, même
organe, **même document PDF**, même dispositif, même sort à la seconde près.
Sur toute la XIVe législature :

| couples (texte, numéro, organe) présents sous les deux stades | 11 945 |
|---|---:|
| même PDF, même dispositif, même sort | 11 906 |
| même PDF, même dispositif, sort différent — une copie restée « A discuter » | 28 |
| amendements réellement distincts | **11** |

Le commentaire de l'extracteur disait l'inverse : « le même numéro désigne
deux amendements différents selon le stade ; les confondre en écrase 2 032 ».
Les 2 032 étaient, à deux près, ce doublon. La distinction des stades était
juste pour les onze ; elle a fait entrer les 11 934 autres deux fois.

`dedoublonner` les fond. L'identité est le document publié, et le dispositif
doit concorder en plus. Le stade gardé est celui des autres amendements, non
doublés, du même texte devant le même organe ; à défaut, BTC en séance
(67 631 amendements seuls contre 19 718), B en commission (50 117 contre 214).
Le sort vient de la copie la plus récente.

## 3. Le projet de loi Hamon manquait

`plan-textes-an-14.tsv`, écrit à la main, avait perdu un saut de ligne :

    JORFDOLE000032669047	4378JORFDOLE000027383756	1015

La ligne se lisait « texte 4378JORFDOLE…\t1015 », qu'aucun amendement ne
porte. Le texte 1015 est le projet de loi relatif à la consommation déposé à
l'Assemblée : **829 amendements** de la loi qui a créé le plus d'articles du
périmètre n'ont jamais été extraits. Rien ne le signalait. Une ligne de plan
mal formée arrête désormais l'extraction.

## 4. Les législatures XV à XVII

**Le plan.** Celui de la XIVe avait été écrit à la main ; `plan_textes_an.py`
le dérive des liens DOLE (rapports, textes) et des textes déposés.
L'Assemblée numérote projets, propositions et rapports dans une seule série
par législature, et le texte de commission porte le numéro du rapport qui
l'annexe : un numéro lu dans un lien du dossier n'appartient qu'à ce dossier.
**Vérifié sur la XIVe** : les numéros dérivés contiennent tous ceux du plan
manuel. Ils trouvent aussi **30 dossiers au lieu de 16** — le plan manuel
datait d'avant `docs/37`, qui a étendu le corpus aux dossiers de tout
l'historique des articles, et personne ne l'avait repris.

Le plan des textes déposés se reconstruit à l'étape 5, à partir des
amendements ; le plan des amendements le lit dans sa version versionnée. Le
cycle converge en un passage : après deux exécutions, les plans des XIVe,
XVIe et XVIIe sont stables.

**Le format.** Depuis la XVe, l'Assemblée ne publie plus de CSV, mais une
fiche JSON par amendement, à des chemins qui changent d'une législature à
l'autre (`15/loi/amendements_legis/Amendements_XV.json.zip`,
`16/…/amendements_div_legis/Amendements.json.zip`). `lire_json` en tire les
colonnes du CSV de la XIVe. Deux écarts : l'organe d'examen n'est plus que
dans `examenRef`, et le numéro est `numeroOrdreDepot`, `numeroLong` y
ajoutant le préfixe de la commission (« AE12 »). L'état « Irrecevable 40 »,
nouveau, porte son motif sous forme courte : `sort_des_amendements` le lit.

**La XVe manque.** Le serveur de l'Assemblée coupe le transfert des gros
fichiers après quelques mégaoctets et refuse la reprise par plage ; les jeux de
la XVIe et de la XVIIe sont passés, celui de la XVe (650 Mo) a échoué plus
de cent cinquante fois dans la journée. `pipeline.sh` réessaie à chaque
exécution et ne garde qu'une archive dont `unzip -t` répond. Aucun chiffre de
cette note ne compte la XVe.

| amendements en base | avant | après |
|---|---:|---:|
| Assemblée | 11 115 | **64 027** |
| — XIVe | 11 115 | 38 369 (dont 6 112 copies fondues avant chargement) |
| — XVIe · XVIIe | — | 10 120 · 15 550 |
| Sénat | 31 027 | 33 199 |
| acteurs | 1 644 | 2 656 |

## 5. `vise` résolue par le contenu

`docs/49` § 2 écartait seize arêtes dont le numéro était démenti par le
contenu, et dont le contenu désignait un autre article de la loi : « elle n'est
pas posée […] 3532 (treize mots, 0,64 vers L121-87 qui n'a rien à voir) dit le
risque ». Elle est posée ici, en `inferee`, avec la fenêtre de l'article écrit
pour preuve et sa constante à elle, à partir d'un alinéa écrit de vingt mots
au moins.

Treize arêtes, jugées toutes : deux juges Sonnet 5, un arbitre Opus 5 sur
l'unique désaccord (14339, qui rédige L121-110 avec d'autres délais — « l'autre
rédaction » de `docs/49` § 2, donc juste). **10 justes sur 13.** Les trois
fausses ont une cause commune, et elles sont seules à l'avoir : l'article
désigné **existait avant la loi**, qui ne l'a que modifié.

| amendement | écrit | le contenu désigne | ce qu'il recopie |
|---|---|---|---|
| 210 (Sénat, rejeté) | « Art. L. 311-17 » | L311-16 (1993) | la définition du crédit renouvelable, pour l'interdire |
| 14123 (rejeté) | « Art. L. 121-106 » | L121-82 (1998) | la sanction de l'appellation « boulanger », pour la pâtisserie |
| 14414 | « Art. L. 121-104 » | L136-1 (2005) | la reconduction tacite, sous le gaz de pétrole liquéfié |

Un amendement qui écrit « Art. L. X. – … » crée un article ; si son alinéa se
retrouve dans un article que la loi n'a fait que modifier, c'est une formule
qu'il recopie. La garde : le contenu ne désigne qu'un article dont la lignée
commence par une version du dossier. Elle retire les trois fausses et aucune
juste — **10 sur 10, Wilson 0,7225**. **Elle est choisie sur l'échantillon qui
la mesure**, et la population n'a pas d'autre membre à tirer : la constante
dit ce qui a été vu, non ce qui tiendra sur les amendements de la XVe.

Deux effets de bord, mesurés par le harnais :

- les deux arêtes de 4384 (L121-106, L121-110) jugées justes par le contenu
  en `docs/49`, perdues depuis, sont revenues ;
- la voie `visee` de `depose_sur` lisait toute la table `vise` : la nouvelle
  arête de 210 vers L311-16 y a retiré une `alinea` jugée juste (L311-17).
  `depose_sur` ne lit plus que les `vise` déclarées ; la population
  `inferee` n'est pas mesurée pour elle.

## 6. Le harnais ne reconnaissait plus `vise`

Les fiches `vise` ne portent que l'identifiant interne de l'amendement. Le
chargement de 55 000 amendements les a tous décalés, et le harnais a déclaré
**168 arêtes « perdues »** au lieu de 63 : les 105 de plus étaient toutes des
`vise` jugées, dont aucune n'avait bougé dans le graphe. `rejouer.py`
reconnaît désormais une `vise` par sa clef stable — chambre, dossier,
dispositif tel que la fiche l'a montré au juge, article —, comme `docs/49`
l'avait fait pour `resulte_de` et `depose_sur`.

| harnais | avant la tranche | après |
|---|---:|---:|
| fiches rejouées | 36 | 39 (les trois de cette tranche) |
| justes tenues | 596 | **642** |
| perdues | 63 | 61 |
| fausses présentes | 5 | 8 — les cinq verdicts humains contestés de `docs/49` § 6, et les trois `resulte_de` du § 7, sans garde |

## 7. Mesuré

La base a gagné 163 arêtes `resulte_de` (les 284 d'avant restent toutes) et
164 arêtes `vise` déclarées. Les constantes avaient été mesurées sur la
population d'avant : elles sont re-mesurées sur les arêtes nouvelles, tirées
disjointes de l'existant par une clef stable — les identifiants internes
ayant glissé, `--sauf` reçoit les arêtes d'avant retrouvées par (segment,
chambre, dossier, numéro) et par (chambre, dossier, dispositif, article).
Deux juges Sonnet 5 par fiche, colonnes séparées ; un arbitre Opus 5 sur
désaccord.

| arête | tirage | n | juge A | juge B | accord | arbitrage | verdict | Wilson |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `vise` · `inferee` | toutes, avant la garde des articles créés | 13 | 9 | 12 | 12 | 1 → juste | 10 / 13 | 0,4974 |
| `vise` · `inferee` | les mêmes, après la garde | 10 | | | | | **10 / 10** | **0,7225** |
| `vise` · déclarée | 20 parmi les 164 nouvelles | 20 | 17 | 17 | 20 | — | 17 / 20 | 0,6396 |
| `vise` · déclarée | **réunies aux 50 de `docs/49`** | 70 | | | | | **64 / 70** | **0,8253** |
| `resulte_de` | 20 parmi les 163 nouvelles | 20 | 17 | 17 | 20 | — | 17 / 20 | 0,6396 |
| `resulte_de` | **réunies aux 37 de `docs/49`** | 57 | | | | | **52 / 57** | **0,8105** |

**`vise`, ce que les fausses ont dicté.** Deux gardes, chacune vérifiée
arête par arête sur ce qu'elle retire et ajoute (13 retirées, 5 ajoutées) :

- *le chapeau vide suivi d'un point* — « L'article L. 111-5-1 est ainsi
  modifié : ». » passait `CHAPEAU_VIDE` à cause du point ; il retire aussi
  L121-37, un « est ainsi rédigé : ». » sans rien après. Il retirait L121-30,
  jugée juste en `docs/46` : « L'article L. 121-20-13 […] **devient
  l'article L. 121-30** et le I est ainsi modifié : ». Le chapeau est vide,
  la renumérotation qu'il porte ne l'est pas ; le harnais l'a dit, et le
  chapeau qui renumérote garde le numéro qu'il donne ;
- *l'anaphore n'est pas un nom* — le numéro nu prenait pour code hôte le
  dernier nom de code lu en amont, et « du présent code », écrit dans
  l'alinéa que l'amendement 47111 insère au code de l'action sociale, passait
  pour le nôtre. Le dernier *nom* compte désormais, l'anaphore ne vaut que
  faute de nom. Retirés : L314-7, L315-14, L315-16 de trois amendements
  identiques, L313-4 (même code), L541-1 (code de l'éducation). Ajoutés :
  cinq « après l'article L. 121-91 **du même code** », à la suite de « du
  code de la consommation », que l'ancienne règle prenait pour un autre code.

Comme en `docs/49`, les fausses qui ont dicté une garde restent dans le
tirage réuni : la constante décrit ce qui a été vu, non la population
d'après, qui n'a pas de tirage à elle.

**`resulte_de`, aucune garde.** Deux fausses sont une formule administrative
qu'un passage destiné à un autre texte partage avec l'alinéa — la suspension
à titre conservatoire d'un agrément (celui de « Mon accompagnateur rénov' »
dans l'amendement, celui de l'article L. 232-3 du code de l'énergie dans
l'alinéa), le plafond d'amende en pourcentage du chiffre d'affaires mondial
(une sanction de l'Arcom dans l'amendement, un délit de place de marché dans
l'alinéa). La troisième est une rédaction dont le barème de majoration n'a
pas été retenu. La corroboration par `vise` ne les sépare pas : sur tous les
tirages de `resulte_de`, les justes « sans visée » sont 225, les fausses 28.
La précision ponctuelle, 91,2 %, reste sous le seuil de 95 % du § 4.2 ; la
dérogation de la phase 2 tient, et son chiffre change.

Les trois fausses restent donc dans la base, et le harnais les nomme : il
échoue de huit arêtes, les cinq verdicts humains contestés de `docs/49` § 6 et
ces trois-là. Un doute sur l'une d'elles, que ni juge n'a soulevé :
l'agrément « Mon Accompagnateur Rénov' » **est**, sauf erreur, celui de
l'article L. 232-3 du code de l'énergie — l'amendement 18 rédigerait alors le
même alinéa, retouché ensuite, et l'arête serait juste. Le verdict n'est pas
retouché ici ; il est signalé pour la relecture humaine.

**`depose_sur` n'est pas re-mesurée.** Sa population passe de 1 093 à 1 237
arêtes ; ses constantes par voie sont celles de `docs/45`.

## 8. Ce qui n'est pas fait

**La XVe législature**, faute d'avoir pu la télécharger (§ 4). Le pipeline la
prendra au premier passage où le serveur la sert, et les constantes de § 7
devront être re-mesurées sur ce qu'elle ajoute.

**L'appariement des textes de l'Assemblée.** 113 jeux d'amendements sur 192
trouvent leur texte discuté, contre 39 sur 39 avant : les textes des XVIe et
XVIIe législatures qui n'ont que des adresses `/dyn/` ou des PDF absents du
plan ne sont pas chargés. Leurs amendements entrent en base avec leur sort et
leur auteur, sans `depose_sur`.

**Les tableaux « au grain de l'article » du README** ne sont pas recalculés :
leurs requêtes ne sont écrites nulle part, et celle que cette tranche a
reconstituée ne redonne pas les chiffres publiés. Ils restent ceux du
21 septembre, et le README le dit.
