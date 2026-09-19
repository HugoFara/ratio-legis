#!/usr/bin/env python3
"""Annoter les 100 articles du jeu, article par article, sans compter un offset.

L'annotateur désigne un passage par **son début et sa fin** — quelques mots
copiés du document, assez pour être uniques. L'outil les retrouve dans le texte
brut, calcule les offsets, montre le passage obtenu et demande confirmation.
Les offsets sont ceux de `texte_brut()`, donc ceux de `document.texte` en base :
c'est ce qui rend l'annotation comparable aux arêtes `motive` (`verifier.py`).

Le fichier `annotations-100.csv` est réécrit après chaque article : on peut
s'arrêter et reprendre, et rien n'est perdu sur une coupure. Un article déjà
annoté n'est pas représenté, sauf `--reprendre <numéro>`.

La recherche est exhaustive (décision du 19 septembre 2026) : la fiche donne
chaque texte de l'historique de l'article, et ce que le corpus n'a pas se
cherche ailleurs. Un document trouvé s'importe avec `e` ; il est converti en
texte brut par la même fonction que le corpus, indexé sous le dossier
`externe:<article>`, et `verifier.py` le signalera comme absent de la base —
ce qui distingue un silence du fonds d'un trou du corpus.

Ce que l'outil ne fait pas, délibérément :

  - il ne propose pas la proposition de la machine comme réponse par défaut. Elle
    est affichée, et l'annotateur doit dire ce qu'il en fait (`proposition_jugee`) ;
    un défaut silencieux transformerait l'annotation en approbation ;
  - il ne cherche pas à la place de l'annotateur. `v` montre les mentions de
    l'article dans un document, `g` y cherche une chaîne : ce sont des aides à
    la lecture, pas des réponses.

Commandes, une fois la fiche affichée :

    a           accepter la proposition telle quelle → verdict `motive`
    p           désigner un passage : document, début, fin → verdict `motive`
    d           `dossier_seulement` — un document motive le texte, pas l'article
                (le passage est facultatif ; il est demandé)
    n           `non_documente` — rien trouvé, après recherche exhaustive
    e <chemin>  ajouter un document trouvé hors corpus (html, txt ou pdf, déjà
                téléchargé) ; son URL est demandée, il devient choisissable
    v <n>       voir toutes les mentions de l'article dans le document n
    g <n> <mots> chercher <mots> dans le document n
    f           réafficher la fiche
    s           passer, sans annoter
    q           quitter

Usage :
    annoter.py <répertoire préparé par preparer.py> --annotateur <initiales>
               [--strate <strate>] [--reprendre <numéro>]

`--strate` restreint la session à une strate du jeu — `origine_ordonnance`,
`eligible_L12_L15`, … — pour annoter par population homogène, la même règle en
tête d'un bout à l'autre.
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "prototype"))
from preparer import COLONNES, aplatir, mentions, nom_texte  # noqa: E402
from commentaires_rapports import texte_brut  # noqa: E402

EXTRAIT = 400        # plafond des extraits versionnés, comme partout ailleurs
CONTEXTE = 300
JUGEMENTS = {"a": "acceptee", "p": "corrigee", "d": "hors_sujet", "n": "hors_sujet"}


class Fin(Exception):
    """L'annotateur a demandé à quitter."""


def demander(invite: str) -> str:
    try:
        reponse = input(invite).strip()
    except EOFError:
        raise Fin from None
    if reponse == "q":
        raise Fin
    return reponse


def documents_de(ligne: dict, repertoire: Path) -> list[tuple[str, str]]:
    """(nom du fichier, texte brut), dans l'ordre de la fiche, externes à la fin."""
    dossiers = set(ligne["dossiers"].split()) | {f"externe:{ligne['num_article']}"}
    docs = []
    with (repertoire / "documents.tsv").open(encoding="utf-8") as f:
        for entree in csv.DictReader(f, delimiter="\t"):
            if entree["dossier"] in dossiers:
                # newline="" : sans lui, Python replie les « \r\n » des pages des
                # chambres en « \n », et chaque offset calculé ici serait décalé
                # de tout ce qui précède par rapport à `document.texte` en base.
                texte = (repertoire / "documents" / nom_texte(entree["fichier"])).read_text(
                    encoding="utf-8", newline="")
                docs.append((entree["fichier"], texte))
    return docs


def convertir(source: Path) -> str | None:
    """Texte brut d'un document trouvé hors corpus (html, txt ou pdf), ou None."""
    if not source.is_file():
        print(f"  fichier introuvable : {source}")
        return None
    if source.suffix.lower() == ".pdf":
        try:
            import fitz  # pymupdf, la seule dépendance du projet
        except ImportError:
            print("  pymupdf est requis pour un PDF (pip install -e .)")
            return None
        with fitz.open(source) as document:
            texte = "\n".join(page.get_text() for page in document)
        texte = re.sub(r"\n{3,}", "\n\n", "\n".join(l.rstrip() for l in texte.split("\n"))).strip()
    else:
        texte = texte_brut(source)
    if len(texte) < 200:
        print(f"  {len(texte)} signes seulement : ce n'est pas un document")
        return None
    return texte


def indexer(texte: str, source: Path, url: str, ligne: dict, repertoire: Path) -> str:
    """Écrit le document sous `externe:<article>` et rend son nom."""
    nom = f"externe__{ligne['num_article']}__{source.name}"
    (repertoire / "documents" / nom_texte(nom)).write_text(texte, encoding="utf-8",
                                                           newline="")
    with (repertoire / "documents.tsv").open("a", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t", lineterminator="\n").writerow(
            [f"externe:{ligne['num_article']}", nom, "externe", len(texte),
             hashlib.sha256(texte.encode()).hexdigest(), url])
    return nom


def importer(chemin: str, ligne: dict, repertoire: Path) -> str | None:
    """Convertit un document trouvé hors corpus et l'indexe ; rend son nom."""
    source = Path(chemin).expanduser()
    texte = convertir(source)
    if texte is None:
        return None
    url = demander("  URL d'où vient ce document (citation résoluble) : ")
    nom = indexer(texte, source, url, ligne, repertoire)
    print(f"  ajouté : {nom} ({len(texte)} signes)")
    return nom


def choisir_document(docs: list[tuple[str, str]], defaut: str = "") -> tuple[str, str] | None:
    defaut = defaut if any(d[0] == defaut for d in docs) else ""
    while True:
        reponse = demander(f"  document [1-{len(docs)}]"
                           f"{' (entrée = ' + defaut + ')' if defaut else ''} : ")
        if not reponse and defaut:
            return next(d for d in docs if d[0] == defaut)
        if reponse.isdigit() and 1 <= int(reponse) <= len(docs):
            return docs[int(reponse) - 1]
        print("  numéro de document attendu")


def localiser(texte: str, fragment: str, apres: int = 0) -> tuple[int, int] | None:
    """Bornes de l'occurrence unique de `fragment` (espaces normalisés), ou None."""
    if not fragment:
        return None
    motif = re.compile(r"\s+".join(re.escape(m) for m in fragment.split()))
    trouves = [(m.start(), m.end()) for m in motif.finditer(texte, apres)]
    if len(trouves) == 1:
        return trouves[0]
    print(f"  {len(trouves)} occurrences — il en faut exactement une ; allongez le "
          "fragment" if trouves else "  fragment introuvable")
    return None


def designer_passage(docs: list[tuple[str, str]], defaut: str = "") -> tuple[str, int, int] | None:
    """(document, offset_debut, offset_fin), désignés par leurs bords."""
    choix = choisir_document(docs, defaut)
    if not choix:
        return None
    nom, texte = choix
    while True:
        bornes = localiser(texte, demander("  premiers mots du passage : "))
        if bornes is None:
            continue
        debut = bornes[0]
        bornes = localiser(texte, demander("  derniers mots du passage : "), debut)
        if bornes is None:
            continue
        fin = bornes[1]
        print(f"\n  [{debut}–{fin}] {aplatir(texte[debut:fin])[:1200]}\n")
        if demander("  c'est ce passage ? [o/n] : ").lower() in ("o", "oui", ""):
            return nom, debut, fin


def montrer_mentions(docs: list[tuple[str, str]], n: str, numeros: list[str]) -> None:
    if not n.isdigit() or not 1 <= int(n) <= len(docs):
        print("  numéro de document attendu")
        return
    nom, texte = docs[int(n) - 1]
    positions = mentions(texte, numeros)
    print(f"  {nom} : {len(positions)} mention(s)")
    for position in positions:
        print(f"  @{position}: …{aplatir(texte[max(0, position - CONTEXTE):position + CONTEXTE])}…\n")


def chercher(docs: list[tuple[str, str]], n: str, mots: str) -> None:
    if not n.isdigit() or not 1 <= int(n) <= len(docs):
        print("  numéro de document attendu")
        return
    nom, texte = docs[int(n) - 1]
    motif = re.compile(r"\s+".join(re.escape(m) for m in mots.split()), re.I)
    trouves = [m.start() for m in motif.finditer(texte)]
    print(f"  {nom} : {len(trouves)} occurrence(s) de « {mots} »")
    for position in trouves[:20]:
        print(f"  @{position}: …{aplatir(texte[max(0, position - CONTEXTE):position + CONTEXTE])}…\n")


def annoter(ligne: dict, repertoire: Path, annotateur: str) -> bool:
    """Remplit les colonnes ANNOT_* de `ligne` ; False si l'article est passé."""
    fiche = (repertoire / "fiches" / f"{ligne['num_article']}.txt").read_text(encoding="utf-8")
    docs = documents_de(ligne, repertoire)
    numeros = [ligne["num_article"]] + re.findall(
        r"[LRD]\d+-[\d-]+", fiche.split("numéros antérieurs", 1)[1].split("\n", 1)[0])
    print("\n" + "=" * 72 + "\n" + fiche)

    while True:
        commande = demander(f"[{ligne['num_article']}] a/p/d/n/v/g/f/s/q > ")
        verbe, _, reste = commande.partition(" ")
        if verbe == "s":
            return False
        if verbe == "f":
            print(fiche)
            continue
        if verbe == "v":
            montrer_mentions(docs, reste, numeros)
            continue
        if verbe == "g":
            n, _, mots = reste.partition(" ")
            chercher(docs, n, mots)
            continue
        if verbe == "e":
            if importer(reste, ligne, repertoire):
                docs = documents_de(ligne, repertoire)
                for rang, (nom, texte) in enumerate(docs, 1):
                    if nom.startswith("externe__"):
                        print(f"  [{rang}] {nom}, {len(texte)} signes")
            continue
        if verbe not in JUGEMENTS:
            continue

        passage: tuple[str, int, int] | None = None
        if verbe == "a":
            if not ligne["proposition_document"]:
                print("  aucune proposition à accepter")
                continue
            passage = (ligne["proposition_document"],
                       int(ligne["proposition_offset_debut"]),
                       int(ligne["proposition_offset_fin"]))
        elif verbe == "d" and ligne["proposition_document"] and demander(
                "  reprendre le document proposé, tel quel ? [o/n] : ").lower() in ("o", "oui"):
            passage = (ligne["proposition_document"],
                       int(ligne["proposition_offset_debut"]),
                       int(ligne["proposition_offset_fin"]))
        elif verbe == "p" or (verbe == "d" and docs and
                              demander("  désigner un passage ? [o/n] : ").lower()
                              in ("o", "oui")):
            passage = designer_passage(docs, ligne["proposition_document"])
            if not passage:
                continue

        verdict = {"a": "motive", "p": "motive", "d": "dossier_seulement",
                   "n": "non_documente"}[verbe]
        commentaire = demander("  commentaire (le passage motive-t-il l'article, ou "
                               "le dispositif d'ensemble ?) : ")
        enregistrer(ligne, docs, verdict, passage, commentaire, annotateur,
                    JUGEMENTS[verbe])
        return True


def enregistrer(ligne: dict, docs: list[tuple[str, str]], verdict: str,
                passage: tuple[str, int, int] | None, commentaire: str,
                annotateur: str, jugement: str) -> None:
    """Écrit le verdict dans la ligne. `jugement` : ce que l'annotateur fait de la
    proposition ; corrigé en « acceptee » si le passage désigné est la proposition
    même, en « aucune » s'il n'y avait rien à juger."""
    if not ligne["proposition_document"]:
        jugement = "aucune"
    elif passage and passage[0] == ligne["proposition_document"] \
            and passage[1] == int(ligne["proposition_offset_debut"]) \
            and passage[2] == int(ligne["proposition_offset_fin"]):
        jugement = "acceptee"
    ligne.update({"ANNOT_verdict": verdict, "ANNOT_commentaire": commentaire,
                  "proposition_jugee": jugement, "annotateur": annotateur,
                  "date": date.today().isoformat(),
                  "ANNOT_document": "", "ANNOT_offset_debut": "",
                  "ANNOT_offset_fin": "", "ANNOT_passage_cite": ""})
    if passage:
        nom, debut, fin = passage
        texte = next(t for n, t in docs if n == nom)
        ligne.update({"ANNOT_document": nom, "ANNOT_offset_debut": debut,
                      "ANNOT_offset_fin": fin,
                      "ANNOT_passage_cite": aplatir(texte[debut:fin])[:EXTRAIT]})


def sauver(lignes: list[dict], chemin: Path) -> None:
    provisoire = chemin.with_suffix(".csv.tmp")
    with provisoire.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES)
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    provisoire.replace(chemin)


def main() -> None:
    args = sys.argv[1:]
    if not args or "--annotateur" not in args:
        sys.exit(__doc__)
    repertoire = Path(args[0])
    annotateur = args[args.index("--annotateur") + 1]
    reprendre = args[args.index("--reprendre") + 1] if "--reprendre" in args else None
    strate = args[args.index("--strate") + 1] if "--strate" in args else None

    chemin = repertoire / "annotations-100.csv"
    lignes = list(csv.DictReader(chemin.open(encoding="utf-8")))
    a_faire = [l for l in lignes
               if (not l["ANNOT_verdict"] or l["num_article"] == reprendre)
               and (strate is None or l["strate"] == strate)]
    print(f"{sum(bool(l['ANNOT_verdict']) for l in lignes)} annoté(s), "
          f"{len(a_faire)} à faire" + (f" dans la strate {strate}" if strate else ""))

    faits = 0
    try:
        for ligne in a_faire:
            if annoter(ligne, repertoire, annotateur):
                sauver(lignes, chemin)
                faits += 1
    except Fin:
        pass
    print(f"\n{faits} article(s) annoté(s) cette session, "
          f"{sum(1 for l in lignes if not l['ANNOT_verdict'])} restant(s) — {chemin}")


if __name__ == "__main__":
    main()
