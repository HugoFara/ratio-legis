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

La date du dossier est celle de la loi promulguée. Pour un amendement, c'est
trop tard : il est écrit sur un texte en discussion, des mois avant, et il
nomme l'article tel qu'il est ce jour-là. « L. 141-3 du code de la
consommation est complété » déposé au Sénat en novembre 2015 sous un dossier
promulgué en novembre 2016 désignait l'article de 2005, abrogé par la
recodification de juillet 2016 — non le L141-3 créé en 2024, seule lignée
ouverte à la date de la loi. `du_dossier` prend donc une date facultative,
celle du texte discuté quand l'appelant la connaît (`docs/49`).
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict


class Resolveur:
    def __init__(self, base: sqlite3.Connection) -> None:
        self.lignees: dict[str, list[tuple[int, int, str, str]]] = defaultdict(list)
        # Une lignée dont toutes les versions sont mort-nées ou annulées n'a
        # jamais été en vigueur : rien ne peut la viser, la modifier ni la
        # commenter. `periode_article` l'ignore, et la jointure interne
        # l'écarte ici — un amendement de 2019 sur L. 217-9 se résolvait vers
        # la lignée d'une version mort-née de 2022 (docs/49 § 8).
        for id_, numero, lignee, debut, fin in base.execute("""
                SELECT a.id, a.numero, a.lignee, p.debut, p.fin
                FROM article a JOIN periode_article p ON p.article_id = a.id
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
            WHERE p.type_lien NOT IN ('ABROGE', 'ABROGATION')
              AND v.etat NOT IN ('MODIFIE_MORT_NE', 'ANNULE')"""):
            self.ecrits[dossier].add(article_id)
        # Les lignées closes par une **modification** qu'une autre lignée du même
        # numéro suit : la disposition d'un autre numéro y est arrivée
        # (`legi_vers_graphe.arrivees_d_un_autre_numero`). La recodification de
        # 2016 clôt par abrogation, et n'en est pas.
        self.closes_par_arrivee: set[int] = {id_ for (id_,) in base.execute("""
            SELECT a.id FROM article a
            JOIN version_article v ON v.article_id = a.id
            WHERE v.date_debut = (SELECT max(date_debut) FROM version_article
                                  WHERE article_id = a.id
                                    AND etat NOT IN ('MODIFIE_MORT_NE', 'ANNULE'))
              AND v.etat = 'MODIFIE'
              AND EXISTS (SELECT 1 FROM article b
                          WHERE b.numero = a.numero AND b.lignee = a.lignee + 1)""")}

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

    def du_dossier(self, numero: str, dossier: str | None,
                   date: str | None = None, existant: bool = False) -> int | None:
        """`existant` : le numéro nomme l'article tel qu'il est au jour du texte
        (« l'article L. 311-14 devient l'article L. 311-20 », « … est abrogé »),
        non l'article que le texte crée (« Art. L. 311-14. – … »). Il ne change
        rien, sauf quand la loi du dossier a fait arriver sous ce numéro la
        disposition d'un autre : la lignée en vigueur au jour du texte, qu'elle
        clôt, est alors celle que l'article existant désigne (docs/59 § 2)."""
        lignees = self.lignees.get(numero.replace(" ", ""))
        if not lignees:
            return None
        quand = date or self.dates.get(dossier or "")
        if len(lignees) > 1 and dossier:
            ecrites = [id_ for _, id_, _, _ in lignees if id_ in self.ecrits.get(dossier, ())]
            if len(ecrites) == 1:
                if existant:
                    en_vigueur = self.a_la_date(numero, quand)
                    if en_vigueur != ecrites[0] and en_vigueur in self.closes_par_arrivee:
                        return en_vigueur
                return ecrites[0]
        return self.a_la_date(numero, quand)

    def courants(self) -> dict[str, int]:
        """numero → identifiant de la lignée la plus haute, pour les boucles."""
        return {n: ls[-1][1] for n, ls in self.lignees.items()}
