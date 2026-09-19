#!/usr/bin/env python3
"""Juger une fiche de précision, arête par arête, en commandes.

Les fiches de `precision_*.py` sont faites pour être remplies à la main : une
ligne par arête tirée, tout ce qu'il faut pour trancher sur la ligne — la
fenêtre de preuve, l'article du texte, l'article du code, le dispositif de
l'amendement —, et une colonne `verdict` vide. Ce module expose la fiche à
un annotateur qui ne tient pas de terminal : lire une arête, rendre `juste`,
`faux` ou `douteux`, signer.

Trois colonnes de verdict, pour que trois juges rendent sans se lire :
`verdict` (celui que `--bilan` compte), `verdict_bis`, `verdict_ter`. Chaque
verdict porte son juge et son commentaire dans des colonnes voisines. Les
écritures prennent un verrou sur le fichier.

    juger.py <fiche.tsv> etat [--colonne verdict|verdict_bis|verdict_ter]
    juger.py <fiche.tsv> montrer <cle>
    juger.py <fiche.tsv> rendre <cle> --verdict juste|faux|douteux --juge <nom>
             --commentaire "…" [--colonne verdict|verdict_bis|verdict_ter]

Ce que chaque arête affirme, et donc ce que « juste » veut dire :

- `porte_sur` : l'article N du texte en discussion **modifie** (crée, réécrit,
  complète, abroge) l'article A du code de la consommation. Faux si le texte
  ne fait que citer A, si A est d'un autre code, ou si l'article du texte est
  mal identifié. Douteux si la fenêtre ne permet pas de trancher.
- `depose_sur` : **l'amendement portait sur l'article A du code** — c'est ce
  que la restitution écrit, et c'est ce qu'on juge. La colonne `voie` dit
  comment l'arête l'a établi, et donc quoi vérifier :
  - `visee` : le dispositif nomme A (ou son ancien numéro). Faux si le
    dispositif nomme A sans le modifier, ou vise en réalité un autre article.
  - `alinea` : le dispositif nomme un alinéa de l'article N du texte, et
    l'instruction du texte qui gouverne cet alinéa réécrit A. Faux si cet
    alinéa relève d'une autre instruction (autre article du code, autre code),
    ou si l'alinéa cité n'est pas celui que le texte numérote ainsi. Lis le
    texte en discussion à l'article N (`travail/corpus/textes/<dossier>__…`)
    et compte les alinéas ; la `fenetre` donne l'instruction retenue.
  - `article_entier` : le dispositif porte sur tout l'article N (« Supprimer
    cet article », « Rédiger ainsi… »), et N ne réécrit que A. Faux si N
    réécrit aussi d'autres articles ou d'autres codes.
  Douteux si la ligne et le texte ne permettent pas de trancher.
- `vise` : **le dispositif de l'amendement modifie, crée, abroge ou réécrit
  l'article A du code de la consommation.** Faux s'il ne fait que le citer,
  le nomme comme ancre (« après l'article A, il est inséré… »), ou vise un
  homonyme d'un autre code. La `formule` dit ce qui a été relevé.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import sys
from datetime import date
from pathlib import Path

VERDICTS = ("juste", "faux", "douteux")
LONGS = ("article_du_fonds", "contexte", "fenetre", "dispositif", "mention_hote")


def charger(fiche: Path) -> tuple[list[str], list[dict]]:
    with fiche.open(encoding="utf-8", newline="") as f:
        lecteur = csv.DictReader(f, delimiter="\t")
        return list(lecteur.fieldnames or []), list(lecteur)


def sauver(fiche: Path, colonnes: list[str], lignes: list[dict]) -> None:
    provisoire = fiche.with_suffix(".tsv.tmp")
    with provisoire.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=colonnes, delimiter="\t",
                                  lineterminator="\n", extrasaction="ignore")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    provisoire.replace(fiche)


def cmd_etat(a) -> None:
    _, lignes = charger(a.fiche)
    for l in lignes:
        print(f"{l['cle']}  {l.get(a.colonne) or '—':<8} "
              f"{l.get('juge' + a.colonne[7:], '')}")
    faits = sum(bool(l.get(a.colonne)) for l in lignes)
    print(f"\n{faits} jugée(s), {len(lignes) - faits} à juger ({a.colonne})")


def cmd_montrer(a) -> None:
    _, lignes = charger(a.fiche)
    ligne = next((l for l in lignes if l["cle"] == a.cle), None)
    if ligne is None:
        sys.exit(f"clef inconnue : {a.cle}")
    for nom, valeur in ligne.items():
        if nom.startswith(("verdict", "juge", "commentaire", "date_jugement")) or not valeur:
            continue
        if nom in LONGS:
            print(f"\n{nom.upper()}\n{valeur}\n")
        else:
            print(f"{nom:<20} {valeur}")


def cmd_rendre(a) -> None:
    if a.verdict not in VERDICTS:
        sys.exit(f"verdict attendu : {', '.join(VERDICTS)}")
    suffixe = a.colonne[7:]          # "", "_bis" ou "_ter"
    with (a.fiche.parent / f".{a.fiche.name}.verrou").open("w") as v:
        fcntl.flock(v, fcntl.LOCK_EX)
        colonnes, lignes = charger(a.fiche)
        for nouvelle in ("verdict_bis", "verdict_ter", "juge", "juge_bis", "juge_ter",
                         "commentaire", "commentaire_bis", "commentaire_ter", "date_jugement"):
            if nouvelle not in colonnes:
                colonnes.append(nouvelle)
        ligne = next((l for l in lignes if l["cle"] == a.cle), None)
        if ligne is None:
            sys.exit(f"clef inconnue : {a.cle}")
        if ligne.get(a.colonne):
            print(f"avertissement : {a.cle} avait déjà {ligne[a.colonne]} "
                  f"({ligne.get('juge' + suffixe, '')}) — remplacé", file=sys.stderr)
        ligne[a.colonne] = a.verdict
        ligne["juge" + suffixe] = a.juge
        ligne["commentaire" + suffixe] = a.commentaire or ""
        ligne["date_jugement"] = date.today().isoformat()
        sauver(a.fiche, colonnes, lignes)
    print(f"{a.cle}: {a.verdict} — {a.juge} ({a.colonne})")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("fiche", type=Path)
    sp = p.add_subparsers(dest="commande", required=True)
    c = sp.add_parser("etat"); c.add_argument("--colonne", default="verdict",
                                             choices=("verdict", "verdict_bis", "verdict_ter"))
    c.set_defaults(f=cmd_etat)
    c = sp.add_parser("montrer"); c.add_argument("cle"); c.set_defaults(f=cmd_montrer)
    c = sp.add_parser("rendre"); c.add_argument("cle")
    c.add_argument("--verdict", required=True); c.add_argument("--juge", required=True)
    c.add_argument("--commentaire")
    c.add_argument("--colonne", default="verdict", choices=("verdict", "verdict_bis", "verdict_ter"))
    c.set_defaults(f=cmd_rendre)
    a = p.parse_args()
    if not a.fiche.exists():
        sys.exit(f"fiche introuvable : {a.fiche}")
    a.f(a)


if __name__ == "__main__":
    main()
