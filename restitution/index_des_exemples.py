"""Page d'entrée des rendus d'exemple, pour qui veut voir sans rien installer.

GitHub affiche un `.html` versionné comme du code source ; publié tel quel par
GitHub Pages, le dossier `restitution/exemples/` devient lisible, à condition
d'avoir une porte d'entrée. Ce script l'écrit. Il ne produit aucune donnée :
il liste des fichiers qui existent et dit, pour chacun, ce qu'il montre — la
phrase vient d'ici, et un rendu que ce script ne connaît pas est listé quand
même, sans phrase, plutôt que tu.

    python3 restitution/index_des_exemples.py restitution/exemples
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import RUBRIQUE, SOCLE  # noqa: E402

# Un rendu par article, dans l'ordre où on conseille de les lire. La phrase dit
# pourquoi cet article-là a été choisi, pas ce qu'il contient.
FICHES = {
    "L224-43": "une chaîne complète, de l'article en vigueur jusqu'à l'amendement et son but déclaré",
    "L122-23": "les quatre paroles côte à côte — Gouvernement, chiffrage, Conseil d'État, Parlement",
    "L111-1": "un article très cité",
    "L511-7": "un article que le droit de l'Union sature",
    "L112-1-1": "aucune motivation parlementaire ; la seule raison connue est une directive",
    "L521-2": "un article suivi à travers la navette et la recodification",
    "L722-10": "une motivation venue d'une section de rapport que rien ne rattachait",
    "L411-1": "l'obligation générale de conformité des produits — l'un des 78 articles de la partie législative dont la raison n'est pas documentée",
    "R121-1": "un article réglementaire que son ascendance législative documente encore",
    "D824-3": "le seul article D du code qu'un rapport de commission explique",
    "R512-31": "la réponse ordinaire de la partie réglementaire — raison non documentée, alors que sept articles le citent",
    "D120-7": "un article dont la seule raison connue vient de quatre règlements de l'Union",
}

TENTATIVES = {
    "L732-3": "trois amendements écartés comme cavaliers, dont celui du Gouvernement",
    "L312-9": "la délégation d'assurance emprunteur",
    "L113-3": "les deux chambres, et un sort lu dans l'état procédural",
    "L224-43": "quatre amendements adoptés dont l'alinéa subsiste",
    "L111-3": "l'article le plus disputé du fonds : 67 tentatives, 56 non abouties",
    "sommet": "les articles les plus disputés",
}

RETENTISSEMENT = {
    "L111-1": "ce qui bougerait, à deux rangs",
    "L221-5": "vingt-quatre articles le citent, et son origine n'est que située",
    "R512-31": "un article réglementaire non documenté, et ceux qui reposent sur lui",
    "D412-51": "huit articles au premier rang",
    "sommet": "les articles les plus cités",
}

SECTIONS = [
    # (sous-dossier ou None, titre, ce que la vue rend, phrases)
    (None, "Pourquoi cet article", "la fiche de provenance, arête par arête : ce qui le motive, qui a écrit chaque alinéa, ce qui le cite, ce qu'on a tenté", FICHES),
    ("notes", "La note, sous contrat", "la même chose en langue naturelle ; aucune phrase sans citation résoluble, et le compte des phrases écartées en pied de page", FICHES),
    ("surlignage", "Qui a écrit quoi", "la couleur donne le texte qui a introduit l'alinéa, la trame signale une retouche, la marque nomme l'amendement", FICHES),
    ("tentatives", "Ce qui a été tenté", "les amendements déposés sur l'article, avec leur sort — et ce qui les a bloqués", TENTATIVES),
    ("retentissement", "Si je modifie cet article", "ce qu'il faudrait relire, par onde de renvois ; pas ce qu'il faudrait y écrire", RETENTISSEMENT),
]

STYLE = SOCLE + """
p{max-width:44rem}
ul{list-style:none;padding:0;margin:0}
li{background:var(--carte);border:1px solid var(--trait);border-radius:2px;
padding:.55rem .8rem;margin:.4rem 0;font-size:.95rem}
li a{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.85rem;
text-decoration:none;margin-right:.6rem}
li a:hover{text-decoration:underline}
h2{margin-bottom:.3rem}
.chapeau{border-bottom:0;padding-bottom:0;margin-bottom:1rem}
.en-tete{border-bottom:3px double var(--trait);margin-bottom:1.6rem}
"""

AVERTISSEMENT = (
    "Ces pages rendent des matériaux et le chemin qui y mène. Elles n'interprètent "
    "pas le droit, ne disent pas ce qu'un article veut dire ni s'il s'applique à "
    "un cas. Chaque arête porte sa méthode et une confiance mesurée."
)


def numero_de(fichier: Path) -> str:
    return fichier.stem


def section(dossier: Path, sous: str | None, titre: str, rend: str, phrases: dict[str, str]) -> str:
    racine = dossier / sous if sous else dossier
    fichiers = {numero_de(f): f for f in racine.glob("*.html") if f.name != "index.html"}
    # Les rendus connus d'abord, dans l'ordre conseillé ; les autres ensuite,
    # par numéro, sans phrase.
    ordre = [n for n in phrases if n in fichiers] + sorted(n for n in fichiers if n not in phrases)
    lignes = []
    for n in ordre:
        chemin = fichiers[n].relative_to(dossier).as_posix()
        phrase = phrases.get(n, "")
        lignes.append(
            f'<li><a href="{html.escape(chemin)}">{html.escape(n)}</a>{html.escape(phrase)}</li>'
        )
    return (
        f"<h2>{html.escape(titre)}</h2><p class=chapeau>{html.escape(rend)}</p>"
        f"<ul>{''.join(lignes)}</ul>"
    )


def page(dossier: Path) -> str:
    corps = "".join(section(dossier, *s) for s in SECTIONS)
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Ratio Legis — ce que ça produit</title><style>{STYLE}</style></head>"
        "<body><main><div class=en-tete>" + RUBRIQUE + "<h1>Ce que le graphe produit</h1>"
        "<p class=chapeau>Pour un article du code de la consommation en vigueur : "
        "pourquoi existe-t-il sous cette forme ? Les rendus ci-dessous sont ceux "
        "que le dépôt versionne, tels que le graphe les produit.</p></div>"
        f"<p>{html.escape(AVERTISSEMENT)}</p>"
        f"{corps}"
        "<footer>Ratio Legis — graphe de provenance normative. Aucune arête sans "
        "source résoluble. Les confiances sont des bornes inférieures mesurées, "
        "documentées dans <code>docs/</code>. Sources : DILA (LEGI, JORF, DOLE), "
        "Assemblée nationale, Sénat, EUR-Lex — Licence Ouverte / Etalab 2.0. "
        'Code et mesures : <a class=depot href="https://github.com/HugoFara/ratio-legis">'
        "github.com/HugoFara/ratio-legis</a>.</footer></main></body></html>"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    dossier = Path(argv[1])
    sortie = dossier / "index.html"
    sortie.write_text(page(dossier), encoding="utf-8")
    print(f"écrit : {sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
