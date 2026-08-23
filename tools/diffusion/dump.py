#!/usr/bin/env python3
"""Produit le dump ouvert du graphe — la réciprocité promise au § 4, phase 4.

Le projet vit d'un écosystème de données publiques et d'outils associatifs. Le
§ 4.4 en tire une obligation : republier le graphe, sous la même Licence Ouverte
que les données amont. Ce n'est pas une exportation de commodité, c'est la
contrepartie.

**Ce que le dump contient.** La base est un fichier : elle *est* le dump. On en
tire une copie compacte, augmentée d'une table `diffusion` qui porte la licence,
les attributions obligatoires, l'horodatage et le commit du code qui l'a produite
— un dump dont on ne peut pas dire quel code l'a écrit n'est pas auditable. Les
tables d'arêtes sont en outre exportées en TSV, pour qui ne veut pas de SQLite.

**Ce qu'il ne contient pas, et pourquoi.** `ATTRIBUTION.md` suspend la
rediffusion du texte des rapports de commission : aucune page des deux assemblées
n'affirme qu'ils relèvent de la Licence Ouverte, contrairement aux jeux de
`data.senat.fr` et `data.assemblee-nationale.fr`. Ce sont des informations
publiques réutilisables au titre du régime général de la loi du 17 juillet 1978,
sans licence explicite. Les 107 Mo de texte de rapport sont donc remplacés par un
avis ; **l'URL, le hachage et les offsets restent**, ce qui suffit à quiconque
veut refaire le lien depuis la source.

Restent les fenêtres de preuve. Les retirer rendrait les arêtes inauditables, ce
qu'interdit le § 5.1 — provenance ou silence. Celles qui viennent d'un rapport
vont jusqu'à 400 caractères, ce qui est un extrait ; elles sont **ramenées aux
soixante caractères** que le schéma exige au minimum. Soixante caractères sont la
preuve irréductible ; quatre cents sont du contenu. C'est un arbitrage explicite
entre deux règles du projet, non un oubli.

L'option `--strict` rend l'autre arbitrage : elle retire du dump les rapports de
commission *et* les arêtes qui en dépendent, et écrit combien.

Les autres sources ne posent pas la question. LEGI, JORF, DOLE, les amendements
des deux chambres et les considérants d'EUR-Lex portent tous une licence de
réutilisation explicite.

Usage :
    dump.py <base.sqlite> <destination/> [--strict]
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AVIS = ("Texte non rediffusé : régime de réutilisation des rapports de commission "
        "non confirmé par les assemblées (voir ATTRIBUTION.md). "
        "L'URL, le hachage et les offsets de ce document sont conservés.")

# Les arêtes et leurs clefs, sans aucun texte long : le format universel, pour
# qui ne veut pas ouvrir un fichier SQLite.
TABLES_TSV = ["article", "renumerote_de", "texte_normatif", "produite_par", "issu_de",
              "dossier", "verdict", "resulte_de", "vise", "porte_sur", "motive",
              "transpose", "cite_acte_ue", "acte_ue", "renvoie_a", "repris_de"]

ATTRIBUTIONS = [
    ("dila", "Source : DILA — Légifrance (fonds LEGI, JORF, DOLE), "
             "Licence Ouverte / Etalab 2.0"),
    ("assemblee", "Source : Assemblée nationale — open data, Licence Ouverte / Etalab"),
    ("senat", "Source : Sénat — data.senat.fr, licence ouverte reprenant les termes "
              "de data.gouv.fr"),
    ("union", "© Union européenne, https://eur-lex.europa.eu, 1998-2026 — "
              "réutilisation autorisée, décision 2011/833/UE"),
    ("rapports", "Rapports de commission : informations publiques (loi du 17 juillet "
                 "1978), régime de réutilisation non confirmé — texte non rediffusé"),
]


def empreinte(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def commit_courant() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "(hors dépôt git)"


def retirer_les_rapports(base: sqlite3.Connection, strict: bool) -> dict[str, int]:
    """Applique la suspension d'ATTRIBUTION.md, dans l'une des deux lectures."""
    compte = {}
    if not strict:
        compte["documents_dont_le_texte_est_retire"] = base.execute(
            "UPDATE document SET texte = ? WHERE type = 'rapport_commission'",
            (AVIS,)).rowcount
        # `CHECK (length(fenetre) >= 60)` : soixante est le plancher du schéma,
        # donc la preuve irréductible. Tout ce qui dépasse est de l'extrait.
        compte["fenetres_de_preuve_ramenees_a_60_caracteres"] = base.execute(
            "UPDATE preuve SET fenetre = substr(fenetre, 1, 60) WHERE length(fenetre) > 60"
            " AND id IN (SELECT m.preuve_id FROM motive m JOIN document d"
            "            ON d.id = m.document_id WHERE d.type = 'rapport_commission')"
        ).rowcount
        return compte

    aretes = [(i, p) for i, p in base.execute(
        "SELECT m.id, m.preuve_id FROM motive m JOIN document d ON d.id = m.document_id "
        "WHERE d.type = 'rapport_commission'")]
    base.executemany("DELETE FROM motive WHERE id = ?", [(i,) for i, _ in aretes])
    base.executemany("DELETE FROM preuve WHERE id = ?",
                     [(p,) for _, p in aretes if p is not None])
    compte["aretes_motive_retirees"] = len(aretes)
    compte["documents_retires"] = base.execute(
        "DELETE FROM document WHERE type = 'rapport_commission'").rowcount
    return compte


def table_diffusion(base: sqlite3.Connection, source: Path, strict: bool,
                    compte: dict[str, int]) -> None:
    base.execute("DROP TABLE IF EXISTS diffusion")
    base.execute("CREATE TABLE diffusion (clef TEXT PRIMARY KEY, valeur TEXT NOT NULL)"
                 " STRICT")
    lignes = [
        ("projet", "Ratio Legis — graphe de provenance normative du droit français"),
        ("licence_donnees", "Licence Ouverte / Etalab 2.0"),
        ("licence_code", "AGPL-3.0-or-later"),
        ("date_production", datetime.now(timezone.utc).isoformat(timespec="seconds")),
        ("commit", commit_courant()),
        ("base_source", source.name),
        ("mode", "strict" if strict else "avis"),
        ("avertissement", "Ce dump est une donnée dérivée. Il ne fait pas foi : "
                          "le droit en vigueur est celui publié par Légifrance."),
        ("non_interpretatif", "Le graphe documente la provenance des textes. Il ne "
                              "produit ni interprétation juridique, ni conseil."),
    ]
    lignes += [(f"attribution_{c}", v) for c, v in ATTRIBUTIONS]
    lignes += [(f"suspension_{c}", str(v)) for c, v in compte.items()]
    base.executemany("INSERT INTO diffusion (clef, valeur) VALUES (?, ?)", lignes)


DICTIONNAIRE = {
    "article": "un article de code, identifié par son numéro",
    "version_article": "une rédaction datée d'un article, telle que LEGI la publie",
    "segment": "un alinéa d'une version, avec ses offsets dans le texte",
    "texte_normatif": "une loi, une ordonnance, un décret ou un arrêté",
    "dossier": "un dossier législatif (DOLE)",
    "document": "un document de motivation : exposé des motifs, étude d'impact, "
                "avis du Conseil d'État, rapport de commission, rapport au Président",
    "amendement": "un amendement déposé, adopté ou non, avec son auteur et son sort",
    "acteur": "un parlementaire ou un groupe, tel que les chambres le nomment",
    "acte_ue": "un acte de l'Union identifié par son CELEX",
    "considerant": "un considérant d'un acte de l'Union, dans l'ordre de publication",
    "texte_discute": "un texte déposé ou transmis, à un stade de la navette",
    "preuve": "la fenêtre textuelle qui fonde une arête dérivée",
    "produite_par": "version d'article → texte qui l'a produite (LEGI, déclarée)",
    "issu_de": "texte → dossier législatif (DOLE, déclarée)",
    "renumerote_de": "article → article dont il reprend la disposition",
    "repris_de": "segment → segment antérieur dont il reprend le texte",
    "resulte_de": "segment → amendement qui l'a écrit — l'arête critique du projet",
    "motive": "document → article ou segment que l'un de ses passages explique",
    "porte_sur": "article d'un texte discuté → article du code qu'il modifie",
    "vise": "amendement → article du code que son dispositif désigne",
    "renvoie_a": "segment → article cité, interne ou externe au code",
    "cite_acte_ue": "segment → acte de l'Union qu'il nomme",
    "transpose": "texte → acte de l'Union dont il déclare la transposition",
    "verdict": "pour chaque article en vigueur, ce que le graphe sait en dire",
    "diffusion": "licence, attributions et provenance de ce dump",
}


def lisez_moi(base: sqlite3.Connection, destination: Path, strict: bool,
              compte: dict[str, int]) -> Path:
    tables = {n for (n,) in base.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    lignes = ["# Ratio Legis — dump ouvert du graphe de provenance", "",
              "Graphe de provenance normative du **code de la consommation** en "
              "vigueur : pour un article, les matériaux qui expliquent pourquoi il "
              "existe sous cette forme.", "",
              "**Ce dump ne fait pas foi.** Le droit en vigueur est celui publié par "
              "Légifrance. Le graphe documente la provenance des textes ; il ne "
              "produit ni interprétation juridique, ni conseil.", "",
              "## Licence", "",
              "Données sous **Licence Ouverte / Etalab 2.0**, code sous "
              "**AGPL-3.0-or-later**. Les mentions ci-dessous sont obligatoires en "
              "cas de réutilisation.", ""]
    lignes += [f"- {v}" for _, v in ATTRIBUTIONS]
    lignes += ["", "## Ce que ce dump ne contient pas", ""]
    if strict:
        lignes += ["Les rapports de commission et les arêtes `motive` qui en "
                   "dépendent en ont été **retirés**, leur régime de réutilisation "
                   "n'étant pas confirmé par les assemblées. Le verdict a été "
                   "recalculé en conséquence : cette base est cohérente avec "
                   "elle-même, non avec celle dont elle vient."]
    else:
        lignes += ["Le **texte** des rapports de commission n'est pas rediffusé : "
                   "leur régime de réutilisation n'est pas confirmé par les "
                   "assemblées. Leur URL, leur hachage et les offsets des passages "
                   "restent présents, ce qui suffit à refaire le lien depuis la "
                   "source. Les fenêtres de preuve qui en viennent sont ramenées aux "
                   "soixante caractères que le schéma exige au minimum."]
    lignes += [""] + [f"- `{c}` : {v}" for c, v in compte.items()]
    lignes += ["", "## Tables", "", "| Table | Lignes | Contenu |", "|---|---:|---|"]
    for nom, description in DICTIONNAIRE.items():
        if nom in tables:
            n = base.execute(f"SELECT COUNT(*) FROM {nom}").fetchone()[0]
            lignes.append(f"| `{nom}` | {n} | {description} |")
    lignes += ["", "## Comment lire une arête", "",
               "Chaque arête dérivée porte une `methode` (`declaree`, `derivee`, "
               "`inferee`), une `confiance` — borne inférieure de Wilson à 95 % de la "
               "précision mesurée à la main — et un `preuve_id` qui pointe la fenêtre "
               "textuelle qui la fonde. Une arête dérivée sans preuve est refusée à "
               "l'écriture, pas signalée à la lecture.", "",
               "Les précisions mesurées et leurs échantillons sont publiés avec le "
               "code, dans `data/mesures/`.", ""]
    chemin = destination / "LISEZ-MOI.md"
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return chemin


def exporter_tsv(base: sqlite3.Connection, destination: Path) -> list[Path]:
    dossier = destination / "tsv"
    dossier.mkdir(parents=True, exist_ok=True)
    connues = {n for (n,) in base.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    ecrits = []
    for table in TABLES_TSV:
        if table not in connues:
            continue
        curseur = base.execute(f"SELECT * FROM {table}")
        colonnes = [c[0] for c in curseur.description]
        chemin = dossier / f"{table}.tsv"
        with chemin.open("w", encoding="utf-8", newline="") as sortie:
            graveur = csv.writer(sortie, delimiter="\t", lineterminator="\n")
            graveur.writerow(colonnes)
            for ligne in curseur:
                graveur.writerow(["" if v is None else
                                  str(v).replace("\t", " ").replace("\n", " ")
                                  for v in ligne])
        ecrits.append(chemin)
    return ecrits


def main() -> None:
    arguments = [a for a in sys.argv[1:] if a != "--strict"]
    strict = "--strict" in sys.argv
    if len(arguments) != 2:
        sys.exit(__doc__)
    source, destination = Path(arguments[0]), Path(arguments[1])
    destination.mkdir(parents=True, exist_ok=True)

    # `VACUUM INTO` produit une copie compacte et cohérente sans toucher à
    # l'original, y compris si celui-ci est en cours de lecture.
    cible = destination / "ratio-legis.sqlite"
    cible.unlink(missing_ok=True)
    sqlite3.connect(source).execute("VACUUM INTO ?", (str(cible),))

    base = sqlite3.connect(cible)
    base.execute("PRAGMA foreign_keys = ON")
    compte = retirer_les_rapports(base, strict)
    base.commit()
    if strict:
        # Retirer 624 arêtes `motive` sans recalculer le verdict laisserait la
        # base affirmer qu'un passage motive un article qu'elle ne peut plus
        # montrer. Un dump doit être cohérent avec lui-même, pas avec la base
        # dont il vient.
        base.close()
        subprocess.run([sys.executable,
                        str(Path(__file__).resolve().parent.parent.parent
                            / "ingestion" / "verdict.py"), str(cible)],
                       check=True, stdout=subprocess.DEVNULL)
        base = sqlite3.connect(cible)
        base.execute("PRAGMA foreign_keys = ON")
        compte["verdict_recalcule_articles_muets"] = base.execute(
            "SELECT COUNT(*) FROM verdict WHERE verdict = 'raison_non_documentee'"
        ).fetchone()[0]
    table_diffusion(base, source, strict, compte)
    base.commit()
    violations = list(base.execute("PRAGMA foreign_key_check"))
    notice = lisez_moi(base, destination, strict, compte)
    fichiers = exporter_tsv(base, destination)
    base.commit()
    base.execute("VACUUM")
    base.close()

    fichiers.insert(0, cible)
    fichiers.insert(1, notice)
    manifeste = destination / "MANIFESTE.tsv"
    with manifeste.open("w", encoding="utf-8", newline="") as sortie:
        graveur = csv.writer(sortie, delimiter="\t", lineterminator="\n")
        graveur.writerow(["fichier", "octets", "sha256"])
        for f in fichiers:
            graveur.writerow([f.relative_to(destination), f.stat().st_size, empreinte(f)])

    print(f"dump écrit dans {destination}")
    print(f"  base            : {cible.stat().st_size / 1048576:.0f} Mo "
          f"(source {source.stat().st_size / 1048576:.0f} Mo)")
    print(f"  tables en TSV   : {len(fichiers) - 1}")
    for clef, valeur in compte.items():
        print(f"  {clef} : {valeur}")
    print(f"  intégrité       : {len(violations)} violation(s) de clef étrangère")
    print(f"  manifeste       : {manifeste}")


if __name__ == "__main__":
    main()
