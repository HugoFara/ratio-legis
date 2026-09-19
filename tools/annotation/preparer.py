#!/usr/bin/env python3
"""Prépare le dossier de l'annotateur : fiches, documents en texte, fichier à remplir.

La phase 0 attend, pour 100 articles, **l'offset du passage qui motive l'article**
ou son absence (`docs/02` § 6). Personne ne compte des caractères à la main dans
un rapport de 1,5 million de signes ; ce que l'annotateur peut faire, c'est
lire, chercher, et désigner un passage par son début et sa fin. Les offsets sont
alors calculés — par `annoter.py` — sur le **même texte** que celui du graphe :
`texte_brut()` du fichier du corpus, dont `document.texte` en base est la copie
et `document.hash` l'empreinte. Un offset annoté et un offset de `motive` sont
ainsi comparables sans conversion, ce qui est la seule chose qui rende
l'annotation utile à la mesure (`verifier.py`).

Ce script écrit, dans un répertoire de travail non versionné :

    documents/<DOLE>__<fichier>.txt   le texte brut de chaque document du dossier
                                      de chaque article du jeu — celui qu'on cite
    fiches/<numéro>.txt               l'article en vigueur, ses documents, où ils
                                      le nomment, et la proposition de la machine
    documents.tsv                     l'index : fichier, type, taille, empreinte
    annotations-100.csv               le fichier à remplir, s'il n'existe pas déjà

La fiche porte **l'historique complet** de l'article : chaque texte qui a produit
une version de lui ou de l'un de ses anciens numéros, avec son dossier
législatif quand LEGI et DOLE le connaissent, et les documents que le corpus
détient pour ce dossier. Le jeu ne retenait qu'un dossier par article — celui du
lien `CREE` le plus ancien du prédécesseur —, ce qui laissait quinze articles
« sans document » alors que leur histoire passe par des lois dont le dossier
est dans le corpus. La recherche est exhaustive (décision du 19 septembre
2026, `docs/36` § 6) : elle part de tous les textes, pas du premier.

Il ne remplit rien : la proposition de `jeu_annotation.py` est copiée dans des
colonnes `proposition_*`, distinctes des colonnes `ANNOT_*` qui restent vides.
Un jeu qui confondrait les deux ne permettrait plus de mesurer ce que la
proposition valait — et c'est l'une des trois mesures attendues.

Les documents sont écrits en entier, mais hors dépôt (`travail/`) : les rapports
de commission n'ont pas de régime de rediffusion confirmé (`ATTRIBUTION.md`).

Usage :
    preparer.py <jeu-prerempli.csv> <base.sqlite> <corpus/rapports/> <destination/>
"""

from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "tools" / "prototype"))
sys.path.insert(0, str(RACINE / "ingestion"))
from commentaires_rapports import texte_brut   # noqa: E402
from rapports_vers_motive import type_document  # noqa: E402

CONTEXTE = 300      # signes montrés de part et d'autre d'une mention
MENTIONS_MAX = 12   # au-delà, la fiche renvoie au document lui-même
EXTRAIT = 400       # même plafond que la restitution (731a62e)

COLONNES = ["num_article", "strate", "id_legi", "texte_origine", "id_dole_origine",
            "proposition_document", "proposition_offset_debut",
            "proposition_offset_fin", "proposition_grain",
            "proposition_declaree_en_entete",
            "ANNOT_document", "ANNOT_offset_debut", "ANNOT_offset_fin",
            "ANNOT_passage_cite", "ANNOT_verdict", "ANNOT_commentaire",
            "proposition_jugee", "annotateur", "date", "dossiers"]

# Comment le fichier du corpus se lit, pour l'annotateur.
LIBELLES = {"expose_des_motifs": "exposé des motifs",
            "etude_impact": "étude d'impact",
            "avis_conseil_etat": "avis du Conseil d'État",
            "rapport_commission": "rapport de commission",
            "rapport_president_republique": "rapport au Président de la République"}


def nom_texte(nom: str) -> str:
    return nom if nom.endswith(".txt") else f"{nom}.txt"


def motif_article(numero: str) -> re.Pattern:
    """« L. 224-3 », « L.224-3 », « L224-3 » — jamais « L. 224-31 »."""
    lettre, reste = numero[0], numero[1:]
    return re.compile(rf"\b{lettre}\.?\s?{re.escape(reste)}(?![\d-])")


def mentions(texte: str, numeros: list[str]) -> list[int]:
    positions: set[int] = set()
    for numero in numeros:
        positions |= {m.start() for m in motif_article(numero).finditer(texte)}
    return sorted(positions)


def article_en_vigueur(base: sqlite3.Connection, numero: str) -> str:
    ligne = base.execute("""SELECT v.texte FROM version_en_vigueur v
                            JOIN article_courant a ON a.id = v.article_id
                            WHERE a.numero = ?
                            ORDER BY v.date_debut DESC, v.id_legi""", (numero,)).fetchone()
    return ligne[0] if ligne else "(aucune version en vigueur dans la base)"


def anciens_numeros(base: sqlite3.Connection, numero: str) -> list[str]:
    return [r[0] for r in base.execute("""
        WITH RECURSIVE asc_a(anc) AS (
            SELECT id FROM article_courant WHERE numero = ?
            UNION SELECT r.ancien_id FROM renumerote_de r JOIN asc_a ON r.article_id = asc_a.anc)
        SELECT DISTINCT a.numero FROM asc_a JOIN article a ON a.id = asc_a.anc
        WHERE a.numero <> ? ORDER BY a.numero""", (numero, numero))]


def historique(base: sqlite3.Connection, numero: str) -> list[dict]:
    """Chaque texte ayant produit une version de l'article ou de ses anciens numéros."""
    return [dict(r) for r in base.execute("""
        WITH RECURSIVE asc_a(anc) AS (
            SELECT id FROM article_courant WHERE numero = ?
            UNION SELECT r.ancien_id FROM renumerote_de r JOIN asc_a ON r.article_id = asc_a.anc)
        SELECT DISTINCT a.numero, v.date_debut, p.type_lien, t.titre, t.nature,
                        t.id_jorf, i.dossier_id, d.titre AS dossier_titre
        FROM asc_a JOIN article a ON a.id = asc_a.anc
        JOIN version_article v ON v.article_id = a.id
        JOIN produite_par p ON p.version_id = v.id_legi
        JOIN texte_normatif t ON t.id_jorf = p.texte_id
        LEFT JOIN issu_de i ON i.texte_id = t.id_jorf
        LEFT JOIN dossier d ON d.id_dole = i.dossier_id
        ORDER BY v.date_debut, a.numero""", (numero,))]


def aplatir(texte: str) -> str:
    return re.sub(r"\s+", " ", texte).strip()


def fiche(ligne: dict, texte_article: str, anciens: list[str],
          textes: list[dict], documents: list[tuple[str, str, str]]) -> str:
    """Le texte de la fiche ; `documents` : (nom, type, texte brut)."""
    numeros = [ligne["num_article"]] + anciens
    dossiers_du_corpus = {nom.split("__", 1)[0] for nom, _, _ in documents}
    parts = [f"ARTICLE {ligne['num_article']}  —  strate : {ligne['strate']}",
             f"texte producteur de la version en vigueur : "
             f"{ligne['texte_producteur_version_en_vigueur'] or '?'}",
             f"texte à l'origine : {ligne['texte_origine'] or '?'}"
             f"  ({ligne['nature_origine'] or '?'}, législature "
             f"{ligne['legislature_origine'] or '?'})",
             f"dossier DOLE : {ligne['id_dole_origine'] or 'aucun'}",
             f"numéros antérieurs (chaîne de renumérotation) : "
             f"{', '.join(anciens) or 'aucun'}",
             "", "TEXTE EN VIGUEUR", "-" * 72, texte_article.strip(), "", ]

    parts += ["HISTORIQUE — chaque texte qui a produit une version, du plus ancien "
              "au plus récent", "-" * 72]
    for t in textes:
        dossier = (f"dossier {t['dossier_id']}"
                   + (" — documents ci-dessous" if t["dossier_id"] in dossiers_du_corpus
                      else " — AUCUN document dans le corpus : "
                           f"https://www.vie-publique.fr/dossierlegislatif/{t['dossier_id']}")
                   if t["dossier_id"] else "pas de dossier législatif connu de DOLE")
        parts.append(f"{t['date_debut']}  {t['numero']:<10} {t['type_lien']:<13} "
                     f"{t['titre']}")
        parts.append(f"{'':12}{t['nature']}, https://www.legifrance.gouv.fr/jorf/id/"
                     f"{t['id_jorf']} ; {dossier}")
    if not textes:
        parts.append("aucun texte producteur dans LEGI")
    parts += ["", "Où chercher ce que le corpus n'a pas : le dossier sur "
              "vie-publique.fr ; les travaux préparatoires d'avant 2008 sur "
              "senat.fr/dossier-legislatif et archives.assemblee-nationale.fr ; "
              "le JO du texte sur Légifrance (exposé des motifs des ordonnances, "
              "rapport au Président) ; Wayback pour les pages disparues. "
              "Un document trouvé s'ajoute (`e` dans annoter.py, `importer` dans "
              "console.py) ; un dossier que le corpus a déjà se rattache "
              "(`rattacher` dans console.py).", ""]

    parts += ["DOCUMENTS DU CORPUS, tous dossiers de l'historique confondus", "-" * 72]
    if not documents:
        parts.append("aucun : la recherche est entièrement à faire, depuis "
                     "l'historique ci-dessus.")
    for rang, (nom, type_doc, texte) in enumerate(documents, 1):
        positions = mentions(texte, numeros)
        parts.append(f"[{rang}] {nom}")
        parts.append(f"    {LIBELLES.get(type_doc, type_doc)}, {len(texte):,} signes, "
                     f"{len(positions)} mention(s) de l'article ou de ses anciens numéros"
                     .replace(",", " "))
        for position in positions[:MENTIONS_MAX]:
            debut = max(0, position - CONTEXTE)
            extrait = aplatir(texte[debut:position + CONTEXTE])
            parts.append(f"    @{position}: …{extrait}…")
        if len(positions) > MENTIONS_MAX:
            parts.append(f"    (+ {len(positions) - MENTIONS_MAX} mentions, "
                         f"voir documents/{nom_texte(nom)})")
        parts.append("")

    parts += ["PROPOSITION DE LA MACHINE", "-" * 72]
    if ligne["ANNOT_document"]:
        texte = next((t for n, _, t in documents if n == ligne["ANNOT_document"]), "")
        debut, fin = int(ligne["ANNOT_offset_debut"]), int(ligne["ANNOT_offset_fin"])
        parts += [f"document : {ligne['ANNOT_document']}  offsets {debut}–{fin}",
                  f"source : {ligne['source_proposee']}, grain « "
                  f"{ligne['grain_du_rattachement']} », article nommé en en-tête : "
                  f"{'oui' if ligne['source_declaree_en_entete'] == '1' else 'non'}",
                  "", aplatir(texte[debut:fin])[:3000] if texte else
                  "(document absent du corpus)", ""]
        if fin - debut > 3000:
            parts.append(f"(… section de {fin - debut} signes, tronquée ici)")
    else:
        parts.append("aucune — la machine n'a rien trouvé qui nomme cet article ; "
                     "le verdict attendu est peut-être « non_documente », mais "
                     "seulement après avoir cherché.")
    parts += ["", "VERDICTS POSSIBLES", "-" * 72,
              "motive              un passage explique pourquoi CET article dit ceci",
              "dossier_seulement   un document motive le texte ou le dispositif, "
              "pas cet article",
              "non_documente       aucun document ne motive L'ORIGINE du dispositif "
              "(le texte qui l'a écrit ; une recodification à droit constant n'est pas "
              "l'origine), après recherche exhaustive — résultat de premier ordre",
              "", "Décisions du 19 septembre 2026 (docs/36 § 6) :",
              "  - un rapport au Président qui ne nomme pas l'article vaut "
              "dossier_seulement, sauf passage consacré au dispositif ;",
              "  - non_documente ne se rend qu'après avoir suivi chaque texte de "
              "l'historique ; écrire dans le commentaire ce qui a été consulté.",
              "", "Au clavier : python3 tools/annotation/annoter.py <ce répertoire> "
              "--annotateur <initiales>",
              "En commandes : python3 tools/annotation/console.py <ce répertoire> …",
              "Protocole : tools/annotation/CONSIGNES.md"]
    return "\n".join(parts) + "\n"


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    jeu, base_chemin, corpus, destination = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(f"file:{base_chemin}?mode=ro", uri=True)
    base.row_factory = sqlite3.Row
    (destination / "documents").mkdir(parents=True, exist_ok=True)
    (destination / "fiches").mkdir(exist_ok=True)

    lignes = list(csv.DictReader(jeu.open(encoding="utf-8")))
    histoires = {l["num_article"]: historique(base, l["num_article"]) for l in lignes}
    dossiers_par_article = {
        numero: sorted({d for d in [ligne["id_dole_origine"]]
                        + [t["dossier_id"] for t in histoires[numero]] if d})
        for ligne in lignes for numero in [ligne["num_article"]]}
    dossiers = sorted(set().union(*dossiers_par_article.values()))

    textes: dict[str, str] = {}
    index: list[tuple[str, str, str, int, str]] = []
    for dossier in dossiers:
        for fichier in sorted(corpus.glob(f"{dossier}__*")):
            if fichier.name.endswith(("#", "_rapport-fond")):
                continue        # page de garde, sans corps — voir telecharger_rapports.sh
            texte = texte_brut(fichier)
            if len(texte) < 2000:
                continue        # page d'index ou erreur, pas un document
            textes[fichier.name] = texte
            (destination / "documents" / nom_texte(fichier.name)).write_text(
                texte, encoding="utf-8", newline="")   # « \r » conservés : offsets
            index.append((dossier, fichier.name, type_document(fichier.name),
                          len(texte), hashlib.sha256(texte.encode()).hexdigest()))

    with (destination / "documents.tsv").open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["dossier", "fichier", "type", "signes", "sha256", "url"])
        ecrivain.writerows([*i, ""] for i in index)

    sans_document = 0
    for ligne in lignes:
        numero = ligne["num_article"]
        ordre = {d: i for i, d in enumerate(dossiers_par_article[numero])}
        documents = sorted(((nom, type_document(nom), texte) for nom, texte in textes.items()
                            if nom.split("__", 1)[0] in ordre),
                           key=lambda d: (ordre[d[0].split("__", 1)[0]], d[0]))
        sans_document += not documents
        (destination / "fiches" / f"{numero}.txt").write_text(
            fiche(ligne, article_en_vigueur(base, numero),
                  anciens_numeros(base, numero), histoires[numero], documents),
            encoding="utf-8")

    annotations = destination / "annotations-100.csv"
    if annotations.exists():
        # Les verdicts restent ; la liste des dossiers consultables suit la base.
        # Sans cela, après la scission des lignées, `fiche` et `documents` ne
        # montraient plus le même historique — vu par un annotateur.
        with annotations.open(encoding="utf-8", newline="") as f:
            existantes = list(csv.DictReader(f))
        for ligne in existantes:
            ligne["dossiers"] = " ".join(dossiers_par_article.get(ligne["num_article"], []))
        provisoire = annotations.with_suffix(".csv.tmp")
        with provisoire.open("w", encoding="utf-8", newline="") as f:
            ecrivain = csv.DictWriter(f, fieldnames=COLONNES)
            ecrivain.writeheader()
            ecrivain.writerows(existantes)
        provisoire.replace(annotations)
    else:
        with annotations.open("w", encoding="utf-8", newline="") as f:
            ecrivain = csv.DictWriter(f, fieldnames=COLONNES)
            ecrivain.writeheader()
            for ligne in lignes:
                ecrivain.writerow({
                    "num_article": ligne["num_article"], "strate": ligne["strate"],
                    "id_legi": ligne["id_legi"], "texte_origine": ligne["texte_origine"],
                    "id_dole_origine": ligne["id_dole_origine"],
                    "proposition_document": ligne["ANNOT_document"],
                    "proposition_offset_debut": ligne["ANNOT_offset_debut"],
                    "proposition_offset_fin": ligne["ANNOT_offset_fin"],
                    "proposition_grain": ligne["grain_du_rattachement"],
                    "proposition_declaree_en_entete": ligne["source_declaree_en_entete"],
                    **{c: "" for c in COLONNES if c.startswith("ANNOT_")},
                    "proposition_jugee": "", "annotateur": "", "date": "",
                    "dossiers": " ".join(dossiers_par_article[ligne["num_article"]])})

    print(f"articles                : {len(lignes)}")
    print(f"dossiers                : {len(dossiers)}")
    print(f"documents en texte      : {len(index)}")
    print(f"articles sans document  : {sans_document}")
    print(f"fichier à remplir       : {annotations}"
          + ("" if annotations.stat().st_size else " (créé)"))


if __name__ == "__main__":
    main()
