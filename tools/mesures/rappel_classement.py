#!/usr/bin/env python3
"""Mesure le classement des considérants : le considérant attendu est-il dans les trois montrés ?

Le classement de `restitution/proximite.py` n'affirme rien — il ordonne — mais il
est la seule chose de la page qui s'affichait sans chiffre. La fiche
`data/mesures/rappel-classement-considerants.tsv` porte des couples (article,
acte, considérants attendus) constitués à la main, en lisant les considérants ;
la colonne `juge` dit qui les a constitués. Un couple est réussi si l'un des
considérants attendus est parmi les trois classés ; « aucun » attendu est réussi
si rien n'est classé — c'est le cas d'un acte qui a créé la règle sans la
motiver, et le classement doit savoir se taire.

Ce script ne modifie pas la fiche, sauf la colonne `rang` — le rang obtenu, ou
« — » —, pour que la fiche versionnée dise ce que la base du jour a rendu.

Usage :
    rappel_classement.py <base.sqlite> <fiche.tsv>
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "restitution"))
from graphe import interroger  # noqa: E402
from precision_vise import wilson  # noqa: E402

COLONNES = ["article", "celex", "attendus", "rang", "juge", "commentaire"]


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    fiche = Path(sys.argv[2])
    lignes = list(csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t"))

    reussis, en_tete = 0, 0
    for l in lignes:
        d = interroger(base, l["article"])
        classes = [c["numero"] for c in d["considerants_classes"].get(l["celex"], [])]
        if l["attendus"] == "aucun":
            ok = not classes
            l["rang"] = "—" if not classes else "classé"
        else:
            attendus = {int(n) for n in l["attendus"].split("|")}
            rangs = [i + 1 for i, n in enumerate(classes) if n in attendus]
            ok = bool(rangs)
            l["rang"] = str(rangs[0]) if rangs else "—"
            en_tete += bool(rangs) and rangs[0] == 1
        reussis += ok
        print(f"{'ok ' if ok else 'NON'}  {l['article']:10s} {l['celex']}  attendu {l['attendus']:12s} "
              f"rendu {', '.join(str(n) for n in classes) or '—'}")

    with fiche.open("w", encoding="utf-8", newline="") as sortie:
        graveur = csv.DictWriter(sortie, COLONNES, delimiter="\t", lineterminator="\n")
        graveur.writeheader()
        graveur.writerows(lignes)
    n = len(lignes)
    print(f"\nrappel@3 : {reussis} / {n}   (en tête : {en_tete})")
    print(f"borne de Wilson 95 % : {wilson(reussis, n):.4f}")


if __name__ == "__main__":
    main()
