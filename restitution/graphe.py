#!/usr/bin/env python3
"""Restitution : traversée du graphe de provenance pour un article du code.

Première forme de la couche de restitution du § 4 de la feuille de route. Elle
n'ajoute aucune donnée : elle interroge le graphe et met en forme ce qu'il sait
dire d'un article, alinéa par alinéa.

Trois règles de la feuille de route commandent la mise en forme, et ce sont elles
qui font la différence entre une restitution et un affichage.

**§ 5.1 — provenance ou silence.** Un alinéa sans arête n'est pas omis : il est
affiché avec la mention de ce qui manque, et pourquoi. Un alinéa de moins de
60 caractères porte « provenance non déterminable par la méthode », jamais
« aucune motivation » : la première phrase décrit notre limite, la seconde
décrirait le droit, et elle serait fausse.

**§ 5.4 — la confiance est une donnée.** Chaque arête affiche sa méthode et sa
confiance, et les valeurs ne sont pas décoratives : elles viennent de contrôles à
la main documentés dans `docs/`. Une arête déclarée par LEGI et un appariement
textuel à 0,71 ne se présentent pas de la même façon.

**§ 4.3 — toute phrase produite est citable.** Chaque motivation porte les offsets
du passage dans son document et l'URL de ce document ; chaque amendement porte la
fenêtre de texte qui a produit l'arête.

Usage :
    graphe.py <base.sqlite> <numéro d'article> [--html <sortie.html>]
"""

from __future__ import annotations

import html
import sqlite3
import sys
from pathlib import Path

import re

SEUIL_APPARIEMENT = 60          # sous ce seuil, aucune preuve textuelle ne discrimine

# Numéro de l'article du PROJET de loi, tel que l'amendement et le commentaire de
# rapport le désignent chacun dans leur convention : « ART. 72 BIS », « APRÈS
# ART. 72 », « art. add. après Article 5 ».
#
# Il a été essayé comme contrôle de cohérence — un amendement rattaché à un alinéa
# dont le commentaire porte sur un autre article du projet serait suspect — et le
# contrôle ne tient pas. Mesuré : 27,1 % des arêtes confrontables sont
# « incohérentes », pour une précision mesurée à 23/26. La raison est structurelle :
# **l'article du projet est renuméroté à chaque lecture**. L'amendement 639 vise
# l'article 55 du texte de commission de l'Assemblée ; le rapport du Sénat commente
# la même disposition sous l'article 72. Le désaccord ne dit rien tant que les deux
# côtés ne sont pas ramenés à la même lecture du même texte — ce que la base ne sait
# pas encore faire. La fonction reste, elle sert l'affichage ; le verdict a été
# retiré (docs/12 § 3).
SUBDIVISION = re.compile(r"art(?:icle)?\.?\s*(?:add\.?\s*)?(?:apr[èe]s\s*)?"
                         r"(?:art(?:icle)?\.?\s*)?(\d+)", re.I)


def article_du_projet(subdivision: str | None) -> str | None:
    trouve = SUBDIVISION.search(subdivision or "")
    return trouve.group(1) if trouve else None


def interroger(base: sqlite3.Connection, numero: str) -> dict:
    base.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in base.execute(s, a)]  # noqa: E731

    version = q("""SELECT v.id_legi, v.date_debut FROM version_article v
                   JOIN article a ON a.id = v.article_id
                   WHERE a.numero = ? AND v.etat = 'VIGUEUR'""", numero)
    if not version:
        return {}

    d = {"numero": numero, "version": version[0]}
    d["anciens"] = [r["numero"] for r in q("""
        WITH RECURSIVE asc_a(anc) AS (
            SELECT id FROM article WHERE numero = ?
            UNION SELECT r.ancien_id FROM renumerote_de r JOIN asc_a ON r.article_id = asc_a.anc)
        SELECT DISTINCT a.numero FROM asc_a JOIN article a ON a.id = asc_a.anc
        WHERE a.numero <> ?""", numero, numero)]

    d["textes"] = q("""SELECT DISTINCT t.titre, t.date_texte, p.type_lien, p.methode
                       FROM version_article v JOIN article a ON a.id = v.article_id
                       JOIN produite_par p ON p.version_id = v.id_legi
                       JOIN texte_normatif t ON t.id_jorf = p.texte_id
                       WHERE a.numero = ? ORDER BY t.date_texte""", numero)

    d["alineas"] = []
    for segment in q("""SELECT s.id, s.ordre, s.texte FROM segment s
                        WHERE s.version_id = ? ORDER BY s.ordre""", d["version"]["id_legi"]):
        # Ascendance de l'alinéa : c'est elle qui permet d'atteindre un amendement
        # antérieur à la recodification. Sans elle, l'arête serait vide sur tout
        # corpus recodifié (docs/09 § 1).
        amendements = q("""
            WITH RECURSIVE seg(cur) AS (
                SELECT ? UNION SELECT r.segment_source_id FROM repris_de r
                JOIN seg ON r.segment_id = seg.cur)
            SELECT am.numero, am.chambre, am.sort, am.texte_discute, am.subdivision,
                   am.objet, ac.nom, ac.groupe,
                   t.titre AS loi, rd.confiance, rd.methode, p.fenetre
            FROM seg JOIN resulte_de rd ON rd.segment_id = seg.cur
            JOIN amendement am ON am.id = rd.amendement_id
            LEFT JOIN acteur ac ON ac.id = am.auteur_id
            JOIN preuve p ON p.id = rd.preuve_id
            LEFT JOIN issu_de i ON i.dossier_id = am.dossier_id
            LEFT JOIN texte_normatif t ON t.id_jorf = i.texte_id
            GROUP BY am.id""", segment["id"])
        renvois = q("""SELECT numero_cite, portee, code_cite FROM renvoie_a
                       WHERE segment_id = ? ORDER BY numero_cite""", segment["id"])
        d["alineas"].append({**segment, "amendements": amendements, "renvois": renvois,
                             "appariable": len(segment["texte"]) >= SEUIL_APPARIEMENT})

    d["raisons"] = q("""
        WITH RECURSIVE asc_a(anc) AS (
            SELECT id FROM article WHERE numero = ?
            UNION SELECT r.ancien_id FROM renumerote_de r JOIN asc_a ON r.article_id = asc_a.anc)
        SELECT doc.type, doc.url, m.article_du_texte, m.confiance, m.methode,
               m.offset_debut, m.offset_fin,
               replace(replace(substr(doc.texte, m.offset_debut, 900), char(10), ' '),
                       char(13), '') AS extrait,
               (SELECT fenetre FROM preuve WHERE id = m.preuve_id) AS preuve
        FROM asc_a JOIN motive m ON m.article_id = asc_a.anc
        JOIN document doc ON doc.id = m.document_id
        GROUP BY m.id ORDER BY m.offset_fin - m.offset_debut""", numero)

    # Contrôle de cohérence structurelle : les articles du projet de loi que les
    # commentaires retenus disent motiver cet article du code.
    d["articles_commentes"] = {r["article_du_texte"] for r in d["raisons"]
                               if r["article_du_texte"]}
    for alinea in d["alineas"]:
        for m in alinea["amendements"]:
            m["article_vise"] = article_du_projet(m["subdivision"])

    # Groupé sur l'article citant, non sur le couple avec sa preuve : un même
    # article cite souvent la cible depuis plusieurs alinéas, et la liste
    # affichait alors deux fois le même numéro.
    d["cite_par"] = q("""SELECT article_citant,
                                min((SELECT fenetre FROM preuve WHERE id = preuve_id)) AS extrait
                         FROM renvois_entrants WHERE article_cite = ?
                         GROUP BY article_citant ORDER BY article_citant""", numero)

    d["tentatives"] = q("""SELECT amendement, sort, auteur, groupe, loi, formule, objet
                           FROM historique_article WHERE article = ?
                           ORDER BY CASE sort WHEN 'Adopté' THEN 0 ELSE 1 END""", numero)
    return d


# ------------------------------------------------------------------ rendu texte

def en_texte(d: dict) -> str:
    if not d:
        return "Article introuvable ou non en vigueur."
    L = [f"ARTICLE {d['numero']}  —  en vigueur depuis le {d['version']['date_debut']}"]
    if d["anciens"]:
        L.append(f"  anciennement : {', '.join(d['anciens'])}")
    L.append(f"  {len(d['textes'])} texte(s) modificateur(s), du "
             f"{d['textes'][0]['date_texte']} au {d['textes'][-1]['date_texte']}"
             if d["textes"] else "  aucun texte producteur déclaré")

    L.append("\nPOURQUOI CET ARTICLE EXISTE")
    if not d["raisons"]:
        L.append("  Aucun passage motivant n'a été rattaché à cet article.")
        L.append("  Ce n'est pas une absence de motivation : c'est une absence dans nos sources.")
    for r in d["raisons"][:2]:
        L.append(f"  [{r['type']}] confiance {r['confiance']:.3f} ({r['methode']})")
        L.append(f"  {r['url']}  offsets {r['offset_debut']}–{r['offset_fin']}")
        L.append(f"    « {r['extrait'][:600].strip()}… »")

    L.append(f"\nALINÉAS ({len(d['alineas'])})")
    for a in d["alineas"]:
        L.append(f"\n  [{a['ordre']}] {a['texte'][:150]}{'…' if len(a['texte']) > 150 else ''}")
        if a["amendements"]:
            for m in a["amendements"]:
                qui = m["nom"] or "auteur non résolu"
                L.append(f"      ← amdt {m['numero']} ({m['chambre']}, {m['sort']}) — {qui}")
                L.append(f"        {m['loi'] or 'loi non résolue'} · confiance {m['confiance']:.3f}")
                L.append(f"        preuve : « …{m['fenetre'][:90].strip()}… »")
                if m["objet"]:
                    L.append("        but déclaré : « "
                             + m["objet"][:230].strip().replace("\n", " ") + "… »")
                if m["article_vise"]:
                    L.append(f"        déposé sur l'article {m['article_vise']} du texte "
                             f"{m['texte_discute']}")
        elif not a["appariable"]:
            L.append(f"      · moins de {SEUIL_APPARIEMENT} caractères : "
                     "provenance non déterminable par la méthode")
        else:
            L.append("      · aucun amendement rattaché")
        if a["renvois"]:
            L.append("        renvoie à : " + ", ".join(
                f"{r['numero_cite']}" + (f" [{r['code_cite']}]" if r["code_cite"] else "")
                for r in a["renvois"]))

    L.append(f"\nCE QUI CITE CET ARTICLE ({len(d['cite_par'])})")
    L.append("  " + ", ".join(c["article_citant"] for c in d["cite_par"]) if d["cite_par"]
             else "  aucun article du fonds ne le cite")

    if d["tentatives"]:
        L.append(f"\nCE QUI A ÉTÉ TENTÉ ({len(d['tentatives'])})")
        for t in d["tentatives"]:
            L.append(f"  amdt {t['amendement']:<12s} {t['sort'] or '?':<14s} "
                     f"{(t['auteur'] or '?')[:30]:<32s} {t['formule']}")
    return "\n".join(L)


# ------------------------------------------------------------------- rendu HTML

def e(x) -> str:
    return html.escape(str(x if x is not None else ""))


def en_html(d: dict) -> str:
    if not d:
        return "<p>Article introuvable.</p>"
    p = [f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(d['numero'])} — provenance</title><style>
:root{{--fond:#fbfaf8;--encre:#1c1a17;--doux:#6b655c;--trait:#ddd8ce;--acc:#7a3b2e;
--vert:#3d5a45;--carte:#fff}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--fond:#16151a;
--encre:#e9e6df;--doux:#9a938a;--trait:#2f2c33;--acc:#d98b76;--vert:#8fbb9c;--carte:#1d1c22}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--fond);color:var(--encre);
font:16px/1.6 "Iowan Old Style",Palatino,Georgia,serif;padding:2.5rem 1.25rem}}
main{{max-width:56rem;margin:0 auto}}
h1{{font-size:1.9rem;margin:0 0 .2rem;letter-spacing:-.01em}}
h2{{font-size:.78rem;letter-spacing:.13em;text-transform:uppercase;color:var(--doux);
font-family:ui-sans-serif,system-ui,sans-serif;margin:2.5rem 0 .9rem;
border-bottom:1px solid var(--trait);padding-bottom:.4rem}}
.chapeau{{color:var(--doux);font-size:.92rem;margin-bottom:.4rem}}
.al{{border-left:3px solid var(--trait);padding:.1rem 0 .1rem 1rem;margin:1.4rem 0}}
.al.tracee{{border-left-color:var(--acc)}}
.num{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.72rem;color:var(--doux)}}
.tx{{margin:.25rem 0 .6rem}}
.arete{{background:var(--carte);border:1px solid var(--trait);border-radius:2px;
padding:.65rem .8rem;margin:.5rem 0;font-size:.9rem}}
.arete b{{color:var(--acc)}}
.meta{{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.75rem;color:var(--doux);
display:flex;gap:.9rem;flex-wrap:wrap;margin-top:.35rem}}
.conf{{font-variant-numeric:tabular-nums}}
.but{{margin-top:.55rem;font-size:.88rem;border-top:1px solid var(--trait);padding-top:.5rem}}
.alerte{{margin-top:.5rem;font-size:.82rem;color:var(--acc);
font-family:ui-sans-serif,system-ui,sans-serif}}
.preuve{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.76rem;
color:var(--doux);margin-top:.4rem;overflow-x:auto;white-space:pre-wrap}}
.silence{{color:var(--doux);font-style:italic;font-size:.87rem;margin:.4rem 0}}
.raison{{background:var(--carte);border:1px solid var(--trait);border-left:3px solid var(--vert);
padding:.9rem 1rem;margin:.8rem 0}}
.puces{{display:flex;flex-wrap:wrap;gap:.35rem;font-family:ui-monospace,monospace;font-size:.8rem}}
.puces span{{border:1px solid var(--trait);padding:.12rem .45rem;border-radius:2px}}
table{{width:100%;border-collapse:collapse;font-size:.85rem;
font-family:ui-sans-serif,system-ui,sans-serif}}
td,th{{text-align:left;padding:.35rem .5rem;border-bottom:1px solid var(--trait);vertical-align:top}}
th{{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--doux)}}
a{{color:var(--acc)}}
footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--trait);
font-size:.78rem;color:var(--doux);font-family:ui-sans-serif,system-ui,sans-serif}}
</style></head><body><main>
<h1>Article {e(d['numero'])}</h1>
<p class="chapeau">En vigueur depuis le {e(d['version']['date_debut'])}"""]
    if d["anciens"]:
        p.append(f" · anciennement {e(', '.join(d['anciens']))}")
    p.append(f" · {len(d['textes'])} texte(s) modificateur(s)</p>")

    p.append("<h2>Pourquoi cet article existe</h2>")
    if not d["raisons"]:
        p.append('<p class="silence">Aucun passage motivant n\'a été rattaché à cet '
                 "article. Ce n'est pas une absence de motivation : c'est une absence "
                 "dans les sources dépouillées.</p>")
    for r in d["raisons"][:2]:
        p.append(f'<div class="raison"><div>« {e(r["extrait"][:700].strip())}… »</div>'
                 f'<div class="meta"><span>{e(r["type"])}</span>'
                 f'<span class="conf">confiance {r["confiance"]:.3f}</span>'
                 f'<span>{e(r["methode"])}</span>'
                 f'<span>offsets {r["offset_debut"]}–{r["offset_fin"]}</span>'
                 f'<a href="{e(r["url"])}">document</a></div></div>')

    p.append(f"<h2>Alinéas et provenance ({len(d['alineas'])})</h2>")
    for a in d["alineas"]:
        p.append(f'<div class="al{" tracee" if a["amendements"] else ""}">'
                 f'<div class="num">alinéa {a["ordre"]}</div>'
                 f'<div class="tx">{e(a["texte"])}</div>')
        for m in a["amendements"]:
            p.append(f'<div class="arete">résulte de l\'<b>amendement {e(m["numero"])}</b> '
                     f'de {e(m["nom"] or "auteur non résolu")}'
                     + (f' ({e(m["groupe"])})' if m["groupe"] else "") +
                     f'<div class="meta"><span>{e(m["chambre"])}</span>'
                     f'<span>{e(m["sort"])}</span><span>{e(m["loi"] or "loi non résolue")}</span>'
                     f'<span class="conf">confiance {m["confiance"]:.3f}</span>'
                     f'<span>{e(m["methode"])}</span></div>'
                     f'<div class="preuve">preuve : …{e(m["fenetre"][:140].strip())}…</div>'
                     + (f'<div class="but"><b>But déclaré par l\'auteur.</b> '
                        f'{e(m["objet"][:520].strip())}…</div>' if m["objet"] else "")
                     + (f'<div class="alerte">Déposé sur l\'article '
                        f'{e(m["article_vise"])} du texte {e(m["texte_discute"])}.</div>'
                        if m["article_vise"] else "")
                     + "</div>")
        if not a["amendements"]:
            p.append('<p class="silence">' + (
                f"Moins de {SEUIL_APPARIEMENT} caractères : provenance non déterminable "
                "par la méthode." if not a["appariable"]
                else "Aucun amendement rattaché à cet alinéa.") + "</p>")
        if a["renvois"]:
            p.append('<div class="puces">renvoie à&nbsp;' + "".join(
                f'<span>{e(r["numero_cite"])}'
                + (f' · {e(r["code_cite"])}' if r["code_cite"] else "") + "</span>"
                for r in a["renvois"]) + "</div>")
        p.append("</div>")

    p.append(f"<h2>Ce qui cite cet article ({len(d['cite_par'])})</h2>")
    p.append('<div class="puces">' + "".join(
        f'<span>{e(c["article_citant"])}</span>' for c in d["cite_par"]) + "</div>"
        if d["cite_par"] else '<p class="silence">Aucun article du fonds ne le cite.</p>')

    if d["tentatives"]:
        p.append(f"<h2>Ce qui a été tenté ({len(d['tentatives'])})</h2><table>"
                 "<tr><th>Amendement</th><th>Sort</th><th>Auteur</th><th>Loi</th>"
                 "<th>Formule</th></tr>")
        for t in d["tentatives"]:
            p.append(f'<tr><td>{e(t["amendement"])}</td><td>{e(t["sort"])}</td>'
                     f'<td>{e(t["auteur"])}</td><td>{e(t["loi"])}</td>'
                     f'<td>{e(t["formule"])}</td></tr>')
        p.append("</table>")

    p.append('<footer>Ratio Legis — graphe de provenance normative. Aucune arête sans '
             'source résoluble. Les confiances sont des bornes inférieures mesurées à la '
             'main, documentées dans <code>docs/</code>. Sources : DILA (LEGI, JORF, '
             'DOLE), Assemblée nationale, Sénat.</footer></main></body></html>')
    return "".join(p)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    donnees = interroger(base, sys.argv[2])
    if "--html" in sys.argv:
        sortie = Path(sys.argv[sys.argv.index("--html") + 1])
        sortie.write_text(en_html(donnees), encoding="utf-8")
        print(f"écrit : {sortie} ({sortie.stat().st_size // 1024} Ko)")
    else:
        print(en_texte(donnees))
    base.close()


if __name__ == "__main__":
    main()
