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
    rapports_vers_motive.py <corpus/rapports> <perimetre.csv> <plan.tsv> <base.sqlite>
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
        a, b, c = m.groups()
        trouves.setdefault(f"L{a}-{b}" + (f"-{c}" if c else ""), (m.start(), m.end()))
    return [(numero, d, f) for numero, (d, f) in trouves.items()]


def fenetre_preuve(texte: str, debut: int, fin: int) -> str | None:
    """Fenêtre citable autour d'une mention, ou None si elle ne prouve rien."""
    marge = max(0, (200 - (fin - debut)) // 2)
    extrait = re.sub(r"\s+", " ", texte[max(0, debut - marge):fin + marge]).strip()
    return extrait if len(extrait) >= FENETRE_MINI else None


def type_document(nom: str) -> str:
    return ("rapport_president_republique" if "rapport-pr" in nom
            else "rapport_commission")


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


def rattachements_legi(perimetre: Path) -> tuple[dict[str, set[str]], dict[str, str],
                                                 dict[str, int | None]]:
    """Ce que LEGI déclare : article → dossiers, dossier → titre du texte.

    Le numéro d'avant recodification est retenu au même titre que le numéro
    actuel : un rapport de 2013 nomme L121-105, jamais L224-65.
    """
    articles: dict[str, set[str]] = defaultdict(set)
    titres: dict[str, str] = {}
    legislatures: dict[str, int | None] = {}
    for ligne in csv.DictReader(perimetre.open(encoding="utf-8")):
        dossier = ligne["id_dole_origine"]
        if not dossier:
            continue
        titres.setdefault(dossier, ligne["texte_origine"])
        legislatures.setdefault(dossier, int(ligne["legislature_origine"])
                                if ligne["legislature_origine"].isdigit() else None)
        for cle in (ligne["num_article"], ligne["article_predecesseur"]):
            if cle:
                articles[cle.replace(" ", "")].add(dossier)
    return articles, titres, legislatures


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    dossier_rapports, perimetre, plan, chemin_base = (Path(a) for a in sys.argv[1:])

    legi, titres, legislatures = rattachements_legi(perimetre)
    liens = urls_du_plan(plan)

    base = sqlite3.connect(chemin_base)
    base.execute("PRAGMA foreign_keys = ON")
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
    ids_articles = {n: i for i, n in base.execute("SELECT id, numero FROM article")}
    par_titre = {t: c for c, t in base.execute(
        "SELECT id_jorf, titre FROM texte_normatif")}
    prochaine_preuve = base.execute(
        "SELECT coalesce(max(id), 0) + 1 FROM preuve").fetchone()[0]

    # ------------------------------------------------------- dossiers et textes
    base.executemany(
        "INSERT OR IGNORE INTO dossier (id_dole, titre, legislature) VALUES (?, ?, ?)",
        [(d, titres[d], legislatures[d]) for d in sorted(titres)])
    issu_de = [(par_titre[titres[d]], d) for d in sorted(titres)
               if titres[d] in par_titre]
    base.executemany(
        "INSERT OR IGNORE INTO issu_de (texte_id, dossier_id) VALUES (?, ?)", issu_de)

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
        url = liens.get(fichier.name) or url_rapport_pr(fichier.name)
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
        return c["dossier"] in legi.get(c["numero"], ())

    # Le dénominateur est restreint aux citations qui désignent un article de ce
    # code. Rapporté à toutes les citations, le taux ne mesurerait rien
    # d'exploitable : un rapport cite des centaines d'articles d'autres codes, et
    # le résultat — 7,9 % — décrirait la composition du corpus, pas la fiabilité
    # d'une arête. La question posée est : le rapporteur nommant un article de ce
    # code dans le commentaire d'un dossier, LEGI rattache-t-il cet article à ce
    # dossier ?
    connus = [c for c in candidats if c["numero"] in ids_articles]
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
        article_id = ids_articles.get(c["numero"])
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
    print(f"arêtes issu_de             : {len(issu_de)}")
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
