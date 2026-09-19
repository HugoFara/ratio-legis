#!/usr/bin/env python3
"""Confronte le graphe aux annotations humaines, article par article.

Tant que le jeu de 100 n'est pas annoté, toute mesure de précision du projet est
une auto-évaluation : des bornes de Wilson calculées sur des tirages que
l'auteur du code a jugés lui-même. Cet outil est ce qui en fait autre chose. Il
lit `annotations-100.csv` — ce qu'un humain a conclu, avec le passage désigné
par ses offsets — et le compare à ce que la base répond pour le même article.

Trois mesures, qui répondent à trois critères écrits :

1. **Le verdict.** Le § 4.3 de la feuille de route exige un taux de « raison
   non documentée » correctement identifié > 90 %, et zéro affirmation non
   étayée. Ici : parmi les articles que l'humain dit `non_documente`, combien la
   base rend-elle `raison_non_documentee` ; et combien d'articles la base dit
   `passage_motivant` alors que l'humain n'a trouvé aucun passage — c'est
   l'affirmation non étayée, celle qui doit être à zéro.

2. **Le passage.** Pour un article que l'humain dit `motive`, la base porte-t-elle
   une arête `motive` — sur l'article ou l'un de ses anciens numéros — dans le
   **même document** et dont l'intervalle **recouvre** le passage annoté ? Le
   document est retrouvé par l'empreinte de son texte brut, jamais par son nom :
   c'est la garantie que les deux offsets comptent dans la même chaîne. Un
   document que l'annotateur a trouvé hors corpus (`annoter.py e`) est compté à
   part, `hors_corpus` : la base ne pouvait pas le citer, et c'est un trou du
   corpus, pas un silence du fonds.

3. **La proposition.** Ce que valait le pré-remplissage de `jeu_annotation.py` :
   acceptée, corrigée, hors sujet — par strate, puisque les strates n'ont pas la
   même population documentaire.

Ne mesure que ce qui est annoté : une ligne sans `ANNOT_verdict` est ignorée et
comptée comme telle. Écrit une fiche par article dans le TSV de sortie, pour que
chaque chiffre du résumé soit retrouvable ligne à ligne.

Usage :
    verifier.py <annotations-100.csv> <base.sqlite> <corpus/rapports/> <sortie.tsv>
"""

from __future__ import annotations

import csv
import hashlib
import math
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "tools" / "prototype"))
from commentaires_rapports import texte_brut  # noqa: E402

# Ce que chaque verdict humain attend du verdict de la base.
ATTENDU = {"motive": {"passage_motivant"},
           "dossier_seulement": {"origine_situee", "motivation_du_texte"},
           "non_documente": {"raison_non_documentee"}}

COLONNES = ["num_article", "strate", "verdict_humain", "verdict_base", "concorde",
            "affirmation_non_etayee", "passage", "aretes_motive", "aretes_concordantes",
            "proposition_jugee", "annotateur"]


def wilson(succes: int, total: int, z: float = 1.96) -> float:
    """Borne inférieure de Wilson à 95 %, la convention de confiance du § 5.4."""
    if total == 0:
        return 0.0
    p = succes / total
    denominateur = 1 + z * z / total
    centre = p + z * z / (2 * total)
    ecart = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return (centre - ecart) / denominateur


def taux(succes: int, total: int) -> str:
    return (f"{succes} / {total} — {100 * succes / total:.1f} %, Wilson "
            f"{wilson(succes, total):.4f}" if total else "0 / 0")


def documents_par_empreinte(base: sqlite3.Connection) -> dict[str, int]:
    return {h: i for i, h in base.execute("SELECT id, hash FROM document")}


def aretes_motive(base: sqlite3.Connection, numero: str) -> list[tuple[int, int, int]]:
    """(document_id, offset_debut, offset_fin) sur l'article et ses anciens numéros."""
    return [tuple(r) for r in base.execute("""
        WITH RECURSIVE asc_a(anc) AS (
            SELECT id FROM article WHERE numero = ?
            UNION SELECT r.ancien_id FROM renumerote_de r JOIN asc_a ON r.article_id = asc_a.anc)
        SELECT DISTINCT m.document_id, m.offset_debut, m.offset_fin
        FROM asc_a JOIN motive m ON m.article_id = asc_a.anc""", (numero,))]


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    annotations, base_chemin, corpus, sortie = (Path(a) for a in sys.argv[1:])
    base = sqlite3.connect(f"file:{base_chemin}?mode=ro", uri=True)
    empreintes = documents_par_empreinte(base)
    verdicts = dict(base.execute(
        "SELECT a.numero, v.verdict FROM verdict v JOIN article a ON a.id = v.article_id"))

    lignes = list(csv.DictReader(annotations.open(encoding="utf-8")))
    annotees = [l for l in lignes if l["ANNOT_verdict"]]
    fiches: list[dict] = []
    # Les empreintes de l'index de preparer.py, quand il est là ; sinon le corpus.
    empreinte_cache: dict[str, str | None] = {}
    index = annotations.parent / "documents.tsv"
    if index.exists():
        with index.open(encoding="utf-8") as f:
            empreinte_cache = {e["fichier"]: e["sha256"]
                               for e in csv.DictReader(f, delimiter="\t")}

    for ligne in annotees:
        numero, humain = ligne["num_article"], ligne["ANNOT_verdict"]
        machine = verdicts.get(numero, "absent")
        aretes = aretes_motive(base, numero)
        fiche = {"num_article": numero, "strate": ligne["strate"],
                 "verdict_humain": humain, "verdict_base": machine,
                 "concorde": int(machine in ATTENDU.get(humain, set())),
                 "affirmation_non_etayee": int(machine == "passage_motivant"
                                               and humain != "motive"),
                 "passage": "", "aretes_motive": len(aretes), "aretes_concordantes": 0,
                 "proposition_jugee": ligne["proposition_jugee"],
                 "annotateur": ligne["annotateur"]}

        if humain == "motive" and ligne["ANNOT_document"]:
            nom = ligne["ANNOT_document"]
            if nom not in empreinte_cache:
                fichier = corpus / nom
                empreinte_cache[nom] = (hashlib.sha256(texte_brut(fichier).encode())
                                        .hexdigest() if fichier.exists() else None)
            document_id = empreintes.get(empreinte_cache[nom] or "")
            debut, fin = int(ligne["ANNOT_offset_debut"]), int(ligne["ANNOT_offset_fin"])
            if document_id is None:
                fiche["passage"] = ("hors_corpus" if nom.startswith("externe__")
                                    else "document_absent_de_la_base")
            else:
                concordantes = [a for a in aretes if a[0] == document_id
                                and a[1] < fin and debut < a[2]]
                fiche["aretes_concordantes"] = len(concordantes)
                fiche["passage"] = ("retrouve" if concordantes else
                                    "autre_passage" if aretes else "aucune_arete")
        fiches.append(fiche)

    with sortie.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES, delimiter="\t",
                                  lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(fiches)

    # ------------------------------------------------------------- résumé
    print(f"articles du jeu : {len(lignes)}, annotés : {len(annotees)}, "
          f"non annotés : {len(lignes) - len(annotees)}")
    if not annotees:
        return
    print("\n1. VERDICT (§ 4.3)")
    humains = Counter(f["verdict_humain"] for f in fiches)
    print("   verdicts humains :", dict(humains))
    croise: dict[str, Counter] = defaultdict(Counter)
    for f in fiches:
        croise[f["verdict_humain"]][f["verdict_base"]] += 1
    for humain, machines in croise.items():
        print(f"   {humain:18} → {dict(machines)}")
    non_doc = [f for f in fiches if f["verdict_humain"] == "non_documente"]
    reconnus = sum(f["verdict_base"] == "raison_non_documentee" for f in non_doc)
    print(f"   « raison non documentée » correctement identifiée (seuil > 90 %) : "
          f"{taux(reconnus, len(non_doc))}")
    non_etayees = sum(f["affirmation_non_etayee"] for f in fiches)
    print(f"   affirmations non étayées — base dit passage_motivant, l'humain n'en "
          f"trouve aucun (doit être 0) : {non_etayees}")
    print(f"   concordance globale : {taux(sum(f['concorde'] for f in fiches), len(fiches))}")

    print("\n2. PASSAGE (arête motive, même document, intervalles recouvrants)")
    motives = [f for f in fiches if f["verdict_humain"] == "motive"]
    etats = Counter(f["passage"] for f in motives)
    print(f"   articles motivés selon l'humain : {len(motives)} → {dict(etats)}")
    print(f"   rappel de motive au grain du passage : "
          f"{taux(etats['retrouve'], len(motives))}")
    print(f"   dont trous du corpus (document trouvé hors corpus) : {etats['hors_corpus']}")
    # Précision : la base affirme un passage ; l'humain le confirme, ou dit
    # qu'un autre passage motive, ou qu'aucun ne motive.
    affirme = [f for f in fiches if f["verdict_base"] == "passage_motivant"]
    confirmes = sum(f["passage"] == "retrouve" for f in affirme)
    print(f"   précision de passage_motivant, confirmée au passage : "
          f"{taux(confirmes, len(affirme))}")

    print("\n3. PROPOSITION DE LA MACHINE (jeu_annotation.py)")
    par_strate: dict[str, Counter] = defaultdict(Counter)
    for f in fiches:
        par_strate[f["strate"]][f["proposition_jugee"] or "?"] += 1
    total = Counter()
    for strate, comptes in sorted(par_strate.items()):
        total.update(comptes)
        print(f"   {strate:28} {dict(comptes)}")
    print(f"   {'total':28} {dict(total)}")
    proposees = total["acceptee"] + total["corrigee"] + total["hors_sujet"]
    print(f"   propositions acceptées telles quelles : {taux(total['acceptee'], proposees)}")
    print(f"   propositions dans le bon document (acceptée ou corrigée) : "
          f"{taux(total['acceptee'] + total['corrigee'], proposees)}")
    print(f"\n→ {sortie}")


if __name__ == "__main__":
    main()
