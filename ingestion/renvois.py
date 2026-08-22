#!/usr/bin/env python3
"""Troisième tranche : le graphe de renvois entre articles.

Les deux premières tranches répondent au citoyen — pourquoi cet article existe.
Celle-ci répond au législateur, dont la question n'est jamais « pourquoi » mais
« si je modifie cet article, qu'est-ce qui bouge ». C'est le premier livrable
prospectif du projet, et il ne demande aucune source nouvelle : la donnée est
dans le texte des articles, elle n'avait simplement jamais été extraite.

Trois précautions, chacune tirée d'une erreur déjà commise dans ce projet.

**La résolution se fait à la date de la citation, pas sur le fonds en vigueur.**
Un numéro d'article n'est pas une identité stable : R. 531-2 a désigné deux
dispositions différentes à deux époques (`01-rapport-verification-sources.md`
§ 2.3 bis). Résoudre un renvoi de 2013 contre le code d'aujourd'hui invente un
lien. La cible retenue est donc la version qui couvrait la date d'entrée en
vigueur du texte citant.

**Ce qu'on ne sait pas est nommé, jamais tu.** Un renvoi vers la partie
réglementaire, vers un autre code ou vers un numéro introuvable ne devient pas un
lien interne et ne disparaît pas non plus : il est enregistré avec sa portée.
Confondre « cité hors de ce code » et « cité et introuvable » ferait passer une
limite de périmètre pour une incohérence du droit.

**La convention légistique fait la détection de code.** Un renvoi qui ne nomme
pas de code vise le code courant ; 2 875 références sur 3 112 sont dans ce cas.
Celles qui nomment un code le nomment juste après le numéro.

Usage :
    renvois.py <base.sqlite> [schema/002-renvois.sql]
"""

from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from legi_vers_graphe import decouper_en_alineas  # noqa: E402

REFERENCE = re.compile(r"\b([LRD])\.?\s?(\d{3})-(\d{1,3})(?:-(\d{1,3}))?")
# Le code cité suit le numéro, avant toute ponctuation forte.
CODE_SUIVANT = re.compile(r"[^.]{0,40}?du (présent code|code [^,;.)]{3,45})")
# La convention légistique nomme le code une seule fois par énumération, et
# l'énumération peut être longue : « aux articles L. 131-2, L. 132-1 et L. 133-44
# du code monétaire et financier ». Le nom peut aussi précéder : « du livre III du
# code monétaire et financier et aux articles… ». Cherché dans les deux sens, mais
# seulement pour une référence qui ne se résout pas dans ce code — sans quoi une
# phrase citant un autre code puis le code courant verrait la seconde référence
# réétiquetée à tort.
CODE_ENUMERATION = re.compile(r"du (code [^,;.)]{3,45})")
MEME_CODE = re.compile(r"du même code")
# La capture court au-delà du nom quand l'énumération reprend : « code de l'action
# sociale et des familles et des ar[ticles] ». Coupures lues dans les valeurs
# effectivement produites, non supposées.
REPRISE = re.compile(r"\s+(?:et\s+(?:aux?\s+)?(?:articles?|des\s+ar)"
                     r"|ainsi\s+que|prévoit|pour\s|dans\s|sont\s|est\s)")
# Le point de « L. 131-2 » n'est pas une fin de phrase. Sans cette exclusion, le
# balayage arrière s'arrête au milieu de l'énumération qu'il devait remonter.
BORNE = re.compile(r"(?<![LRD])(?<!art)(?<!n°)[.;]")
FENETRE_MINI = 60

# Précision mesurée à la main sur 20 renvois internes tirés au sort : voir
# `docs/08-graphe-de-renvois.md` § 3. Borne inférieure de Wilson à 95 %.
CONFIANCE = 0.8389


def numero(m: re.Match) -> str:
    return f"{m.group(1)}{m.group(2)}-{m.group(3)}" + (f"-{m.group(4)}" if m.group(4) else "")


def fenetre(texte: str, debut: int, fin: int) -> str | None:
    marge = max(0, (200 - (fin - debut)) // 2)
    extrait = re.sub(r"\s+", " ", texte[max(0, debut - marge):fin + marge]).strip()
    return extrait if len(extrait) >= FENETRE_MINI else None


def code_de_l_enumeration(texte: str, debut: int, fin: int) -> str | None:
    """Code nommé dans la même énumération que la référence, en aval ou en amont.

    N'est appelée que pour une référence introuvable dans ce code : la fonction
    lève un doute, elle n'en crée pas.
    """
    borne = BORNE.search(texte, fin)
    limite = borne.start() if borne else len(texte)
    aval = CODE_ENUMERATION.search(texte, fin, limite)
    if aval:
        return REPRISE.split(aval.group(1))[0].strip()
    # « du même code » renvoie au dernier code nommé, y compris par-delà une borne
    # de phrase : c'est la convention qui rendait introuvables des renvois au code
    # de l'environnement cités en série.
    amont_borne = max((m.end() for m in BORNE.finditer(texte, 0, debut)), default=0)
    depart = 0 if MEME_CODE.search(texte, fin, limite) else amont_borne
    amont = list(CODE_ENUMERATION.finditer(texte, depart, debut))
    return REPRISE.split(amont[-1].group(1))[0].strip() if amont else None


def main() -> None:
    if not 2 <= len(sys.argv) <= 3:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    schema = Path(sys.argv[2]) if len(sys.argv) == 3 else \
        Path(__file__).resolve().parent.parent / "schema" / "002-renvois.sql"
    base.executescript("DROP VIEW IF EXISTS renvois_entrants; "
                       "DROP TABLE IF EXISTS renvoie_a;")
    base.executescript(schema.read_text(encoding="utf-8"))

    # Index numéro → intervalles de validité. La borne haute 2999-01-01 est la
    # sentinelle du fonds LEGI pour « en vigueur ».
    versions: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for numero_article, debut, fin, article_id in base.execute(
            "SELECT a.numero, v.date_debut, v.date_fin, a.id "
            "FROM version_article v JOIN article a ON a.id = v.article_id"):
        versions[numero_article].append((debut, fin or "2999-01-01", article_id))

    def resoudre(cle: str, date: str) -> int | None:
        for debut, fin, article_id in versions.get(cle, ()):
            if debut <= date < fin:
                return article_id
        return None

    prochaine_preuve = base.execute(
        "SELECT coalesce(max(id), 0) + 1 FROM preuve").fetchone()[0]

    # Le seuil de 60 caractères imposé aux preuves vise l'appariement flou, où une
    # fenêtre courte ne discrimine rien. Une référence explicite n'a pas ce
    # défaut : elle se suffit. Mais elle doit rester citable, et un alinéa de
    # quarante caractères ne fournit pas de contexte lisible. Le contexte est donc
    # pris dans l'article entier, qui contient le segment — 864 renvois étaient
    # sinon perdus, et ce sont souvent des alinéas de pure énumération de renvois,
    # les plus utiles pour la question posée.
    plein: dict[str, str] = {}
    for id_legi, texte in base.execute("SELECT id_legi, texte FROM version_article"):
        plein[id_legi] = " ".join(decouper_en_alineas(texte))

    renvois, preuves = [], []
    compte: dict[str, int] = defaultdict(int)
    vus: set[tuple[str, str]] = set()
    for segment_id, texte, date, version_id in base.execute(
            "SELECT s.id, s.texte, v.date_debut, v.id_legi FROM segment s "
            "JOIN version_article v ON v.id_legi = s.version_id"):
        propre = re.sub(r"\s+", " ", texte)
        contexte = plein.get(version_id, propre)
        decalage = contexte.find(propre)
        if decalage < 0:
            contexte, decalage = propre, 0
        for m in REFERENCE.finditer(propre):
            cle = numero(m)
            if (segment_id, cle) in vus:
                continue
            suite = CODE_SUIVANT.match(propre[m.end():m.end() + 70])
            nomme = suite.group(1) if suite else ""
            code_cite = None
            if nomme.startswith("code ") and "consommation" not in nomme:
                portee, article_id = "externe", None
                code_cite = REPRISE.split(nomme)[0].strip()
            elif m.group(1) in "RD":
                portee, article_id = "reglementaire", None
            else:
                article_id = resoudre(cle, date)
                portee = "interne" if article_id else "non_resolue"
                if portee == "non_resolue":
                    # Cherché dans l'article entier : une énumération de renvois
                    # traverse les alinéas, et le code n'est nommé qu'une fois.
                    code_cite = code_de_l_enumeration(
                        contexte, decalage + m.start(), decalage + m.end())
                    if code_cite:
                        portee = "externe"
            extrait = fenetre(contexte, decalage + m.start(), decalage + m.end())
            if extrait is None:
                compte["sans_preuve"] += 1
                continue
            vus.add((segment_id, cle))
            compte[portee] += 1
            preuves.append((prochaine_preuve, "renvoi_dans_le_texte", extrait,
                            decalage + m.start()))
            renvois.append((segment_id, article_id, cle, code_cite, portee,
                            CONFIANCE, prochaine_preuve))
            prochaine_preuve += 1

    base.executemany(
        "INSERT INTO preuve (id, methode, fenetre, source_offset) VALUES (?, ?, ?, ?)",
        preuves)
    base.executemany(
        "INSERT INTO renvoie_a (segment_id, article_id, numero_cite, code_cite, "
        "portee, confiance, preuve_id) VALUES (?, ?, ?, ?, ?, ?, ?)", renvois)
    base.commit()

    violations = base.execute("PRAGMA foreign_key_check").fetchall()
    cites, citants = base.execute(
        "SELECT count(DISTINCT article_cite), count(DISTINCT article_citant) "
        "FROM renvois_entrants").fetchone()
    en_vigueur = base.execute(
        "SELECT count(DISTINCT article_id) FROM version_article "
        "WHERE etat = 'VIGUEUR'").fetchone()[0]

    print(f"renvois relevés            : {len(renvois)}")
    for portee in ("interne", "reglementaire", "externe", "non_resolue"):
        print(f"  {portee:14s}         : {compte[portee]} "
              f"({100 * compte[portee] / len(renvois):.1f} %)")
    print(f"  écartés faute de preuve  : {compte['sans_preuve']}")
    print(f"\nsur les versions en vigueur :")
    print(f"  articles citant un autre : {citants} ({100 * citants / en_vigueur:.1f} %)")
    print(f"  articles cités par un autre : {cites} ({100 * cites / en_vigueur:.1f} %)")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
