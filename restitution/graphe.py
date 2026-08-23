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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
from union_europeenne import ANCRE  # noqa: E402

PLAFOND_CONSIDERANTS = 25          # au-delà, la page devient illisible
PLAFOND_TEXTES = 8                 # en texte seulement : le HTML les rend tous
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


MOT_TYPE = {"directive": "directive", "reglement": "règlement",
            "decision": "décision"}
# Ce que chaque verdict veut dire, en clair. Le dernier est le seul que la feuille
# de route nomme, et c'est le plus important des quatre.
VERDICT = {
    "passage_motivant":
        ("un passage des travaux préparatoires explique cet article",
         "Il est cité ci-dessous, avec sa source et ses offsets."),
    "origine_situee":
        ("aucun passage n'explique cet article",
         "On sait seulement sous quel article de quel texte il a été discuté."),
    "motivation_du_texte":
        ("aucun passage n'explique cet article",
         "Seul le texte qui l'a produit est motivé, dans son entier — ce qui "
         "peut représenter plusieurs centaines d'articles."),
    "raison_non_documentee":
        ("raison non documentée",
         "Aucune des sources dépouillées n'explique cet article, à aucun grain. "
         "Ce n'est pas un échec de la méthode : c'est un état du fonds "
         "documentaire, et c'est un résultat."),
}
COMPLEMENT_REGLEMENTAIRE = (
    "Pour un article de la partie réglementaire, c'est l'état ordinaire : un "
    "décret n'a ni exposé des motifs, ni débat, ni amendement. 84 % des articles "
    "R et 94 % des articles D du code sont dans ce cas, contre 1 % des articles L.")
# Le § 4.3 impose de distinguer à l'écran qui parle. Ces deux documents motivent
# le texte entier et sont tous deux la parole du Gouvernement, mais l'un précède
# le débat et l'autre le remplace : un projet de loi expose ses motifs devant le
# Parlement, une ordonnance rend compte au Président.
LIBELLE_DOCUMENT = {
    "expose_des_motifs": "exposé des motifs du Gouvernement",
    "etude_impact": "étude d'impact",
    "avis_conseil_etat": "avis du Conseil d'État",
    "rapport_president_republique": "rapport au Président de la République",
}
# L'ordre d'affichage suit celui de la procédure, non celui de la base : ce que
# le Gouvernement a voulu, ce qu'il a chiffré, ce que le Conseil d'État a
# objecté — et, pour une ordonnance, le rapport qui remplace tout cela.
ORDRE_DOCUMENT = {t: r for r, t in enumerate(
    ("expose_des_motifs", "etude_impact", "avis_conseil_etat",
     "rapport_president_republique"))}


def nommer(acte) -> str:
    """Désignation lisible d'un acte de l'Union.

    `denomination` est la forme littéralement écrite dans le code, et une
    citation en énumération ne porte pas son mot-type : « les règlements (CE)
    n° 1184/2006 et n° 1224/2009 » ne laisse, pour le second, que
    « n° 1224/2009 ». Le mot manquant n'est pas inventé — il vient du pluriel qui
    gouverne l'énumération, et c'est lui qui a fixé `type_acte` à l'ingestion.
    """
    mot = MOT_TYPE[acte["type_acte"]]
    return acte["denomination"] if ANCRE.match(acte["denomination"]) \
        else f"{mot} {acte['denomination']}"


def article_du_projet(subdivision: str | None) -> str | None:
    trouve = SUBDIVISION.search(subdivision or "")
    return trouve.group(1) if trouve else None


def interroger(base: sqlite3.Connection, numero: str) -> dict:
    base.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in base.execute(s, a)]  # noqa: E731

    version = q("""SELECT v.id_legi, v.date_debut FROM version_article v
                   JOIN article a ON a.id = v.article_id
                   WHERE a.numero = ? AND v.etat = 'VIGUEUR'
                   ORDER BY v.date_debut DESC, v.id_legi""", numero)
    if not version:
        return {}

    d = {"numero": numero, "version": version[0]}
    d["anciens"] = [r["numero"] for r in q("""
        WITH RECURSIVE asc_a(anc) AS (
            SELECT id FROM article WHERE numero = ?
            UNION SELECT r.ancien_id FROM renumerote_de r JOIN asc_a ON r.article_id = asc_a.anc)
        SELECT DISTINCT a.numero FROM asc_a JOIN article a ON a.id = asc_a.anc
        WHERE a.numero <> ? ORDER BY a.numero""", numero, numero)]

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
            GROUP BY am.id ORDER BY am.chambre, am.numero""", segment["id"])
        renvois = q("""SELECT numero_cite, portee, code_cite FROM renvoie_a
                       WHERE segment_id = ? ORDER BY numero_cite""", segment["id"])
        # « cite » et rien de plus : voir schema/004-union.sql. Un alinéa peut
        # nommer une directive pour l'écarter ; la qualification du lien n'est
        # pas dans les données, elle n'est donc pas affichée.
        actes = q("""SELECT u.celex, u.denomination, u.url, u.type_acte,
                            c.article_cite, aa.intitule AS article_intitule,
                            aa.url AS article_url
                     FROM cite_acte_ue c JOIN acte_ue u ON u.celex = c.celex
                     LEFT JOIN article_acte_ue aa ON aa.celex = c.celex
                                                 AND aa.numero = c.article_cite
                     WHERE c.segment_id = ? ORDER BY c.offset_debut""", segment["id"])
        d["alineas"].append({**segment, "amendements": amendements, "renvois": renvois,
                             "actes_ue": actes,
                             "appariable": len(segment["texte"]) >= SEUIL_APPARIEMENT})

    # Le verdict est rendu avant tout le reste, y compris — surtout — quand il est
    # négatif : le § 4.3 en fait un résultat de premier ordre. Se taire n'est pas
    # la même chose que dire qu'on a cherché et qu'il n'y a rien.
    verdict = q("SELECT verdict, partie FROM verdict v JOIN article a "
                "ON a.id = v.article_id WHERE a.numero = ?", numero)
    d["verdict"] = verdict[0] if verdict else None

    d["raisons"] = q("""
        WITH RECURSIVE asc_a(anc) AS (
            SELECT id FROM article WHERE numero = ?
            UNION SELECT r.ancien_id FROM renumerote_de r JOIN asc_a ON r.article_id = asc_a.anc)
        SELECT doc.type, doc.url, m.article_du_texte, m.confiance, m.methode,
               m.offset_debut, m.offset_fin,
               replace(replace(substr(doc.texte, m.offset_debut, 900), char(10), ' '),
                       char(13), '') AS extrait,
               (SELECT fenetre FROM preuve WHERE id = m.preuve_id) AS preuve,
               (SELECT methode FROM preuve WHERE id = m.preuve_id) AS voie
        FROM asc_a JOIN motive m ON m.article_id = asc_a.anc
        JOIN document doc ON doc.id = m.document_id
        -- Un même passage peut motiver l'article et l'un de ses ancêtres : sans
        -- ce regroupement, la remontée de la chaîne l'affiche deux fois.
        GROUP BY doc.id, m.offset_debut, m.offset_fin
        -- La déclaration en en-tête passe avant : elle nomme l'article dans le
        -- commentaire même, là où le rattachement par l'article du texte est
        -- structurel et ne se lit pas dans le passage montré.
        ORDER BY (voie = 'section_appariee'), m.offset_fin - m.offset_debut""",
        numero)

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
    # Motivation d'une ordonnance. Elle ne passe pas par `motive` : le rapport au
    # Président ne nomme pas les articles du code, il n'a donc pas d'en-tête
    # déclaratif et l'extraction n'en tire aucune arête. Le lien existe pourtant, et
    # il est **déclaré** de bout en bout — LEGI dit quel texte a produit la version,
    # DOLE dit quel dossier a produit le texte, et le dossier porte son rapport.
    # Aucune inférence, donc aucune preuve textuelle à exiger.
    #
    # Le grain est celui de l'ordonnance entière, jamais de l'article : la
    # restitution doit le dire, sous peine de laisser croire que ce passage
    # explique cet article-là.
    d["motivation_du_texte"] = q("""
        SELECT DISTINCT t.titre, doc.url, doc.type,
               replace(replace(substr(doc.texte, 1, 900), char(10), ' '), char(13), '')
               AS extrait, length(doc.texte) AS taille
        FROM version_article v JOIN article a ON a.id = v.article_id
        JOIN produite_par p ON p.version_id = v.id_legi
        JOIN texte_normatif t ON t.id_jorf = p.texte_id
        JOIN issu_de i ON i.texte_id = t.id_jorf
        JOIN document doc ON doc.dossier_id = i.dossier_id
        WHERE a.numero = ? AND doc.type IN ('rapport_president_republique',
                                            'expose_des_motifs', 'etude_impact',
                                            'avis_conseil_etat')""", numero)
    # Le tri doit être total : sans le second critère, deux documents de même
    # type sortaient dans l'ordre du plan d'exécution, qui change avec les
    # statistiques du planificateur. Une restitution dont l'ordre dépend d'un
    # index n'est pas reproductible, et la reproductibilité est ce que ce projet
    # vend (§ 5.2).
    d["motivation_du_texte"].sort(key=lambda m: (ORDRE_DOCUMENT[m["type"]], m["url"]))

    # La transposition n'est retenue que si le texte français la déclare dans son
    # intitulé au Journal officiel. Elle porte sur le texte entier, comme le
    # rapport au Président : l'avertissement est le même.
    d["transposition"] = q("""
        SELECT DISTINCT u.denomination, u.type_acte, u.url, t.titre, p.fenetre
        FROM version_article v
        JOIN article a          ON a.id = v.article_id
        JOIN produite_par pp    ON pp.version_id = v.id_legi
        JOIN texte_normatif t   ON t.id_jorf = pp.texte_id
        JOIN transpose tr       ON tr.texte_id = t.id_jorf
        JOIN acte_ue u          ON u.celex = tr.celex
        LEFT JOIN preuve p      ON p.id = tr.preuve_id
        WHERE a.numero = ? ORDER BY u.celex""", numero)

    # Les considérants motivent l'acte, jamais l'article français : rien ne les
    # relie l'un à l'autre, et deux tentatives de sélection ont été mesurées puis
    # abandonnées (docs/14 § 5). Le nombre et le lien sont donc rendus au grain de
    # l'acte, sans prétendre désigner celui qui explique cet article-ci.
    d["actes_motivants"] = q("""
        SELECT u.celex, u.denomination, u.type_acte, u.url,
               count(c.rang) AS considerants,
               max(EXISTS (SELECT 1 FROM transpose tr
                           JOIN produite_par pp ON pp.texte_id = tr.texte_id
                           JOIN version_article vv ON vv.id_legi = pp.version_id
                           JOIN article aa ON aa.id = vv.article_id
                           WHERE tr.celex = u.celex AND aa.numero = ?
                             AND vv.etat = 'VIGUEUR')) AS transposee
        FROM acte_ue u
        LEFT JOIN considerant c ON c.celex = u.celex
        WHERE u.celex IN (SELECT celex FROM union_par_article WHERE article = ?)
           OR EXISTS (SELECT 1 FROM transpose tr
                      JOIN produite_par pp ON pp.texte_id = tr.texte_id
                      JOIN version_article vv ON vv.id_legi = pp.version_id
                      JOIN article aa ON aa.id = vv.article_id
                      WHERE tr.celex = u.celex AND aa.numero = ? AND vv.etat = 'VIGUEUR')
        GROUP BY u.celex ORDER BY transposee DESC, u.celex""",
        numero, numero, numero)
    d["considerants"] = {
        a["celex"]: q("""SELECT rang, numero, texte, url FROM considerant
                         WHERE celex = ? ORDER BY rang""", a["celex"])
        for a in d["actes_motivants"]}

    # Sous quel article du texte en discussion cet article a-t-il été débattu.
    # `direct` distingue la cible nommée telle quelle de celle atteinte par la
    # chaîne de renumérotation : un texte de 2014 vise L. 121-42, devenu L. 224-43.
    d["textes_discutes"] = q("""
        SELECT chambre, stade, article_du_texte, numero_cite, direct, url
        FROM articles_du_texte WHERE article = ?
        ORDER BY direct DESC, chambre, stade""", numero)

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

    if d["verdict"]:
        titre, glose = VERDICT[d["verdict"]["verdict"]]
        L.append(f"\nVERDICT : {titre.upper()}")
        L.append(f"  {glose}")
        if (d["verdict"]["verdict"] == "raison_non_documentee"
                and d["verdict"]["partie"] in ("R", "D")):
            L.append("  " + COMPLEMENT_REGLEMENTAIRE)

    L.append("\nPOURQUOI CET ARTICLE EXISTE")
    if not d["raisons"]:
        L.append("  Aucun passage motivant n'a été rattaché à cet article.")
        L.append("  Ce n'est pas une absence de motivation : c'est une absence dans nos sources.")
    for r in d["raisons"][:2]:
        L.append(f"  [{r['type']}] confiance {r['confiance']:.3f} ({r['methode']})")
        L.append(f"  {r['url']}  offsets {r['offset_debut']}–{r['offset_fin']}")
        if r["voie"] == "section_appariee":
            L.append(f"  ⚠ rattaché parce que cette section commente l'article "
                     f"{r['article_du_texte']} du texte, qui modifie cet article du "
                     "code. Le lien est structurel : le passage ci-dessous ne le "
                     "nomme pas forcément.")
        L.append(f"    « {r['extrait'][:600].strip()}… »")

    for m in d["motivation_du_texte"]:
        L.append(f"\n  [{LIBELLE_DOCUMENT[m['type']]}] lien déclaré, "
                 f"{m['taille']} caractères")
        L.append(f"  {m['url']}")
        L.append(f"  ⚠ porte sur « {m['titre']} » dans son entier, non sur cet article")
        # Début du document, et rien d'autre : aucun passage n'est désigné comme
        # motivant cet article-ci, et en choisir un serait le prétendre.
        L.append(f"    début du document : « {m['extrait'][:500].strip()}… »")

    for tr in d["transposition"]:
        L.append(f"\n  [transposition déclarée] {nommer(tr)}")
        L.append(f"  {tr['url']}")
        L.append(f"  déclarée par l'intitulé de « {tr['titre']} », "
                 "qui porte sur le texte entier, non sur cet article")

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
        for u in a["actes_ue"]:
            precision = ""
            if u["article_cite"]:
                precision = f", article {u['article_cite']}" + (
                    f" — {u['article_intitule']}" if u["article_intitule"] else "")
            L.append(f"        cite {nommer(u)}{precision}")
            L.append(f"          {u['article_url'] or u['url']}")

    if d["actes_motivants"]:
        L.append(f"\nCE QUE L'UNION EN DIT ({len(d['actes_motivants'])} acte(s))")
        L.append("  Un considérant motive l'acte entier. Rien ne dit lequel motive")
        L.append("  cet article-ci : l'acte ne l'écrit pas, et nous ne le devinons pas.")
        for u in d["actes_motivants"]:
            marque = " [transposition déclarée]" if u["transposee"] else ""
            L.append(f"\n  {nommer(u)}{marque} — {u['considerants']} considérant(s)")
            L.append(f"  {u['url']}")
            if u["considerants"]:
                L.append("    les deux premiers, dans l'ordre du texte :")
            for c in d["considerants"][u["celex"]][:2]:
                rang = f"({c['numero']})" if c["numero"] else f"[{c['rang']}e, non numéroté]"
                L.append(f"    {rang} {c['texte'][:220].strip()}…")
            reste = max(0, u["considerants"] - 2)
            if reste:
                L.append(f"    … et {reste} autre(s), sur EUR-Lex")

    if d["textes_discutes"]:
        L.append(f"\nSOUS QUEL ARTICLE IL A ÉTÉ DISCUTÉ ({len(d['textes_discutes'])})")
        for x in d["textes_discutes"][:PLAFOND_TEXTES]:
            sous = "" if x["direct"] else f" (visé sous {x['numero_cite']})"
            L.append(f"  article {x['article_du_texte']}{sous} — {x['stade']}")
            L.append(f"    {x['url']}")
        reste = len(d["textes_discutes"]) - PLAFOND_TEXTES
        if reste > 0:
            L.append(f"  … et {reste} autre(s) — la liste complète est dans le rendu HTML")

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
.verdict{{border:1px solid var(--trait);border-left:3px solid var(--vert);
background:var(--carte);padding:.8rem 1rem;margin:1.4rem 0}}
.verdict.muet{{border-left-color:var(--acc)}}
.verdict b{{font-size:1.05rem}}
.cons{{font-size:.85rem;margin:.5rem 0;padding-left:.8rem;
border-left:1px solid var(--trait)}}
details summary{{cursor:pointer;font-size:.82rem;color:var(--acc);margin-top:.5rem;
font-family:ui-sans-serif,system-ui,sans-serif}}
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

    if d["verdict"]:
        titre, glose = VERDICT[d["verdict"]["verdict"]]
        muet = d["verdict"]["verdict"] == "raison_non_documentee"
        p.append(f'<div class="verdict{" muet" if muet else ""}">'
                 f'<div class="num">verdict</div><b>{e(titre)}</b>'
                 f'<p class="silence">{e(glose)}'
                 + ("<br>" + e(COMPLEMENT_REGLEMENTAIRE)
                    if muet and d["verdict"]["partie"] in ("R", "D") else "")
                 + "</p></div>")

    p.append("<h2>Pourquoi cet article existe</h2>")
    if not d["raisons"]:
        p.append('<p class="silence">Aucun passage motivant n\'a été rattaché à cet '
                 "article. Ce n'est pas une absence de motivation : c'est une absence "
                 "dans les sources dépouillées.</p>")
    for r in d["raisons"][:2]:
        p.append(f'<div class="raison">'
                 + (f'<p class="alerte">Rattaché parce que cette section commente '
                    f'l\'article {e(r["article_du_texte"])} du texte, qui modifie cet '
                    "article du code. Le lien est structurel : le passage ci-dessous "
                    "ne le nomme pas forcément.</p>"
                    if r["voie"] == "section_appariee" else "")
                 + f'<div>« {e(r["extrait"][:700].strip())}… »</div>'
                 f'<div class="meta"><span>{e(r["type"])}</span>'
                 f'<span class="conf">confiance {r["confiance"]:.3f}</span>'
                 f'<span>{e(r["methode"])}</span>'
                 f'<span>offsets {r["offset_debut"]}–{r["offset_fin"]}</span>'
                 f'<a href="{e(r["url"])}">document</a></div></div>')

    for m in d["motivation_du_texte"]:
        p.append(f'<div class="raison"><div class="meta">'
                 f'<span>{e(LIBELLE_DOCUMENT[m["type"]])}</span><span>lien déclaré</span>'
                 f'<a href="{e(m["url"])}">document</a></div>'
                 f'<p class="silence">Ce document motive « {e(m["titre"])} » dans '
                 f'son entier, et non cet article en particulier. Rien n\'y désigne '
                 f'le passage qui le concerne ; voici son début.</p>'
                 f'<div>« {e(m["extrait"][:700].strip())}… »</div></div>')

    for tr in d["transposition"]:
        p.append(f'<div class="raison"><div class="meta">'
                 f'<span>transposition déclarée</span>'
                 f'<span class="conf">confiance 1.000</span><span>declaree</span>'
                 f'<a href="{e(tr["url"])}">acte de l\'Union</a></div>'
                 f'<div>{e(nommer(tr))}</div>'
                 f'<p class="silence">Déclarée par l\'intitulé de « {e(tr["titre"])} », '
                 f'qui porte sur le texte entier, non sur cet article.</p></div>')

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
        if a["actes_ue"]:
            p.append('<div class="puces">cite&nbsp;' + "".join(
                f'<span><a href="{e(u["article_url"] or u["url"])}">{e(nommer(u))}'
                + (f' · art. {e(u["article_cite"])}' if u["article_cite"] else "")
                + (f' — {e(u["article_intitule"])}' if u["article_intitule"] else "")
                + "</a></span>" for u in a["actes_ue"]) + "</div>")
        p.append("</div>")

    if d["actes_motivants"]:
        p.append(f"<h2>Ce que l'Union en dit ({len(d['actes_motivants'])})</h2>")
        p.append('<p class="silence">Un considérant motive l\'acte entier. Rien '
                 "ne dit lequel motive cet article-ci : l'acte ne l'écrit nulle "
                 "part, et deux méthodes pour le deviner ont été essayées, "
                 "mesurées, et écartées.</p>")
        for u in d["actes_motivants"]:
            liste = d["considerants"][u["celex"]]
            montres = liste[:PLAFOND_CONSIDERANTS]
            p.append(f'<div class="raison"><div class="meta">'
                     + ('<span>transposition déclarée</span>' if u["transposee"] else
                        '<span>cité par cet article</span>')
                     + f'<span>{len(liste)} considérant(s)</span>'
                     f'<a href="{e(u["url"])}">acte de l\'Union</a></div>'
                     f'<div><b>{e(nommer(u))}</b></div>')
            if montres:
                p.append("<details><summary>lire les considérants</summary>")
                for c in montres:
                    rang = (f"({c['numero']})" if c["numero"]
                            else f"[{c['rang']}<sup>e</sup>, non numéroté]")
                    p.append(f'<p class="cons"><a href="{e(c["url"])}">{rang}</a> '
                             f'{e(c["texte"][:1200])}</p>')
                if len(liste) > len(montres):
                    p.append(f'<p class="silence">{len(montres)} premiers sur '
                             f'{len(liste)} — la suite sur EUR-Lex.</p>')
                p.append("</details>")
            p.append("</div>")

    if d["textes_discutes"]:
        p.append(f"<h2>Sous quel article il a été discuté "
                 f"({len(d['textes_discutes'])})</h2>")
        p.append("<table><tr><th>Article du texte</th><th>Chambre</th>"
                 "<th>Stade</th><th>Visé sous</th></tr>")
        for x in d["textes_discutes"]:
            p.append(f'<tr><td><a href="{e(x["url"])}">article '
                     f'{e(x["article_du_texte"])}</a></td>'
                     f'<td>{e(x["chambre"])}</td><td>{e(x["stade"])}</td>'
                     f'<td>{"" if x["direct"] else e(x["numero_cite"])}</td></tr>')
        p.append("</table>")

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
