# Cinquième tranche — la couche européenne

**Objet :** cesser de rendre « aucune raison documentée » pour des articles que le
droit de l'Union dicte mot pour mot.
**Date : 23 août 2026.**
**Code :** `ingestion/union_europeenne.py`, `tools/ue/verifier_celex.py`,
`tools/dila/titres_jorf.py`. **Schéma :** `schema/004-union.sql`.

---

## 1. Ce que le produit disait de faux

Les tables `acte_ue` et `transpose` existaient depuis le § 3 de la feuille de
route. Elles étaient vides, et c'est la seule chose que ce projet ait jamais
rendue *fausse* plutôt qu'incomplète.

Le silence, ici, n'est pas neutre. Le contrat de restitution du § 4.3 donne au
produit un verdict explicite — **`raison non documentée`** — et en fait un
résultat de premier ordre. Un article du code de la consommation entièrement
commandé par un règlement européen recevait ce verdict. La bonne réponse était
imprimée dans son propre texte, à trois mots de là.

Le code de la consommation est l'un des codes les plus européens du droit
français. **280 actes de l'Union sont nommés dans son texte**, en toutes lettres,
déjà présents dans le fonds LEGI. Aucune source nouvelle n'a été nécessaire.

Les trois CELEX vérifiés qui n'entrent pas en base sont ceux que la coupure du
§ 6 écarte : ils figurent dans un intitulé français, mais au titre d'une
modification, pas d'une transposition.

## 2. Ce que la tranche produit

| | |
|---|---:|
| CELEX construits et confrontés à Cellar | 287 |
| **Actes retenus en base** | **284** |
| dont règlements | 229 |
| dont directives | 53 |
| dont décisions | 2 |
| Citations rattachées à un alinéa, avec offsets | **1 478** |
| écartées faute de preuve exploitable | 0 |
| Actes atteignant au moins un article en vigueur | 165 |
| **Articles en vigueur nommant un acte de l'Union** | **117 sur 2 104 (5,6 %)** |
| Transpositions déclarées dans un intitulé au JO | 8, sur 8 textes |
| **Articles en vigueur atteignant une transposition déclarée** | **63** |

Les plus cités : le règlement (UE) n° 1169/2011 sur l'information des
consommateurs sur les denrées alimentaires (12 articles), le règlement (UE)
2017/2394 sur la coopération entre autorités (10), le règlement (CE) n° 178/2002
sur la législation alimentaire (10), le règlement (CE) n° 2006/2004 (9), le
règlement (UE) 2016/679 — le RGPD (8).

Ce que la restitution rend, pour L. 511-7 :

```
  [1] 1° Du règlement (UE) 2021/782 du Parlement européen et du Conseil du
      29 avril 2021 sur les droits et obligations des voyageurs ferroviaires ;
        cite règlement (UE) 2021/782
          https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32021R0782
```

## 3. Le numéro français ne donne pas l'ordre année/numéro

C'est le piège central, et il est silencieux.

« Règlement (CE) n° 1008/2008 » se lit *numéro 1008 de l'année 2008*. « Règlement
(UE) 2018/302 » se lit *année 2018, numéro 302*. La numérotation des actes de
l'Union s'est inversée en 2015, et les deux formes coexistent dans un même
alinéa. Une directive, elle, porte toujours l'année en tête, y compris sur deux
chiffres — « 93/13/CEE ».

Sur 1 478 citations, **102 ont leurs deux composantes plausibles comme années**.
La plus fréquente est la pire : « règlement (CE) n° 2006/2004 », le règlement
coopération, cité 75 fois. L'inverser produit `32006R2004` — un identifiant
parfaitement valide, qui désigne un règlement sur les résidus de pesticides.
L'erreur n'aurait rien cassé et n'aurait rien signalé.

Le signe qui tranche est la mention `n°`, héritée de l'ancienne forme. Dans le
corpus, elle est présente sur les **91** citations à l'ancienne et absente sur les
**11** à la nouvelle, **sans une seule exception**. Le codificateur français
l'ajoute parfois à tort sur un acte récent — « règlement (UE) n° 2015/751 » — mais
là une seule des deux composantes est une année plausible, et la plausibilité
suffit. Quand aucune ne l'est, la citation est abandonnée, jamais devinée
(§ 5.1).

## 4. Un identifiant construit doit être vérifié

Aucun CELEX n'est recopié d'une source : chacun est **déduit** d'un numéro écrit
en français. Une déduction bien formée reste plausible quand elle est fausse —
c'est précisément ce que montre le cas ci-dessus.

Chaque identifiant est donc confronté à **Cellar**, le service d'identifiants de
l'Office des publications de l'Union, qui répond 303 vers la ressource pour un
acte connu et 404 sinon. C'est la seule étape du projet qui demande le réseau ;
son résultat est versionné dans `data/corpus/celex-verifies.tsv`, pour que tout le
reste reste rejouable hors ligne.

**280 sur 280 sont reconnus, aucun inconnu.** Ce chiffre prouve que les actes
existent — il ne prouve pas que ce sont les bons, puisqu'une inversion produit un
identifiant tout aussi réel.

La précision a donc été mesurée séparément : **20 citations tirées au sort**,
chacune confrontée au titre officiel publié par Cellar. **20 sur 20 exactes**, y
compris les deux tirages du cas piège `n° 2006/2004`, correctement résolus en
`32004R2006` — « coopération entre les autorités nationales chargées de veiller à
l'application de la législation en matière de protection des consommateurs ».
Borne inférieure de Wilson à 95 % : **`CONFIANCE = 0,8389`**.

Un défaut d'affichage a été trouvé par ce tirage, non par le code. Un acte cité en
énumération n'a pas de mot-type à lui : « les règlements (CE) n° 1184/2006 et
n° 1224/2009 » ne laisse, pour le second, que « n° 1224/2009 », qui ne dit pas ce
qu'est l'acte. La dénomination retenue est désormais la plus fréquente *parmi
celles qui nomment le type*, et le mot manquant, quand il n'en existe aucune,
vient du pluriel qui gouverne l'énumération — jamais d'une reconstruction.

### Le même défaut d'idempotence, une troisième fois

Le fichier de schéma détruit `cite_acte_ue` et `transpose` à chaque exécution,
mais pas les lignes de `preuve` qu'elles référençaient. Après quelques passages,
la base portait **8 908 preuves orphelines** pour 1 478 arêtes — plus de déchet
que de donnée.

C'est exactement le défaut déjà commis sur `resulte_de` (`docs/09`) puis sur
`document` (`docs/12`). Il est silencieux : rien ne casse, les compteurs affichés
restent justes, et seule une requête qu'on n'a pas de raison d'écrire le révèle.
La purge est faite **après** la destruction des tables — dans l'autre ordre, la
clef étrangère la refuse, et elle a raison de le faire. Deux exécutions
consécutives rendent maintenant des compteurs identiques et zéro orpheline.

## 5. Citer n'est pas transposer

L'arête s'appelle `cite_acte_ue` et ne dit rien de plus que ce qu'elle constate :
**cet alinéa nomme cet acte, à cet offset**.

La tentation était d'appeler cela « met en œuvre » ou « transpose ». Ce serait
faux trois fois. Un règlement européen ne se transpose pas, il s'applique
directement. Un article qui cite une directive pour en **écarter** l'application
la cite exactement autant qu'un article qui l'applique. Et un article peut citer
un acte au seul titre d'une définition qu'il emprunte.

La qualification du lien n'est pas dans les données. Elle n'est donc pas produite,
et la restitution tient le mot : elle écrit « cite ».

## 6. La transposition déclarée, elle, est ailleurs

LEGI ne porte que la forme courte du titre d'un texte — « Ordonnance n°2021-650 du
26 mai 2021 ». La forme longue, publiée au Journal officiel, dit ce que le texte
prétend faire : « … **portant transposition de la directive (UE) 2018/1972** … ».

C'est une déclaration de l'auteur du texte, pas une déduction : `methode =
declaree`, `confiance = 1.0`. `tools/dila/titres_jorf.py` la reprend du miroir,
dans `<TITREFULL>` du fichier `version` — au même endroit que pour les rapports au
Président, et contrairement au corps des articles, qui n'y est pas (`docs/12`).

Comme le rapport au Président, elle porte sur le **texte entier**, non sur
l'article. La restitution le dit à chaque fois.

Deux pièges, tous deux trouvés en lisant les huit arêtes produites plutôt qu'en
lisant le code.

**Un intitulé français reprend le titre officiel de la directive**, et ce titre
nomme les actes que *la directive* modifie. Le décret n° 2016-622 « portant
transposition de la directive 2014/17/UE … **et modifiant les directives**
2008/48/CE et 2013/36/UE et le règlement (UE) n° 1093/2010 » se voyait attribuer
quatre transpositions au lieu d'une. Tout ce qui suit une charnière de ce genre —
« modifiant », « abrogeant », « et mesures d'adaptation » — relève d'un autre
rapport, et n'est pas retenu. Huit textes, huit directives, une chacun.

**Quatre transpositions déclarées disparaissaient en silence** parce que la
directive n'est citée nulle part dans le texte du code : la DSP2, la directive
crédit immobilier, la directive électricité, et l'« Omnibus » 2019/2161 — soit
quatre des directives les plus structurantes du droit de la consommation récent.
Le balayage des candidats à vérifier ne portait que sur les alinéas. Il porte
maintenant aussi sur les intitulés.

C'est ce dernier correctif qui produit le cas le plus net de la tranche. L'article
L. 112-1-1 — l'obligation d'afficher le prix antérieur lors d'une annonce de
réduction — n'a **aucune** motivation parlementaire : il est né d'une ordonnance,
et le produit répondait « aucun passage motivant n'a été rattaché à cet article ».
Il porte désormais sa directive :

```
  [transposition déclarée] directive 2019/2161
  https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32019L2161
  déclarée par l'intitulé de « Ordonnance n°2021-1734 du 22 décembre 2021 »,
  qui porte sur le texte entier, non sur cet article
```

## 7. Ce que la tranche ne fait pas

**Les 5,3 % sont un plancher, pas une mesure de l'emprise européenne.** Un article
peut transposer une directive sans jamais la nommer — c'est même le cas ordinaire,
la transposition consistant à réécrire la règle en droit interne. Cette tranche ne
voit que les articles qui **citent**. L'absence d'acte de l'Union sur un article ne
dit rien de son origine européenne, et la restitution n'en tire aucune conclusion.

**Les considérants ne sont pas chargés.** La colonne `acte_ue.considerants` reste
vide. C'est pourtant là qu'est le « pourquoi » du droit de l'Union : un considérant
de directive est l'exposé des motifs que le droit français n'a pas. Les charger
donnerait, pour les 113 articles concernés, une motivation d'une qualité que le
corpus parlementaire n'atteint nulle part. C'est la suite naturelle de cette
tranche.

**La correspondance article par article n'est pas faite.** Savoir que L. 224-43
relève de la directive 2011/83/UE ne dit pas de quel article de la directive. Les
tableaux de concordance existent, en annexe des textes de transposition ; ils ne
sont pas ingérés.

**La jurisprudence de la Cour de justice est hors périmètre**, et le restera tant
que le § 1 n'a pas été rouvert par une nouvelle note de cadrage.
