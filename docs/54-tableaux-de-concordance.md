# Quarante-huitième tranche — les tableaux de concordance, et deux gardes qu'on n'a pas posées

**Objet :** le lien européen au grain de l'article, que le README donnait
pour « seul chemin connu » : les tableaux de concordance annexés aux études
d'impact. En amont, deux essais de garde sur `resulte_de`, mesurés et
abandonnés, et les fiches de mesure qui montrent désormais au juge l'article
dans la version que la loi du dossier a écrite.
**Date : 24 septembre 2026.**
**Code :** `ingestion/concordances.py` (nouveau), `schema/012-concordances.sql`
(nouveau), `tools/mesures/precision_concordances.py` (nouveau),
`tools/mesures/precision_porte_sur.py`, `tools/mesures/precision_vise.py`,
`tools/mesures/precision_depose_sur.py`, `tools/mesures/rejouer.py`,
`tools/mesures/juger.py`, `tools/mesures/grain.py`, `pipeline.sh`.
**Données :** `precision-concordances.tsv`.

---

## 1. `resulte_de` : deux gardes essayées, aucune posée

Les cinq dernières fausses `resulte_de` (`docs/50`, `docs/53`) sont trois
formules administratives partagées par un passage destiné ailleurs, une
rédaction non retenue, un alinéa attribué au mauvais amendement du dossier.
Trois règles ont été mesurées sur les 299 arêtes jugées, sans être posées.

| règle | fausses retirées | justes retirées |
|---|---:|---:|
| seuil sur le nombre de fenêtres communes, ou sur la part du segment couverte | — | des justes n'ont qu'une fenêtre, des fausses en ont huit |
| l'alinéa doit être dans un article que `depose_sur` donne à l'amendement | 0 | 7 |
| l'article de l'alinéa doit être du même chapitre que ce que gouverne l'alinéa du texte cité | 2 | 18 |

La deuxième ne voit pas la fausse de l'amendement 447, qui n'a pas de
`depose_sur` ; elle retire des articles créés à côté de la cible
(L. 121-34-1 sous l'instruction de L. 121-34). La troisième confond la
numérotation de 2014 et celle de 2016 : L. 334-5 gouverne dans le texte un
alinéa devenu L. 332-5-2. La cause est comprise — l'amendement 447 écrit
dans « l'alinéa 29 », sous L. 141-1, et une fenêtre commune le relie à
L. 218-5-5 — mais aucune règle simple ne la sépare des justes.

## 2. Les fiches montrent la version du dossier

`docs/51` § 7 : la fiche d'une `depose_sur` montrait le premier état de la
lignée de l'article, non celui que le texte de l'amendement réécrivait. Les
fiches `vise` et `depose_sur` montrent désormais la version que la loi du
dossier a produite et celle qu'elle a remplacée ; à défaut, la version en
vigueur à la date de la loi. Le préfixe « L111-5 (date de la lignée) » est
gardé : le harnais y lit la lignée montrée. La fiche `porte_sur` garde le
premier état, par choix — il sert à voir qu'un hôte a dérivé.

## 3. Les tableaux de concordance

**Ce qu'ils sont.** Quand un projet de loi transpose une directive, son
étude d'impact annexe un tableau : une ligne par disposition de la
directive, en face l'article du droit interne. Neuf études d'impact et un
avis du corpus en portent ; trois touchent le code de la consommation, deux pour des actes
présents en base — la directive 2011/83/UE (loi consommation, 2013) et la
directive (UE) 2020/1828 (2024).

**Pourquoi le texte ne suffit pas.** L'extraction en texte du PDF aplatit les
colonnes : les articles de la directive, puis ceux du code, sans la ligne qui
les appariait. `concordances.py` relit la page avec la position de chaque
bloc. Une ligne commence à l'ancre d'un article de l'acte, dans la colonne
de l'acte, et court jusqu'à la suivante ; les articles du code écrits **en
tête** d'une cellule de cette ligne sont ceux que le tableau met en face.
Le tableau de 2013 est tourné d'un quart de tour — la ligne se lit en
abscisse — ; celui de 2024 est droit. Le sens des lignes de texte, que le
PDF porte, dit lequel.

**Les gardes de lecture**, chacune née d'un défaut vu sur ces deux tableaux :

- le tableau commence à un titre **en haut de page** et s'arrête à l'annexe
  suivante — le corps de l'étude cite « tableau de concordance » ailleurs ;
- seuls les numéros en tête de cellule comptent — les citations du droit
  existant et les commentaires en nomment d'autres ;
- une cellule qui s'ouvre sur un guillemet est une citation ;
- notre code seul : la cellule le nomme, ou l'en-tête de colonne le nomme et
  la cellule n'en nomme pas un autre — le tableau de 2024 mêle le code de
  justice administrative et le code de la santé publique ;
- l'article de l'acte doit exister dans l'acte : « Article 3 1) » lu « 31 »
  dans une directive qui en compte 26 ;
- les numéros sont ceux du projet de loi — l'étude de 2013 le dit en note —
  et se résolvent à la date du dossier.

| | |
|---|---:|
| lignes de tableau lues | 44 |
| article de l'acte inconnu | 1 |
| numéro absent du fonds (articles remplacés depuis) | 8 |
| **arêtes `transpose_article`** | **33** |
| dont directive 2011/83/UE | 20, 17 articles du code |
| dont directive (UE) 2020/1828 | 13, 9 articles du code |

**Mesuré sur la population entière.** Deux juges Sonnet 5, colonnes
séparées, qui ont relu chaque ligne sur la page rendue : **33 sur 33**,
d'accord partout. Wilson 0,8957.

Au grain de l'article, **35 articles en vigueur** sont reliés à un article
d'acte de l'Union par un tableau — la chaîne de renumérotation porte
L. 121-16 de 2014 jusqu'à ses héritiers de 2016. C'est peu à côté des 117
qui nomment un acte eux-mêmes ; ce sont d'autres articles, et le lien est
plus fin : non « cet article cite la directive », mais « cet article est
l'article 6 de la directive ».

La fiche d'un article la montre (`restitution/graphe.py`) : « transpose
l'article 6 de la directive 2011/83/UE », la page de l'étude d'impact, le
numéro du projet de loi, la confiance, et le lien de signalement. L. 221-5,
l'ancien L. 121-17, en est l'exemple.

## 4. Ce qui n'est pas fait

**Les autres tableaux.** Sept études d'impact portent des tableaux pour des
actes absents de `acte_ue` ou pour d'autres codes ; les rapports de
commission en reproduisent parfois. Les actes de l'Union ne sont chargés que
s'ils sont cités par un article du fonds.

**Les mailles de `porte_sur` (`docs/47` § 5)** : le plan propre hors
glissement ne touche que `vise`, mesurée 20 sur 20 en `docs/53` ; les 124
articles écrits non résolus ne produisent aucune arête fausse, et les
résoudre au numéro voisin sans preuve de contenu est ce que `docs/47`
refuse ; la navette entière demande de charger chaque lecture. Aucune n'est
entreprise.
