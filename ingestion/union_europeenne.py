#!/usr/bin/env python3
"""Cinquième tranche : la couche européenne.

Le graphe savait dire quel texte français a produit un article, et quel document
parlementaire le motive. Il ne savait pas dire ce que ce texte n'avait pas le
choix d'écrire. Pour le code de la consommation, c'est une omission de premier
ordre : **280 actes de l'Union sont cités dans son propre texte**. Tant qu'ils
manquaient, un article entièrement dicté par une directive était rendu comme un
article sans motivation connue — le silence du produit signifie « raison non
documentée », et il était ici mensonger.

Rien de tout cela ne demande une source nouvelle. Les actes sont nommés en toutes
lettres dans les alinéas, publiés au Journal officiel, déjà dans le fonds LEGI.

Trois choses méritent d'être dites, parce qu'aucune n'est évidente.

**Le numéro français ne donne pas l'ordre année/numéro.** « Règlement (CE)
n° 1008/2008 » se lit numéro 1008 de l'année 2008 ; « règlement (UE) 2018/302 »
se lit année 2018, numéro 302. La numérotation s'est inversée en 2015. Sur 1 478
citations, 102 ont leurs deux composantes plausibles comme années — dont
« n° 2006/2004 », le règlement coopération, où se tromper produit un identifiant
valide désignant un autre acte. Le signe qui tranche est la mention `n°`, héritée
de l'ancienne forme : elle est présente sur les 91 anciennes et absente sur les
11 nouvelles, sans exception dans le corpus. Quand ni l'une ni l'autre
composante n'est une année plausible, la citation est abandonnée, pas devinée.

**Le CELEX est construit, donc il doit être vérifié.** Un identifiant fabriqué
depuis un numéro est une hypothèse, et une hypothèse bien formée reste plausible
même quand elle est fausse. Chaque CELEX est confronté à Cellar, le service
d'identifiants de l'Office des publications, qui répond 303 pour un acte connu et
404 sinon (`tools/ue/verifier_celex.py`). Ce qui n'est pas vérifié n'entre pas
dans la base. Le résultat de cette vérification est versionné dans
`data/corpus/celex-verifies.tsv`, pour que le pipeline reste rejouable hors ligne.

**Citer n'est pas transposer.** L'arête produite s'appelle `cite_acte_ue` et ne
dit rien de plus que ce qu'elle constate : cet alinéa nomme cet acte, à cet
offset. Un article peut citer une directive pour l'écarter ; un règlement ne se
transpose jamais. La qualification du lien n'est pas dans les données, elle n'est
donc pas produite. La transposition, elle, est enregistrée à part et seulement
quand le texte français la **déclare** dans son intitulé au Journal officiel.

Usage :
    union_europeenne.py <base.sqlite> <celex-verifies.tsv> [titres-jorf.tsv]
"""

from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ANNEE_MAX = 2026
FENETRE_MINI = 60

# Le mot-type ancre la citation. Les formes « délégué » et « d'exécution » sont
# des règlements à part entière et portent la même lettre CELEX.
ANCRE = re.compile(r"\b(directives?"
                   r"|r[eè]glements?(?:\s+(?:d[ée]l[ée]gu[ée]s?|d'ex[ée]cution))?"
                   r"|d[ée]cisions?)\b", re.I)
# Les espaces parasites sont ceux du fonds : « 2009/22/ CE » est tel quel dans le
# XML LEGI, coupure de ligne comprise.
NUMERO = re.compile(r"(?:\(\s*(?:UE|CE|CEE|Euratom)\s*\)\s*)?"
                    r"(n\s*[°º]\s*)?(\d{2,4})\s*/\s*(\d{1,4})"
                    r"(?:\s*/\s*(?:UE|CE|CEE|Euratom))?")
# Ce qui peut séparer deux actes d'une même énumération, et rien d'autre :
# « les directives 2013/36/UE et (UE) 2019/1937 ». Au-delà, il faut une nouvelle
# ancre — sans quoi le titre d'un acte, qui cite les actes qu'il modifie,
# rattacherait ceux-ci au mot-type du premier.
LIAISON = re.compile(r"^[\s,]*(?:et|ou|ainsi que)?[\s,]*$")
# La déclaration de transposition est dans l'intitulé complet publié au JO :
# « portant transposition de », « transposant ».
TRANSPOSITION = re.compile(r"transpos", re.I)
# Un intitulé français reprend le titre officiel de la directive qu'il transpose,
# et ce titre nomme les actes que *la directive* modifie. Sans coupure, le décret
# n° 2016-622 se voit attribuer la transposition des directives 2008/48/CE et
# 2013/36/UE et du règlement 1093/2010, qui ne sont que ce que la directive
# 2014/17/UE modifie. Tout ce qui suit une de ces charnières relève d'un autre
# rapport que la transposition, et n'est pas retenu.
RUPTURE = re.compile(r"\b(?:modifiant|abrogeant|complétant|remplaçant)\b"
                     r"|\bet\s+(?:mesures|relati\w+|adaptation|diverses)", re.I)

# Un article de l'acte n'est retenu que s'il est **seul** dans la fenêtre qui
# précède : « De l'article 23 du règlement (CE) n° 1008/2008 ». Les énumérations
# — « des articles 5 ter, 8, 9 et 16 » — ne sont pas découpées : une première
# version qui s'y essayait attribuait à un acte les articles de celui cité juste
# avant, et perdait les suffixes (« 5 ter » lu « 5 »). 150 citations sur 1 478
# sont dans le cas simple ; pour les autres le champ reste nul plutôt que faux.
BORNE = re.compile(r"(?<![LRD])(?<!art)(?<!n°)[.;:]")
ARTICLE_SEUL = re.compile(r"\bl['’]article\s+(\d{1,3})\s+d[ue]s?\s*$", re.I)
MOT_ARTICLE = re.compile(r"\barticles?\b", re.I)

TYPE = {"L": "directive", "R": "reglement", "D": "decision"}
URL = "https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:{}"

# Précision mesurée à la main sur 20 citations tirées au sort : voir
# `docs/13-couche-europeenne.md` § 4. Borne inférieure de Wilson à 95 %.
CONFIANCE = 0.8389


def lettre(ancre: str) -> str:
    a = ancre.lower()
    if a.startswith("direct"):
        return "L"
    return "R" if a.startswith(("règl", "regl")) else "D"


def plausible(annee: int) -> bool:
    return 1952 <= annee <= ANNEE_MAX          # 1952 : entrée en vigueur du traité CECA


def celex(ancre: str, marque_numero: bool, a: int, b: int) -> str | None:
    """Identifiant CELEX d'un acte cité, ou None si l'ordre n'est pas décidable.

    Une directive porte toujours l'année en tête, y compris sur deux chiffres
    (« 93/13/CEE »). Un règlement ou une décision dépend de la réforme de 2015,
    que la mention `n°` signale.
    """
    type_acte = lettre(ancre)
    if type_acte == "L":
        annee, numero = a, b
    else:
        a_ok, b_ok = plausible(a), plausible(b)
        if a_ok and b_ok:
            annee, numero = (b, a) if marque_numero else (a, b)
        elif b_ok:
            annee, numero = b, a
        elif a_ok:
            annee, numero = a, b
        else:
            return None                        # § 5.1 : abandonnée, pas devinée
    if annee < 100:
        annee += 1900
    if not plausible(annee) or not 1 <= numero <= 9999:
        return None
    return f"3{annee:04d}{type_acte}{numero:04d}"


def citations(texte: str):
    """Rend (celex, denomination, debut, fin) pour chaque acte de l'Union cité.

    `debut` est l'offset du mot-type, non du numéro : la dénomination retenue est
    ce que le législateur a écrit, « règlement (CE) n° 2006/2004 » et non un
    numéro nu. Pour les items suivants d'une énumération, il n'y a pas de
    mot-type propre et l'offset part du numéro.
    """
    for ancre in ANCRE.finditer(texte):
        pos, premier = ancre.end(), True
        while True:
            portee = pos + (60 if premier else 30)
            m = NUMERO.search(texte, pos, portee)
            if not m or not LIAISON.match(texte[pos:m.start()]):
                break
            identifiant = celex(ancre.group(1), bool(m.group(1)),
                                int(m.group(2)), int(m.group(3)))
            if identifiant:
                debut = ancre.start() if premier else m.start()
                yield (identifiant,
                       re.sub(r"\s+", " ", texte[debut:m.end()]).strip(),
                       debut, m.end())
            pos, premier = m.end(), False


def designation(formes: Counter) -> str:
    """Forme littérale retenue pour nommer l'acte, parmi celles observées.

    Un acte cité en énumération n'a pas de mot-type à lui : « les règlements
    (CE) n° 1184/2006 et n° 1224/2009 » ne donne, pour le second, que
    « n° 1224/2009 ». Si cette forme tronquée est la plus fréquente, l'acte est
    affiché sans dire qu'il est un règlement. On préfère donc la plus fréquente
    *parmi celles qui nomment le type*, et on ne se rabat sur les autres que
    lorsqu'il n'en existe aucune. Toutes restent des formes réellement écrites
    par le législateur : on choisit entre des observations, on n'en fabrique pas.
    """
    nommees = Counter({f: n for f, n in formes.items() if ANCRE.match(f)})
    return (nommees or formes).most_common(1)[0][0]


def article_de_l_acte(texte: str, depart: int, debut: int) -> str | None:
    """Numéro de l'article de l'acte cité, si et seulement s'il est sans ambiguïté.

    La fenêtre part de la citation précédente ou de la dernière borne de phrase,
    selon la plus tardive : sans cette borne basse, l'énumération d'un acte est
    lue comme celle du suivant.
    """
    bornes = [m.end() for m in BORNE.finditer(texte, depart, debut)]
    fenetre_amont = re.sub(r"\s+", " ",
                           texte[max(bornes[-1] if bornes else 0, depart):debut]).rstrip()
    trouve = ARTICLE_SEUL.search(fenetre_amont)
    if trouve and len(MOT_ARTICLE.findall(fenetre_amont)) == 1:
        return trouve.group(1)
    return None


def fenetre(texte: str, debut: int, fin: int) -> str | None:
    marge = max(0, (200 - (fin - debut)) // 2)
    extrait = re.sub(r"\s+", " ", texte[max(0, debut - marge):fin + marge]).strip()
    return extrait if len(extrait) >= FENETRE_MINI else None


def prochain_identifiant(base: sqlite3.Connection) -> int:
    return (base.execute("SELECT COALESCE(MAX(id), 0) FROM preuve").fetchone()[0]) + 1


def main() -> None:
    if not 3 <= len(sys.argv) <= 4:
        sys.exit(__doc__)
    base = sqlite3.connect(Path(sys.argv[1]))
    verifies_tsv, titres_tsv = Path(sys.argv[2]), \
        Path(sys.argv[3]) if len(sys.argv) == 4 else None
    schema = Path(__file__).resolve().parent.parent / "schema" / "004-union.sql"

    verifies: dict[str, str] = {}
    for ligne in csv.DictReader(verifies_tsv.open(encoding="utf-8"), delimiter="\t"):
        if ligne["statut"] == "verifie":
            verifies[ligne["celex"]] = ligne["verifie_le"]
    if not verifies:
        sys.exit(f"aucun CELEX vérifié dans {verifies_tsv} : "
                 f"lancer tools/ue/verifier_celex.py")

    base.executescript(schema.read_text(encoding="utf-8"))
    # Le schéma détruit `cite_acte_ue` et `transpose`, mais pas les preuves
    # qu'elles référençaient : sans cette purge, chaque exécution en laisse une
    # couche, et la base finit par contenir plus de preuves orphelines que
    # d'arêtes. Le défaut avait déjà été commis sur `resulte_de` puis sur
    # `document` ; il est ici supprimé après la destruction des tables, sinon la
    # clef étrangère le refuse — dans l'autre sens, elle a raison.
    base.execute("DELETE FROM preuve WHERE methode IN "
                 "('citation_acte_ue', 'transposition_declaree')")

    # 1. Relevé des citations dans le texte des alinéas.
    formes: dict[str, Counter] = defaultdict(Counter)
    trouvees, compte = [], Counter()
    for segment_id, texte, decalage in base.execute(
            "SELECT id, texte, offset_debut FROM segment"):
        precedente = 0
        for identifiant, denomination, debut, fin in citations(texte):
            article = article_de_l_acte(texte, precedente, debut)
            precedente = fin
            if identifiant not in verifies:
                compte["non_verifie"] += 1
                continue
            extrait = fenetre(texte, debut, fin)
            if extrait is None:
                compte["sans_preuve"] += 1
                continue
            compte["avec_article"] += article is not None
            formes[identifiant][denomination] += 1
            trouvees.append((segment_id, identifiant, article, decalage + debut,
                             decalage + fin, extrait))

    # 2. Transpositions déclarées dans l'intitulé complet du texte français.
    #    Relevées **avant** d'écrire `acte_ue` : quatre directives majeures — dont
    #    l'« Omnibus » 2019/2161 et la DSP2 — sont déclarées transposées sans être
    #    citées nulle part dans le code. Les chercher après aurait fait disparaître
    #    leur déclaration faute d'acte à référencer.
    declarations = []
    if titres_tsv and titres_tsv.exists():
        textes = {i for (i,) in base.execute("SELECT id_jorf FROM texte_normatif")}
        for ligne in csv.DictReader(titres_tsv.open(encoding="utf-8"),
                                    delimiter="\t"):
            titre = ligne["titre"]
            mention = TRANSPOSITION.search(titre)
            if not mention or ligne["id_jorf"] not in textes:
                continue
            rupture = RUPTURE.search(titre, mention.end())
            limite = rupture.start() if rupture else len(titre)
            for identifiant, denomination, debut, fin in citations(titre):
                if not (mention.start() <= debut and fin <= limite):
                    continue
                if identifiant not in verifies:
                    compte["non_verifie"] += 1
                    continue
                extrait = fenetre(titre, debut, fin)
                if extrait is None:
                    compte["sans_preuve"] += 1
                    continue
                formes[identifiant][denomination] += 1
                declarations.append((ligne["id_jorf"], identifiant, debut, extrait))

    preuves, aretes = [], []
    suivant = prochain_identifiant(base)
    vus = set()
    for segment_id, identifiant, article, debut, fin, extrait in trouvees:
        if (segment_id, identifiant, debut) in vus:
            continue
        vus.add((segment_id, identifiant, debut))
        preuves.append((suivant, "citation_acte_ue", extrait, debut))
        aretes.append((segment_id, identifiant, article, debut, fin, "derivee",
                       CONFIANCE, suivant))
        suivant += 1

    actes = [(identifiant, TYPE[identifiant[5]], int(identifiant[1:5]),
              int(identifiant[6:]), designation(formes[identifiant]),
              URL.format(identifiant), verifies[identifiant])
             for identifiant in sorted(formes)]
    base.executemany(
        "INSERT INTO acte_ue (celex, type_acte, annee, numero, denomination, "
        "url, verifie_le) VALUES (?, ?, ?, ?, ?, ?, ?)", actes)
    base.executemany(
        "INSERT INTO preuve (id, methode, fenetre, source_offset) "
        "VALUES (?, ?, ?, ?)", preuves)
    base.executemany(
        "INSERT INTO cite_acte_ue (segment_id, celex, article_cite, offset_debut, "
        "offset_fin, methode, confiance, preuve_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", aretes)

    for texte_id, identifiant, debut, extrait in declarations:
        base.execute("INSERT INTO preuve (id, methode, fenetre, source_offset) "
                     "VALUES (?, ?, ?, ?)",
                     (suivant, "transposition_declaree", extrait, debut))
        base.execute("INSERT OR IGNORE INTO transpose (texte_id, celex, methode, "
                     "confiance, preuve_id) VALUES (?, ?, ?, ?, ?)",
                     (texte_id, identifiant, "declaree", 1.0, suivant))
        suivant += 1
    base.commit()

    violations = base.execute("PRAGMA foreign_key_check").fetchall()
    articles, en_vigueur = base.execute(
        "SELECT (SELECT count(DISTINCT article) FROM union_par_article), "
        "(SELECT count(DISTINCT article_id) FROM version_en_vigueur)").fetchone()

    print(f"actes de l'Union vérifiés  : {len(actes)}")
    for type_acte in ("directive", "reglement", "decision"):
        n = sum(1 for a in actes if a[1] == type_acte)
        print(f"  {type_acte:12s}           : {n}")
    print(f"citations retenues         : {len(aretes)}")
    print(f"  nommant un article précis : {compte['avec_article']}")
    print(f"  CELEX non vérifié        : {compte['non_verifie']}")
    print(f"  écartées faute de preuve : {compte['sans_preuve']}")
    print(f"transpositions déclarées   : {len(declarations)} "
          f"sur {len({d[0] for d in declarations})} texte(s)")
    print(f"\nsur les versions en vigueur :")
    print(f"  articles citant un acte de l'Union : {articles} "
          f"({100 * articles / en_vigueur:.1f} %)")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère")
    base.close()


if __name__ == "__main__":
    main()
