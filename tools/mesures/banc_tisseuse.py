#!/usr/bin/env python3
"""Passe les dispositifs des arêtes `vise` jugées dans l'extracteur de Tisseuse.

Tisseuse (Tricoteuses, AGPL) extrait d'un texte modificatif des directives
typées : `insert_after`, `insert_before`, `replace`, `replace_portion`,
`delete`, `delete_portion`, `delete_article`, chacune avec la référence
qu'elle touche. C'est la fonction que DuraLex tenait. La question est de
savoir si elle peut tenir celle de `vise` : pour chaque arête jugée, le numéro
d'article que nous visons est-il la référence d'une des directives que
Tisseuse extrait du même dispositif ?

Trois issues par fiche : `meme_article` (une directive porte sur l'article
visé), `autre_cible` (des directives, aucune sur lui), `aucune` (pas de
directive). Croisées avec notre verdict, elles disent deux choses : sur les
justes, ce que Tisseuse retrouve ; sur les fausses, lesquelles de nos erreurs
il commet aussi. Ce n'est pas une précision de Tisseuse : nos verdicts sont
des verdicts d'agents, et `autre_cible` n'est pas jugée.

Le script écrit un petit programme TypeScript dans le paquet `tisseuse` du
dépôt `tricoteuses-juridique` (l'alias `$lib` n'y résout que là), l'exécute
par `npx tsx`, puis l'efface. Le paquet doit être installé
(`npm install --ignore-scripts -w packages/tisseuse` à la racine du dépôt).

Usage :
    banc_tisseuse.py <racine tricoteuses-juridique> <sortie.tsv> [fiche.tsv ...]
    (sans fiche : toutes les data/mesures/precision-vise*.tsv)
"""

from __future__ import annotations

import collections
import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]

PROGRAMME = """\
import { readFileSync } from "node:fs"
import { extractActionDirectivesFromText } from "$lib/extractors/action_directives.js"

for (const ligne of readFileSync(process.argv[2], "utf-8").split("\\n")) {
  if (!ligne) continue
  const { dispositif } = JSON.parse(ligne)
  let directives: unknown[] = []
  let erreur: string | null = null
  try {
    directives = extractActionDirectivesFromText(dispositif).map((d) => ({
      kind: d.kind, reference: d.reference,
    }))
  } catch (e) {
    erreur = String(e)
  }
  console.log(JSON.stringify({ directives, erreur }))
}
"""


def numeros(noeud, acc: list[str]) -> list[str]:
    """Les numéros de toutes les références d'article d'un arbre Tisseuse."""
    if isinstance(noeud, dict):
        if noeud.get("type") == "article" and "num" in noeud:
            acc.append(noeud["num"])
        for v in noeud.values():
            numeros(v, acc)
    elif isinstance(noeud, list):
        for v in noeud:
            numeros(v, acc)
    return acc


def normalise(numero: str) -> str:
    return re.sub(r"[\s. ]", "", numero.replace("‑", "-")).upper()


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    depot, sortie = Path(sys.argv[1]), Path(sys.argv[2])
    fiches = [Path(f) for f in sys.argv[3:]] or sorted(
        (RACINE / "data/mesures").glob("precision-vise*.tsv"))
    paquet = depot / "packages/tisseuse"

    lignes = []
    for fiche in fiches:
        with fiche.open(encoding="utf-8") as flux:
            for r in csv.DictReader(flux, delimiter="\t"):
                lignes.append({"fiche": fiche.name, **r})

    programme = paquet / "src/_banc_ratio_legis.ts"
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", encoding="utf-8") as entree:
        for r in lignes:
            entree.write(json.dumps({"dispositif": r["dispositif"]}, ensure_ascii=False) + "\n")
        entree.flush()
        programme.write_text(PROGRAMME, encoding="utf-8")
        try:
            resultat = subprocess.run(
                ["npx", "tsx", str(programme.relative_to(paquet)), entree.name],
                cwd=paquet, capture_output=True, text=True, check=True)
        finally:
            programme.unlink()
    extraits = [json.loads(l) for l in resultat.stdout.splitlines() if l]
    assert len(extraits) == len(lignes), "une sortie par dispositif"

    tableau = collections.Counter()
    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.writer(flux, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["fiche", "cle", "article", "formule", "verdict",
                           "issue", "directives", "cibles_tisseuse"])
        for r, x in zip(lignes, extraits):
            cibles = sorted({normalise(n) for d in x["directives"]
                             for n in numeros(d["reference"], [])})
            issue = ("erreur" if x["erreur"] else
                     "aucune" if not x["directives"] else
                     "meme_article" if normalise(r["article"]) in cibles else
                     "autre_cible")
            verdict = r["verdict"] or "non_juge"
            tableau[verdict, issue] += 1
            ecrivain.writerow([r["fiche"], r["cle"], r["article"], r["formule"], verdict,
                               issue, " ".join(d["kind"] for d in x["directives"]),
                               " ".join(cibles)])

    issues = ["meme_article", "autre_cible", "aucune", "erreur"]
    print(f"{len(lignes)} fiches, {len({r['cle'] for r in lignes})} arêtes distinctes")
    print(f"{'verdict':<10}" + "".join(f"{i:>14}" for i in issues))
    for verdict in sorted({v for v, _ in tableau}):
        print(f"{verdict:<10}" + "".join(f"{tableau[verdict, i]:>14}" for i in issues))
    formules = collections.Counter(r["formule"] for r, x in zip(lignes, extraits)
                                   if r["verdict"] == "juste" and not x["directives"])
    print("formules des justes sans directive :",
          ", ".join(f"{f} {n}" for f, n in formules.most_common(8)))


if __name__ == "__main__":
    main()
