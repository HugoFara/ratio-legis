# Douzième tranche — convertir le gisement de sections écartées

**Objet :** faire descendre la motivation au grain de l'article, sans source
nouvelle.
**Date : 23 août 2026.**
**Code :** `ingestion/sections_vers_motive.py`.

---

## 1. Un chiffre mal lu, et ce qu'il cachait

La recommandation qui a ouvert cette tranche s'appuyait sur une comparaison
fausse : `motive` couvrait « 65 articles » contre 807 pour `porte_sur`. Le 65
était le compte **direct**, le 807 le compte **chaîné**. Or la restitution remonte
la chaîne de renumérotation depuis toujours : `motive` atteignait déjà **651**
articles en vigueur. La leçon vaut d'être écrite : sur ce corpus, tout compteur
qui ne dit pas s'il suit la renumérotation est ininterprétable.

Le gisement, lui, était réel. Un rapport de commission commente article par
article, et le corpus porte **6 475 sections** dont l'en-tête ne déclare aucun
article du code. Elles étaient jetées faute de savoir de quel article du code
elles parlaient. La onzième tranche l'a appris : `porte_sur` relie l'article du
texte en discussion à l'article du code.

## 2. Ce que la tranche produit

| | |
|---|---:|
| Sections sans déclaration examinées | 6 475 |
| Couples (dossier, article du texte) exploitables | 196 |
| écartés faute d'un second état du texte | 172 |
| écartés pour contradiction entre états | 41 |
| **Arêtes `motive` ajoutées** | **105** |
| écartées, non corroborées par LEGI | 255 |
| déjà connues par la déclaration en en-tête | 87 |
| Articles en vigueur atteints par `motive`, chaîne comprise | 651 → **695** |
| **dont ceux dont c'est la seule motivation** | **44** |

Le gain est modeste et il faut le dire ainsi : **+44 articles**, pas les 436 que
l'estimation initiale annonçait. L'écart vient des deux gardes, qui n'avaient pas
été appliquées à l'estimation — la corroboration LEGI écarte les trois quarts des
candidats, et 87 arêtes étaient déjà connues par une voie plus sûre.

## 3. La renumérotation, mesurée puis contournée

Le piège est celui qui avait fait retirer le contrôle de cohérence structurelle
(`docs/11`) : les articles d'un texte sont renumérotés à chaque lecture. Il est
ici **visible dans la donnée**. Sur 237 couples (dossier, article du texte)
présents dans plusieurs états du texte, **41 ont une intersection vide** : le même
numéro y désigne des articles du code entièrement différents.

D'où la règle retenue, **l'intersection sur au moins deux états** : la cible est
ce sur quoi tous les états du texte s'accordent. Un couple présent dans un seul
état ne fournit aucun recoupement et n'est pas retenu — 172 couples écartés à ce
titre. La variante permissive a été mesurée avant d'être écartée : accepter les
états uniques ajouterait 62 arêtes sur 18 articles historiques, en échange de la
perte du seul recoupement disponible. Le rapport ne le justifie pas.

Deux gardes indépendantes s'ajoutent : LEGI doit rattacher l'article au dossier,
et la section ne doit pas déjà porter une déclaration en en-tête — celle-là est
plus sûre et reste traitée par `rapports_vers_motive.py`.

## 4. Un défaut ancien, révélé par un usage nouveau

`ENTETE`, dans `commentaires_rapports.py`, ne capturait que le **nombre** :
« Article 18 bis » rendait `18`, donc le même identifiant que l'article 18. Tant
que `article_du_texte` n'était qu'une donnée d'affichage, la confusion restait
sans conséquence. Elle en a une dès qu'on s'en sert pour rattacher : elle
attribuait à l'article 18 ce qui commentait l'article 18 bis. La capture couvre
désormais l'ordinal et la lettre — 482 valeurs distinctes là où il y en avait une
poignée.

Le texte brut mettant chaque balise sur sa ligne, « Article 1<sup>er</sup> »
rendait `1\n \n er` : l'espacement est réduit à l'écriture, et le rapprochement se
fait sur une clef sans espaces ni casse, les deux corpus n'écrivant pas
« 1er », « 1 er » et « 10 bis A » de la même façon.

## 5. La précision se mesure sur la bonne preuve

Le premier tirage de vingt donnait **13 sur 20** — jugé sur les 175 premiers
caractères de la section. Sept cas paraissaient douteux : la section commentait
visiblement le code de la sécurité sociale, ou la loi de 1971 sur les professions
judiciaires, et se voyait attribuer un article du code de la consommation.

**Les sept étaient justes.** Vérification faite contre ce que `porte_sur` affirme,
l'article 11 quater B modifie bien le III de l'article L. 141-1 en plus du code de
la sécurité sociale ; l'article 19 quater insère bien L. 121-117, L. 121-118 et
L. 121-119 en plus de modifier le code de l'environnement ; l'article 58 complète
bien L. 132-2. Le tirage est **20 sur 20**. Borne inférieure de Wilson à 95 % :
**`CONFIANCE = 0,8389`**, mesurée de bout en bout — section, article du texte,
article du code.

**C'est la mesure qui était mal faite, pas l'arête.** Et cela révèle un défaut de
restitution réel : le passage montré est le début de la section, où le lien ne se
lit pas. La restitution le dit désormais explicitement — « rattaché parce que
cette section commente l'article N du texte, qui modifie cet article du code ; le
lien est structurel, le passage ci-dessous ne le nomme pas forcément » — et fait
passer les rattachements déclarés en en-tête avant ceux-ci.

## 6. Ce que la tranche ne fait pas

**Elle ne protège pas contre une lecture absente du corpus.** L'intersection ne
recoupe que les états du texte dont on dispose. Si le rapport commente une lecture
qu'aucun état chargé ne représente, rien ne le signale.

**Une section sur 105 est un compte rendu de séance**, non un commentaire :
« M. Hervé Maurey, rapporteur pour avis. - Favorable au n°281. » Le passage
pointé est bien la section que le rapport consacre à cet article du texte, mais
elle n'explique rien. Mesuré, une seule sur 105 — contre zéro sur 519 pour la
classe déclarée. Trop peu pour justifier un filtre, assez pour être écrit.

**Les 172 couples à état unique restent inexploités.** Charger d'autres états du
texte — notamment les textes déposés, absents pour les projets de loi
(`docs/16` § 6) — les rendrait recoupables.
