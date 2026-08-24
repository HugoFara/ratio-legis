#!/usr/bin/env python3
"""« Qu'a-t-on déjà tenté sur cet article, et qu'est-ce qui l'a fait échouer ? »

`graphe.py` remonte à l'origine, `retentissement.py` descend aux conséquences.
Ce module regarde de côté : **ce qui a été proposé sur cet article et n'a pas
abouti**. C'est le seul rendu du produit dont la matière soit majoritairement
faite de droit qui n'existe pas.

La fiche de `graphe.py` en portait déjà une table de cinq colonnes, triée par
comparaison littérale à la chaîne « Adopté », affichant le libellé source sans le
traduire, et muette sur ce que l'amendement proposait. Ce module rend la même
matière avec ce qui lui manquait : la famille du sort, le motif de
l'irrecevabilité quand il est déclaré, l'objet cité, l'adresse de la pièce, et la
voie par laquelle la tentative est rattachée.

**Deux voies, et elles ne valent pas la même chose.** Elles sont distinguées à
l'écran, comme l'exige la règle § 5.4 :

- `alinéa écrit` — l'amendement a écrit un alinéa qui subsiste dans la version en
  vigueur, la chaîne `resulte_de` puis `repris_de` le porte. Confiance 0,8933.
- `cible déclarée` — le dispositif de l'amendement nomme cet article et la
  formule qui le modifie. C'est la seule voie ouverte à un amendement rejeté, qui
  par construction n'a écrit aucun texte. Confiance 0,6212, la plus basse du
  graphe (`docs/10` § 3).

**Ce que le module ne dit pas.** Il ne dit pas pourquoi un amendement a échoué.
« Rejeté » est un fait, « retiré » aussi ; ce qui s'est joué entre les deux est
dans le compte rendu de séance, que le graphe ne contient pas. Il ne dit pas
davantage qu'un amendement retiré a échoué : un auteur retire couramment le sien
après avoir obtenu satisfaction. Le sort est nommé, jamais interprété.

**Un fait s'y lit pourtant sans commentaire.** L'irrecevabilité au titre de
l'article 40 de la Constitution est le seul motif d'échec dont la cause soit
publiée : l'amendement aggravait une charge publique et n'a jamais été discuté.
Rendre visible qu'un dispositif a été écarté sans débat, et par qui, est
exactement ce que le § 4.3 appelle « un résultat de premier ordre ».

Usage :
    tentatives.py <base.sqlite> <numéro d'article> [--html <fichier>]
    tentatives.py <base.sqlite> --sommet [N] [--html <fichier>]
"""

from __future__ import annotations

import html
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
from citation import cite, extrait  # noqa: E402
from sort_des_amendements import ECHEC, EN_FRANCAIS  # noqa: E402

SOMMET = 25

VOIES = {
    "alinea_ecrit": "a écrit un alinéa qui subsiste",
    "cible_declaree": "cible déclarée par le dispositif",
}

# Ce que dit le fondement d'une irrecevabilité, en une ligne. Le motif est publié
# par la chambre ; sa portée ne l'est pas, et un lecteur qui voit « article 40 »
# sans savoir ce qu'il interdit ne sait rien.
PORTEE_DU_MOTIF = {
    "article 40": "aggravait une charge publique — article 40 de la Constitution",
    "article 45": "sans lien avec le texte — cavalier, article 45 de la Constitution",
    "article 41": "relevait du domaine réglementaire — article 41 de la Constitution",
    "article 44 bis": "règle de l'entonnoir — article 44 bis du règlement du Sénat",
    "LOLF": "contraire à la loi organique relative aux lois de finances",
    "LOLFSS": "contraire à la loi organique relative aux lois de financement de "
              "la sécurité sociale",
}

CHAMBRES = {"assemblee": "Assemblée nationale", "senat": "Sénat"}

# L'Assemblée ne publie pas d'adresse par amendement dans son jeu open data. Le
# dire est préférable à laisser un blanc : le § 4.3 exige que toute pièce reste
# citable, et une pièce qu'on ne peut pas atteindre doit s'annoncer comme telle.
SANS_URL = "pas d'adresse publiée dans le jeu open data de la chambre"


def _naturel(numero: str) -> tuple:
    """Ordre de tri d'un numéro d'amendement : « 9 » avant « 73 rect. »."""
    tete = "".join(c for c in numero if c.isdigit())
    return (int(tete) if tete else 0, numero)


def tenter(base: sqlite3.Connection, numero: str) -> dict:
    base.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in base.execute(s, a)]  # noqa: E731

    version = q("""SELECT v.id_legi, v.date_debut FROM version_en_vigueur v
                   JOIN article a ON a.id = v.article_id
                   WHERE a.numero = ? ORDER BY v.date_debut DESC, v.id_legi""", numero)
    if not version:
        return {}

    # Les amendements dont un alinéa subsiste. La récursion remonte `repris_de`
    # depuis les segments de la version en vigueur : l'arête `resulte_de` porte sur
    # la version qu'a produite la loi de l'amendement, jamais sur celle
    # d'aujourd'hui — c'est tout l'objet de la quatrième tranche.
    ecrivains = {r["amendement_id"]: r["confiance"] for r in q("""
        WITH RECURSIVE remonte(courant) AS (
            SELECT s.id FROM segment s
            JOIN version_en_vigueur v ON v.id_legi = s.version_id
            JOIN article a ON a.id = v.article_id WHERE a.numero = ?
            UNION
            SELECT r.segment_source_id FROM repris_de r
            JOIN remonte ON r.segment_id = remonte.courant)
        SELECT rd.amendement_id, max(rd.confiance) AS confiance
        FROM remonte JOIN resulte_de rd ON rd.segment_id = remonte.courant
        GROUP BY rd.amendement_id""", numero)}

    tentatives = {t["amendement_id"]: t for t in
                  q("SELECT * FROM tentative_sur_article WHERE article = ?", numero)}

    # Un amendement qui a écrit un alinéa sans que son dispositif nomme l'article
    # — parce qu'il le rédige au lieu de le viser — n'a pas d'arête `vise`. Il est
    # pourtant la tentative la mieux établie qui soit : l'omettre montrerait les
    # échecs sans les réussites.
    manquants = [i for i in ecrivains if i not in tentatives]
    if manquants:
        marques = ",".join("?" * len(manquants))
        for t in q(f"""
                SELECT am.id AS amendement_id, am.numero AS amendement,
                       am.chambre, s.famille, s.motif, s.libelle AS sort_publie,
                       s.source AS sort_lu_dans, ac.nom AS auteur, ac.groupe,
                       am.subdivision AS article_du_texte, am.objet, am.url,
                       NULL AS formule, NULL AS confiance,
                       (SELECT t.titre FROM issu_de i JOIN texte_normatif t
                          ON t.id_jorf = i.texte_id WHERE i.dossier_id = am.dossier_id
                          ORDER BY t.date_texte, t.id_jorf LIMIT 1) AS loi,
                       (SELECT t.date_texte FROM issu_de i JOIN texte_normatif t
                          ON t.id_jorf = i.texte_id WHERE i.dossier_id = am.dossier_id
                          ORDER BY t.date_texte, t.id_jorf LIMIT 1) AS date_texte
                FROM amendement am
                JOIN sort_amendement s ON s.amendement_id = am.id
                LEFT JOIN acteur ac ON ac.id = am.auteur_id
                WHERE am.id IN ({marques})""", *manquants):
            tentatives[t["amendement_id"]] = t

    for identifiant, t in tentatives.items():
        ecrit = identifiant in ecrivains
        t["voie"] = "alinea_ecrit" if ecrit else "cible_declaree"
        t["a_ecrit_un_alinea"] = ecrit
        t["confiance"] = ecrivains[identifiant] if ecrit else t["confiance"]
        t["sort"] = EN_FRANCAIS[t["famille"]]
        t["portee_du_motif"] = PORTEE_DU_MOTIF.get(t["motif"] or "")
        t["objet_cite"] = extrait(t["objet"] or "")

    ordre = sorted(tentatives.values(),
                   key=lambda t: (t["date_texte"] or "", t["chambre"],
                                  _naturel(t["amendement"])))
    compte: dict[str, int] = {}
    for t in ordre:
        compte[t["famille"]] = compte.get(t["famille"], 0) + 1
    motifs: dict[str, int] = {}
    for t in ordre:
        if t["famille"] == "irrecevable":
            motifs[t["motif"] or "(non précisé)"] = \
                motifs.get(t["motif"] or "(non précisé)", 0) + 1

    return {
        "numero": numero, "version": version[0], "tentatives": ordre,
        "compte_par_sort": compte, "motifs_d_irrecevabilite": motifs,
        "abouties": sum(1 for t in ordre if t["famille"] == "adopte"),
        "non_abouties": sum(1 for t in ordre if t["famille"] in ECHEC),
        "sans_objet_publie": sum(1 for t in ordre if not t["objet_cite"]),
    }


def sommet(base: sqlite3.Connection, combien: int = SOMMET) -> list[dict]:
    """Les articles sur lesquels le plus de tentatives ont échoué."""
    base.row_factory = sqlite3.Row
    marques = ",".join("?" * len(ECHEC))
    return [dict(r) for r in base.execute(f"""
        SELECT t.article AS numero, count(*) AS echecs,
               sum(t.famille = 'irrecevable') AS irrecevables,
               v.verdict, v.partie
        FROM tentative_sur_article t
        JOIN article a ON a.numero = t.article
        JOIN version_en_vigueur e ON e.article_id = a.id
        LEFT JOIN verdict v ON v.article_id = a.id
        WHERE t.famille IN ({marques})
        GROUP BY t.article
        ORDER BY echecs DESC, t.article LIMIT ?""", (*ECHEC, combien))]


# ------------------------------------------------------------------ rendu texte

def en_texte(d: dict) -> str:
    if not d:
        return "Article introuvable ou non en vigueur."
    L = [f"CE QUI A ÉTÉ TENTÉ SUR L'ARTICLE {d['numero']}",
         f"  version en vigueur depuis le {d['version']['date_debut']}", ""]
    if not d["tentatives"]:
        L.append("  Aucun amendement du corpus chargé ne désigne cet article, et "
                 "aucun\n  n'a écrit un alinéa qui y subsiste. Le silence est celui "
                 "du corpus,\n  non celui du Parlement : voir docs/30 § 5.")
        return "\n".join(L)

    L.append(f"  {len(d['tentatives'])} tentative(s) — {d['abouties']} aboutie(s), "
             f"{d['non_abouties']} non aboutie(s)")
    L.append("  par sort : " + ", ".join(
        f"{EN_FRANCAIS[f]} — {n}" for f, n in sorted(d["compte_par_sort"].items())))
    if d["motifs_d_irrecevabilite"]:
        L.append("  irrecevabilités : " + ", ".join(
            f"{m} — {n}" for m, n in sorted(d["motifs_d_irrecevabilite"].items())))

    loi = None
    for t in d["tentatives"]:
        if t["loi"] != loi:
            loi = t["loi"]
            L.append(f"\n  ── {loi or 'texte non identifié'} ──")
        L.append(f"\n  amdt {t['amendement']} · {CHAMBRES.get(t['chambre'], '?')} · "
                 f"{t['sort'].upper()}")
        signature = t["auteur"] or "auteur non résolu"
        if t["groupe"]:
            signature += f" ({t['groupe']})"
        L.append(f"      {signature}")
        if t["portee_du_motif"]:
            L.append(f"      {t['portee_du_motif']}")
        if t["sort_lu_dans"] == "etat":
            L.append("      sort lu dans l'état procédural — la chambre ne publie "
                     "pas de sort pour cet amendement")
        L.append(f"      {VOIES[t['voie']]} · confiance {t['confiance']:.3f}"
                 + (f" · formule « {t['formule']} »" if t["formule"] else ""))
        if t["article_du_texte"]:
            L.append(f"      déposé sur {t['article_du_texte']}")
        L.append("      " + (cite(t["objet"] or "") if t["objet_cite"]
                             else "[objet non publié par la chambre]"))
        L.append(f"      {t['url'] or SANS_URL}")
    if d["sans_objet_publie"]:
        L.append(f"\n  {d['sans_objet_publie']} tentative(s) sans objet publié. "
                 "Améli ne publie pas\n  l'objet d'un amendement retiré avant séance "
                 "ou déclaré irrecevable :\n  l'absence est celle de la source, non "
                 "celle d'une justification.")
    return "\n".join(L)


def sommet_en_texte(lignes: list[dict]) -> str:
    L = ["LES ARTICLES LES PLUS DISPUTÉS DU FONDS",
         "  Nombre de tentatives déclarées qui n'ont pas abouti — rejetées,",
         "  retirées, non soutenues, tombées ou déclarées irrecevables.",
         "  La mesure porte sur le corpus chargé, non sur le droit français.", "",
         f"  {'article':22s}{'échecs':>8}{'irrecev.':>10}  partie"]
    for r in lignes:
        L.append(f"  {r['numero']:22s}{r['echecs']:8d}{r['irrecevables'] or 0:10d}"
                 f"  {r['partie'] or '?'}")
    return "\n".join(L)


# ------------------------------------------------------------------- rendu HTML

def e(x) -> str:
    return html.escape(str(x if x is not None else ""))


STYLE = """
:root{--fond:#fbfaf8;--encre:#1c1a17;--doux:#6b655c;--trait:#ddd8ce;--acc:#7a3b2e;
--vert:#3d5a45;--carte:#fff}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--fond:#16151a;
--encre:#e9e6df;--doux:#9a938a;--trait:#2f2c33;--acc:#d98b76;--vert:#8fbb9c;--carte:#1d1c22}}
*{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--encre);
font:16px/1.6 "Iowan Old Style",Palatino,Georgia,serif;padding:2.5rem 1.25rem}
main{max-width:52rem;margin:0 auto}
h1{font-size:1.8rem;margin:0 0 .2rem;letter-spacing:-.01em}
h2{font-size:.78rem;letter-spacing:.13em;text-transform:uppercase;color:var(--doux);
font-family:ui-sans-serif,system-ui,sans-serif;margin:2.4rem 0 .9rem;
border-bottom:1px solid var(--trait);padding-bottom:.4rem}
.chapeau{color:var(--doux);font-size:.92rem;margin-bottom:1.2rem}
.bilan{display:flex;flex-wrap:wrap;gap:.6rem;margin:.8rem 0 1.4rem;
font-family:ui-sans-serif,system-ui,sans-serif;font-size:.8rem}
.bilan span{border:1px solid var(--trait);background:var(--carte);
padding:.3rem .6rem;border-radius:2px}
.bilan .abouti{border-color:var(--vert);color:var(--vert)}
.bilan .bloque{border-color:var(--acc);color:var(--acc)}
.tent{border-left:3px solid var(--trait);padding:.45rem 0 .5rem .9rem;margin:.9rem 0}
.tent.abouti{border-left-color:var(--vert)}
.tent.bloque{border-left-color:var(--acc)}
.tent b{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.95rem}
.sort{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.72rem;
letter-spacing:.09em;text-transform:uppercase;padding:.1rem .45rem;
border:1px solid var(--trait);border-radius:2px;margin-left:.5rem}
.sort.abouti{border-color:var(--vert);color:var(--vert)}
.sort.bloque{border-color:var(--acc);color:var(--acc)}
.meta{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.74rem;
color:var(--doux);display:flex;gap:.8rem;flex-wrap:wrap;margin-top:.25rem}
.objet{font-size:.9rem;margin-top:.45rem;color:var(--encre)}
.silence{color:var(--doux);font-style:italic;font-size:.88rem}
table{width:100%;border-collapse:collapse;font-size:.85rem;
font-family:ui-sans-serif,system-ui,sans-serif}
td,th{text-align:left;padding:.35rem .5rem;border-bottom:1px solid var(--trait)}
th{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--doux)}
a{color:var(--acc)}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--trait);
font-size:.78rem;color:var(--doux);font-family:ui-sans-serif,system-ui,sans-serif}
"""

PIED = ("""<footer>Ratio Legis — le sort d'un amendement est celui que la chambre
publie, jamais un jugement porté sur lui : « retiré » ne dit pas si l'auteur a cédé
ou obtenu satisfaction. Les tentatives sont rattachées soit par l'alinéa qu'elles
ont écrit (arête <code>resulte_de</code>), soit par la cible que leur dispositif
déclare (arête <code>vise</code>) ; les deux voies portent leur confiance. Aucune
arête inférée, aucun modèle de langue. Extraits d'objet limités à 400 caractères
(voir ATTRIBUTION.md). Donnée dérivée : ne fait pas foi. Sources : Sénat —
data.senat.fr ; Assemblée nationale — open data ; DILA — Légifrance, Licence
Ouverte / Etalab&nbsp;2.0.</footer>""")


def _classe(t: dict) -> str:
    if t["famille"] == "adopte":
        return "abouti"
    return "bloque" if t["famille"] == "irrecevable" else ""


def en_html(d: dict) -> str:
    if not d:
        return "<p>Article introuvable.</p>"
    p = [f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(d['numero'])} — ce qui a été tenté</title><style>{STYLE}</style></head>
<body><main>
<h1>Ce qui a été tenté sur l'article {e(d['numero'])}</h1>
<p class="chapeau">Version en vigueur depuis le {e(d['version']['date_debut'])}</p>"""]

    if not d["tentatives"]:
        p.append('<p class="silence">Aucun amendement du corpus chargé ne désigne '
                 "cet article, et aucun n'a écrit un alinéa qui y subsiste. Le "
                 "silence est celui du corpus — les amendements de la XIII<sup>e</sup> "
                 "législature ne sont pas en open data — et non celui du "
                 "Parlement.</p>" + PIED + "</main></body></html>")
        return "".join(p)

    p.append(f'<h2>{len(d["tentatives"])} tentative(s)</h2><div class="bilan">'
             f'<span class="abouti">{d["abouties"]} aboutie(s)</span>'
             f'<span>{d["non_abouties"]} non aboutie(s)</span>'
             + "".join(f"<span>{e(EN_FRANCAIS[f])} — {n}</span>"
                       for f, n in sorted(d["compte_par_sort"].items()))
             + "".join(f'<span class="bloque">{e(m)} — {n}</span>'
                       for m, n in sorted(d["motifs_d_irrecevabilite"].items()))
             + "</div>")

    loi = "\0"
    for t in d["tentatives"]:
        if t["loi"] != loi:
            loi = t["loi"]
            p.append(f'<h2>{e(loi or "Texte non identifié")}</h2>')
        classe = _classe(t)
        signature = e(t["auteur"] or "auteur non résolu")
        if t["groupe"]:
            signature += f' <span class="silence">({e(t["groupe"])})</span>'
        p.append(f'<div class="tent {classe}"><b>amendement {e(t["amendement"])}</b>'
                 f'<span class="sort {classe}">{e(t["sort"])}</span>'
                 f'<div class="meta"><span>{e(CHAMBRES.get(t["chambre"], "?"))}</span>'
                 f'<span>{signature}</span>'
                 + (f'<span>déposé sur {e(t["article_du_texte"])}</span>'
                    if t["article_du_texte"] else "")
                 + f'<span>{e(VOIES[t["voie"]])} · confiance '
                   f'{t["confiance"]:.3f}</span></div>')
        if t["portee_du_motif"]:
            p.append(f'<div class="meta"><span class="bloque">'
                     f'{e(t["portee_du_motif"])}</span></div>')
        if t["sort_lu_dans"] == "etat":
            p.append('<div class="meta"><span>sort lu dans l\'état procédural — la '
                     "chambre ne publie pas de sort pour cet amendement</span></div>")
        p.append(f'<div class="objet">{e(cite(t["objet"] or ""))}</div>'
                 if t["objet_cite"] else
                 '<div class="objet silence">Objet non publié par la chambre.</div>')
        p.append('<div class="meta">' + (
            f'<a href="https:{e(t["url"])}">l\'amendement au Sénat</a>'
            if (t["url"] or "").startswith("//") else
            f'<a href="{e(t["url"])}">l\'amendement</a>' if t["url"]
            else f"<span>{SANS_URL}</span>") + "</div></div>")

    if d["sans_objet_publie"]:
        p.append(f'<p class="silence">{d["sans_objet_publie"]} tentative(s) sans '
                 "objet publié. Améli ne publie pas l'objet d'un amendement retiré "
                 "avant séance ou déclaré irrecevable : l'absence est celle de la "
                 "source, non celle d'une justification.</p>")
    p.append(PIED + "</main></body></html>")
    return "".join(p)


def sommet_en_html(lignes: list[dict]) -> str:
    p = [f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Les articles les plus disputés</title><style>{STYLE}</style></head>
<body><main><h1>Les articles les plus disputés du fonds</h1>
<p class="chapeau">Nombre de tentatives déclarées qui n'ont pas abouti — rejetées,
retirées, non soutenues, tombées ou déclarées irrecevables. La mesure porte sur le
corpus chargé, non sur le droit français.</p>
<table><tr><th>Article</th><th>Échecs</th><th>dont irrecevables</th>
<th>Partie</th></tr>"""]
    for r in lignes:
        p.append(f'<tr><td>{e(r["numero"])}</td><td>{r["echecs"]}</td>'
                 f'<td>{r["irrecevables"] or 0}</td><td>{e(r["partie"] or "?")}</td></tr>')
    p.append("</table>" + PIED + "</main></body></html>")
    return "".join(p)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    sortie = (Path(sys.argv[sys.argv.index("--html") + 1])
              if "--html" in sys.argv else None)

    if "--sommet" in sys.argv:
        suite = [a for a in sys.argv[sys.argv.index("--sommet") + 1:]
                 if not a.startswith("--")]
        combien = int(suite[0]) if suite and suite[0].isdigit() else SOMMET
        lignes = sommet(base, combien)
        rendu = sommet_en_html(lignes) if sortie else sommet_en_texte(lignes)
    else:
        donnees = tenter(base, sys.argv[2])
        rendu = en_html(donnees) if sortie else en_texte(donnees)

    if sortie:
        sortie.write_text(rendu, encoding="utf-8")
        print(f"écrit : {sortie} ({sortie.stat().st_size // 1024} Ko)")
    else:
        print(rendu)
    base.close()


if __name__ == "__main__":
    main()
