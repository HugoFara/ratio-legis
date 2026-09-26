#!/usr/bin/env python3
"""Deuxième tranche : les rapports de commission deviennent des arêtes `motive`.

La première tranche (`legi_vers_graphe.py`) a chargé le *comment* : quel texte a
produit quelle version, quel alinéa reprend quel alinéa. Elle ne dit rien du
*pourquoi*. Cette tranche charge la seule source du corpus qui commente le droit
article par article — le rapport de commission — et produit l'arête `motive`,
avec les offsets du passage qui motive chaque article.

Deux règles de la feuille de route commandent la conception.

**§ 5.6 — un LLM ne décide jamais d'une arête, et la topologie vient de LEGI.**
La citation d'un numéro d'article par un rapporteur est une déclaration
éditoriale, pas un lien de provenance : sur la loi de 2014, rapporteurs et LEGI
ne déclarent que 130 articles en commun sur 241 et 280 respectivement. Une arête
`motive` n'est donc écrite que pour un couple (article, dossier) que **LEGI
rattache déjà**. Le rapport apporte la raison, jamais la topologie. Ce n'est pas
circulaire : la topologie n'est pas ce qu'on cherche à établir ici.

**§ 5.3 — précision avant rappel.** Seules les citations de la **parenthèse
d'en-tête** produisent une arête. Un contrôle à la main d'arêtes tirées au sort
donne 20/20 pour l'en-tête déclaré contre 5/14 pour la citation au fil du corps. Les neuf échecs ont deux causes : des
numéros identiques dans d'autres codes — L. 221-3 du code de la route, L. 123-6
du code de l'environnement, L. 721-5 du code de la propriété intellectuelle —
et des sections dont la fin déborde sur l'article suivant. La corroboration par
LEGI ne les rattrape pas : elle vérifie que *ce numéro* vient de ce dossier, pas
qu'il désigne le bon code. D'où la seconde condition : la parenthèse doit nommer
le code de la consommation.

**§ 5.4 — la confiance est une donnée.** La valeur écrite est la borne inférieure
de Wilson à 95 % de la précision mesurée à la main sur la version courante de
l'extraction, soit 0,839 pour 20 succès sur 20. Écrire 1,0 serait surestimer ce que ces vérifications établissent ; la
borne inférieure se resserrera d'elle-même quand l'annotation humaine en cours
élargira l'échantillon.

Les offsets de `motive` délimitent le commentaire à afficher ; la preuve porte la
fenêtre plus étroite où l'article est nommé. Les deux sont nécessaires : la
première sert la restitution, la seconde sert le contrôle.

Usage :
    rapports_vers_motive.py <corpus/rapports> <perimetre.csv> <plan.tsv>
                            <base.sqlite> [plan-impacts.tsv]
"""

from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "prototype"))
from commentaires_rapports import ARTICLE, PLAGE, commentaires, texte_brut  # noqa: E402
from lignees import Resolveur  # noqa: E402

FENETRE_MINI = 60          # longueur minimale d'une preuve, imposée par le schéma


def mentions(fragment: str) -> list[tuple[str, int, int]]:
    """Numéros d'articles cités, avec leur position dans le fragment.

    `numeros_cites` du module de phase 0 rend un ensemble, ce qui suffisait à
    mesurer une couverture. Ici il faut la position : sans elle, aucune preuve
    ne peut être extraite et l'arête serait refusée à l'écriture.
    """
    trouves: dict[str, tuple[int, int]] = {}
    for m in PLAGE.finditer(fragment):
        livre_d, debut, livre_f, fin = m.groups()
        if livre_d == livre_f and int(fin) - int(debut) < 40:
            for n in range(int(debut), int(fin) + 1):
                trouves.setdefault(f"L{livre_d}-{n}", (m.start(), m.end()))
    for m in ARTICLE.finditer(fragment):
        a, b, c, d = m.groups()
        trouves.setdefault(f"L{a}-{b}" + "".join(f"-{x}" for x in (c, d) if x),
                           (m.start(), m.end()))
    return [(numero, d, f) for numero, (d, f) in trouves.items()]


def fenetre_preuve(texte: str, debut: int, fin: int) -> str | None:
    """Fenêtre citable autour d'une mention, ou None si elle ne prouve rien."""
    marge = max(0, (200 - (fin - debut)) // 2)
    extrait = re.sub(r"\s+", " ", texte[max(0, debut - marge):fin + marge]).strip()
    return extrait if len(extrait) >= FENETRE_MINI else None


MARQUEURS = (("expose-motifs", "expose_des_motifs"),
             ("etude-impact", "etude_impact"),
             ("avis-ce", "avis_conseil_etat"),
             ("rapport-pr", "rapport_president_republique"))


RAPPORT_DYN_AN = re.compile(
    r"https?://www\.assemblee-nationale\.fr/dyn/(\d+)/rapports/[^/]+/l\d+b(\d+)_rapport-fond$")


def type_document(nom: str) -> str:
    """Le type se lit dans le nom du fichier, posé par l'outil qui l'a écrit."""
    for marqueur, type_document in MARQUEURS:
        if marqueur in nom:
            return type_document
    return "rapport_commission"


def urls_du_plan(plan: Path) -> dict[str, str]:
    """Nom de fichier local → URL d'origine.

    Le plan ne liste que les pages d'index du Sénat ; la version `_mono.html`,
    seule à porter le texte, s'en déduit mécaniquement. Sans cette
    reconstruction, deux tiers des rapports du Sénat entreraient en base sans
    URL, donc sans citation résoluble.
    """
    liens: dict[str, str] = {}
    for ligne in plan.read_text(encoding="utf-8").splitlines():
        if "\t" not in ligne:
            continue
        dossier, url = ligne.split("\t", 1)
        nom = url.rsplit("/", 1)[-1]
        liens[f"{dossier}__{nom}"] = url
        if "senat.fr/rap/" in url and nom.endswith(".html"):
            liens[f"{dossier}__{nom[:-5]}_mono.html"] = f"{url[:-5]}_mono.html"
        # Même situation à l'Assemblée depuis la XVIe législature : le plan pointe
        # une page de garde, le texte est sous /dyn/opendata/ (voir
        # `telecharger_rapports.sh`, qui applique la même règle).
        integral = RAPPORT_DYN_AN.match(url.split("#", 1)[0])
        if integral:
            nom = f"RAPPANR5L{integral.group(1)}B{integral.group(2)}.html"
            liens[f"{dossier}__{nom}"] = \
                f"https://www.assemblee-nationale.fr/dyn/opendata/{nom}"
    return liens


def url_rapport_pr(nom: str) -> str | None:
    """URL Légifrance d'un rapport au Président de la République.

    Ces rapports ne figurent pas au plan des rapports de commission : une
    ordonnance n'en a pas. Ils seraient donc écartés faute d'URL — et avec eux la
    seule motivation qui existe pour les ordonnances, dont le fonds compte trois
    des recodifications du périmètre. Leur identifiant JORF est dans le nom du
    fichier ; l'URL s'en déduit.
    """
    trouve = re.search(r"(JORFTEXT\d+)", nom)
    return (f"https://www.legifrance.gouv.fr/jorf/id/{trouve.group(1)}"
            if trouve and "rapport-pr" in nom else None)


def urls_des_impacts(plan: Path | None) -> dict[str, str]:
    """Nom de fichier local → URL du PDF, pour les études d'impact et avis.

    Ces documents n'ont pas de page propre : leur seule adresse est celle du PDF
    servi par le chemin média de Légifrance. Sans elle, ils entreraient sans
    citation résoluble, et le § 4.3 les écarterait.
    """
    if plan is None or not plan.exists():
        return {}
    noms = {"etude_impact": "etude-impact", "avis_conseil_etat": "avis-ce"}
    liens = {}
    for ligne in csv.DictReader(plan.open(encoding="utf-8"), delimiter="\t"):
        liens[f"{ligne['dossier']}__{noms[ligne['type']]}-{ligne['rang']}.txt"] = \
            ligne["url"]
    return liens


def url_dossier(nom: str) -> str | None:
    """URL d'un exposé des motifs, qui n'a pas d'adresse propre.

    L'exposé n'est pas un document publié à part : il est une balise du dossier
    DOLE. Sa citation résout donc sur la page du dossier — et celle-ci n'est plus
    sur Légifrance, qui redirige les dossiers législatifs vers vie-publique.fr.
    """
    trouve = re.search(r"(JORFDOLE\d+)", nom)
    return (f"https://www.vie-publique.fr/dossierlegislatif/{trouve.group(1)}"
            if trouve and "expose-motifs" in nom else None)


def rattachements_legi(base: sqlite3.Connection) -> tuple[dict[int, set[str]], dict[str, str],
                                                          dict[str, int | None]]:
    """Ce que LEGI et DOLE déclarent : article → dossiers, dossier → titre, législature.

    Lu dans la base, non dans le périmètre. Le périmètre ne porte qu'un dossier
    par article — celui du texte qui a créé le prédécesseur — et le corpus s'y
    était aligné : 94 dossiers de textes ayant **modifié** un article en vigueur
    n'y figuraient pas, et leurs rapports n'auraient de toute façon pas été
    retenus ici, « dossier hors périmètre ». La base sait mieux : `produite_par`
    dit quel texte a produit chaque version, `issu_de` le dossier du texte.

    Clé par identifiant de lignée, non par numéro : un rapport de 2010 nommant
    L313-10 est corroboré par le dossier de 2010 pour la lignée du cautionnement,
    et par rien pour celle de la fiche standardisée. Chaque lignée porte les
    dossiers de ses propres versions plus ceux de ses ancêtres renumérotés.
    """
    articles: dict[int, set[str]] = defaultdict(set)
    for article_id, dossier in base.execute("""
        WITH RECURSIVE asc_a(art, anc) AS (
            SELECT id, id FROM article
            UNION SELECT a.art, r.ancien_id FROM renumerote_de r JOIN asc_a a
            ON r.article_id = a.anc)
        SELECT DISTINCT a.art, i.dossier_id FROM asc_a a
        JOIN version_article v ON v.article_id = a.anc
        JOIN produite_par p    ON p.version_id = v.id_legi
        JOIN issu_de i         ON i.texte_id = p.texte_id"""):
        articles[article_id].add(dossier)
    # Une lignée close par une arrivée — « l'article L. 311-14 devient l'article
    # L. 311-20 », que LEGI écrit comme une modification — est touchée par la loi
    # qui la renumérote, bien que cette loi n'en produise aucune version : elle
    # produit ce qu'elle devient. Sans cela, la section du rapport qui commente
    # la renumérotation n'était plus corroborée depuis la scission (docs/59 § 2).
    for article_id, dossier in base.execute("""
        SELECT r.ancien_id, i.dossier_id FROM renumerote_de r
        JOIN article a ON a.id = r.ancien_id
        JOIN version_article v ON v.article_id = r.article_id
        JOIN produite_par p    ON p.version_id = v.id_legi
        JOIN issu_de i         ON i.texte_id = p.texte_id
        WHERE v.date_debut = (SELECT min(date_debut) FROM version_article
                              WHERE article_id = r.article_id)
          AND EXISTS (SELECT 1 FROM article b
                      WHERE b.numero = a.numero AND b.lignee = a.lignee + 1)
          AND (SELECT etat FROM version_article WHERE article_id = a.id
               ORDER BY date_debut DESC LIMIT 1) = 'MODIFIE'"""):
        articles[article_id].add(dossier)
    titres: dict[str, str] = {}
    legislatures: dict[str, int | None] = {}
    for dossier, titre, legislature in base.execute(
            "SELECT id_dole, titre, legislature FROM dossier"):
        titres[dossier] = titre
        legislatures[dossier] = legislature
    return articles, titres, legislatures


def main() -> None:
    if not 5 <= len(sys.argv) <= 6:
        sys.exit(__doc__)
    dossier_rapports, perimetre, plan, chemin_base = (Path(a) for a in sys.argv[1:5])
    plan_impacts = Path(sys.argv[5]) if len(sys.argv) == 6 else None

    liens = urls_du_plan(plan) | urls_des_impacts(plan_impacts)

    base = sqlite3.connect(chemin_base)
    base.execute("PRAGMA foreign_keys = ON")
    legi, titres, legislatures = rattachements_legi(base)
    resolveur = Resolveur(base)
    # Reconstruction, non complément : les documents portent des identifiants
    # explicites et une seconde exécution entrait sinon en collision. Le même
    # défaut avait laissé en base des arêtes `resulte_de` à l'ancienne confiance.
    # L'ordre compte : les preuves sont référencées par les arêtes, et les arêtes
    # par les documents. La clef étrangère refuse l'inverse — c'est elle qui l'a
    # signalé, et c'est ce qu'on lui demande.
    anciennes = [i for (i,) in base.execute(
        "SELECT preuve_id FROM motive WHERE preuve_id IS NOT NULL")]
    base.execute("DELETE FROM motive")
    base.execute("DELETE FROM document")
    base.executemany("DELETE FROM preuve WHERE id = ?", [(i,) for i in anciennes])
    prochaine_preuve = base.execute(
        "SELECT coalesce(max(id), 0) + 1 FROM preuve").fetchone()[0]
    # Dossiers et `issu_de` sont désormais écrits par `dossiers_des_textes.py`,
    # avant le périmètre ; cette tranche les lit, elle ne les fabrique plus.

    # ------------------------------------------------ documents et candidatures
    documents, candidats, sans_url = [], [], 0
    for fichier in sorted(dossier_rapports.iterdir()):
        if "__" not in fichier.name:
            continue
        if (fichier.parent / f"{fichier.stem}_mono.html").exists():
            # Page d'index d'un rapport paginé du Sénat. Elle porte le sommaire,
            # non le commentaire : ses « sections » sont des lignes de table des
            # matières, qui nomment les bons articles mais n'expliquent rien. Le
            # texte est dans la version `_mono`, chargée à côté.
            continue
        dossier = fichier.name.split("__", 1)[0]
        if dossier not in titres:
            continue          # dossier hors périmètre : rien à motiver
        url = (liens.get(fichier.name) or url_rapport_pr(fichier.name)
               or url_dossier(fichier.name))
        if not url:
            sans_url += 1
            continue          # § 4.3 : pas de citation résoluble, pas de document
        texte = texte_brut(fichier)
        identifiant = len(documents) + 1
        documents.append((identifiant, dossier, type_document(fichier.name), url,
                          texte, hashlib.sha256(texte.encode()).hexdigest(),
                          datetime.fromtimestamp(fichier.stat().st_mtime,
                                                 timezone.utc).date().isoformat()))
        try:
            sections = commentaires(fichier)
        except Exception:
            continue
        for section in sections:
            debut, fin = section["offset_debut"], section["offset_fin"]
            corps = texte[debut:fin]
            paren = re.search(r"\(([^)]{10,400})\)", re.sub(r"\s+", " ", corps[:260]))
            # La parenthèse doit nommer le code : « L. 221-3 » existe aussi au code
            # de la route, et LEGI corrobore alors le mauvais article sans rien
            # signaler. C'est l'erreur de confusion de cible déjà rencontrée sur le
            # golden set de phase 0.
            declaration = paren.group(1) if paren and "consommation" in paren.group(1).lower() else ""
            for numero, md, mf in mentions(corps):
                candidats.append({
                    "document": identifiant, "dossier": dossier, "numero": numero,
                    "article_id": resolveur.du_dossier(numero, dossier),
                    "article_du_texte": section["article_du_texte"],
                    "offset_debut": debut, "offset_fin": fin,
                    "mention": (debut + md, debut + mf),
                    "en_tete": numero in {n for n, _, _ in mentions(declaration)},
                })

    base.executemany(
        "INSERT INTO document (id, dossier_id, type, url, texte, hash, "
        "date_recuperation) VALUES (?, ?, ?, ?, ?, ?, ?)", documents)

    # -------------------------------------------- confiance mesurée, non choisie
    def corrobore(c: dict) -> bool:
        return c["dossier"] in legi.get(c["article_id"], ())

    # Le dénominateur est restreint aux citations qui désignent un article de ce
    # code. Rapporté à toutes les citations, le taux ne mesurerait rien
    # d'exploitable : un rapport cite des centaines d'articles d'autres codes, et
    # le résultat — 7,9 % — décrirait la composition du corpus, pas la fiabilité
    # d'une arête. La question posée est : le rapporteur nommant un article de ce
    # code dans le commentaire d'un dossier, LEGI rattache-t-il cet article à ce
    # dossier ?
    connus = [c for c in candidats if c["article_id"] is not None]
    taux = {}
    for classe in (True, False):
        groupe = [c for c in connus if c["en_tete"] is classe]
        taux[classe] = (sum(map(corrobore, groupe)) / len(groupe)) if groupe else 0.0
    # Précision mesurée à la main sur 20 arêtes de la classe retenue : 20/20.
    # Borne inférieure de Wilson à 95 % — voir l'en-tête de module.
    CONFIANCE = 0.8389

    # ----------------------------------------------------------- arêtes motive
    aretes, preuves, sans_preuve = [], [], 0
    vus: set[tuple[int, int]] = set()
    for c in candidats:
        article_id = c["article_id"]
        if article_id is None or not c["en_tete"] or not corrobore(c):
            continue
        if (c["document"], article_id) in vus:
            continue
        texte = documents[c["document"] - 1][4]
        extrait = fenetre_preuve(texte, *c["mention"])
        if extrait is None:
            sans_preuve += 1
            continue
        vus.add((c["document"], article_id))
        preuves.append((prochaine_preuve, "citation_dans_un_rapport", extrait,
                        c["mention"][0], None))
        aretes.append((c["document"], article_id, c["article_du_texte"],
                       c["offset_debut"], c["offset_fin"], "derivee", CONFIANCE,
                       prochaine_preuve))
        prochaine_preuve += 1

    base.executemany(
        "INSERT INTO preuve (id, methode, fenetre, source_offset, cible_offset) "
        "VALUES (?, ?, ?, ?, ?)", preuves)
    base.executemany(
        "INSERT INTO motive (document_id, article_id, article_du_texte, offset_debut,"
        " offset_fin, methode, confiance, preuve_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        aretes)
    base.commit()

    violations = base.execute("PRAGMA foreign_key_check").fetchall()
    orphelines = base.execute(
        "SELECT count(*) FROM motive WHERE methode <> 'declaree' AND preuve_id IS NULL"
    ).fetchone()[0]
    couverts = base.execute(
        "SELECT count(DISTINCT article_id) FROM motive").fetchone()[0]
    eligibles = sum(1 for l in csv.DictReader(perimetre.open(encoding="utf-8"))
                    if l["eligible_resulte_de"] == "1")

    print(f"documents chargés          : {len(documents)}")
    print(f"  sans URL, écartés        : {sans_url}")
    print(f"dossiers                   : {len(titres)}")
    print(f"\ncitations d'article candidates : {len(candidats)}")
    print(f"  désignant un article de ce code : {len(connus)}")
    print(f"    déclarées en en-tête   : {sum(1 for c in connus if c['en_tete'])} "
          f"(corroborées par LEGI : {100 * taux[True]:.1f} %)")
    print(f"    citées dans le corps   : {sum(1 for c in connus if not c['en_tete'])} "
          f"(corroborées par LEGI : {100 * taux[False]:.1f} %)")
    print(f"\narêtes motive (en-tête déclaré uniquement) : {len(aretes)}")
    print(f"  écartées faute de preuve : {sans_preuve}")
    print(f"articles du code motivés   : {couverts} "
          f"({100 * couverts / eligibles:.1f} % des {eligibles} éligibles)")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère, "
          f"{orphelines} arête(s) dérivée(s) sans preuve")
    base.close()


if __name__ == "__main__":
    main()
