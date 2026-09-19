#!/usr/bin/env python3
"""L'annotation en commandes, une par appel, sans clavier.

`annoter.py` est une session : une fiche, un dialogue, un verdict. Ce module
expose les mêmes gestes en commandes indépendantes, pour qu'un annotateur qui
ne tient pas un terminal — un agent, ou plusieurs en parallèle, chacun sur un
article — puisse lire, chercher, désigner un passage et rendre un verdict, avec
exactement les mêmes garanties : offsets calculés sur le texte brut du corpus,
occurrence unique exigée pour un fragment, proposition jamais reprise en
silence, passage cité plafonné à 400 signes.

Ce que le fichier enregistre en plus, pour cet usage : la colonne `annotateur`
dit qui a rendu le verdict. Un agent s'y nomme `agent:<modèle>` ; `verifier.py`
ventile par annotateur, de sorte qu'un jugement de machine ne se confonde
jamais avec un jugement humain dans les chiffres. La règle du README tient : la
phase 3 exige une évaluation humaine en aveugle, et un agent ne l'est pas.

Plusieurs appels peuvent écrire en même temps : chaque écriture prend un verrou
sur le répertoire, relit le fichier, modifie sa ligne, réécrit. Deux agents sur
deux articles ne se voient pas ; deux agents sur le même article, le second
écrase le premier, et `etat` le dit.

Commandes (toutes précédées du répertoire préparé par `preparer.py`) :

    etat [--strate S] [--a-faire]          où en est le jeu, ligne par ligne
    fiche <article>                        la fiche, telle que l'annotateur la lit
    documents <article>                    les documents numérotés, avec leur taille
    mentions <article> <n>                 chaque mention de l'article dans le document n
    chercher <article> <n> <mots…>         occurrences de <mots> dans le document n
    lire <article> <n> <offset> [longueur] un extrait du document n, à l'offset donné
    importer <article> <chemin> --url URL  un document trouvé hors corpus
    rendre <article> --annotateur A --verdict V [--document n --debut "mots" --fin "mots"]
                                           [--commentaire "…"] [--proposition acceptee|corrigee|hors_sujet]
    rendre <article> --annotateur A --verdict V --proposition acceptee
                                           reprendre le passage proposé tel quel

`--verdict` : motive | dossier_seulement | non_documente. Un `motive` sans
passage est refusé : le protocole exige l'offset. `--debut` et `--fin` sont
les premiers et derniers mots du passage, copiés du document ; la commande
rend les offsets calculés et le passage, ou l'erreur qui a empêché de le situer.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import re
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from annoter import (CONTEXTE, aplatir, convertir, documents_de,  # noqa: E402
                     enregistrer, indexer, localiser, mentions, sauver)

VERDICTS = ("motive", "dossier_seulement", "non_documente")
JUGEMENTS = ("acceptee", "corrigee", "hors_sujet")


@contextmanager
def verrou(repertoire: Path):
    with (repertoire / ".verrou").open("w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def charger(repertoire: Path) -> list[dict]:
    with (repertoire / "annotations-100.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ligne_de(lignes: list[dict], article: str) -> dict:
    for ligne in lignes:
        if ligne["num_article"] == article:
            return ligne
    sys.exit(f"article inconnu du jeu : {article}")


def document_n(docs: list[tuple[str, str]], n: int) -> tuple[str, str]:
    if not 1 <= n <= len(docs):
        sys.exit(f"document {n} : il y en a {len(docs)}, numérotés de 1 à {len(docs)}")
    return docs[n - 1]


def numeros_de(ligne: dict, repertoire: Path) -> list[str]:
    fiche = (repertoire / "fiches" / f"{ligne['num_article']}.txt").read_text(encoding="utf-8")
    return [ligne["num_article"]] + re.findall(
        r"[LRD]\d+-[\d-]+", fiche.split("numéros antérieurs", 1)[1].split("\n", 1)[0])


# ------------------------------------------------------------------ commandes

def cmd_etat(a) -> None:
    lignes = charger(a.repertoire)
    for l in lignes:
        if a.strate and l["strate"] != a.strate:
            continue
        if a.a_faire and l["ANNOT_verdict"]:
            continue
        print(f"{l['num_article']:<12} {l['strate']:<26} "
              f"{l['ANNOT_verdict'] or '—':<18} {l['annotateur'] or '':<16} "
              f"{'proposition' if l['proposition_document'] else ''}")
    faits = sum(bool(l["ANNOT_verdict"]) for l in lignes)
    print(f"\n{faits} annoté(s), {len(lignes) - faits} à faire")


def cmd_fiche(a) -> None:
    print((a.repertoire / "fiches" / f"{a.article}.txt").read_text(encoding="utf-8"))


def cmd_documents(a) -> None:
    ligne = ligne_de(charger(a.repertoire), a.article)
    for rang, (nom, texte) in enumerate(documents_de(ligne, a.repertoire), 1):
        marque = "  ← proposition" if nom == ligne["proposition_document"] else ""
        print(f"[{rang}] {nom}  {len(texte)} signes{marque}")


def cmd_mentions(a) -> None:
    ligne = ligne_de(charger(a.repertoire), a.article)
    nom, texte = document_n(documents_de(ligne, a.repertoire), a.n)
    positions = mentions(texte, numeros_de(ligne, a.repertoire))
    print(f"{nom} : {len(positions)} mention(s)")
    for position in positions:
        print(f"@{position}: …{aplatir(texte[max(0, position - CONTEXTE):position + CONTEXTE])}…\n")


def cmd_chercher(a) -> None:
    ligne = ligne_de(charger(a.repertoire), a.article)
    nom, texte = document_n(documents_de(ligne, a.repertoire), a.n)
    mots = " ".join(a.mots)
    motif = re.compile(r"\s+".join(re.escape(m) for m in mots.split()), re.I)
    trouves = [m.start() for m in motif.finditer(texte)]
    print(f"{nom} : {len(trouves)} occurrence(s) de « {mots} »")
    for position in trouves[:a.max]:
        print(f"@{position}: …{aplatir(texte[max(0, position - CONTEXTE):position + CONTEXTE])}…\n")


def cmd_lire(a) -> None:
    ligne = ligne_de(charger(a.repertoire), a.article)
    nom, texte = document_n(documents_de(ligne, a.repertoire), a.n)
    fin = min(len(texte), a.offset + a.longueur)
    print(f"{nom} [{a.offset}–{fin}] sur {len(texte)}\n")
    print(texte[a.offset:fin])


def cmd_importer(a) -> None:
    source = Path(a.chemin).expanduser()
    texte = convertir(source)
    if texte is None:
        sys.exit(1)
    with verrou(a.repertoire):
        ligne = ligne_de(charger(a.repertoire), a.article)
        nom = indexer(texte, source, a.url, ligne, a.repertoire)
    docs = documents_de(ligne, a.repertoire)
    rang = next(i for i, (n, _) in enumerate(docs, 1) if n == nom)
    print(f"ajouté : [{rang}] {nom} ({len(texte)} signes)")


def cmd_rendre(a) -> None:
    if a.verdict not in VERDICTS:
        sys.exit(f"verdict attendu : {', '.join(VERDICTS)}")
    with verrou(a.repertoire):
        lignes = charger(a.repertoire)
        ligne = ligne_de(lignes, a.article)
        docs = documents_de(ligne, a.repertoire)
        passage = None
        if a.proposition == "acceptee" and not a.debut:
            if not ligne["proposition_document"]:
                sys.exit("aucune proposition à reprendre pour cet article")
            passage = (ligne["proposition_document"],
                       int(ligne["proposition_offset_debut"]),
                       int(ligne["proposition_offset_fin"]))
        elif a.debut or a.fin or a.document:
            if not (a.document and a.debut and a.fin):
                sys.exit("un passage se désigne par --document, --debut et --fin, les trois")
            nom, texte = document_n(docs, a.document)
            bornes = localiser(texte, a.debut)
            if bornes is None:
                sys.exit("--debut : fragment introuvable ou non unique dans ce document")
            debut = bornes[0]
            bornes = localiser(texte, a.fin, debut)
            if bornes is None:
                sys.exit("--fin : fragment introuvable ou non unique après --debut")
            passage = (nom, debut, bornes[1])
        if a.verdict == "motive" and passage is None:
            sys.exit("un verdict `motive` exige un passage : --document, --debut, --fin, "
                     "ou --proposition acceptee")
        if ligne["ANNOT_verdict"]:
            print(f"avertissement : {a.article} avait déjà un verdict "
                  f"({ligne['ANNOT_verdict']}, {ligne['annotateur']}) — remplacé",
                  file=sys.stderr)
        jugement = a.proposition or ("corrigee" if passage else "hors_sujet")
        enregistrer(ligne, docs, a.verdict, passage, a.commentaire or "",
                    a.annotateur, jugement)
        sauver(lignes, a.repertoire / "annotations-100.csv")
    print(f"{a.article}: {ligne['ANNOT_verdict']} — proposition {ligne['proposition_jugee']}"
          f" — {ligne['annotateur']}")
    if passage:
        print(f"  {ligne['ANNOT_document']} [{ligne['ANNOT_offset_debut']}–"
              f"{ligne['ANNOT_offset_fin']}]\n  {ligne['ANNOT_passage_cite']}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("repertoire", type=Path)
    sp = p.add_subparsers(dest="commande", required=True)

    c = sp.add_parser("etat"); c.add_argument("--strate"); c.add_argument("--a-faire", action="store_true")
    c.set_defaults(f=cmd_etat)
    c = sp.add_parser("fiche"); c.add_argument("article"); c.set_defaults(f=cmd_fiche)
    c = sp.add_parser("documents"); c.add_argument("article"); c.set_defaults(f=cmd_documents)
    c = sp.add_parser("mentions"); c.add_argument("article"); c.add_argument("n", type=int)
    c.set_defaults(f=cmd_mentions)
    c = sp.add_parser("chercher"); c.add_argument("article"); c.add_argument("n", type=int)
    c.add_argument("mots", nargs="+"); c.add_argument("--max", type=int, default=20)
    c.set_defaults(f=cmd_chercher)
    c = sp.add_parser("lire"); c.add_argument("article"); c.add_argument("n", type=int)
    c.add_argument("offset", type=int); c.add_argument("longueur", type=int, nargs="?", default=3000)
    c.set_defaults(f=cmd_lire)
    c = sp.add_parser("importer"); c.add_argument("article"); c.add_argument("chemin")
    c.add_argument("--url", required=True); c.set_defaults(f=cmd_importer)
    c = sp.add_parser("rendre"); c.add_argument("article")
    c.add_argument("--annotateur", required=True); c.add_argument("--verdict", required=True)
    c.add_argument("--document", type=int); c.add_argument("--debut"); c.add_argument("--fin")
    c.add_argument("--commentaire"); c.add_argument("--proposition", choices=JUGEMENTS)
    c.set_defaults(f=cmd_rendre)

    a = p.parse_args()
    if not (a.repertoire / "annotations-100.csv").exists():
        sys.exit(f"{a.repertoire} : pas de annotations-100.csv — lancer preparer.py d'abord")
    a.f(a)


if __name__ == "__main__":
    main()
