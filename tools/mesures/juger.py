#!/usr/bin/env python3
"""Juger une fiche de précision, arête par arête, en commandes.

Les fiches de `precision_*.py` sont faites pour être remplies à la main : une
ligne par arête tirée, tout ce qu'il faut pour trancher sur la ligne — la
fenêtre de preuve, l'article du texte, l'article du code, le dispositif de
l'amendement —, et une colonne `verdict` vide. Ce module expose la fiche à
un annotateur qui ne tient pas de terminal : lire une arête, rendre `juste`,
`faux` ou `douteux`, signer.

Deux colonnes de verdict, pour que deux juges rendent sans se lire :
`verdict` (le premier, celui que `--bilan` compte) et `verdict_bis`. Chaque
verdict porte son juge et son commentaire dans des colonnes voisines. Les
écritures prennent un verrou sur le fichier.

    juger.py <fiche.tsv> etat [--colonne verdict|verdict_bis]
    juger.py <fiche.tsv> montrer <cle>
    juger.py <fiche.tsv> rendre <cle> --verdict juste|faux|douteux --juge <nom>
             --commentaire "…" [--colonne verdict|verdict_bis]

Ce que chaque arête affirme, et donc ce que « juste » veut dire :

- `porte_sur` : l'article N du texte en discussion **modifie** (crée, réécrit,
  complète, abroge) l'article A du code de la consommation. Faux si le texte
  ne fait que citer A, si A est d'un autre code, ou si l'article du texte est
  mal identifié. Douteux si la fenêtre ne permet pas de trancher.
- `depose_sur` : l'amendement fut déposé sur l'article N du texte, et cet
  article N réécrit A — donc l'amendement portait sur A. Faux si la
  subdivision déclarée n'est pas N, si N réécrit plusieurs articles, ou si le
  dispositif de l'amendement vise manifestement autre chose. Douteux sinon.
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
              f"{l.get('juge' if a.colonne == 'verdict' else 'juge_bis', '')}")
    faits = sum(bool(l.get(a.colonne)) for l in lignes)
    print(f"\n{faits} jugée(s), {len(lignes) - faits} à juger ({a.colonne})")


def cmd_montrer(a) -> None:
    _, lignes = charger(a.fiche)
    ligne = next((l for l in lignes if l["cle"] == a.cle), None)
    if ligne is None:
        sys.exit(f"clef inconnue : {a.cle}")
    for nom, valeur in ligne.items():
        if nom in ("verdict", "verdict_bis", "juge", "juge_bis", "commentaire",
                   "commentaire_bis") or not valeur:
            continue
        if nom in LONGS:
            print(f"\n{nom.upper()}\n{valeur}\n")
        else:
            print(f"{nom:<20} {valeur}")


def cmd_rendre(a) -> None:
    if a.verdict not in VERDICTS:
        sys.exit(f"verdict attendu : {', '.join(VERDICTS)}")
    suffixe = "" if a.colonne == "verdict" else "_bis"
    with (a.fiche.parent / f".{a.fiche.name}.verrou").open("w") as v:
        fcntl.flock(v, fcntl.LOCK_EX)
        colonnes, lignes = charger(a.fiche)
        for nouvelle in ("verdict_bis", "juge", "juge_bis", "commentaire",
                         "commentaire_bis", "date_jugement"):
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
                                             choices=("verdict", "verdict_bis"))
    c.set_defaults(f=cmd_etat)
    c = sp.add_parser("montrer"); c.add_argument("cle"); c.set_defaults(f=cmd_montrer)
    c = sp.add_parser("rendre"); c.add_argument("cle")
    c.add_argument("--verdict", required=True); c.add_argument("--juge", required=True)
    c.add_argument("--commentaire")
    c.add_argument("--colonne", default="verdict", choices=("verdict", "verdict_bis"))
    c.set_defaults(f=cmd_rendre)
    a = p.parse_args()
    if not a.fiche.exists():
        sys.exit(f"fiche introuvable : {a.fiche}")
    a.f(a)


if __name__ == "__main__":
    main()
