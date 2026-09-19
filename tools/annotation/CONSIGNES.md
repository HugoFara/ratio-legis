# Consignes d'annotation — un article, un verdict, un passage

Tu annotes **un article** du code de la consommation : dire s'il existe, dans
les travaux préparatoires, un passage qui explique pourquoi *cet article* dit
ce qu'il dit — et le désigner au caractère près. Tu ne crées aucune arête, tu
n'interprètes pas le droit : tu dis où la raison est écrite, ou qu'elle ne
l'est pas. « Non documenté » est un résultat de premier ordre, pas un échec.

Tout passe par une commande, jamais par le clavier :

    C="python3 tools/annotation/console.py travail/annotation"

## 1. Lire

    $C fiche <article>

La fiche donne : le texte en vigueur ; **l'historique** — chaque texte qui a
produit une version de l'article ou de l'un de ses anciens numéros, avec son
dossier législatif et ce que le corpus en détient ; les documents de tous ces
dossiers, numérotés, avec **chaque mention** de l'article et 300 signes de
contexte ; la proposition de la machine ; les verdicts possibles.

    $C documents <article>          les documents, numérotés — ce sont les n ci-dessous
    $C mentions <article> <n>       chaque mention de l'article dans le document n
    $C chercher <article> <n> mots  occurrences de « mots » dans le document n
    $C lire <article> <n> <offset> [longueur]   le texte lui-même, autour d'un offset

## 2. Les trois verdicts

| verdict | quand |
|---|---|
| `motive` | un passage explique **cet article** — son dispositif, pas le texte entier. Il faut le désigner. |
| `dossier_seulement` | un document motive le texte ou le dispositif d'ensemble, pas cet article. Le désigner si un passage s'en approche, sinon reprendre le document proposé. |
| `non_documente` | rien, **après recherche exhaustive** (§ 4). |

## 3. Deux règles fixées le 19 septembre 2026, à appliquer sans exception

1. **Un rapport au Président de la République qui ne nomme pas l'article vaut
   `dossier_seulement`**, sauf s'il consacre un passage au dispositif de
   l'article — alors `motive`, avec ce passage.
2. **La recherche est exhaustive.** Le dossier d'origine du jeu est une
   convention (le texte qui a *créé* l'article, un saut). L'historique de la
   fiche liste **tous** les textes ; pour un article recodifié en 2016, la
   raison est presque toujours dans le rapport d'une loi antérieure, sous
   l'**ancien numéro** (la fiche les donne, `mentions` les cherche). On ne rend
   `non_documente` qu'après avoir suivi chaque texte de l'historique.

## 4. Chercher hors corpus

Quand un dossier de l'historique est marqué « AUCUN document dans le corpus »,
la fiche donne le lien vie-publique du dossier et le lien Légifrance du texte.
Si tu peux y récupérer un document (rapport de commission, exposé des motifs,
étude d'impact, rapport au Président), enregistre-le d'abord sur disque, puis :

    $C importer <article> <chemin> --url <URL d'origine>

Il devient le document numéro n suivant, citable comme les autres. Un document
trouvé hors corpus est compté à part par la mesure : c'est un **trou du
corpus**, distinct d'un silence du fonds — c'est une donnée en soi.

## 5. Rendre le verdict

    $C rendre <article> --annotateur agent:<modèle> --verdict motive \
        --document <n> --debut "premiers mots du passage" --fin "derniers mots" \
        --commentaire "…"

`--debut` et `--fin` sont copiés du document, assez longs pour n'y figurer
**qu'une fois** — sinon la commande refuse et le dit. Elle rend les offsets
calculés et le passage retenu : relis-le, c'est ce qui sera cité.

    $C rendre <article> --annotateur agent:<modèle> --verdict dossier_seulement \
        --proposition acceptee --commentaire "…"

reprend le document proposé tel quel (`--proposition hors_sujet` s'il n'a rien
à voir, ou `--document/--debut/--fin` pour en désigner un autre).

    $C rendre <article> --annotateur agent:<modèle> --verdict non_documente \
        --commentaire "consulté : …"

Le **commentaire est obligatoire de fait** : il dit si le passage motive
l'article ou seulement le dispositif d'ensemble, et pour `non_documente`, la
liste de ce qui a été consulté (documents du corpus, dossiers vie-publique,
Wayback). C'est ce qu'un relecteur humain lira en premier.

## 6. Ce qu'on ne fait pas

- **On n'accepte pas la proposition par défaut.** Elle vient d'une machine qui
  cherche un numéro d'article dans un rapport ; elle peut être hors sujet, et
  tu dois pouvoir le dire (`--proposition hors_sujet`).
- **On ne désigne pas un passage qui ne parle pas de l'article.** Un lien faux
  coûte plus que dix liens manquants (règle § 5.3 du projet).
- **On ne tronque pas la recherche** pour rendre `non_documente` plus vite.
- **On ne réécrit pas un verdict existant** sans raison : `etat` montre qui a
  déjà rendu quoi ; `rendre` avertit et remplace.
- **On se nomme `agent:<modèle>`** dans `--annotateur`, jamais autrement. Les
  verdicts d'agents sont ventilés à part par `verifier.py` ; ils ne valent pas
  l'évaluation humaine en aveugle qu'exige la phase 3 du projet, et personne ne
  doit pouvoir les confondre avec elle.

## 7. Où en est-on

    $C etat --strate <strate> --a-faire

Les strates : `origine_ordonnance`, `eligible_L12_L15`, `eligible_L16_L17`,
`loi_hors_open_data`, `reclassement_reglementaire`, `sans_origine`.
