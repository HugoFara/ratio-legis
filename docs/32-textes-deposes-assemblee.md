# Vingt-sixième tranche — les textes déposés de l'Assemblée

**Objet :** charger le texte déposé d'un projet de loi, que DOLE ne lie pas, en
passant par le numéro de dépôt de la chambre. **Date : 25 août 2026.**
**Code :** `tools/an/plan_textes_deposes.py`.

---

## 1. Ce que DOLE ne lie pas

Le `<ARBORESCENCE>` d'un dossier DOLE lie le rapport, le texte de la commission
et le texte adopté. Il ne lie pas le **texte déposé** d'un projet de loi.
`docs/15` § 5 l'avait constaté sans en sortir : aucun des dossiers ayant une étude
d'impact n'a de texte déposé dans le corpus, parce que DOLE ne lie ce texte que
pour les propositions de loi, qui n'ont jamais d'étude d'impact.

C'est le chaînon qui manquait à deux chantiers. L'étude d'impact chiffre les
articles du **texte déposé** ; et les amendements de l'Assemblée portent une
référence — `B1015`, `BTC2442` — qui désigne un document de la chambre, non un
lien DOLE.

## 2. Le numéro se lit dans le rapport, il ne se devine pas

Le rapport de commission nomme le texte qu'il rapporte, dès son titre :

> N° 2145 — Rapport de Mme Sophie Errante sur le projet de loi, après engagement
> de la procédure accélérée, relatif à la simplification de la vie des
> entreprises **(n° 2060)**

La convention distingue les deux séries — projet de loi, proposition de loi —, et
c'est elle qui décide de la rubrique de l'URL : `/projets/pl…` ou
`/propositions/pion…`. La législature vient de `dossier.legislature`, renseignée
pour les 199 dossiers du périmètre. Le numéro est cadré sur quatre chiffres :
`/17/projets/pl0529.asp` répond, `pl529.asp` non.

**Le plan est une hypothèse ; le téléchargement est sa vérification.** Un couple
(législature, numéro) faux rend 404 et rien n'est écrit. Sur les 55 textes
déposés relevés, **55 ont été servis** — la lecture du rapport ne s'est trompée
aucune fois.

Un second contrôle suit au chargement, celui de `docs/31` § 3 : les subdivisions
des amendements doivent tomber dans la plage d'articles du texte. 3 842 sur
3 922, soit 98,0 %.

## 3. Deux erreurs silencieuses, et c'est le vrai sujet de la tranche

**`BTC?` n'est pas `B(?:TC)?`.** La première expression se lit « un B, puis un T,
puis un C facultatif » : elle reconnaît `BTC1156` et **jamais** `B1247`. Elle
était écrite ainsi à deux endroits — dans le relevé des numéros et dans la
correspondance des identifiants de la tranche précédente.

Conséquence : les 13 jeux d'amendements de l'Assemblée que `docs/31` § 3 donnait
pour « non appariés, faute d'un document de la bonne série dans le corpus »
n'étaient pas un trou de corpus. C'était une faute de lecture, et l'explication
publiée était fausse. **L'Assemblée passe de 26 jeux appariés sur 39 à 39 sur
39.**

L'erreur ne produisait aucun message : une expression rationnelle qui ne
reconnaît rien rend une liste vide, et une liste vide se traite comme une absence
de donnée. C'est le troisième défaut de cette famille dans le projet, après le
chemin d'archive de `docs/10` § 4 et le bloc de style de `docs/30` § 3.

**Le premier lien PDF d'une page n'est pas le document.** Toutes les pages de
l'Assemblée portent en pied un lien vers leur déclaration d'accessibilité, et sur
les textes de commission de la XIVe législature servis par l'application `dyn`,
c'est le **seul** PDF déclaré. `telecharger_textes.py` prenait le premier venu :
**23 fichiers de 110 324 octets chacun, tous identiques, tous la déclaration
d'accessibilité**, écrits dans le corpus à la place des textes. Le chargement n'y
trouvait aucun article, et ne le signalait pas — un texte à zéro article est
indiscernable d'un texte qui ne modifie rien.

Le document se déclare pourtant par une relation vérifiable : **son URL est celle
de la page suivie de `.pdf`**. C'est cette relation qui est désormais exigée ;
aucun lien qui la vérifie, aucun fichier écrit. Un échec nommé vaut mieux qu'un
faux document dans le corpus.

Les 23 fichiers ont été supprimés et la voie corrigée : les textes de commission
de la XIVe législature sont servis en entier par la forme historique
`/14/ta-commission/r{numéro}-a0.asp`. C'est celle que DOLE emploie déjà pour ceux
qu'il lie, si bien que 25 des 79 documents relevés se sont révélés être des
doublons du plan DOLE et ont été écartés — le plan final en compte 54, dont 53
textes déposés et un seul texte de commission qui manquait vraiment.

## 4. Ce que la tranche rapporte, mesuré

| | avant | après |
|---|---:|---:|
| textes en discussion chargés | 371 | **424** |
| dont Assemblée | 197 | **250** |
| arêtes `porte_sur` | 30 337 | **33 772** |
| dont internes au code | 2 546 | **2 860** |
| articles en vigueur reliés à un article de texte | 812 | **819** |
| jeux d'amendements de l'Assemblée appariés | 26 / 39 | **39 / 39** |
| arêtes `depose_sur` | 618 | **637** |

**Le gain se voit surtout dans le verdict.** Le texte déposé est un **état de
plus** du texte, et `sections_vers_motive.py` exige que les états s'accordent :
212 couples (dossier, article du texte) sont désormais exploitables contre 201, et
43 sont écartés pour contradiction entre états contre 41. Les arêtes `motive`
baissent de 639 à 634 — moins nombreuses, mieux corroborées — mais la partie
législative gagne **douze articles** qui passent d'« origine située » à « un
passage les motive » :

| partie L | avant | après |
|---|---:|---:|
| un passage les motive | 696 | **708** |
| origine située seulement | 177 | 168 |
| motivation du texte seule | 415 | 412 |
| raison non documentée | 5 | 5 |

## 5. Ce que la tranche ne débloque pas, et c'est ce qu'on venait chercher

**L'étude d'impact reste au grain du texte.** Zéro arête `motive` en vient, avant
comme après. Le texte déposé était nécessaire, il n'est pas suffisant.

La cause est ailleurs, et elle est mesurable. `sections_vers_motive.py` découpe un
document en commentaires d'article selon la convention du **rapport de
commission** : un repère « EXAMEN DES ARTICLES », un en-tête déclarant les
dispositions visées ou suivi d'un titre, et un plancher de 800 caractères qui
écarte les lignes de sommaire. Une étude d'impact n'a aucune de ces marques, et
elle n'en a pas de commune :

| étude d'impact | en-têtes « Article N » en début de ligne |
|---|---:|
| loi de modernisation agricole (2010) | 4 |
| loi sur le marché de l'électricité (2010) | 2 |
| loi DDADUE (2013) | 359 |
| loi de séparation bancaire (2013) | 0 |

De 0 à 359 sur quatre documents : il n'y a pas de convention à suivre, il y a un
découpeur à écrire, et il devra être mesuré comme l'a été celui des rapports.
C'est une tranche à part entière, et elle ne dépendait pas de celle-ci — ce qui
est en soi le renseignement : **le chaînon manquant n'était pas celui qu'on
croyait.**

## 6. Ce que la tranche ne fait pas

**42 rapports ne nomment aucun numéro.** Ce sont les coquilles JavaScript de
l'application `dyn`, dont la page ne porte ni le titre développé ni la première
page du rapport. Les dossiers récents — onze de ceux qui ont une étude d'impact —
restent donc sans texte déposé.

**Un texte de commission reste introuvable**, `r2964-a0` pour la loi sur
l'économie bleue : son annexe ne porte pas le rang 0. Il est déclaré en échec
plutôt que remplacé par une approximation.

**Huit jeux du Sénat sur 75 restent non appariés**, inchangés : il leur manque un
document dans le corpus, et cette tranche n'a rien fait pour eux.
