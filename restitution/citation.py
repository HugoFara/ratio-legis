#!/usr/bin/env python3
"""Ce que la restitution a le droit de montrer d'un document, et sous quelle forme.

Une même règle, tenue à trois endroits, finit par être tenue différemment aux
trois. C'est arrivé : `note.py` plafonnait les extraits à 400 caractères,
`graphe.py` à 700, et 772 caractères de rapport se sont retrouvés dans les
exemples versionnés. Le plafond est donc nommé **une fois**, ici, et les modules
de restitution l'importent.

**D'où vient le nombre.** `ATTRIBUTION.md` distingue deux gestes. Rediffuser le
corps d'un rapport de commission est une republication, et les régimes des deux
chambres l'interdisent sous Licence Ouverte. En citer un passage à fin de
contrôle est une citation, couverte deux fois : par l'absence de droit d'auteur
sur les documents parlementaires si l'on suit les chambres, par l'exception de
courte citation de l'article L. 122-5, 3° a) du code de la propriété
intellectuelle si l'on ne les suit pas. 400 caractères tiennent dans les deux
lectures ; le corps entier ne tient dans aucune.

Ce plafond commande aussi la **fenêtre de classement** de `proximite.py` : ce
qu'on classe et ce qu'on montre doivent être le même passage, sans quoi le
lecteur juge un extrait sur les mérites d'un texte plus long qu'il ne voit pas.
"""

from __future__ import annotations

PLAFOND_EXTRAIT = 400

# Un dump ouvert peut légitimement ne pas rediffuser le texte d'un document —
# voir `tools/diffusion/dump.py`. La citation devient alors vide, et des
# guillemets vides affirment sans montrer : exactement ce que le § 4.3 interdit.
# On dit ce qui manque et où le retrouver, plutôt que de laisser un blanc.
ABSENT = "texte non rediffusé dans cette base — le document reste à son URL"


def extrait(texte: str, limite: int = PLAFOND_EXTRAIT, sinon: str = "") -> str:
    """Le passage, ramené au plafond, espaces normalisés, coupe signalée."""
    propre = " ".join((texte or "").split())
    if not propre:
        return sinon
    return propre[:limite] + ("…" if len(propre) > limite else "")


def cite(texte: str, limite: int = PLAFOND_EXTRAIT) -> str:
    """Le même passage, entre guillemets — ou la mention de ce qui manque."""
    court = extrait(texte, limite)
    return f"« {court} »" if court else f"[{ABSENT}]"
