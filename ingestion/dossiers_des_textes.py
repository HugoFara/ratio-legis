#!/usr/bin/env python3
"""Rattache chaque texte normatif à son dossier législatif, depuis DOLE.

L'arête `issu_de` du § 3 relie un TexteNormatif à son Dossier. Elle était
construite dans `rapports_vers_motive.py` à partir du périmètre, qui ne porte
qu'une seule colonne de dossier : `id_dole_origine`, celui du texte qui a **créé**
l'article. Les textes qui se contentent de le **modifier** n'ont donc jamais été
résolus. Sur les 68 lois et ordonnances qui produisent une version en vigueur, 24
restaient sans dossier — loi Macron de 2015, Sapin II, loi du 10 mai 2024 sur
l'espace numérique. Aucune ne manque à la source : l'ingestion ne l'a pas demandée.

Le rattachement est **déclaré**, pas déduit. Chaque dossier DOLE énumère ses
textes sous `<ID_TEXTE_n>` : l'index inverse de ces listes est la réponse.

    <ID_TEXTE_1>JORFTEXT…</ID_TEXTE_1>   le projet ou l'ordonnance
    <ID_TEXTE_2>JORFTEXT…</ID_TEXTE_2>   le rapport au Président
    <ID_TEXTE_4>JORFTEXT…</ID_TEXTE_4>   la loi de ratification

Un texte peut donc figurer dans plusieurs dossiers — l'ordonnance apparaît aussi
dans le dossier de la loi qui la ratifie. Quand c'est le cas, on retient le
dossier dont le **titre porte le numéro du texte**, et aucun si l'ambiguïté
subsiste. Deux textes du périmètre sont dans ce cas ; ils restent sans arête,
conformément au § 5.3.

Vérification, faite avant d'écrire quoi que ce soit : sur les 89 arêtes que la
méthode par le périmètre avait produites, celle-ci en retrouve **89 sur 89**, et
elle en ajoute 111. Les deux signaux — le numéro dans le titre du dossier et la
liste `ID_TEXTE_n` — ne se contredisent nulle part.

Ce que la méthode ne trouve pas, et pourquoi : 212 décrets et 2 arrêtés ne sont
listés par aucun dossier, parce que DOLE est le fonds des **dossiers
législatifs** et qu'un décret n'en a pas. Leur silence est structurel, pas un
défaut de couverture.

Usage :
    dossiers_des_textes.py <miroir_dila/> <base.sqlite>
"""

from __future__ import annotations

import re
import sqlite3
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "dila"))
from fonds import deployer  # noqa: E402

TITRE = re.compile(r"<TITRE>(.*?)</TITRE>", re.S)
# `<LEGISLATURE>` est un conteneur, pas une valeur : il porte `<NUMERO>` et
# `<DATE_DEBUT>`. Une première version lisait `<LEGISLATURE>13</LEGISLATURE>`,
# forme qui n'existe pas dans le fonds — l'extraction n'a **jamais** rien rendu,
# et la colonne était en réalité remplie par `rapports_vers_motive.py` depuis le
# périmètre. L'échec ne s'est vu qu'en inversant l'ordre des deux étapes.
LEGISLATURE = re.compile(r"<LEGISLATURE>\s*<NUMERO>(\d+)</NUMERO>", re.S)
ID_TEXTE = re.compile(r"<ID_TEXTE_\d+>(JORFTEXT\d+)</ID_TEXTE_\d+>")
# Le numéro du texte dont le dossier traite : celui qui suit immédiatement la
# nature, en tête de titre. Un titre de loi de ratification en cite plusieurs
# autres ensuite, qui ne sont pas les siens.
NUMERO_DOSSIER = re.compile(
    r"^\s*(?:loi|ordonnance|d[ée]cret|arr[êe]t[ée])\s+n[°º]\s*(\d{4}-\d+)", re.I)
NUMERO_TEXTE = re.compile(r"n[°º]\s*(\d{4}-\d+)")


def espaces(fragment: str) -> str:
    return re.sub(r"\s+", " ", fragment).strip()


def lire_dossiers(miroir: Path) -> tuple[dict[str, tuple[str, int | None]],
                                         dict[str, list[str]], dict[str, str]]:
    """Rend les dossiers lus, l'index inverse texte → dossiers, et leurs numéros."""
    dossiers: dict[str, tuple[str, int | None]] = {}       # id -> (titre, législature)
    numeros: dict[str, str] = {}                           # id -> numéro du texte
    listent: dict[str, list[str]] = defaultdict(list)      # JORFTEXT -> [dossiers]
    with tempfile.TemporaryDirectory() as tmp:
        # Le global seul ne voit aucun dossier ouvert depuis juillet 2025.
        deployer(miroir, "dole", Path(tmp))
        for fichier in Path(tmp).rglob("JORFDOLE*.xml"):
            brut = fichier.read_text(encoding="utf-8", errors="replace")
            trouve = TITRE.search(brut)
            if not trouve:
                continue
            titre = espaces(trouve.group(1))
            legislature = LEGISLATURE.search(brut)
            dossiers[fichier.stem] = (titre,
                                      int(legislature.group(1)) if legislature else None)
            numero = NUMERO_DOSSIER.match(titre)
            if numero:
                numeros[fichier.stem] = numero.group(1)
            for texte in ID_TEXTE.findall(brut):
                listent[texte].append(fichier.stem)
    return dossiers, listent, numeros


def resoudre(base: sqlite3.Connection, listent: dict[str, list[str]],
             numeros: dict[str, str]) -> tuple[dict[str, str], int, dict[str, int]]:
    resolus: dict[str, str] = {}
    ambigus = 0
    absents: dict[str, int] = defaultdict(int)
    for identifiant, nature, titre in base.execute(
            "SELECT id_jorf, nature, titre FROM texte_normatif"):
        candidats = listent.get(identifiant, [])
        if not candidats:
            absents[nature] += 1
            continue
        if len(candidats) == 1:
            resolus[identifiant] = candidats[0]
            continue
        # Plusieurs dossiers le listent : celui dont le titre porte son numéro.
        numero = NUMERO_TEXTE.search(titre)
        exacts = [d for d in candidats if numero and numeros.get(d) == numero.group(1)]
        if len(exacts) == 1:
            resolus[identifiant] = exacts[0]
        else:
            ambigus += 1
    return resolus, ambigus, dict(absents)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    miroir, chemin_base = (Path(a) for a in sys.argv[1:])

    base = sqlite3.connect(chemin_base)
    base.execute("PRAGMA foreign_keys = ON")
    dossiers, listent, numeros = lire_dossiers(miroir)
    resolus, ambigus, absents = resoudre(base, listent, numeros)

    # Recoupement avec ce qui est déjà en base : la mesure de fiabilité de la
    # méthode, faite sur les arêtes qu'une autre source avait déjà produites.
    anciennes = dict(base.execute("SELECT texte_id, dossier_id FROM issu_de"))
    communes = sorted(set(anciennes) & set(resolus))
    accord = sum(1 for t in communes if anciennes[t] == resolus[t])
    desaccords = [(t, anciennes[t], resolus[t]) for t in communes
                  if anciennes[t] != resolus[t]]

    nouvelles = sorted(set(resolus) - set(anciennes))
    base.executemany(
        "INSERT OR IGNORE INTO dossier (id_dole, titre, legislature) VALUES (?, ?, ?)",
        [(resolus[t], *dossiers[resolus[t]]) for t in nouvelles])
    base.executemany(
        "INSERT OR IGNORE INTO issu_de (texte_id, dossier_id, methode) "
        "VALUES (?, ?, 'declaree')",
        [(t, resolus[t]) for t in nouvelles])
    base.commit()

    total = base.execute("SELECT COUNT(*) FROM issu_de").fetchone()[0]
    print(f"dossiers DOLE lus                 : {len(dossiers)}")
    print(f"textes rattachés                  : {len(resolus)}")
    print(f"  plusieurs dossiers, non tranché : {ambigus}")
    print(f"  listés par aucun dossier        : "
          + ", ".join(f"{n} {c}" for n, c in sorted(absents.items())))
    print(f"recoupement avec l'existant       : {accord}/{len(communes)} d'accord")
    for texte, ancien, neuf in desaccords:
        print(f"  désaccord {texte} : {ancien} vs {neuf}")
    print(f"arêtes issu_de ajoutées           : {len(nouvelles)}  (total {total})")


if __name__ == "__main__":
    main()
