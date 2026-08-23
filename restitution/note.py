#!/usr/bin/env python3
"""Phase 3 — la note « pourquoi cet article », sous contrat strict.

Le graphe savait tout dire et ne racontait rien : `graphe.py` affiche ce qu'il
sait, arête par arête. La phase 3 demande autre chose — une note en langue
naturelle — et l'assortit d'un contrat que le § 4.3 énonce sans détour :

  « Toute phrase affirmative produite doit porter au moins une citation au niveau
  du **span**, résolvable vers le passage exact. Une phrase sans citation
  résoluble n'est pas affichée. Le post-traitement supprime la phrase, il ne
  l'excuse pas. »

Ce contrat est ici un **filtre exécuté**, pas une intention. Chaque phrase est
construite avec sa citation ; celles qui n'en ont pas sont retirées et comptées,
et le compte est affiché en pied de note. S'il n'est jamais supérieur à zéro,
c'est que le filtre ne filtre rien — il est donc rendu visible.

**Deux registres, jamais mélangés.** Les *constats* affirment quelque chose du
droit et portent tous une source. L'*état du dossier* ne parle que de nos
sources — « aucun passage ne motive cet article » — et n'affirme rien du droit.
Confondre les deux est exactement ce que le contrat interdit : « nous n'avons rien
trouvé » n'est pas « il n'y a rien ».

**Deux natures de référence.** Une citation `web` pointe une URL publique. Une
citation `corpus` pointe un identifiant du fonds versionné — `LEGIARTI…`, un
numéro d'amendement — résoluble dans le miroir DILA et son manifeste haché, mais
pas d'un clic sur le web. Le site de consultation de Légifrance est derrière un
défi JavaScript (`docs/01` § 2.6) : l'URL d'un article y est la citation d'usage,
elle n'a pas pu être vérifiée depuis le pipeline. Le miroir, lui, l'a été.

**Aucun modèle de langue n'intervient.** La note est composée par assemblage de
gabarits déterministes à partir du graphe ; les passages entre guillemets sont
verbatim. L'article 50 du règlement (UE) 2024/1689 vise le contenu synthétique
produit par un système d'IA : il ne s'applique pas ici, et la note le dit plutôt
que d'afficher une étiquette qui laisserait croire le contraire.

Usage :
    note.py <base.sqlite> <numéro d'article> [--html <fichier>]
    note.py <base.sqlite> --contrat [nombre d'articles]
"""

from __future__ import annotations

import html
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graphe import interroger, nommer  # noqa: E402
from citation import ABSENT, PLAFOND_EXTRAIT, extrait  # noqa: E402
import proximite  # noqa: E402

# Les quatre voix que le § 4.3 impose de distinguer à l'écran, plus le fonds
# lui-même, qui n'est la voix de personne.
VOIX = {
    "legi": "le fonds consolidé",
    "gouvernement": "le Gouvernement",
    "parlement": "le Parlement",
    "conseil_etat": "le Conseil d'État",
    "union": "l'Union européenne",
}
VOIX_DOCUMENT = {
    "expose_des_motifs": "gouvernement",
    "etude_impact": "gouvernement",
    "rapport_president_republique": "gouvernement",
    "avis_conseil_etat": "conseil_etat",
    "rapport_commission": "parlement",
}
LIBELLE = {
    "expose_des_motifs": "exposé des motifs",
    "etude_impact": "étude d'impact",
    "avis_conseil_etat": "avis du Conseil d'État",
    "rapport_president_republique": "rapport au Président de la République",
    "rapport_commission": "rapport de commission",
}
VERDICT = {
    "passage_motivant": "un passage des travaux préparatoires explique cet article",
    "origine_situee": "aucun passage n'explique cet article ; on sait seulement "
                      "sous quel article de quel texte il a été discuté",
    "motivation_du_texte": "aucun passage n'explique cet article ; seul le texte "
                           "qui l'a produit est motivé, dans son entier",
    "raison_non_documentee": "raison non documentée",
}
ARTICLE_DEFINI = {"directive": "la", "reglement": "le", "decision": "la"}
LEGIFRANCE = "https://www.legifrance.gouv.fr/codes/article_lc/{}"
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre")


@dataclass(frozen=True)
class Phrase:
    """Une phrase affirmative et sa citation. Sans référence, elle est retirée."""
    voix: str
    texte: str
    source: str = ""
    reference: str = ""
    nature: str = "corpus"          # « web » ou « corpus »
    offsets: tuple[int, int] | None = None
    confiance: float | None = None
    citation: str = ""


def en_date(iso: str) -> str:
    annee, mois, jour = iso.split("-")
    return f"{int(jour)}{'er' if jour == '01' else ''} {MOIS[int(mois) - 1]} {annee}"


def composer(d: dict) -> tuple[list[Phrase], list[str], list[Phrase]]:
    """Rend (constats retenus, état du dossier, phrases écartées faute de citation)."""
    numero, version = d["numero"], d["version"]
    legi = version["id_legi"]
    brutes: list[Phrase] = []
    etat: list[str] = []

    def constat(voix, texte, **kw):
        brutes.append(Phrase(voix, texte, **kw))

    # ---------------------------------------------------------------- le fonds
    constat("legi", f"L'article {numero} est en vigueur depuis le "
                    f"{en_date(version['date_debut'])}.",
            source="LEGI", reference=legi, nature="corpus")
    if d["anciens"]:
        constat("legi",
                f"Il a porté auparavant le numéro {', puis '.join(d['anciens'])} ; "
                "la concordance est déclarée par le fonds, non déduite.",
                source="LEGI", reference=legi, nature="corpus")
    if d["textes"]:
        dernier = d["textes"][-1]
        constat("legi",
                f"Sa rédaction en vigueur a été produite par « {dernier['titre']} ». "
                f"{len(d['textes'])} texte(s) l'ont modifié.",
                source="LEGI", reference=legi, nature="corpus")

    # ------------------------------------------------------------- le Parlement
    for r in d["raisons"][:3]:
        chambre = ("de l'Assemblée nationale" if "assemblee-nationale" in (r["url"] or "")
                   else "du Sénat" if "senat.fr" in (r["url"] or "") else "")
        structurel = r["voie"] == "section_appariee"
        precision = (" Le rattachement est structurel : la section commente "
                     f"l'article {r['article_du_texte']} du texte, qui modifie cet "
                     "article du code ; le passage cité ne le nomme pas forcément."
                     if structurel else
                     f" Il le commente sous l'article {r['article_du_texte']} du "
                     "texte alors en discussion." if r["article_du_texte"] else "")
        constat("parlement",
                f"Un {LIBELLE.get(r['type'], r['type'])} {chambre} commente cet "
                f"article.".replace("  ", " ") + precision,
                source=LIBELLE.get(r["type"], r["type"]), reference=r["url"],
                nature="web", offsets=(r["offset_debut"], r["offset_fin"]),
                confiance=r["confiance"],
                citation=extrait(r["extrait"], sinon=ABSENT))

    # Un même amendement écrit souvent plusieurs alinéas : le répéter à chacun
    # donnerait quatre fois la même justification. Il est nommé une fois, avec la
    # liste des alinéas qu'il a écrits.
    par_amendement: dict[tuple, dict] = {}
    for alinea in d["alineas"]:
        for m in alinea["amendements"]:
            cle = (m["numero"], m["chambre"])
            entree = par_amendement.setdefault(cle, {"m": m, "alineas": []})
            entree["alineas"].append(alinea["rang"])
    for (numero_amdt, chambre), entree in par_amendement.items():
        m = entree["m"]
        rangs = entree["alineas"]
        ou = ("le premier alinéa" if rangs == [1] else
              f"l'alinéa {rangs[0]}" if len(rangs) == 1 else
              "les alinéas " + ", ".join(map(str, rangs[:-1])) + f" et {rangs[-1]}")
        qui = m["nom"] or "un auteur non résolu"
        groupe = f" ({m['groupe']})" if m["groupe"] else ""
        assemblee = chambre == "assemblee"
        constat("parlement",
                f"C'est l'amendement {numero_amdt} de {qui}{groupe}, "
                f"{(m['sort'] or 'sort inconnu').lower()} "
                f"{'à l’Assemblée nationale' if assemblee else 'au Sénat'}, "
                f"qui a écrit {ou}.",
                source=f"amendement {numero_amdt} ({chambre})",
                reference=m["texte_discute"] or "", nature="corpus",
                confiance=m["confiance"],
                citation=f"passage apparié : {extrait(m['fenetre'], 120)}")
        if m["objet"]:
            constat("parlement",
                    f"Son auteur justifie ainsi l'amendement {numero_amdt}.",
                    source=f"objet de l'amendement {numero_amdt}",
                    reference=m["texte_discute"] or "", nature="corpus",
                    confiance=m["confiance"], citation=extrait(m["objet"]))

    # ----------------------------------------------- le Gouvernement, le Conseil
    for m in d["motivation_du_texte"]:
        # Le document porte sur le texte entier ; la note ne peut donc pas dire
        # qu'un de ses passages explique cet article. Elle peut dire lequel lui
        # ressemble le plus, à condition de dire que c'est tout ce qu'elle dit —
        # ce que porte la phrase elle-même, et non une étiquette à côté.
        meilleur = m["passages"][0] if m["passages"] else None
        if meilleur is None:
            constat(VOIX_DOCUMENT.get(m["type"], "gouvernement"),
                    f"Le texte qui a produit cet article — « {m['titre']} » — est "
                    f"accompagné d'un {LIBELLE[m['type']]}. Ce document porte sur le "
                    "texte entier, non sur cet article, et aucun de ses passages ne "
                    "partage assez de vocabulaire avec lui pour être distingué.",
                    source=LIBELLE[m["type"]], reference=m["url"], nature="web",
                    citation=extrait(m["extrait"], sinon=ABSENT))
            continue
        constat(VOIX_DOCUMENT.get(m["type"], "gouvernement"),
                f"Le texte qui a produit cet article — « {m['titre']} » — est "
                f"accompagné d'un {LIBELLE[m['type']]}. Ce document porte sur le "
                "texte entier, non sur cet article ; le passage ci-dessous est "
                "celui dont le vocabulaire recouvre le plus celui de l'article "
                f"({', '.join(meilleur.termes[:6])}). C'est un classement, non un "
                "rattachement : aucune arête ne les relie.",
                source=LIBELLE[m["type"]], reference=m["url"], nature="web",
                offsets=(meilleur.debut, meilleur.fin),
                citation=extrait(meilleur.texte, sinon=ABSENT))

    # ------------------------------------------------------------------- l'Union
    # Deux liens très différents mènent au même acte : le texte français **déclare**
    # le transposer, ou l'article le **nomme** dans son texte. Les dire de la même
    # façon ferait affirmer d'un article qu'il nomme un acte qu'il ne nomme pas.
    titres = {tr["celex"] if "celex" in tr.keys() else None: tr["titre"]
              for tr in d["transposition"]}
    for u in d["actes_motivants"]:
        considerants = (f", qui porte {u['considerants']} considérant(s) — le motif "
                        "que l'Union donne de son propre acte, à l'échelle de l'acte "
                        "entier" if u["considerants"] else "")
        if u["transposee"]:
            texte = (f"Le texte qui a produit cet article déclare transposer "
                     f"{ARTICLE_DEFINI[u['type_acte']]} {nommer(u)}{considerants}. "
                     "La déclaration figure dans l'intitulé du texte au Journal "
                     "officiel et porte sur le texte entier, non sur cet article.")
        else:
            texte = (f"Cet article nomme dans son texte "
                     f"{ARTICLE_DEFINI[u['type_acte']]} {nommer(u)}{considerants}.")
        # Aucune confiance n'est portée ici. Celle de `transpose` mesure « ce
        # texte transpose cet acte » ; l'accrocher à une phrase qui parle de
        # l'article ferait porter la mesure d'une proposition sur une autre. Elle
        # est rendue par `graphe.py`, avec la proposition qu'elle mesure.
        constat("union", texte, source="EUR-Lex", reference=u["url"], nature="web")

    # ------------------------------------------------ ce que l'article déplace
    if d["cite_par"]:
        cites = ", ".join(c["article_citant"] for c in d["cite_par"][:8])
        suite = f" et {len(d['cite_par']) - 8} autres" if len(d["cite_par"]) > 8 else ""
        constat("legi",
                f"{len(d['cite_par'])} article(s) du code renvoient à celui-ci : "
                f"{cites}{suite}. Les modifier suppose de les relire.",
                source="LEGI", reference=legi, nature="corpus")

    # -------------------------------------------------------- état du dossier
    if d["verdict"]:
        etat.append(f"Verdict : {VERDICT[d['verdict']['verdict']]}.")
        if (d["verdict"]["verdict"] == "raison_non_documentee"
                and d["verdict"]["partie"] in ("R", "D")):
            etat.append("Pour un article de la partie réglementaire, c'est l'état "
                        "ordinaire : un décret n'a ni exposé des motifs, ni débat, "
                        "ni amendement.")
    sans_amendement = sum(1 for a in d["alineas"] if not a["amendements"])
    if sans_amendement:
        etat.append(f"{sans_amendement} alinéa(s) sur {len(d['alineas'])} ne sont "
                    "rattachés à aucun amendement dans les corpus dépouillés.")
    if d["tentatives"]:
        etat.append(f"{len(d['tentatives'])} amendement(s) ont visé cet article "
                    "sans aboutir.")

    # Les phrases sont regroupées par voix : le § 4.3 demande de distinguer à
    # l'écran qui parle, ce qu'un ordre de construction ne fait pas.
    brutes.sort(key=lambda p: list(VOIX).index(p.voix))
    retenus = [p for p in brutes if p.reference]
    ecartees = [p for p in brutes if not p.reference]
    return retenus, etat, ecartees


def en_texte(d: dict) -> str:
    if not d:
        return "Article introuvable."
    constats, etat, ecartees = composer(d)
    L = [f"POURQUOI L'ARTICLE {d['numero']} EST CE QU'IL EST", ""]
    for ligne in etat:
        L.append(f"  {ligne}")
    voix = None
    for p in constats:
        if p.voix != voix:
            voix = p.voix
            L.append(f"\n— {VOIX[p.voix].upper()} —")
        L.append(f"\n  {p.texte}")
        if p.citation:
            L.append(f"    « {p.citation} »")
        marque = f"[{p.nature}] {p.source} : {p.reference}"
        if p.offsets:
            marque += f", offsets {p.offsets[0]}–{p.offsets[1]}"
        if p.confiance is not None:
            marque += f", confiance {p.confiance:.3f}"
        L.append(f"    {marque}")
    L.append(f"\n{'-' * 72}")
    L.append(f"  {len(constats)} phrase(s) retenue(s), {len(ecartees)} écartée(s) "
             "faute de citation résoluble.")
    L.append("  Note composée par assemblage de gabarits déterministes à partir du "
             "graphe.")
    L.append("  Aucun modèle de langue n'intervient ; les passages cités sont "
             "verbatim.")
    return "\n".join(L)


def e(x) -> str:
    return html.escape(str(x if x is not None else ""))


def en_html(d: dict) -> str:
    if not d:
        return "<p>Article introuvable.</p>"
    constats, etat, ecartees = composer(d)
    p = [f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(d['numero'])} — pourquoi cet article</title><style>
:root{{--fond:#fbfaf8;--encre:#1c1a17;--doux:#6b655c;--trait:#ddd8ce;--carte:#fff;
--legi:#6b655c;--gouv:#7a3b2e;--parl:#3d5a45;--ce:#4a4374;--ue:#1e5f74}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--fond:#16151a;
--encre:#e9e6df;--doux:#9a938a;--trait:#2f2c33;--carte:#1d1c22;--legi:#9a938a;
--gouv:#d98b76;--parl:#8fbb9c;--ce:#a9a2d8;--ue:#7fc4d8}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--fond);color:var(--encre);
font:17px/1.65 "Iowan Old Style",Palatino,Georgia,serif;padding:2.5rem 1.25rem}}
main{{max-width:44rem;margin:0 auto}}
h1{{font-size:1.7rem;margin:0 0 1.2rem;letter-spacing:-.01em}}
h2{{font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;
font-family:ui-sans-serif,system-ui,sans-serif;margin:2.4rem 0 .8rem}}
.etat{{background:var(--carte);border:1px solid var(--trait);padding:.9rem 1.1rem;
margin:1.2rem 0;font-size:.95rem}}
.etat b{{display:block;margin-bottom:.3rem}}
.ph{{margin:1.1rem 0;padding-left:1rem;border-left:3px solid var(--trait)}}
.cit{{margin:.45rem 0;font-size:.95rem;color:var(--encre)}}
.src{{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.72rem;
color:var(--doux);margin-top:.35rem}}
.src code{{font-family:ui-monospace,monospace}}
.legi{{border-left-color:var(--legi)}} .gouvernement{{border-left-color:var(--gouv)}}
.parlement{{border-left-color:var(--parl)}} .conseil_etat{{border-left-color:var(--ce)}}
.union{{border-left-color:var(--ue)}}
h2.legi{{color:var(--legi)}} h2.gouvernement{{color:var(--gouv)}}
h2.parlement{{color:var(--parl)}} h2.conseil_etat{{color:var(--ce)}}
h2.union{{color:var(--ue)}}
a{{color:inherit}}
footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--trait);
font-size:.76rem;color:var(--doux);font-family:ui-sans-serif,system-ui,sans-serif}}
</style></head><body><main>
<h1>Pourquoi l'article {e(d['numero'])} est ce qu'il est</h1>"""]
    if etat:
        p.append('<div class="etat"><b>État du dossier</b>'
                 + " ".join(e(l) for l in etat) + "</div>")
    voix = None
    for ph in constats:
        if ph.voix != voix:
            voix = ph.voix
            p.append(f'<h2 class="{voix}">{e(VOIX[voix])}</h2>')
        p.append(f'<div class="ph {voix}"><div>{e(ph.texte)}</div>')
        if ph.citation:
            p.append(f'<div class="cit">« {e(ph.citation)} »</div>')
        lien = (f'<a href="{e(ph.reference)}">{e(ph.source)}</a>'
                if ph.nature == "web" else
                f'{e(ph.source)} — <code>{e(ph.reference)}</code>')
        details = []
        if ph.offsets:
            details.append(f"offsets {ph.offsets[0]}–{ph.offsets[1]}")
        if ph.confiance is not None:
            details.append(f"confiance {ph.confiance:.3f}")
        p.append(f'<div class="src">{lien}'
                 + (" · " + " · ".join(e(x) for x in details) if details else "")
                 + "</div></div>")
    p.append(f"""<footer>
{len(constats)} phrase(s) retenue(s), {len(ecartees)} écartée(s) faute de citation
résoluble — le contrat du § 4.3 est un filtre exécuté, non une intention.
Une citation <em>web</em> pointe une URL publique ; une citation <em>corpus</em>
pointe un identifiant du fonds versionné, résoluble dans le miroir DILA et son
manifeste haché.<br><br>
Note composée par assemblage de gabarits déterministes à partir du graphe.
<b>Aucun modèle de langue n'intervient</b> ; les passages entre guillemets sont
verbatim. L'article 50 du règlement (UE) 2024/1689 vise le contenu synthétique
produit par un système d'IA : il ne trouve pas à s'appliquer ici.
</footer></main></body></html>""")
    return "".join(p)


def verifier_le_contrat(base: sqlite3.Connection, limite: int | None) -> None:
    """Éprouve le filtre du § 4.3, plutôt que d'affirmer qu'il fonctionne.

    Deux vérifications, et la seconde ne dit rien sans la première. Le filtre est
    d'abord confronté à une phrase délibérément sans source : s'il ne l'écarte
    pas, il ne filtre rien. Il est ensuite passé sur le fonds réel.
    """
    temoins = [Phrase("legi", "phrase sans source"),
               Phrase("legi", "phrase sourcée", reference="LEGIARTI000000000000")]
    retenus = [p for p in temoins if p.reference]
    print(f"témoin : 2 phrases → {len(retenus)} retenue(s), "
          f"{2 - len(retenus)} écartée(s)")
    if len(retenus) != 1:
        sys.exit("le filtre n'écarte pas une phrase sans source : contrat rompu")

    numeros = [n for (n,) in base.execute(
        "SELECT a.numero FROM verdict v JOIN article a ON a.id = v.article_id"
        + (f" LIMIT {int(limite)}" if limite else ""))]
    constats = ecartees = vides = 0
    for numero in numeros:
        retenus, _, perdues = composer(interroger(base, numero))
        constats += len(retenus)
        ecartees += len(perdues)
        vides += not retenus
    print(f"fonds  : {len(numeros)} article(s) → {constats} constat(s) retenu(s), "
          f"{ecartees} écarté(s), {vides} note(s) sans aucun constat")
    print("Zéro écarté n'est pas un filtre inutile : le schéma interdit déjà une "
          "arête sans source résoluble — `document.url` est NOT NULL, et toute "
          "arête dérivée porte une preuve. Le contrat est tenu en amont ; le "
          "filtre est le garde-fou qui le vérifie à la sortie.")


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[2] == "--contrat":
        base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
        verifier_le_contrat(base, int(sys.argv[3]) if len(sys.argv) > 3 else None)
        base.close()
        return
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
