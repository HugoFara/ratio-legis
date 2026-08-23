#!/usr/bin/env python3
"""API REST de lecture du graphe — second livrable du § 4.4.

Elle n'expose rien de neuf : `restitution/graphe.py` sait déjà remonter la
provenance d'un article, `restitution/note.py` sait déjà la rédiger sous le
contrat du § 4.3. L'API les rend interrogeables, et impose trois choses que la
ligne de commande laissait à l'appelant.

**L'attribution voyage avec la donnée.** `ATTRIBUTION.md` en fait une obligation
de licence, pas une politesse : elle « doit apparaître dans l'interface, dans
l'API et dans tout export du graphe ». Chaque réponse porte donc l'en-tête
`X-Attribution`, chaque charge utile porte le bloc `mentions`, et
`/attribution` les donne en entier. Une donnée ouverte qu'on peut consommer sans
jamais voir d'où elle vient n'est pas attribuée.

**Le produit n'interprète pas.** Le § 0 l'écrit en non-objectif et le § 8 en fait
un risque de positionnement. Chaque réponse le redit, parce qu'une API se
consomme sans lire le README.

**La base est ouverte en lecture seule**, une connexion par requête. SQLite n'est
pas sûr entre fils d'exécution, et FastAPI exécute les fonctions synchrones dans
un pool ; partager une connexion marcherait presque toujours, ce qui est la pire
des situations.

Le coût d'une requête est celui de la seizième tranche : médiane 9 ms, 95ᵉ
centile 33 ms — voir `docs/22`.

Usage :
    RATIO_LEGIS_BASE=travail/ratio-legis.sqlite uvicorn restitution.api:app
    python3 restitution/api.py [base.sqlite] [port]      # équivalent, pour essayer
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from starlette.requests import Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graphe  # noqa: E402
import note  # noqa: E402
import retentissement  # noqa: E402
import surlignage  # noqa: E402

BASE = Path(os.environ.get("RATIO_LEGIS_BASE", "travail/ratio-legis.sqlite"))

MENTIONS = {
    "licence_donnees": "Licence Ouverte / Etalab 2.0",
    "licence_code": "AGPL-3.0-or-later",
    "attributions": [
        "Source : DILA — Légifrance (fonds LEGI, JORF, DOLE), "
        "Licence Ouverte / Etalab 2.0",
        "Source : Assemblée nationale — open data, Licence Ouverte / Etalab",
        "Source : Sénat — data.senat.fr, licence ouverte reprenant les termes "
        "de data.gouv.fr",
        "© Union européenne, https://eur-lex.europa.eu, 1998-2026 — "
        "réutilisation autorisée, décision 2011/833/UE",
        "Rapports de commission : informations publiques (loi du 17 juillet 1978), "
        "régime de réutilisation non confirmé",
    ],
    "ne_fait_pas_foi": "Donnée dérivée. Le droit en vigueur est celui publié par "
                       "Légifrance.",
    "non_interpretatif": "Ce service documente la provenance des textes. Il ne "
                         "produit ni interprétation juridique, ni conseil.",
}

# Un en-tête HTTP ne transporte que du latin-1 : le tiret cadratin et le symbole
# © des mentions complètes y font échouer la réponse entière. L'en-tête porte donc
# une forme courte, sans accent, et renvoie à `/attribution` pour le texte exact —
# qui est de toute façon dans chaque charge utile.
EN_TETE_ATTRIBUTION = ("Sources : DILA/Legifrance, Assemblee nationale, Senat, "
                       "Union europeenne (EUR-Lex) ; voir /attribution")
assert EN_TETE_ATTRIBUTION.isascii(), "un en-tete HTTP ne transporte que du latin-1"

RESUME = ("Ratio Legis — graphe de provenance normative du droit français. "
          "Pour un article de code en vigueur, les matériaux qui expliquent "
          "pourquoi il existe sous cette forme.")

app = FastAPI(title="Ratio Legis", summary=RESUME, version="0.17.0",
              license_info={"name": "AGPL-3.0-or-later"})


def connexion():
    """Une connexion en lecture seule par requête, refermée à la fin."""
    if not BASE.exists():
        raise HTTPException(503, f"base absente : {BASE}")
    base = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    try:
        yield base
    finally:
        base.close()


@app.middleware("http")
async def attribution(requete: Request, suite):
    reponse = await suite(requete)
    reponse.headers["X-Attribution"] = EN_TETE_ATTRIBUTION
    reponse.headers["X-Licence"] = "Licence Ouverte / Etalab 2.0"
    reponse.headers["X-Avertissement"] = ("Donnee derivee, ne fait pas foi ; "
                                          "aucune interpretation juridique")
    return reponse


def enveloppe(charge: dict[str, Any]) -> dict[str, Any]:
    return {**charge, "mentions": MENTIONS}


def sans_ensembles(valeur: Any) -> Any:
    """`interroger` rend un `set` ; JSON n'en connaît pas, et l'ordre doit être stable.

    Il rend aussi des `Passage` — les extraits classés par `proximite.py`. Un
    `dataclass` n'est pas non plus du JSON, et le sérialiser à la main ailleurs
    ferait diverger la sortie de l'API de celle des autres rendus.
    """
    if is_dataclass(valeur) and not isinstance(valeur, type):
        return sans_ensembles(asdict(valeur))
    if isinstance(valeur, set):
        return sorted(map(str, valeur))
    if isinstance(valeur, dict):
        return {c: sans_ensembles(v) for c, v in valeur.items()}
    if isinstance(valeur, list):
        return [sans_ensembles(v) for v in valeur]
    return valeur


# --------------------------------------------------------------------- racine
@app.get("/", summary="Ce qu'est ce service, et ce qu'il n'est pas")
def racine() -> dict:
    return enveloppe({
        "service": "Ratio Legis", "resume": RESUME,
        "points_d_entree": {
            "/articles": "liste des articles en vigueur, filtrable par partie et "
                         "par verdict",
            "/articles/{numero}": "fiche de provenance complète",
            "/articles/{numero}/note": "la note « pourquoi cet article », sous le "
                                       "contrat du § 4.3",
            "/articles/{numero}/surlignage": "chaque alinéa, et le texte qui l'a "
                                             "introduit",
            "/articles/{numero}/retentissement": "si je modifie cet article, "
                                                 "qu'est-ce qui bouge",
            "/renvois/sommet": "les articles que le plus d'autres articles citent",
            "/mesures": "métriques d'hygiène législative",
            "/attribution": "les mentions obligatoires, en entier",
            "/sante": "état de la base servie",
            "/docs": "documentation OpenAPI",
        },
    })


@app.get("/attribution", summary="Les mentions obligatoires")
def attribution_complete() -> dict:
    return enveloppe({"obligation": "L'attribution est une obligation de licence, "
                                    "pas une politesse."})


@app.get("/sante", summary="État de la base servie")
def sante(base: sqlite3.Connection = Depends(connexion)) -> dict:
    compte = {t: base.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("article", "verdict", "motive", "resulte_de", "porte_sur",
                        "acte_ue", "considerant")}
    diffusion = {}
    try:
        diffusion = dict(base.execute("SELECT clef, valeur FROM diffusion"))
    except sqlite3.OperationalError:
        pass          # base de travail, non issue d'un dump : pas de table diffusion
    return enveloppe({"base": BASE.name, "octets": BASE.stat().st_size,
                      "compte": compte, "diffusion": diffusion})


# ------------------------------------------------------------------- articles
@app.get("/articles", summary="Les articles en vigueur")
def articles(base: sqlite3.Connection = Depends(connexion),
             partie: str | None = Query(None, pattern="^[LRD]$"),
             verdict: str | None = Query(None),
             depuis: str | None = Query(None, description="numéro d'article exclu, "
                                                          "pour paginer"),
             limite: int = Query(100, ge=1, le=1000)) -> dict:
    conditions, valeurs = [], []
    if partie:
        conditions.append("v.partie = ?")
        valeurs.append(partie)
    if verdict:
        conditions.append("v.verdict = ?")
        valeurs.append(verdict)
    if depuis:
        conditions.append("a.numero > ?")
        valeurs.append(depuis)
    ou = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    lignes = base.execute(
        f"""SELECT a.numero, v.partie, v.verdict, v.a_passage_motivant,
                   v.a_amendement, v.a_article_du_texte, v.a_document_du_texte,
                   v.a_acte_ue
            FROM verdict v JOIN article a ON a.id = v.article_id
            {ou} ORDER BY a.numero LIMIT ?""", (*valeurs, limite)).fetchall()
    colonnes = ["numero", "partie", "verdict", "a_passage_motivant", "a_amendement",
                "a_article_du_texte", "a_document_du_texte", "a_acte_ue"]
    resultat = [dict(zip(colonnes, l)) for l in lignes]
    total = base.execute(
        f"SELECT COUNT(*) FROM verdict v JOIN article a ON a.id = v.article_id {ou}",
        valeurs).fetchone()[0]
    suite = resultat[-1]["numero"] if len(resultat) == limite else None
    return enveloppe({"total_du_filtre": total, "rendus": len(resultat),
                      "suite_depuis": suite, "articles": resultat})


@app.get("/articles/{numero}", summary="La fiche de provenance d'un article")
def article(numero: str, base: sqlite3.Connection = Depends(connexion)) -> dict:
    donnees = graphe.interroger(base, numero)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    return enveloppe(sans_ensembles(donnees))


@app.get("/articles/{numero}/note", summary="La note « pourquoi cet article »")
def note_article(numero: str, base: sqlite3.Connection = Depends(connexion)) -> dict:
    donnees = graphe.interroger(base, numero)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    retenus, etat, ecartees = note.composer(donnees)
    return enveloppe({
        "numero": numero,
        "verdict": donnees.get("verdict"),
        "constats": [asdict(p) for p in retenus],
        "etat_du_dossier": etat,
        "ecartees_faute_de_citation": len(ecartees),
        "contrat": "Toute phrase affirmative porte une citation résoluble "
                   "(document et offsets). Une phrase sans citation est supprimée "
                   "avant rendu, pas excusée — § 4.3 de la feuille de route.",
        "sans_modele_de_langue": "Note composée par assemblage de gabarits "
                                 "déterministes à partir du graphe. Aucun modèle de "
                                 "langue n'intervient ; les passages cités sont "
                                 "verbatim.",
    })


@app.get("/articles/{numero}/note.html", response_class=HTMLResponse,
         summary="La même note, en HTML")
def note_html(numero: str, base: sqlite3.Connection = Depends(connexion)) -> str:
    donnees = graphe.interroger(base, numero)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    return note.en_html(donnees)


@app.get("/articles/{numero}/surlignage",
         summary="Chaque alinéa, et le texte qui l'a introduit")
def surlignage_article(numero: str,
                       base: sqlite3.Connection = Depends(connexion)) -> dict:
    donnees = surlignage.surligner(base, numero)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    return enveloppe({**donnees, "ce_que_la_couleur_dit":
                      "Le texte qui a introduit l'alinéa, jamais qui l'a voulu. "
                      "Les deux arêtes utilisées — produite_par et repris_de — sont "
                      "déclarées par LEGI ou portent leur fenêtre de preuve ; les "
                      "liens d'abrogation en sont exclus, un texte qui supprime un "
                      "article ne l'a pas écrit."})


@app.get("/articles/{numero}/surlignage.html", response_class=HTMLResponse,
         summary="Le même surlignage, à lire")
def surlignage_html(numero: str,
                    base: sqlite3.Connection = Depends(connexion)) -> str:
    donnees = surlignage.surligner(base, numero)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    return surlignage.en_html(donnees)


# --------------------------------------------------------- ce qui retentit
# La question du légiste, et non celle du chercheur : `graphe.py` remonte à
# l'origine, celui-ci descend aux conséquences. Voir `retentissement.py`.
@app.get("/articles/{numero}/retentissement",
         summary="Si je modifie cet article, qu'est-ce qui bouge")
def retentissement_article(
        numero: str, base: sqlite3.Connection = Depends(connexion),
        profondeur: int = Query(retentissement.PROFONDEUR, ge=1, le=6)) -> dict:
    donnees = retentissement.retentir(base, numero, profondeur)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    return enveloppe({**donnees, "ce_que_l_onde_dit":
                      "Le rang 1 cite cet article ; le rang n cite un article du "
                      "rang n-1. Arête renvoie_a, dérivée du texte des articles et "
                      "munie de sa fenêtre de preuve. La liste dit ce qu'il faudrait "
                      "relire, jamais ce qu'il faudrait y écrire."})


@app.get("/articles/{numero}/retentissement.html", response_class=HTMLResponse,
         summary="Le même retentissement, à lire")
def retentissement_html(
        numero: str, base: sqlite3.Connection = Depends(connexion),
        profondeur: int = Query(retentissement.PROFONDEUR, ge=1, le=6)) -> str:
    donnees = retentissement.retentir(base, numero, profondeur)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    return retentissement.en_html(donnees)


@app.get("/renvois/sommet", summary="Les articles que le plus d'autres articles citent")
def renvois_sommet(base: sqlite3.Connection = Depends(connexion),
                   limite: int = Query(retentissement.SOMMET, ge=1, le=500)) -> dict:
    return enveloppe({"mesure": "nombre d'articles en vigueur qui renvoient à "
                                "celui-ci, au rang 1. Mesure de structure : elle ne "
                                "dit pas qu'un article compte, elle dit combien "
                                "d'autres le nomment.",
                      "articles": retentissement.sommet(base, limite)})


@app.get("/articles/{numero}/graphe.txt", response_class=PlainTextResponse,
         summary="Le graphe brut de l'article, arête par arête")
def graphe_texte(numero: str, base: sqlite3.Connection = Depends(connexion)) -> str:
    donnees = graphe.interroger(base, numero)
    if not donnees:
        raise HTTPException(404, f"aucun article {numero} en vigueur dans ce fonds")
    return graphe.en_texte(donnees)


# -------------------------------------------------------------------- mesures
@app.get("/mesures", summary="Les métriques d'hygiène législative")
def mesures(base: sqlite3.Connection = Depends(connexion),
            famille: str | None = Query(None)) -> dict:
    chemin = Path(__file__).resolve().parent.parent / "data" / "mesures" / "hygiene.tsv"
    if not chemin.exists():
        raise HTTPException(503, "mesures absentes : lancer tools/mesures/hygiene.py")
    lignes = []
    with chemin.open(encoding="utf-8") as source:
        entete = source.readline().rstrip("\n").split("\t")
        for ligne in source:
            valeurs = dict(zip(entete, ligne.rstrip("\n").split("\t")))
            if famille and valeurs.get("famille") != famille:
                continue
            lignes.append(valeurs)
    return enveloppe({"avertissement": "Ces taux décrivent le corpus servi, non le "
                                       "droit français dans son ensemble.",
                      "mesures": lignes})


def main() -> None:
    import uvicorn
    global BASE
    if len(sys.argv) > 1:
        BASE = Path(sys.argv[1])
    uvicorn.run(app, host="127.0.0.1",
                port=int(sys.argv[2]) if len(sys.argv) > 2 else 8000)


if __name__ == "__main__":
    main()
