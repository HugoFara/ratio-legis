"""Résoudre un numéro d'article vers la bonne lignée.

Depuis la scission des lignées (`schema/001`, `legi_vers_graphe.py`), un numéro
peut désigner plusieurs nœuds `article` : L313-10 en a deux, le cautionnement
disproportionné de 1993 à 2016 et la fiche standardisée d'information depuis.
Toute résolution par numéro doit donc dire **à quelle date** — et la date est
presque toujours connue : un rapport de commission, un texte en discussion, un
amendement appartiennent à un dossier, et le dossier a un texte daté. Un
rapport de 2010 qui nomme L313-10 parle du cautionnement.

Deux résolutions, et rien entre les deux :

- `courant(numero)` : la lignée la plus haute, pour ce qui entre par un numéro
  sans date — la restitution, l'API, les mesures sur le droit en vigueur ;
- `du_dossier(numero, dossier)` : d'abord la lignée dont un texte du dossier a
  **écrit** une version — créée ou modifiée, jamais seulement abrogée ; c'est
  la déclaration de LEGI elle-même, et elle tranche le cas de la
  recodification, dont l'ordonnance est datée de mars 2016 pour des versions
  qui entrent en vigueur en juillet. À défaut, `a_la_date(numero, date)` : la
  lignée dont la période couvre la date du texte du dossier ; avant la
  première, la première ; après la dernière, la dernière.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict


class Resolveur:
    def __init__(self, base: sqlite3.Connection) -> None:
        self.lignees: dict[str, list[tuple[int, int, str, str]]] = defaultdict(list)
        for id_, numero, lignee, debut, fin in base.execute("""
                SELECT a.id, a.numero, a.lignee,
                       coalesce(p.debut, '0000-00-00'), coalesce(p.fin, '9999-12-31')
                FROM article a LEFT JOIN periode_article p ON p.article_id = a.id
                ORDER BY a.numero, a.lignee"""):
            self.lignees[numero.replace(" ", "")].append((lignee, id_, debut, fin))
        self.dates: dict[str, str] = dict(base.execute("""
            SELECT i.dossier_id, min(t.date_texte) FROM issu_de i
            JOIN texte_normatif t ON t.id_jorf = i.texte_id GROUP BY i.dossier_id"""))
        self.numeros: dict[int, str] = {id_: n for n, ls in self.lignees.items()
                                        for _, id_, _, _ in ls}
        self.ecrits: dict[str, set[int]] = defaultdict(set)   # dossier → lignées écrites
        for dossier, article_id in base.execute("""
            SELECT DISTINCT i.dossier_id, v.article_id FROM issu_de i
            JOIN produite_par p ON p.texte_id = i.texte_id
            JOIN version_article v ON v.id_legi = p.version_id
            WHERE p.type_lien NOT IN ('ABROGE', 'ABROGATION')"""):
            self.ecrits[dossier].add(article_id)

    def courant(self, numero: str) -> int | None:
        lignees = self.lignees.get(numero.replace(" ", ""))
        return lignees[-1][1] if lignees else None

    def a_la_date(self, numero: str, date: str | None) -> int | None:
        lignees = self.lignees.get(numero.replace(" ", ""))
        if not lignees:
            return None
        if date is None or len(lignees) == 1:
            return lignees[-1][1]
        for _, id_, debut, fin in lignees:
            if date < fin:
                return id_
        return lignees[-1][1]

    def du_dossier(self, numero: str, dossier: str | None) -> int | None:
        lignees = self.lignees.get(numero.replace(" ", ""))
        if not lignees:
            return None
        if len(lignees) > 1 and dossier:
            ecrites = [id_ for _, id_, _, _ in lignees if id_ in self.ecrits.get(dossier, ())]
            if len(ecrites) == 1:
                return ecrites[0]
        return self.a_la_date(numero, self.dates.get(dossier or ""))

    def courants(self) -> dict[str, int]:
        """numero → identifiant de la lignée la plus haute, pour les boucles."""
        return {n: ls[-1][1] for n, ls in self.lignees.items()}
