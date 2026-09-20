#!/usr/bin/env python3
"""« Si je modifie cet article, qu'est-ce qui bouge ? »

La question du légiste n'est pas celle du chercheur. `graphe.py` remonte le
temps : pourquoi cet article est ce qu'il est. Ce module descend l'arête
`renvoie_a` dans l'autre sens : **ce qu'une modification déplacerait**, article
par article, avec la phrase exacte qui crée la dépendance.

C'est le produit le plus immédiatement utilisable de toute la base, et il était
enterré au milieu d'une fiche de provenance sous le titre « ce qui cite cet
article », réduit à une liste de numéros. Il ne dépend d'aucune arête difficile :
`renvoie_a` est dérivée du texte des articles, elle porte sa fenêtre de preuve, et
elle est complète sur le fonds chargé — parties réglementaire comprise.

**Ce qu'il rend, et pourquoi ce découpage.**

*Ce qui dépend de cet article*, par onde. Le rang 1 est direct : un article le
cite. Le rang 2 cite un article du rang 1 — il ne bougerait qu'en second, mais il
bougerait. Un légiste qui ne regarde que le rang 1 relit la moitié de ce qu'il
faut relire.

*Ce dont cet article dépend*, avec l'état de résolution de chaque cible. Une
citation non résolue n'est pas une incohérence du droit : c'est une limite du
fonds chargé, et les confondre ferait passer un trou de périmètre pour un défaut
de la loi. La distinction est dans la donnée (`renvoie_a.portee`), elle est
rendue telle quelle.

*Le verdict de chaque article touché.* Un article que rien ne documente et que la
modification déplace est le cas coûteux : personne ne pourra dire pourquoi il
était écrit ainsi. C'est le renseignement que la partie réglementaire rend le
plus souvent, et c'est là que ce module sert le plus.

**Aucune inférence.** Les arêtes descendues sont celles de `renvoie_a`, toutes
munies d'une fenêtre de preuve ou déclarées. Le module ne calcule aucune
distance, ne pondère rien, n'ordonne que par le rang de l'onde puis par le numéro
— un ordre total, donc reproductible (§ 5.2).

Usage :
    retentissement.py <base.sqlite> <numéro d'article> [--profondeur N] [--html <f>]
    retentissement.py <base.sqlite> --sommet [N]
"""

from __future__ import annotations

import html
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citation import extrait  # noqa: E402
from style import RUBRIQUE, SOCLE  # noqa: E402

PROFONDEUR = 3
# Au-delà, la liste cesse d'être une liste de relecture et devient un extrait du
# code. Le total, lui, reste affiché : une troncature muette ferait passer une
# limite d'affichage pour un résultat.
PLAFOND_LISTE = 40
SOMMET = 25

PARTIES = ("L", "R", "D")
VERDICT_COURT = {
    "passage_motivant": "un passage l'explique",
    "origine_situee": "origine située",
    "motivation_du_texte": "seul son texte est motivé",
    "raison_non_documentee": "raison non documentée",
}
PORTEE = {
    "interne": "résolue dans le fonds",
    "externe": "autre code — hors du fonds chargé",
    "non_resolue": "numéro de ce code sans version couvrant la date de citation",
}


def partie_de(numero: str) -> str:
    return numero[:1] if numero[:1] in PARTIES else "?"


def retentir(base: sqlite3.Connection, numero: str,
             profondeur: int = PROFONDEUR) -> dict:
    base.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in base.execute(s, a)]  # noqa: E731

    version = q("""SELECT v.id_legi, v.date_debut FROM version_en_vigueur v
                   JOIN article_courant a ON a.id = v.article_id
                   WHERE a.numero = ? ORDER BY v.date_debut DESC, v.id_legi""", numero)
    if not version:
        return {}
    d = {"numero": numero, "version": version[0], "profondeur": profondeur}

    # L'onde. `min(rang)` parce qu'un article peut être atteint par deux chemins de
    # longueurs différentes : c'est le plus court qui dit quand il bouge. La borne
    # sur le rang termine la récursion même si le code se cite en cycle, ce qu'il
    # fait (L121-2 cite L112-1-1, qui peut le citer en retour à travers un tiers).
    d["entrants"] = q("""
        WITH RECURSIVE onde(numero, rang) AS (
            SELECT ?, 0
            UNION
            SELECT r.article_citant, o.rang + 1
            FROM onde o JOIN renvois_entrants r ON r.article_cite = o.numero
            WHERE o.rang < ?)
        SELECT o.numero, min(o.rang) AS rang, v.verdict, v.partie
        FROM onde o
        LEFT JOIN article_courant a ON a.numero = o.numero
        LEFT JOIN verdict v ON v.article_id = a.id
        WHERE o.rang > 0 AND o.numero <> ?
        GROUP BY o.numero
        ORDER BY rang, o.numero""", numero, profondeur, numero)

    # La phrase qui crée la dépendance, pour le seul rang direct : c'est celle que
    # le légiste devra rouvrir. Aux rangs suivants, elle ne parle plus de cet
    # article-ci et l'afficher tromperait.
    preuves = {r["article_citant"]: r for r in q("""
        SELECT article_citant,
               min((SELECT fenetre FROM preuve WHERE id = preuve_id)) AS fenetre
        FROM renvois_entrants WHERE article_cite = ?
        GROUP BY article_citant""", numero)}
    for e_ in d["entrants"]:
        e_["fenetre"] = (preuves.get(e_["numero"], {}) or {}).get("fenetre")

    d["par_rang"] = {}
    d["par_partie"] = {}
    for e_ in d["entrants"]:
        d["par_rang"][e_["rang"]] = d["par_rang"].get(e_["rang"], 0) + 1
        partie = e_["partie"] or partie_de(e_["numero"])
        d["par_partie"][partie] = d["par_partie"].get(partie, 0) + 1
    d["muets"] = sum(1 for e_ in d["entrants"]
                     if e_["verdict"] == "raison_non_documentee")

    # Ce dont l'article dépend. `porte_sur` n'entre pas ici : la question est le
    # texte, pas le dossier législatif.
    d["sortants"] = q("""
        SELECT s.ordre + 1 AS alinea, r.numero_cite, r.code_cite, r.portee,
               (SELECT fenetre FROM preuve WHERE id = r.preuve_id) AS fenetre,
               (SELECT v.verdict FROM article a2 JOIN verdict v ON v.article_id = a2.id
                WHERE a2.id = r.article_id) AS verdict
        FROM version_en_vigueur v
        JOIN article_courant a  ON a.id = v.article_id
        JOIN segment s  ON s.version_id = v.id_legi
        JOIN renvoie_a r ON r.segment_id = s.id
        WHERE a.numero = ?
        ORDER BY s.ordre, r.numero_cite""", numero)
    return d


def sommet(base: sqlite3.Connection, combien: int = SOMMET) -> list[dict]:
    """Les articles dont la modification déplacerait le plus de monde, au rang 1.

    Mesure de structure, pas de provenance : elle ne dit pas qu'un article est
    important, elle dit combien d'articles en vigueur le citent. C'est la même
    donnée que la fiche, lue à l'échelle du code.
    """
    base.row_factory = sqlite3.Row
    return [dict(r) for r in base.execute("""
        SELECT r.article_cite AS numero, count(DISTINCT r.article_citant) AS citants,
               v.verdict, v.partie
        FROM renvois_entrants r
        LEFT JOIN article_courant a ON a.numero = r.article_cite
        LEFT JOIN verdict v ON v.article_id = a.id
        GROUP BY r.article_cite
        ORDER BY citants DESC, r.article_cite
        LIMIT ?""", (combien,))]


# ------------------------------------------------------------------ rendu texte

def en_texte(d: dict) -> str:
    if not d:
        return "Article introuvable ou non en vigueur."
    L = [f"RETENTISSEMENT DE L'ARTICLE {d['numero']}",
         f"  version en vigueur depuis le {d['version']['date_debut']}",
         f"  onde suivie jusqu'au rang {d['profondeur']}", ""]

    L.append(f"CE QUI BOUGERAIT ({len(d['entrants'])} article(s) en vigueur)")
    if not d["entrants"]:
        L.append("  Aucun article du fonds chargé ne renvoie à celui-ci, ni "
                 "directement ni par ricochet.")
    else:
        L.append("  par rang : " + ", ".join(
            f"rang {r} — {n}" for r, n in sorted(d["par_rang"].items())))
        L.append("  par partie : " + ", ".join(
            f"{p} — {n}" for p, n in sorted(d["par_partie"].items())))
        L.append(f"  dont {d['muets']} dont la raison n'est pas documentée : les "
                 "déplacer, c'est déplacer des articles dont personne ne peut dire "
                 "pourquoi ils sont écrits ainsi.")
    for e_ in d["entrants"][:PLAFOND_LISTE]:
        marque = VERDICT_COURT.get(e_["verdict"], "hors verdict")
        L.append(f"\n  [rang {e_['rang']}] {e_['numero']}  ({marque})")
        if e_["fenetre"]:
            L.append("      " + extrait(e_["fenetre"], 200))
    reste = len(d["entrants"]) - PLAFOND_LISTE
    if reste > 0:
        L.append(f"\n  … et {reste} autre(s) — la liste complète est dans le rendu "
                 "HTML et dans l'API.")

    L.append(f"\nCE DONT IL DÉPEND ({len(d['sortants'])} renvoi(s))")
    if not d["sortants"]:
        L.append("  Cet article ne renvoie à aucun autre.")
    for r in d["sortants"]:
        cible = r["numero_cite"] + (f" [{r['code_cite']}]" if r["code_cite"] else "")
        L.append(f"  alinéa {r['alinea']} → {cible}  ({PORTEE[r['portee']]})")
    return "\n".join(L)


def sommet_en_texte(lignes: list[dict]) -> str:
    L = ["LES ARTICLES LES PLUS CITÉS DU FONDS",
         "  Nombre d'articles en vigueur qui renvoient à celui-ci, au rang 1.",
         "  Mesure de structure : elle ne dit pas qu'un article compte, elle dit",
         "  combien d'autres le nomment.", ""]
    L.append(f"  {'article':22s}{'citants':>8}  {'partie':7s}verdict")
    for r in lignes:
        L.append(f"  {r['numero']:22s}{r['citants']:8d}  {r['partie'] or '?':7s}"
                 f"{VERDICT_COURT.get(r['verdict'], 'hors verdict')}")
    return "\n".join(L)


# ------------------------------------------------------------------- rendu HTML

def e(x) -> str:
    return html.escape(str(x if x is not None else ""))


STYLE = SOCLE + """
main{max-width:52rem}
.bilan{display:flex;flex-wrap:wrap;gap:.6rem;margin:.8rem 0 1.4rem;font-size:.8rem}
.bilan span{border:1px solid var(--trait);background:var(--carte);
padding:.3rem .6rem;border-radius:2px}
.bilan .muet{border-color:var(--acc);color:var(--acc)}
.onde{border-left:3px solid var(--trait);padding:.35rem 0 .35rem .9rem;margin:.7rem 0}
.onde.direct{border-left-color:var(--acc)}
.onde b{font-size:.95rem}
.meta{font-size:.74rem;color:var(--doux);display:flex;gap:.8rem;flex-wrap:wrap;margin-top:.2rem}
.meta .muet{color:var(--acc)}
.preuve{font-size:.76rem;color:var(--doux);margin-top:.3rem;white-space:pre-wrap}
"""

PIED = ("""<footer>Ratio Legis — arête <code>renvoie_a</code>, dérivée du texte des
articles et munie de sa fenêtre de preuve. Aucune arête inférée, aucun modèle de
langue. « Ce qui bougerait » nomme les articles qui citent celui-ci, directement ou
par ricochet ; il ne dit pas ce qu'il faudrait y écrire. Donnée dérivée : ne fait
pas foi. Source : DILA — Légifrance (fonds LEGI), Licence Ouverte /
Etalab&nbsp;2.0.</footer>""")


def en_html(d: dict) -> str:
    if not d:
        return "<p>Article introuvable.</p>"
    p = [f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(d['numero'])} — retentissement</title><style>{STYLE}</style></head>
<body><main>
{RUBRIQUE}
<h1>Si je modifie l'article {e(d['numero'])}</h1>
<p class="chapeau">Version en vigueur depuis le {e(d['version']['date_debut'])} ·
onde suivie jusqu'au rang {d['profondeur']}</p>
<h2>Ce qui bougerait ({len(d['entrants'])})</h2>"""]
    if not d["entrants"]:
        p.append('<p class="silence">Aucun article du fonds chargé ne renvoie à '
                 "celui-ci, ni directement ni par ricochet.</p>")
    else:
        p.append('<div class="bilan">' + "".join(
            f"<span>rang {r} — {n} article(s)</span>"
            for r, n in sorted(d["par_rang"].items()))
            + "".join(f"<span>partie {e(pa)} — {n}</span>"
                      for pa, n in sorted(d["par_partie"].items()))
            + (f'<span class="muet">{d["muets"]} sans raison documentée</span>'
               if d["muets"] else "") + "</div>")
        if d["muets"]:
            p.append('<p class="silence">Les déplacer, c\'est déplacer des articles '
                     "dont aucune source dépouillée ne dit pourquoi ils sont écrits "
                     "ainsi. C'est le coût que la mesure d'hygiène chiffre à "
                     "l'échelle du code.</p>")
    for x in d["entrants"]:
        muet = x["verdict"] == "raison_non_documentee"
        p.append(f'<div class="onde{" direct" if x["rang"] == 1 else ""}">'
                 f'<b>{e(x["numero"])}</b>'
                 f'<div class="meta"><span>rang {x["rang"]}</span>'
                 f'<span>partie {e(x["partie"] or partie_de(x["numero"]))}</span>'
                 f'<span class="{"muet" if muet else ""}">'
                 f'{e(VERDICT_COURT.get(x["verdict"], "hors verdict"))}</span></div>'
                 + (f'<div class="preuve">{e(extrait(x["fenetre"], 300))}</div>'
                    if x["fenetre"] else "") + "</div>")

    p.append(f"<h2>Ce dont il dépend ({len(d['sortants'])})</h2>")
    if not d["sortants"]:
        p.append('<p class="silence">Cet article ne renvoie à aucun autre.</p>')
    else:
        p.append("<table><tr><th>Alinéa</th><th>Cible</th><th>État de la cible</th>"
                 "<th>Verdict de la cible</th></tr>")
        for r in d["sortants"]:
            cible = e(r["numero_cite"]) + (f' <span class="silence">'
                                           f'{e(r["code_cite"])}</span>'
                                           if r["code_cite"] else "")
            p.append(f'<tr><td>{r["alinea"]}</td><td>{cible}</td>'
                     f'<td>{e(PORTEE[r["portee"]])}</td>'
                     f'<td>{e(VERDICT_COURT.get(r["verdict"], "—"))}</td></tr>')
        p.append("</table>")
    p.append(PIED + "</main></body></html>")
    return "".join(p)


def sommet_en_html(lignes: list[dict]) -> str:
    p = [f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Les articles les plus cités</title><style>{STYLE}</style></head>
<body><main>{RUBRIQUE}<h1>Les articles les plus cités du fonds</h1>
<p class="chapeau">Nombre d'articles en vigueur qui renvoient à celui-ci, au
rang 1. Mesure de structure : elle ne dit pas qu'un article compte, elle dit
combien d'autres le nomment.</p>
<table><tr><th>Article</th><th>Citants</th><th>Partie</th><th>Verdict</th></tr>"""]
    for r in lignes:
        p.append(f'<tr><td>{e(r["numero"])}</td><td>{r["citants"]}</td>'
                 f'<td>{e(r["partie"] or "?")}</td>'
                 f'<td>{e(VERDICT_COURT.get(r["verdict"], "hors verdict"))}</td></tr>')
    p.append("</table>" + PIED + "</main></body></html>")
    return "".join(p)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    sortie = (Path(sys.argv[sys.argv.index("--html") + 1])
              if "--html" in sys.argv else None)

    if "--sommet" in sys.argv:
        suite = sys.argv[sys.argv.index("--sommet") + 1:]
        combien = int(suite[0]) if suite and suite[0].isdigit() else SOMMET
        lignes = sommet(base, combien)
        rendu = sommet_en_html(lignes) if sortie else sommet_en_texte(lignes)
    else:
        profondeur = PROFONDEUR
        if "--profondeur" in sys.argv:
            profondeur = int(sys.argv[sys.argv.index("--profondeur") + 1])
        donnees = retentir(base, sys.argv[2], profondeur)
        rendu = en_html(donnees) if sortie else en_texte(donnees)

    if sortie:
        sortie.write_text(rendu, encoding="utf-8")
        print(f"écrit : {sortie} ({sortie.stat().st_size // 1024} Ko)")
    else:
        print(rendu)
    base.close()


if __name__ == "__main__":
    main()
