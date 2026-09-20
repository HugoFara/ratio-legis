"""Le lien « signaler cette arête », sur chaque arête de chaque page.

Un lien faux coûte plus que dix liens manquants (§ 5.3), et le projet n'a pas
d'autre source de jugement humain que ses lecteurs : les confiances sont des
bornes calculées sur des tirages jugés par l'auteur ou par des agents, et le
jeu d'annotation attend toujours sa relecture. Le canal le moins cher vers un
verdict humain est donc la page elle-même : chaque arête porte un lien qui
ouvre un rapport pré-rempli — l'article, l'arête, la cible, la preuve — dans le
dépôt public. Le lecteur n'a qu'à dire ce qui lui fait dire qu'elle est fausse.

Le lien est une URL, rien d'autre : aucun script, aucune requête à l'ouverture
de la page. GitHub ne voit le lecteur que s'il clique.
"""

from __future__ import annotations

import html
from urllib.parse import quote

DEPOT = "https://github.com/HugoFara/ratio-legis"
GABARIT = "arete-fausse.md"


def lien(arete: str, article: str, cible: str, preuve: str = "") -> str:
    """L'ancre HTML « signaler », vers un rapport pré-rempli."""
    titre = f"Arête fausse : {arete} sur {article} → {cible}"
    corps = (f"**Article :** {article}\n**Arête :** `{arete}`\n**Cible :** {cible}\n"
             + (f"**Preuve montrée :** {preuve}\n" if preuve else "")
             + "\n**Ce qui vous fait dire qu'elle est fausse :**\n\n\n"
             "_(Les lignes ci-dessus viennent de la page ; laissez-les, elles "
             "identifient l'arête.)_\n")
    url = (f"{DEPOT}/issues/new?template={GABARIT}"
           f"&title={quote(titre[:200])}&body={quote(corps)}")
    return (f'<a class="signaler" href="{html.escape(url)}" rel="nofollow" '
            f'title="Cette arête vous paraît fausse ? Dites-le : c\'est le rapport de '
            f'bug le plus utile au projet.">signaler</a>')
