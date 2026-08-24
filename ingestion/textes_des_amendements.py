#!/usr/bin/env python3
"""Vingt-cinquième tranche : la correspondance des identifiants de texte.

`docs/16` § 6 la posait comme le dernier verrou du chaînon des textes en
discussion : « `vise` relie un amendement à sa subdivision — "Article 10" — et
`porte_sur` relie cette subdivision au code. Les deux se joindraient, mais les
identifiants de texte des deux corpus ne se correspondent pas. Une table de
correspondance est nécessaire, et elle n'est pas écrite. »

Elle l'est ici, et elle n'est pas devinée.

**Sénat.** Un document du Sénat est numéroté par (session, numéro) : le texte
n° 283 de la session 2013-2014. C'est exactement la clef d'une URL Améli, et
c'est aussi ce que porte le nom du fichier récupéré depuis DOLE —
`leg/pjl13-283.html`, ou `petite-loi-ameli/2013-2014/283.html`. Les deux
identifiants désignent le même document.

Les liens `tas` sont écartés : `leg/tas06-135.html` est le **texte adopté**
n° 135, série distincte de celle des textes déposés. Les confondre rattacherait
des amendements à un document qu'ils n'ont jamais amendé.

**Assemblée.** La référence d'un amendement porte la série et le numéro —
`L14B1015` pour le texte déposé, `L14BTC2442` pour le texte de commission —, et
`amendement.texte_discute` en garde la forme `B1015` / `BTC2442`. Les documents
de l'Assemblée présents dans le corpus emploient le même numéro : `l14b2442` dans
les URL `dyn`, `r2442-a0` pour un texte de commission annexé à son rapport. La
série `ta{N}` est écartée pour la même raison que `tas` au Sénat.

**Deux contrôles, tous deux rejoués à chaque exécution.**

1. *Le dossier concorde.* Le texte trouvé par le numéro doit appartenir au même
   dossier DOLE que les amendements. 67 jeux sur 67 au Sénat, 26 sur 39 à
   l'Assemblée — les 13 restants n'ont aucun document de la bonne série dans le
   corpus, ce qui est un trou de corpus et non un désaccord.
2. *Les subdivisions tombent dans la plage.* Un amendement déposé sur l'article 12
   suppose que le texte ait au moins douze articles, et `texte_discute.articles`
   les compte. 3 578 sur 3 655, soit 97,9 %. C'est le contrôle qui tranche : un
   appariement faux s'y verrait avant tout autre.

Un troisième a servi à décider, sans être rejouable en une passe : apparier
chaque jeu à un texte tiré au hasard fait tomber la concordance des subdivisions
avec `porte_sur` de 40,9 % à 15,3 % au Sénat, de 7,6 % à 2,4 % à l'Assemblée.

**Ce que la correspondance débloque, et ce qu'elle ne débloque pas.** Voir
`docs/31`. En deux mots : l'arête existe, elle est déclarée aux deux bouts, et
elle ne rattrape presque aucun amendement orphelin — parce qu'un amendement
orphelin ne vise pas un article existant, il en crée un.

Usage :
    textes_des_amendements.py <base.sqlite> [schema/011-textes-des-amendements.sql]
"""

from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# --- identification des documents, par chambre --------------------------------
# Sénat : (session, numéro). `petite-loi-ameli` porte la session en entier ; les
# préfixes `pjl`/`ppl` la portent sur deux chiffres — `pjl13-283` est le texte 283
# de la session 2013-2014.
SENAT_PETITE = re.compile(r"petite-loi-ameli-(\d{4})-(\d{4})-(\d+)")
SENAT_DEPOSE = re.compile(r"leg-(?:pjl|ppl)(\d{2})-(\d+)")
# Assemblée : la série « b », celle des textes déposés et des textes de
# commission, seule comparable à la référence des amendements.
ASSEMBLEE = (re.compile(r"dyn-\d+-textes-l\d+b0*(\d+)_"),
             re.compile(r"/\d+-propositions-pion0*(\d+)"),
             re.compile(r"/\d+-ta-commission-r0*(\d+)-"),
             re.compile(r"/\d+-rapports-r0*(\d+)-"))
AMENDEMENT_AN = re.compile(r"^BTC?(\d+)/")

# --- lecture d'une subdivision -------------------------------------------------
# Le Sénat écrit « Article 12 », l'Assemblée « ART. 12 » ; les deux écrivent
# « premier » pour 1. Le suffixe latin fait partie du numéro : l'article 19 octies
# n'est pas l'article 19.
SUBDIVISION = re.compile(
    r"\bart(?:icle)?\.?\s+(premier|1er|\d+)\s*"
    r"(bis|ter|quater|quinquies|sexies|septies|octies|nonies|decies)?", re.I)
# « art. add. après Article 19 » ne vise pas l'article 19. L'amendement demande la
# création d'un article qui n'existe pas encore, dont le numéro dans le code n'est
# pas fixé et ne le sera qu'à la codification. La subdivision ne dit alors rien du
# code, et la lire comme une cible serait le contresens le plus coûteux possible.
ARTICLE_ADDITIONNEL = re.compile(
    r"art\.?\s*add|article\s+additionnel|apr[èe]s\s+(?:l')?\s*art|avant\s+(?:l')?\s*art",
    re.I)

# Borne inférieure de Wilson à 95 % pour 15 arêtes justes sur 15 vérifiées à la
# main, tirées après la garde et disjointes de l'échantillon qui a servi à la
# concevoir. Le premier tirage, sur le graphe d'avant la garde, donnait 13/15 —
# ses deux erreurs sont celles que la garde retire.
#
# Ce n'est pas la confiance de `porte_sur` (0,8389) reprise telle quelle : une
# chaîne de deux liens ne vaut pas son maillon le plus fort, et le mesurer était
# moins cher que d'en discuter. Voir `docs/31` § 4.
CONFIANCE = 0.7961


def numero_de_subdivision(subdivision: str | None) -> str | None:
    trouve = SUBDIVISION.search(subdivision or "")
    if not trouve:
        return None
    tete = trouve.group(1).lower()
    tete = "1er" if tete in ("premier", "1er") else tete
    return tete + (" " + trouve.group(2).lower() if trouve.group(2) else "")


def tete_numerique(numero: str) -> int | None:
    chiffres = numero.split(" ")[0]
    return int(chiffres) if chiffres.isdigit() else (1 if chiffres == "1er" else None)


def correspondances(base: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """(chambre, clef du corpus d'amendements, identifiant du texte discuté)."""
    par_clef: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for identifiant, dossier, chambre in base.execute(
            "SELECT id, dossier_id, chambre FROM texte_discute"):
        if chambre == "senat":
            trouve = SENAT_PETITE.search(identifiant)
            if trouve:
                clef = f"{trouve.group(1)}-{trouve.group(2)}_{trouve.group(3)}.csv"
                par_clef[("senat", clef)].append((identifiant, dossier))
                continue
            trouve = SENAT_DEPOSE.search(identifiant)
            if trouve:
                debut = 2000 + int(trouve.group(1))
                clef = f"{debut}-{debut + 1}_{trouve.group(2)}.csv"
                par_clef[("senat", clef)].append((identifiant, dossier))
            continue
        for marque in ASSEMBLEE:
            trouve = marque.search(identifiant)
            if trouve:
                par_clef[("assemblee", trouve.group(1))].append((identifiant, dossier))

    trouvees = []
    for dossier, chambre, corpus in base.execute(
            "SELECT DISTINCT dossier_id, chambre, texte_discute FROM amendement"):
        if chambre == "assemblee":
            reference = AMENDEMENT_AN.match(corpus)
            clef = reference.group(1) if reference else None
        else:
            clef = corpus
        # Le dossier doit concorder : le numéro seul se répète d'une session à
        # l'autre et d'une chambre à l'autre. Sans cette condition, un texte
        # homonyme d'un autre dossier passerait, et c'est le mode d'échec que la
        # phase 0 a payé le plus cher.
        candidats = [i for i, d in par_clef.get((chambre, clef or ""), [])
                     if d == dossier]
        if candidats:
            trouvees.append((chambre, corpus, sorted(candidats)[0]))
    return trouvees


def construire(base: sqlite3.Connection, schema: Path) -> dict:
    base.executescript(schema.read_text(encoding="utf-8"))
    compte: dict[str, int] = defaultdict(int)

    # `porte_sur` retient une convention légistique : quand un dispositif ne nomme
    # aucun code, il modifie le sien. Elle vaut pour ce qu'elle mesure — `docs/16`
    # § 4 la donne à 20/20 — et elle ne supporte pas d'être composée. Un contrôle
    # à la main sur quinze arêtes en a donné deux fausses, toutes deux de la même
    # cause : « Le code de la propriété intellectuelle est ainsi modifié : … 9°
    # L'article L. 722-1 est complété », où l'hôte est déclaré une seule fois en
    # tête du bloc, hors de la fenêtre de preuve du 9°.
    #
    # La garde ne devine pas : elle exige que **la fenêtre de preuve nomme le code
    # de la consommation**, au lieu de se contenter de l'avoir supposé. Elle coûte
    # 1 398 cibles, et c'est le prix de la règle § 5.3 ; elle en libère aussi, un
# article de texte qui semblait en réécrire plusieurs n'en réécrivant plus
# qu'un une fois les cibles supposées retirées.
    CODE = "consommation"
    cibles: dict[tuple[str, str], set[int]] = defaultdict(set)
    for texte_id, article_du_texte, article_id, fenetre in base.execute(
            "SELECT p.texte_id, lower(p.article_du_texte), p.article_id, pr.fenetre "
            "FROM porte_sur p LEFT JOIN preuve pr ON pr.id = p.preuve_id "
            "WHERE p.portee = 'interne'"):
        if CODE not in (fenetre or "").lower():
            compte["hote_suppose_non_nomme"] += 1
            continue
        cibles[(texte_id, article_du_texte)].add(article_id)

    lignes, aretes = [], []
    for chambre, corpus, texte_id in correspondances(base):
        etendue = base.execute("SELECT articles FROM texte_discute WHERE id = ?",
                               (texte_id,)).fetchone()[0]
        distinctes, dans_la_plage = set(), 0
        for amendement_id, subdivision in base.execute(
                "SELECT id, subdivision FROM amendement "
                "WHERE chambre = ? AND texte_discute = ?", (chambre, corpus)):
            numero = numero_de_subdivision(subdivision)
            if numero and numero not in distinctes:
                distinctes.add(numero)
                tete = tete_numerique(numero)
                if tete is not None and etendue and tete <= etendue:
                    dans_la_plage += 1
            # L'article additionnel se reconnaît avant que le numéro soit lu :
            # « art. add. après Article 77 bis » en est un, que la tête du numéro
            # se laisse extraire ou non. Tester dans l'autre ordre en rangeait
            # vingt parmi les subdivisions illisibles, et faisait diverger ce
            # compte de celui des mesures d'hygiène.
            if ARTICLE_ADDITIONNEL.search(subdivision or ""):
                compte["article_additionnel"] += 1
                continue
            if not numero:
                compte["subdivision_illisible"] += 1
                continue
            vises = cibles.get((texte_id, numero))
            if not vises:
                compte["subdivision_sans_cible_dans_le_code"] += 1
                continue
            if len(vises) > 1:
                compte["cible_non_unique"] += 1
                continue
            aretes.append((amendement_id, next(iter(vises)), texte_id, numero,
                           "derivee", CONFIANCE))
        lignes.append((chambre, corpus, texte_id, "numero_declare",
                       len(distinctes), dans_la_plage))

    base.executemany(
        "INSERT INTO texte_des_amendements (chambre, texte_corpus, texte_id,"
        " methode, subdivisions, dans_la_plage) VALUES (?, ?, ?, ?, ?, ?)", lignes)
    base.executemany(
        "INSERT OR IGNORE INTO depose_sur (amendement_id, article_id, texte_id,"
        " article_du_texte, methode, confiance) VALUES (?, ?, ?, ?, ?, ?)", aretes)
    compte["jeux_apparies"] = len(lignes)
    compte["aretes"] = len(aretes)
    return compte


def main() -> None:
    if not 2 <= len(sys.argv) <= 3:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    schema = Path(sys.argv[2]) if len(sys.argv) == 3 else \
        Path(__file__).resolve().parent.parent / "schema" / \
        "011-textes-des-amendements.sql"
    base.execute("PRAGMA foreign_keys = ON")
    compte = construire(base, schema)
    base.commit()

    jeux = base.execute(
        "SELECT chambre, count(*), sum(subdivisions), sum(dans_la_plage) "
        "FROM texte_des_amendements GROUP BY 1").fetchall()
    total = dict(base.execute(
        "SELECT chambre, count(DISTINCT texte_discute) FROM amendement GROUP BY 1"))
    print("correspondances établies")
    for chambre, jeux_apparies, subdivisions, plage in jeux:
        print(f"  {chambre:10s} {jeux_apparies:3d} jeux sur {total[chambre]:3d}"
              f"   subdivisions dans la plage du texte : "
              f"{plage}/{subdivisions} ({100 * plage / max(1, subdivisions):.1f} %)")

    print("\namendements écartés, et pourquoi")
    print(f"  article additionnel — ne vise aucun article existant : "
          f"{compte['article_additionnel']}")
    print(f"  subdivision sans cible interne dans le code          : "
          f"{compte['subdivision_sans_cible_dans_le_code']}")
    print(f"  l'article du texte en modifie plusieurs              : "
          f"{compte['cible_non_unique']}")
    print(f"  cible écartée, code hôte supposé et non nommé        : "
          f"{compte['hote_suppose_non_nomme']}")
    print(f"  subdivision illisible                                : "
          f"{compte['subdivision_illisible']}")

    articles, amendements = base.execute(
        "SELECT count(DISTINCT article_id), count(DISTINCT amendement_id) "
        "FROM depose_sur").fetchone()
    en_vigueur = base.execute(
        "SELECT count(DISTINCT d.article_id) FROM depose_sur d "
        "JOIN version_en_vigueur v ON v.article_id = d.article_id").fetchone()[0]
    neufs = base.execute("""
        SELECT count(DISTINCT a.numero) FROM depose_sur d
        JOIN article a ON a.id = d.article_id
        JOIN version_en_vigueur v ON v.article_id = a.id
        WHERE a.numero NOT IN (SELECT article FROM tentative_sur_article)"""
    ).fetchone()[0]
    print(f"\narêtes depose_sur          : {compte['aretes']}")
    print(f"  amendements positionnés  : {amendements}")
    print(f"  articles du code atteints: {articles}  (en vigueur : {en_vigueur})")
    print(f"  dont sans aucune tentative déclarée jusqu'ici : {neufs}")
    print(f"intégrité : {len(base.execute('PRAGMA foreign_key_check').fetchall())} "
          "violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
