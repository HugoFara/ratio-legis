#!/usr/bin/env python3
"""Vingt-quatrième tranche : le sort d'un amendement, lu et rendu comparable.

Le sort était en base depuis la cinquième tranche — 33 217 amendements le
portent — et il n'était ni lisible, ni comparable, ni rendu nulle part. Trois
défauts, de trois natures différentes, se tenaient devant lui.

**1 141 sorts déclarés vides alors qu'ils sont écrits.** L'Assemblée publie deux
colonnes : `sort[1]/sortEnSeance[1]`, et l'état procédural `etat[1]`. La
cinquième tranche avait retenu la première, à juste titre — `etat` vaut
« Discuté » sur les 9 966 amendements qui ont un sort, et le prendre pour le sort
aurait effacé 3 280 rejets. Mais la réciproque n'avait pas été regardée : sur les
1 149 amendements sans sort publié, `etat` vaut **« Retiré » 694 fois et
« Irrecevable » 447 fois**. Huit seulement sont réellement en attente.

Conséquence, visible dans la restitution : l'Assemblée n'affichait **aucune**
irrecevabilité, quand le Sénat en affiche 1 735. Le lecteur en aurait conclu que
l'Assemblée ne déclare rien d'irrecevable, ce qui est faux.

**63 sorts illisibles au Sénat.** Réparés en amont, dans `lire_ameli` : le défaut
était de lecture, pas de source.

**Des libellés qu'on ne peut pas additionner.** « Adopté » et « Adopté - vote
unique » sont le même sort, et le second n'était compté nulle part — pas même
dans la sélection des amendements adoptés qui construit `resulte_de`.
« Irrecevable art. 40 C » et « Irrecevable art. 45, al. 1 C (cavalier) » sont au
contraire deux faits opposés : le premier dit que l'amendement coûtait de
l'argent, le second qu'il était hors sujet. La famille sert à compter, le libellé
source à citer, et les deux sont conservés.

**Ce que cette tranche ne fait pas.** Elle ne juge pas. « Retiré » ne dit pas si
l'auteur a cédé ou obtenu satisfaction ; « Tombé » ne dit pas lequel des
amendements concurrents l'a emporté. Ces deux questions se lisent dans le compte
rendu de séance, que le graphe ne contient pas (§ 2.2 de la feuille de route).

Usage :
    sort_des_amendements.py <base.sqlite> [schema/010-sort.sql]
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

# Familles, dans l'ordre où elles se lisent : le sort d'abord, l'état ensuite.
# Le motif d'irrecevabilité est capturé séparément — c'est lui qui porte le fait
# intéressant, non le mot « irrecevable ».
FAMILLES: tuple[tuple[str, re.Pattern[str]], ...] = (
    # « Adopté - vote unique » est un adopté : le vote unique est une modalité de
    # scrutin, pas un sort. Vingt-deux amendements du périmètre étaient exclus de
    # la construction de `resulte_de` pour cette seule raison.
    ("adopte",      re.compile(r"^adopt[ée]", re.I)),
    ("rejete",      re.compile(r"^rejet[ée]", re.I)),
    # Améli écrit tantôt « Retiré », tantôt la phrase entière « Cet amendement est
    # retiré avant séance » — 1 603 fois, soit le tiers de ses retraits.
    ("retire",      re.compile(r"^retir[ée]|retir[ée]\s+avant\s+s[ée]ance", re.I)),
    ("non_soutenu", re.compile(r"^non\s+soutenu", re.I)),
    ("tombe",       re.compile(r"^tomb[ée]", re.I)),
    ("irrecevable", re.compile(r"^irrecevable", re.I)),
    # « Recevable art. 40 C / LOLF » est une décision de recevabilité, pas un
    # sort : elle dit que l'amendement pouvait être discuté, non ce qu'il est
    # devenu. « A discuter » dit la même chose à l'Assemblée.
    ("non_statue",  re.compile(r"^recevable|^[àa]\s+discuter", re.I)),
)

# Les fondements que les deux chambres déclarent. L'article 40 de la Constitution
# interdit d'aggraver une charge publique, l'article 45 les cavaliers, l'article
# 41 l'empiètement sur le domaine réglementaire ; l'article 44 bis du règlement du
# Sénat est la règle de l'entonnoir. L'Assemblée écrit « Irrecevable » sans
# motif : la colonne reste alors vide, et n'est pas devinée.
MOTIFS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("article 40",     re.compile(r"art\.?\s*40", re.I)),
    ("article 45",     re.compile(r"art\.?\s*45", re.I)),
    ("article 41",     re.compile(r"art\.?\s*41", re.I)),
    ("article 44 bis", re.compile(r"art\.?\s*44\s*bis", re.I)),
    ("LOLFSS",         re.compile(r"lolfss", re.I)),
    ("LOLF",           re.compile(r"lolf", re.I)),
)

# Ce que la famille se dit en français, pour la restitution. Les huit libellés
# sont ici et nulle part ailleurs : `citation.py` a montré ce que coûte une règle
# tenue à trois endroits.
EN_FRANCAIS = {
    "adopte":      "adopté",
    "rejete":      "rejeté",
    "retire":      "retiré",
    "non_soutenu": "non soutenu",
    "tombe":       "tombé",
    "irrecevable": "déclaré irrecevable",
    "non_statue":  "non examiné",
    "inconnu":     "sort non publié",
}

# Les familles qui disent qu'une tentative n'a pas abouti. « Retiré » et « non
# soutenu » en font partie sans qu'on sache pourquoi — c'est bien pour cela que
# la restitution nomme la famille au lieu de dire « échec ».
#
# `non_statue` en est absent : un amendement déclaré recevable ou resté à
# discuter n'a ni abouti ni échoué, et le ranger dans l'un des deux camps serait
# affirmer ce que la source ne dit pas. Il reste compté dans le total.
ECHEC = ("rejete", "retire", "non_soutenu", "tombe", "irrecevable")


def lire(sort: str | None, etat: str | None) -> tuple[str, str | None, str | None,
                                                      str | None]:
    """(famille, motif, libellé source, colonne d'où il vient).

    Le sort publié prime toujours sur l'état procédural : quand les deux sont
    lisibles, `etat` ne dit que « Discuté », qui n'est pas un sort.
    """
    for colonne, valeur in (("sort", sort), ("etat", etat)):
        libelle = (valeur or "").strip()
        if not libelle:
            continue
        for famille, marque in FAMILLES:
            if marque.search(libelle):
                motif = next((nom for nom, m in MOTIFS if m.search(libelle)), None)
                return famille, motif if famille == "irrecevable" else None, \
                    libelle, colonne
    return "inconnu", None, None, None


def est_adopte(sort: str | None, etat: str | None = None) -> bool:
    """Seul point d'entrée pour « cet amendement a-t-il été adopté ».

    Importé par `amendements_vers_resulte_de.py`, qui comparait auparavant le
    libellé à la chaîne « Adopté ». Une règle, un endroit.
    """
    return lire(sort, etat)[0] == "adopte"


def construire(base: sqlite3.Connection, schema: Path) -> dict:
    base.executescript(schema.read_text(encoding="utf-8"))
    lignes = [(identifiant, *lire(sort, etat)) for identifiant, sort, etat
              in base.execute("SELECT id, sort, etat FROM amendement")]
    base.executemany(
        "INSERT INTO sort_amendement (amendement_id, famille, motif, libelle, source)"
        " VALUES (?, ?, ?, ?, ?)", lignes)
    # Test de contrat, au sens du § 8 : un libellé non vide qu'aucune famille ne
    # reconnaît est le symptôme d'une dérive de format en amont — c'est ainsi que
    # les 63 enregistrements brisés d'Améli se signalaient. Il est compté et
    # nommé, jamais rangé en silence.
    illisibles = [(identifiant, sort) for identifiant, famille, sort in
                  base.execute("SELECT a.id, s.famille, coalesce(a.sort, a.etat) "
                               "FROM amendement a JOIN sort_amendement s "
                               "ON s.amendement_id = a.id")
                  if famille == "inconnu" and (sort or "").strip()]
    return {"amendements": len(lignes), "illisibles": illisibles}


def main() -> None:
    if not 2 <= len(sys.argv) <= 3:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    schema = Path(sys.argv[2]) if len(sys.argv) == 3 else \
        Path(__file__).resolve().parent.parent / "schema" / "010-sort.sql"
    base.execute("PRAGMA foreign_keys = ON")
    compte = construire(base, schema)
    base.commit()

    print(f"amendements classés : {compte['amendements']}")
    print("\n%-11s %-14s %8s %8s" % ("chambre", "famille", "nombre", "via état"))
    for chambre, famille, nombre, etat in base.execute("SELECT * FROM sort_par_chambre"):
        print("%-11s %-14s %8d %8d" % (chambre, famille, nombre, etat or 0))

    print("\nmotifs d'irrecevabilité :")
    for motif, nombre in base.execute(
            "SELECT coalesce(motif, '(non précisé)'), count(*) FROM sort_amendement "
            "WHERE famille = 'irrecevable' GROUP BY 1 ORDER BY 2 DESC"):
        print(f"  {motif:16s} {nombre}")

    tentatives, articles = base.execute(
        "SELECT count(*), count(DISTINCT article) FROM tentative_sur_article"
    ).fetchone()
    echouees = base.execute(
        "SELECT count(*) FROM tentative_sur_article WHERE famille != 'adopte'"
    ).fetchone()[0]
    print(f"\ntentatives déclarées sur un article du code : {tentatives}")
    print(f"  articles concernés     : {articles}")
    print(f"  tentatives non abouties : {echouees}")

    if compte["illisibles"]:
        print(f"\nALERTE — {len(compte['illisibles'])} libellé(s) non reconnu(s) ; "
              "le format amont a dérivé :")
        for identifiant, libelle in compte["illisibles"][:5]:
            print(f"  amendement {identifiant} : {libelle[:60]!r}")
    else:
        print("\naucun libellé non reconnu")
    print(f"intégrité : {len(base.execute('PRAGMA foreign_key_check').fetchall())} "
          "violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
