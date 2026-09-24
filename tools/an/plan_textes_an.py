#!/usr/bin/env python3
"""Le plan « dossier DOLE → numéros de texte de l'Assemblée », pour une législature.

Un amendement de l'Assemblée ne nomme pas son dossier : il nomme le texte sur
lequel il est déposé, `PRJLANR5L15B1234` ou `…BTC1234`. Le plan de la XIVe
(`plan-textes-an-14.tsv`) avait été écrit à la main ; celui des législatures
suivantes est dérivé, et la dérivation se vérifie contre lui.

**D'où viennent les numéros.** DOLE lie, pour chaque dossier, les textes déposés
et les rapports de l'Assemblée ; les plans versionnés de l'étape 2 en gardent
l'URL. L'Assemblée numérote dans **une seule série par législature** projets,
propositions et rapports : un numéro lu dans le lien d'un dossier n'appartient
qu'à ce dossier. Le texte de commission (`BTC`) porte le numéro du rapport qui
l'annexe, d'où la lecture des rapports aussi.

**Vérifié sur la XIVe** : pour chacun des 16 dossiers du plan écrit à la main,
les numéros dérivés **contiennent** ceux du plan. Ils en ajoutent — le texte
d'une autre lecture, un rapport sans amendement — et un numéro de trop ne coûte
rien : il n'a d'amendements que s'il a été amendé, et ils sont alors bien de ce
dossier.

Usage :
    plan_textes_an.py <législature> <sortie.tsv> <plan.tsv>…
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# `/15/rapports/r0123.asp`, `/15/propositions/pion0123.asp`, `/15/projets/pl0123.asp`,
# et depuis la XVe les adresses `/dyn/15/textes/l15b0123_…` ou
# `/dyn/16/rapports/cion-eco/l16b0123_…`.
MOTIFS = (
    re.compile(r"assemblee-nationale\.fr/(\d+)/(?:rapports/r|propositions/pion|projets/pl)0*(\d+)"),
    re.compile(r"/dyn/(\d+)/\w+/(?:[\w-]+/)?l\d+b0*(\d+)"),
)
DOSSIER = re.compile(r"JORFDOLE\d+")


def numeros(plans: list[Path], legislature: str) -> set[tuple[str, str]]:
    couples = set()
    for plan in plans:
        for ligne in plan.read_text(encoding="utf-8").splitlines():
            dossier = DOSSIER.match(ligne)
            if not dossier:
                continue
            for motif in MOTIFS:
                for trouve in motif.finditer(ligne):
                    if trouve.group(1) == legislature:
                        couples.add((dossier.group(0), trouve.group(2).lstrip("0")))
    return couples


def main() -> None:
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    legislature, sortie = sys.argv[1], Path(sys.argv[2])
    couples = numeros([Path(p) for p in sys.argv[3:]], legislature)
    sortie.write_text("".join(f"{d}\t{n}\n" for d, n in sorted(couples)), encoding="utf-8")
    print(f"législature {legislature} : {len(couples)} textes, "
          f"{len({d for d, _ in couples})} dossiers → {sortie}")


if __name__ == "__main__":
    main()
