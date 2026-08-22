#!/usr/bin/env python3
"""Pré-remplissage du jeu d'annotation depuis les rapports de commission.

L'annotateur humain devait produire, pour chaque article, l'offset du passage qui
le motive (`docs/02-golden-set.md` § 6). Ce script propose ce passage à partir
d'une source externe — le commentaire d'article du rapport de commission — de
sorte que le travail humain devienne une **validation** plutôt qu'une recherche.

La distinction n'est pas cosmétique. Valider une proposition et la produire
n'exigent pas le même temps, mais surtout : une proposition fausse est plus
dangereuse qu'une case vide, parce qu'elle biaise l'annotateur. D'où deux
précautions inscrites dans le format de sortie :

  - la colonne `ANNOT_verdict` reste **vide** : la machine ne préjuge pas ;
  - `source_declaree_en_entete` distingue les cas où le rapporteur a nommé
    l'article dans l'en-tête de son commentaire — rattachement fort — de ceux où
    l'article n'est que cité dans le corps — rattachement faible, à vérifier.

L'annotateur doit pouvoir conclure « passage proposé hors sujet » et le dire.

Usage :
    jeu_annotation.py <jeu_annotation.csv> <repertoire_rapports> <sortie.csv>

Les rapports sont nommés `<ID_DOLE>__<fichier>` pour porter leur rattachement au
dossier ; c'est la convention produite par le téléchargement depuis les liens
`ARBORESCENCE` de DOLE.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commentaires_rapports import commentaires, texte_brut  # noqa: E402

EXTRAIT = 400


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    jeu, repertoire, sortie = (Path(a) for a in sys.argv[1:])

    par_dossier: dict[str, list[dict]] = defaultdict(list)
    textes: dict[str, str] = {}
    for fichier in sorted(repertoire.iterdir()):
        if "__" not in fichier.name:
            continue
        dossier = fichier.name.split("__", 1)[0]
        try:
            sections = commentaires(fichier)
        except Exception:  # un rapport peut être un PDF ou une page d'index
            continue
        if not sections:
            continue
        textes[fichier.name] = texte_brut(fichier)
        par_dossier[dossier].extend(sections)

    lignes = list(csv.DictReader(jeu.open(encoding="utf-8")))
    colonnes = list(lignes[0]) + ["source_proposee", "source_declaree_en_entete",
                                  "grain_du_rattachement"]

    proposes = 0
    for ligne in lignes:
        ligne["source_proposee"] = ""
        ligne["source_declaree_en_entete"] = ""
        ligne["grain_du_rattachement"] = ""
        sections = par_dossier.get(ligne["id_dole_origine"], [])
        if not sections:
            continue
        cles = [c for c in (ligne["num_article"].replace(" ", ""),
                            ligne["article_predecesseur"].replace(" ", "")) if c]
        fortes = [s for s in sections if any(c in s["articles_declares"] for c in cles)]
        faibles = [s for s in sections if any(c in s["articles_cites"] for c in cles)]
        # Le rapport au Président de la République ne nomme presque jamais les
        # articles : mesuré, il n'en cite que 2 sur 25 dans l'échantillon. Le
        # proposer quand même, mais au grain du texte entier et en le disant —
        # c'est la seule motivation qui existe pour une ordonnance, et une case
        # vide ferait croire à tort qu'il n'y en a aucune.
        grossieres = [s for s in sections if "rapport-pr" in s["rapport"]]
        retenues = fortes or faibles or grossieres
        if not retenues:
            continue
        ligne["grain_du_rattachement"] = ("article" if (fortes or faibles)
                                          else "texte entier")
        # à rattachement égal, la section la plus courte est la plus spécifique
        section = min(retenues, key=lambda s: s["offset_fin"] - s["offset_debut"])
        texte = textes.get(section["rapport"], "")
        extrait = re.sub(r"\s+", " ",
                         texte[section["offset_debut"]:section["offset_debut"] + EXTRAIT])

        ligne["ANNOT_document"] = section["rapport"]
        ligne["ANNOT_offset_debut"] = section["offset_debut"]
        ligne["ANNOT_offset_fin"] = section["offset_fin"]
        ligne["ANNOT_passage_cite"] = extrait
        ligne["source_proposee"] = ("rapport au Président de la République"
                                    if "rapport-pr" in section["rapport"]
                                    else "rapport de commission")
        ligne["source_declaree_en_entete"] = int(bool(fortes))
        proposes += 1

    with sortie.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes)
        writer.writeheader()
        writer.writerows(lignes)

    fortes = sum(1 for l in lignes if l["source_declaree_en_entete"] == 1)
    grossier = sum(1 for l in lignes if l["grain_du_rattachement"] == "texte entier")
    print(f"rapports exploitables      : {len(textes)}")
    print(f"dossiers couverts          : {len(par_dossier)}")
    print(f"articles du jeu            : {len(lignes)}")
    print(f"  avec passage proposé     : {proposes} ({100 * proposes / len(lignes):.0f} %)")
    print(f"  dont rattachement fort   : {fortes}")
    print(f"  au grain du texte entier : {grossier}")
    print(f"  laissés à la recherche humaine : {len(lignes) - proposes}")


if __name__ == "__main__":
    main()
