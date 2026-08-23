#!/usr/bin/env python3
"""Confronte à Cellar les identifiants CELEX construits depuis le texte français.

Un CELEX n'est jamais recopié d'une source : il est déduit d'un numéro cité en
français (« règlement (CE) n° 2006/2004 » → `32004R2006`). Une déduction bien
formée reste plausible quand elle est fausse — inverser année et numéro produit
un identifiant parfaitement valide qui désigne un autre acte. Publier un tel lien
serait exactement l'invention que le § 5.1 interdit.

Cellar, le service d'identifiants de l'Office des publications de l'Union, tranche
sans ambiguïté : 303 vers la ressource pour un acte connu, 404 sinon. C'est la
seule étape du projet qui demande le réseau ; son résultat est versionné dans
`data/corpus/celex-verifies.tsv` pour que le pipeline reste rejouable hors ligne.

Le fichier est complété, jamais réécrit : les identifiants déjà tranchés ne sont
pas réinterrogés, et un acte retiré du corpus garde sa ligne — elle documente une
vérification qui a eu lieu.

Les candidats viennent de deux endroits, et le second est facile à oublier : le
texte des alinéas, mais aussi l'intitulé complet des textes français, où se
déclarent les transpositions. Quatre directives majeures — dont l'« Omnibus »
2019/2161 et la DSP2 — sont **déclarées transposées sans être citées nulle part
dans le code**. Ne balayer que les alinéas les faisait disparaître en silence.

Usage :
    verifier_celex.py <base.sqlite> <celex-verifies.tsv> [titres-jorf.tsv]
"""

from __future__ import annotations

import csv
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ingestion"))
from union_europeenne import citations  # noqa: E402

CELLAR = "https://publications.europa.eu/resource/celex/{}"
PAUSE = 0.3          # le service est public et gratuit : on ne le martèle pas


class SansRedirection(urllib.request.HTTPRedirectHandler):
    """La redirection *est* la réponse : la suivre téléchargerait 1 Mo par acte.

    Cellar répond 303 vers la notice quand l'acte existe. En laissant urllib la
    suivre, on paierait le corps entier pour n'en lire que le code. Ne pas la
    suivre fait remonter le 303 comme une HTTPError, que l'appelant lit.
    """

    def redirect_request(self, *_args, **_kwargs):
        return None


SANS_REDIRECTION = urllib.request.build_opener(SansRedirection())


def statut(identifiant: str) -> str | None:
    """« verifie » si Cellar connaît l'acte, « inconnu » s'il répond 404.

    Rend None sur toute autre issue — panne, coupure, quota. Un échec réseau
    n'est pas une réponse : le traiter comme « inconnu » effacerait des actes
    réels au premier incident.
    """
    requete = urllib.request.Request(
        CELLAR.format(identifiant), method="HEAD",
        headers={"Accept": "application/xml;notice=object"})
    try:
        with SANS_REDIRECTION.open(requete, timeout=30) as reponse:
            return "verifie" if reponse.status in (200, 300, 303) else None
    except urllib.error.HTTPError as erreur:
        if erreur.code in (300, 303):
            return "verifie"
        return "inconnu" if erreur.code == 404 else None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def main() -> None:
    if not 3 <= len(sys.argv) <= 4:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    plan = Path(sys.argv[2])
    titres = Path(sys.argv[3]) if len(sys.argv) == 4 else None

    candidats = set()
    for (texte,) in base.execute("SELECT texte FROM segment"):
        candidats.update(c for c, _, _, _ in citations(texte))
    base.close()
    if titres and titres.exists():
        for ligne in csv.DictReader(titres.open(encoding="utf-8"), delimiter="\t"):
            candidats.update(c for c, _, _, _ in citations(ligne["titre"]))

    connus: dict[str, tuple[str, str]] = {}
    if plan.exists():
        for ligne in csv.DictReader(plan.open(encoding="utf-8"), delimiter="\t"):
            connus[ligne["celex"]] = (ligne["statut"], ligne["verifie_le"])

    aujourdhui = date.today().isoformat()
    a_faire = sorted(candidats - set(connus))
    print(f"candidats : {len(candidats)}   déjà tranchés : "
          f"{len(candidats) - len(a_faire)}   à vérifier : {len(a_faire)}")

    echecs = 0
    for rang, identifiant in enumerate(a_faire, 1):
        issue = statut(identifiant)
        if issue is None:
            echecs += 1
            print(f"  [{rang}/{len(a_faire)}] {identifiant} : sans réponse")
        else:
            connus[identifiant] = (issue, aujourdhui)
        time.sleep(PAUSE)

    with plan.open("w", encoding="utf-8", newline="") as sortie:
        ecrivain = csv.writer(sortie, delimiter="\t", lineterminator="\n")
        ecrivain.writerow(["celex", "statut", "verifie_le"])
        for identifiant in sorted(connus):
            ecrivain.writerow([identifiant, *connus[identifiant]])

    verifies = sum(1 for s, _ in connus.values() if s == "verifie")
    print(f"vérifiés : {verifies}   inconnus de Cellar : {len(connus) - verifies}"
          f"   sans réponse : {echecs}")
    print(f"→ {plan}")


if __name__ == "__main__":
    main()
