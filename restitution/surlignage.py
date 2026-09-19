#!/usr/bin/env python3
"""Le surlignage par étape — dernier livrable du § 4.4.

Sur le texte d'un article en vigueur, colorer chaque alinéa selon **l'étape qui
l'a introduit**. La Fabrique de la loi l'a éprouvé sur la navette ; ici la
question est plus longue, parce qu'elle traverse la recodification : l'alinéa que
vous lisez sous L. 224-43 a pu être écrit en 2014 sous L. 121-42.

**La chaîne existe déjà.** `repris_de` relie un alinéa à celui dont il reprend le
texte, d'une version à l'autre ; `produite_par` dit quel texte a produit une
version. Remonter la première, puis lire la seconde sur le plus ancien ancêtre,
donne le texte qui a introduit l'alinéa. Rien n'est inféré : les deux arêtes sont
déclarées par LEGI, et `repris_de` porte sa fenêtre de preuve.

Couverture mesurée sur les 7 496 alinéas en vigueur du corpus :

    7 437 (99,1 %) ont un texte introducteur
    1 766 (23,5 %) ont été retouchés depuis leur introduction
      145          remontent jusqu'à un amendement nommé

**Ce que la couleur dit, et ne dit pas.** Elle dit quel texte a introduit
l'alinéa, pas qui l'a voulu : 139 alinéas seulement remontent à un amendement.
Confondre les deux ferait passer une ordonnance de recodification pour un auteur.
Le rendu distingue donc trois plans — le texte introducteur (la couleur), la
retouche ultérieure (la trame), et l'amendement quand il existe (la marque).

Usage :
    surlignage.py <base.sqlite> <numero> [--html <sortie.html>]
"""

from __future__ import annotations

import html
import sqlite3
import sys
from pathlib import Path

# Palette assignée par ordre chronologique du texte introducteur. Volontairement
# peu saturée : ce n'est pas une carte de chaleur, c'est un texte de loi.
PALETTE = ["#7a3b2e", "#3d5a45", "#4a4374", "#1e5f74", "#7a5c1e",
           "#5c3a5e", "#2f5d4a", "#6b3a52", "#3a4a6b", "#6b5535"]
NEUTRE = "#8a857c"


def e(x) -> str:
    return html.escape(str(x if x is not None else ""))


def surligner(base: sqlite3.Connection, numero: str) -> dict:
    base.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in base.execute(s, a)]  # noqa: E731

    version = q("""SELECT v.id_legi, v.date_debut, v.texte FROM version_en_vigueur v
                   JOIN article_courant a ON a.id = v.article_id
                   WHERE a.numero = ?
                   ORDER BY v.date_debut DESC, v.id_legi""", numero)
    if not version:
        return {}
    version = version[0]

    alineas = q("""SELECT id, ordre, texte, offset_debut, offset_fin FROM segment
                   WHERE version_id = ? ORDER BY ordre""", version["id_legi"])

    # Ascendance de chaque alinéa. `part_reprise` vaut 1 quand la reprise est
    # intégrale ; en deçà, la version d'arrivée a retouché l'alinéa, et c'est une
    # information distincte de son introduction.
    ascendance: dict[str, list[dict]] = {a["id"]: [] for a in alineas}
    for r in q("""
            WITH RECURSIVE remonte(depart, courant, part) AS (
                SELECT s.id, s.id, 1.0 FROM segment s WHERE s.version_id = ?
                UNION
                SELECT r.depart, rd.segment_source_id, rd.part_reprise
                FROM remonte r JOIN repris_de rd ON rd.segment_id = r.courant)
            SELECT r.depart, r.courant, r.part, s.version_id, v.date_debut
            FROM remonte r JOIN segment s ON s.id = r.courant
            JOIN version_article v ON v.id_legi = s.version_id
            ORDER BY v.date_debut, s.id""", version["id_legi"]):
        if r["depart"] in ascendance:
            ascendance[r["depart"]].append(r)

    # Textes producteurs, par version. **Les liens d'abrogation sont exclus** : le
    # texte qui a supprimé un article ne l'a pas écrit. Sans ce filtre, l'ordonnance
    # de recodification de 2016 apparaissait comme introductrice de tout ce qu'elle
    # avait abrogé — c'est-à-dire de l'essentiel du code, et l'inverse exact de ce
    # que le surlignage sert à montrer.
    versions = {r["version_id"] for liste in ascendance.values() for r in liste}
    producteurs: dict[str, list[dict]] = {}
    if versions:
        marques = ",".join("?" * len(versions))
        for r in q(f"""SELECT p.version_id, t.id_jorf, t.titre, t.date_texte, t.nature,
                              p.type_lien, p.methode
                       FROM produite_par p JOIN texte_normatif t ON t.id_jorf = p.texte_id
                       WHERE p.version_id IN ({marques})
                         AND p.type_lien NOT IN ('ABROGE', 'ABROGATION')
                       ORDER BY t.date_texte, t.id_jorf""", *sorted(versions)):
            producteurs.setdefault(r["version_id"], []).append(r)

    # Amendements atteints par la chaîne. Rares — 139 alinéas sur 7 496 — et
    # c'est le renseignement le plus précieux du graphe : ils nomment un auteur.
    segments = {r["courant"] for liste in ascendance.values() for r in liste}
    amendements: dict[str, list[dict]] = {}
    if segments:
        marques = ",".join("?" * len(segments))
        for r in q(f"""SELECT rd.segment_id, am.numero, am.chambre, am.sort, am.url,
                              coalesce(ac.nom, '') AS auteur, rd.confiance
                       FROM resulte_de rd JOIN amendement am ON am.id = rd.amendement_id
                       LEFT JOIN acteur ac ON ac.id = am.auteur_id
                       WHERE rd.segment_id IN ({marques})
                       ORDER BY am.chambre, am.numero""", *sorted(segments)):
            amendements.setdefault(r["segment_id"], []).append(r)

    # ------------------------------------------------- attribution par alinéa
    couleurs: dict[str, str] = {}
    resultat = []
    for alinea in alineas:
        chaine = ascendance[alinea["id"]]
        origine = producteurs.get(chaine[0]["version_id"], []) if chaine else []
        # Retouche : un maillon repris partiellement, donc modifié en chemin.
        retouches = [r for r in chaine if r["part"] is not None and r["part"] < 1]
        trouves = [a for r in chaine for a in amendements.get(r["courant"], [])]
        # `ordre` compte depuis zéro parce qu'il sert de clef ; l'alinéa se
        # compte depuis un en droit français. Voir `graphe.py`.
        resultat.append({**alinea,
                         "rang": alinea["ordre"] + 1,
                         "ancetres": len(chaine) - 1,
                         "introduit_par": origine,
                         "date_introduction": chaine[0]["date_debut"] if chaine else None,
                         "retouche": bool(retouches),
                         "amendements": trouves})
        for t in origine:
            couleurs.setdefault(t["id_jorf"], "")

    # Couleur par rang chronologique du texte introducteur.
    legende = []
    tous = {t["id_jorf"]: t for a in resultat for t in a["introduit_par"]}
    for rang, identifiant in enumerate(sorted(tous, key=lambda i: (tous[i]["date_texte"],
                                                                   i))):
        couleurs[identifiant] = PALETTE[rang % len(PALETTE)]
        legende.append({**tous[identifiant], "couleur": couleurs[identifiant],
                        "alineas": sum(1 for a in resultat
                                       if any(t["id_jorf"] == identifiant
                                              for t in a["introduit_par"]))})
    for a in resultat:
        a["couleur"] = (couleurs[a["introduit_par"][0]["id_jorf"]]
                        if a["introduit_par"] else NEUTRE)

    return {"numero": numero, "version": version, "alineas": resultat,
            "legende": legende,
            "sans_origine": sum(1 for a in resultat if not a["introduit_par"])}


# ------------------------------------------------------------------- rendus
def en_texte(d: dict) -> str:
    if not d:
        return "Article introuvable ou hors vigueur."
    L = [f"SURLIGNAGE DE L'ARTICLE {d['numero']}  —  version du "
         f"{d['version']['date_debut']}", ""]
    for t in d["legende"]:
        L.append(f"  ▉ {t['titre']}  ({t['alineas']} alinéa(s))")
    if d["sans_origine"]:
        L.append(f"  ▉ origine non documentée  ({d['sans_origine']} alinéa(s))")
    L.append("")
    for a in d["alineas"]:
        titres = ", ".join(t["titre"] for t in a["introduit_par"]) or "origine non documentée"
        L.append(f"[alinéa {a['rang']}] {a['texte'][:300]}")
        marques = []
        if a["ancetres"]:
            marques.append(f"{a['ancetres']} version(s) antérieure(s)")
        if a["retouche"]:
            marques.append("retouché en chemin")
        L.append(f"      introduit par : {titres}"
                 + (f"  ({', '.join(marques)})" if marques else ""))
        for am in a["amendements"]:
            L.append(f"      amendement {am['numero']} ({am['chambre']}) "
                     f"de {am['auteur']} — confiance {am['confiance']:.3f}")
        L.append("")
    return "\n".join(L)


def en_html(d: dict) -> str:
    if not d:
        return "<p>Article introuvable.</p>"
    p = [f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(d['numero'])} — qui a écrit quoi</title><style>
:root{{--fond:#fbfaf8;--encre:#1c1a17;--doux:#6b655c;--trait:#ddd8ce;--carte:#fff}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--fond:#16151a;
--encre:#e9e6df;--doux:#9a938a;--trait:#2f2c33;--carte:#1d1c22}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--fond);color:var(--encre);
font:17px/1.65 "Iowan Old Style",Palatino,Georgia,serif;padding:2.5rem 1.25rem}}
main{{max-width:46rem;margin:0 auto}}
h1{{font-size:1.7rem;margin:0 0 .4rem;letter-spacing:-.01em}}
.sous{{color:var(--doux);font-size:.9rem;margin-bottom:1.6rem}}
h2{{font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;
font-family:ui-sans-serif,system-ui,sans-serif;margin:2.2rem 0 .8rem;color:var(--doux)}}
.leg{{display:flex;flex-wrap:wrap;gap:.5rem 1.2rem;margin-bottom:1.6rem;
font-family:ui-sans-serif,system-ui,sans-serif;font-size:.8rem}}
.leg span{{display:flex;align-items:center;gap:.45rem}}
.pastille{{width:.85rem;height:.85rem;border-radius:.2rem;flex:none}}
.al{{margin:0 0 1.15rem;padding:.7rem .95rem;background:var(--carte);
border-left:5px solid var(--trait);border-radius:0 .25rem .25rem 0}}
.al.retouche{{background-image:repeating-linear-gradient(135deg,transparent,
transparent 7px,rgba(128,128,128,.09) 7px,rgba(128,128,128,.09) 14px)}}
.src{{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.73rem;
color:var(--doux);margin-top:.5rem}}
.amend{{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.76rem;
margin-top:.4rem;padding:.35rem .6rem;border:1px dashed var(--trait);
border-radius:.25rem;display:inline-block}}
a{{color:inherit}}
footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--trait);
font-size:.76rem;color:var(--doux);font-family:ui-sans-serif,system-ui,sans-serif}}
</style></head><body><main>
<h1>Article {e(d['numero'])} — qui a écrit quoi</h1>
<div class="sous">Version en vigueur depuis le {e(d['version']['date_debut'])}.
La couleur donne le texte qui a <b>introduit</b> l'alinéa, la trame signale qu'il a
été <b>retouché</b> depuis, et la marque nomme l'<b>amendement</b> quand la chaîne y
mène.</div>
<h2>Textes introducteurs</h2><div class="leg">"""]
    for t in d["legende"]:
        p.append(f'<span><i class="pastille" style="background:{t["couleur"]}"></i>'
                 f'{e(t["titre"])} — {t["alineas"]} alinéa(s)</span>')
    if d["sans_origine"]:
        p.append(f'<span><i class="pastille" style="background:{NEUTRE}"></i>'
                 f'origine non documentée — {d["sans_origine"]} alinéa(s)</span>')
    p.append("</div><h2>Le texte, alinéa par alinéa</h2>")

    for a in d["alineas"]:
        classe = "al retouche" if a["retouche"] else "al"
        p.append(f'<div class="{classe}" style="border-left-color:{a["couleur"]}">'
                 f'<div>{e(a["texte"])}</div>')
        if a["introduit_par"]:
            sources = " ; ".join(
                f'{e(t["titre"])} <span style="opacity:.7">({e(t["type_lien"]).lower()},'
                f' {e(t["methode"])} par LEGI)</span>' for t in a["introduit_par"])
            detail = f"introduit par {sources}"
            if a["ancetres"]:
                detail += (f" — repris depuis {a['ancetres']} version(s) antérieure(s)"
                           f", chaîne <code>repris_de</code>")
            if a["retouche"]:
                detail += " — retouché en chemin"
        else:
            detail = ("origine non documentée : aucune version antérieure ne porte "
                      "cet alinéa et aucun texte producteur n'est déclaré")
        p.append(f'<div class="src">{detail}</div>')
        for am in a["amendements"]:
            lien = (f'<a href="{e(am["url"])}">amendement {e(am["numero"])}</a>'
                    if am["url"] else f'amendement {e(am["numero"])}')
            p.append(f'<div class="amend">✎ {lien} ({e(am["chambre"])}, '
                     f'{e(am["sort"] or "sort inconnu")}) de {e(am["auteur"])} — '
                     f'confiance {am["confiance"]:.3f}</div>')
        p.append("</div>")

    p.append(f"""<footer>
La couleur dit quel texte a <b>introduit</b> l'alinéa, jamais qui l'a voulu :
{sum(len(a['amendements']) for a in d['alineas'])} amendement(s) seulement sont
atteints sur cet article. Une ordonnance de recodification n'est pas un auteur.<br>
Les deux arêtes utilisées — <code>produite_par</code> et <code>repris_de</code> —
sont déclarées par LEGI ou portent leur fenêtre de preuve. Aucune n'est inférée.<br>
Donnée dérivée : ne fait pas foi, le droit en vigueur est celui publié par
Légifrance. Ce service documente la provenance ; il ne produit ni interprétation
juridique, ni conseil.<br>
Source : DILA — Légifrance, Licence Ouverte / Etalab 2.0 ; Assemblée nationale et
Sénat — open data.
</footer></main></body></html>""")
    return "\n".join(p)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    donnees = surligner(base, sys.argv[2])
    if "--html" in sys.argv:
        sortie = Path(sys.argv[sys.argv.index("--html") + 1])
        sortie.write_text(en_html(donnees), encoding="utf-8")
        print(f"écrit : {sortie} ({sortie.stat().st_size // 1024} Ko)")
    else:
        print(en_texte(donnees))
    base.close()


if __name__ == "__main__":
    main()
