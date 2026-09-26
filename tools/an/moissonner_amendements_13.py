#!/usr/bin/env python3
"""Les amendements de séance de la XIIIe législature, lus page par page.

**La XIIIe n'a jamais été publiée en open data** (`docs/10` § 5) : le dépôt de
l'Assemblée commence à la XIVe. On la croyait reconstructible seulement depuis
la Wayback Machine, qui n'en garde qu'environ 10 500 pages sur 379 textes, et
une fraction de nos dossiers. Mais **le site de l'Assemblée sert encore chaque
page en direct**, à une adresse régulière :

    /13/amendements/2449/244900001.asp     amendement n° 1 sur le texte n° 2449
    /13/amendements/0842/0842S0001.asp     n° 1 en seconde délibération

Un numéro absent répond 404. Chaque page porte en métadonnées la date de dépôt,
l'article et l'alinéa visés, le sort en séance ; le corps, l'en-tête de
subdivision, les signataires, le dispositif et l'exposé sommaire.

**On énumère.** Pour chaque texte du plan, les numéros sont essayés dans l'ordre
jusqu'à `TROU` absences consécutives après le dernier trouvé ; un texte dont
aucun des `TETE` premiers numéros n'existe n'a pas d'amendement de séance. Les
pages sont gardées dans `travail/an/13/`, et un texte énuméré jusqu'au bout y
laisse un témoin : une reconstruction relit le cache sans réseau.

**Le signataire est un nom, non une référence.** La page écrit « M. Carayon »,
« M. Loïc Bouvard », « le Gouvernement ». Le premier signataire est résolu
parmi les députés de la XIIIe du jeu Acteurs historique — nom seul s'il est
unique, prénom et nom sinon —, et son groupe est celui du mandat en cours à la
date de dépôt. Un nom qui ne se résout pas reste sans référence : le chargeur
le compte comme non résolu, il ne le devine pas.

Usage :
    moissonner_amendements_13.py <plan-textes-an-13.tsv> <plan-rapports.tsv>
                                 <acteurs_historique.json.zip> <cache/> <sortie.csv>
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

SITE = "https://www.assemblee-nationale.fr/13/amendements"
AGENT = "ratio-legis (recherche ; lecture lente, une page à la fois)"
PAUSE = 0.3           # secondes entre deux requêtes
TETE = 10             # numéros essayés avant de conclure qu'un texte n'a rien
TROU = 100            # absences consécutives qui closent l'énumération
SERIES = {"": "seance", "S": "seconde-deliberation"}

COLONNES = ["dossier", "texte", "stade", "numero", "ref_texte", "organe_examen", "etat",
            "type_auteur", "acteur_ref", "organe_ref", "groupe_ref", "division",
            "dispositif", "expose", "sort", "url"]

META = re.compile(r'<meta\s+name="([A-Z_]+)"\s+content="([^"]*)"', re.I)
DIVISION = re.compile(r"\n((?:APR[ÈE]S|AVANT) L['’]ART\.[^\n]*|ART\.[^\n]*|TITRE[^\n]*"
                      r"|INTITUL[ÉE][^\n]*)\n\s*N°", re.I)
NUMERO = re.compile(r"(?:SOUS-)?AMENDEMENT\s+N°\s*\n?\s*([^\n]+)")
SIGNATAIRES = re.compile(r"présenté par\s*\n(.*?)\n\s*-{5,}", re.S)
DISPOSITIF = re.compile(r"-{5,}\s*\n(.*?)(?:\n\s*EXPOSÉ SOMMAIRE|\Z)", re.S)
EXPOSE = re.compile(r"EXPOSÉ SOMMAIRE\s*\n(.*?)(?:checkMeta\(\)|\Z)", re.S)
ENTETE_ARTICLE = re.compile(r"^ARTICLE\s*\n?\s*[^\n]*\n", re.I)
ADDITIONNEL = re.compile(r"^ARTICLE ADDITIONNEL\s+((?:APR[ÈE]S|AVANT)\s+L['’]ARTICLE)\s+"
                         r"([^,\n]+?)\s*,", re.I)
RAPPORT = re.compile(r"assemblee-nationale\.fr/13/rapports/r0*(\d+)")


# --- lecture d'une page --------------------------------------------------------

def texte_de(page: str) -> str:
    corps = page[page.find("<body"):]
    corps = re.sub(r"<script.*?</script>|<style.*?</style>", " ", corps, flags=re.S | re.I)
    corps = re.sub(r"<(?:br|/p|/div|/tr|/h\d|/td)[^>]*>", "\n", corps, flags=re.I)
    corps = html.unescape(re.sub(r"<[^>]+>", " ", corps)).replace("\xa0", " ")
    lignes = (re.sub(r"[ \t]+", " ", l).strip() for l in corps.split("\n"))
    return "\n".join(l for l in lignes if l)


def lire(page: str) -> dict:
    metas = {k.upper(): v for k, v in META.findall(page)}
    texte = "\n" + texte_de(page)
    division = DIVISION.search(texte)
    numero = NUMERO.search(texte)
    signataires = SIGNATAIRES.search(texte)
    dispositif = DISPOSITIF.search(texte, signataires.end() - 12 if signataires else 0)
    expose = EXPOSE.search(texte)
    corps = dispositif.group(1).strip() if dispositif else ""
    additionnel = ADDITIONNEL.match(" ".join(corps.split("\n")[:4]))
    if additionnel:
        corps = (f"{additionnel.group(1).capitalize()} {additionnel.group(2).lower()}, "
                 + " ".join(corps.split("\n")[:4])[additionnel.end():].strip()
                 + "\n" + "\n".join(corps.split("\n")[4:]))
    else:
        corps = ENTETE_ARTICLE.sub("", corps, count=1)
    return {
        "date": metas.get("DATE_BADAGE", ""),
        "sort": metas.get("SORT_EN_SEANCE", "").strip(),
        "division": (division.group(1) if division else metas.get("DESIGNATION_ARTICLE", "")).strip(),
        "numero": re.sub(r"\s+", " ", numero.group(1)).strip().replace("Rect.", "rect.") if numero else "",
        "signataires": " ".join(signataires.group(1).split()) if signataires else "",
        "dispositif": corps.strip(),
        "expose": expose.group(1).strip() if expose else "",
    }


# --- signataires ---------------------------------------------------------------

def cle(nom: str) -> str:
    # « Philippe-Armand » d'un côté, « Philippe Armand » de l'autre.
    nom = unicodedata.normalize("NFKD", nom.replace("’", "'").replace("-", " "))
    return " ".join("".join(c for c in nom if not unicodedata.combining(c)).lower().split())


def deputes_de_la_xiiie(archive: Path) -> tuple[dict, dict]:
    """Nom → références `PA…` possibles, et `PA…` → mandats de groupe datés."""
    par_nom: dict[str, set[str]] = {}
    groupes: dict[str, list[tuple[str, str, str]]] = {}
    z = zipfile.ZipFile(archive)
    for nom in z.namelist():
        if "/acteur/" not in nom:
            continue
        acteur = json.loads(z.read(nom)).get("acteur", {})
        mandats = acteur.get("mandats", {}).get("mandat", [])
        mandats = [mandats] if isinstance(mandats, dict) else mandats
        treize = [m for m in mandats if m.get("legislature") == "13"]
        if not any(m.get("typeOrgane") == "ASSEMBLEE" for m in treize):
            continue
        uid = acteur.get("uid")
        uid = uid.get("#text") if isinstance(uid, dict) else uid
        ident = acteur.get("etatCivil", {}).get("ident", {})
        for forme in (ident.get("nom", ""), f"{ident.get('prenom', '')} {ident.get('nom', '')}"):
            par_nom.setdefault(cle(forme), set()).add(uid)
        groupes[uid] = [(m.get("dateDebut") or "", m.get("dateFin") or "9999",
                         m.get("organes", {}).get("organeRef", ""))
                        for m in treize if m.get("typeOrgane") == "GP"]
    return par_nom, groupes


def premier_signataire(signataires: str) -> str:
    premier = re.split(r",| et ", signataires, maxsplit=1)[0]
    return re.sub(r"^(?:M\.|Mme|Mlle)\s+", "", premier.strip())


def resoudre(signataires: str, jour: str, par_nom: dict, groupes: dict) -> tuple[str, str, str]:
    """(type d'auteur, référence `PA…`, référence de groupe `PO…`)."""
    if re.match(r"le Gouvernement", signataires, re.I):
        return "Gouvernement", "", ""
    candidats = par_nom.get(cle(premier_signataire(signataires)), set())
    if len(candidats) != 1:
        return "Député", "", ""
    uid = next(iter(candidats))
    try:
        j, m, a = jour.split("/")
        quand = date(int(a), int(m), int(j)).isoformat()
    except ValueError:
        quand = ""
    groupe = next((po for debut, fin, po in groupes.get(uid, []) if debut <= quand <= fin), "")
    return "Député", uid, groupe


# --- énumération ---------------------------------------------------------------

def page(url: str) -> str | None:
    for essai in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": AGENT}), timeout=60) as r:
                corps = r.read().decode("cp1252", errors="replace")
            time.sleep(PAUSE)
            return corps
        except urllib.error.HTTPError as e:
            time.sleep(PAUSE)
            if e.code == 404:
                return None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(5 * (essai + 1))
    raise RuntimeError(f"{url} : pas de réponse après quatre essais")


def enumerer(texte: int, serie: str, cache: Path) -> list[tuple[int, Path]]:
    dossier = cache / f"{texte:04d}"
    temoin = dossier / f"termine{serie or '-seance'}"
    motif = f"{texte:04d}{serie}{{:0{5 - len(serie)}d}}.asp"
    if temoin.exists():
        return [(int(n), dossier / motif.format(int(n)))
                for n in temoin.read_text().split()]
    trouves, dernier, n = [], 0, 1
    while n <= TETE or n - dernier <= TROU:
        if n > TETE and not trouves:
            break
        fichier = dossier / motif.format(n)
        if not fichier.exists():
            contenu = page(f"{SITE}/{texte:04d}/{motif.format(n)}")
            if contenu is not None:
                dossier.mkdir(parents=True, exist_ok=True)
                fichier.write_text(contenu, encoding="utf-8")
        if fichier.exists():
            trouves.append((n, fichier))
            dernier = n
        n += 1
    dossier.mkdir(parents=True, exist_ok=True)
    temoin.write_text(" ".join(str(n) for n, _ in trouves))
    return trouves


def main() -> None:
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    plan, rapports, acteurs, cache, sortie = (Path(a) for a in sys.argv[1:])
    couples = [tuple(l.split("\t")) for l in plan.read_text(encoding="utf-8").splitlines() if l]
    # Le texte de commission porte le numéro du rapport qui l'annexe (`BTC`) ;
    # un autre numéro est un texte déposé (`B`). L'appariement ne lit que le
    # numéro, le stade n'est qu'une étiquette.
    de_commission = {int(n) for n in RAPPORT.findall(rapports.read_text(encoding="utf-8"))}
    par_nom, groupes = deputes_de_la_xiiie(acteurs)
    compte = {"textes": 0, "textes_amendes": 0, "pages": 0, "illisibles": 0,
              "gouvernement": 0, "resolus": 0, "non_resolus": 0}
    with sortie.open("w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.DictWriter(flux, fieldnames=COLONNES)
        ecrivain.writeheader()
        for dossier, numero_texte in couples:
            texte = int(numero_texte)
            compte["textes"] += 1
            stade = "BTC" if texte in de_commission else "B"
            amende = False
            for serie, organe in SERIES.items():
                for n, fichier in enumerer(texte, serie, cache):
                    amende = True
                    compte["pages"] += 1
                    fiche = lire(fichier.read_text(encoding="utf-8"))
                    if not fiche["numero"] or not fiche["dispositif"]:
                        compte["illisibles"] += 1
                        continue
                    type_auteur, acteur, groupe = resoudre(
                        fiche["signataires"], fiche["date"], par_nom, groupes)
                    compte["gouvernement" if type_auteur == "Gouvernement"
                           else "resolus" if acteur else "non_resolus"] += 1
                    irrecevable = fiche["sort"].lower().startswith("irrecevable")
                    ecrivain.writerow({
                        "dossier": dossier, "texte": texte, "stade": stade,
                        "numero": fiche["numero"],
                        "ref_texte": f"L13{stade}{texte}", "organe_examen": organe,
                        "etat": "Irrecevable" if irrecevable else ("Discuté" if fiche["sort"] else ""),
                        "type_auteur": type_auteur, "acteur_ref": acteur, "organe_ref": "",
                        "groupe_ref": groupe, "division": fiche["division"],
                        "dispositif": fiche["dispositif"], "expose": fiche["expose"],
                        "sort": "" if irrecevable else fiche["sort"],
                        "url": f"{SITE}/{fichier.parent.name}/{fichier.name}"})
            compte["textes_amendes"] += amende
            print(f"   {dossier} n° {texte} : {'amendé' if amende else '—'}", flush=True)
    print(f"textes du plan              : {compte['textes']}, dont amendés : {compte['textes_amendes']}")
    print(f"pages d'amendement          : {compte['pages']}, illisibles : {compte['illisibles']}")
    print(f"signataire : gouvernement {compte['gouvernement']}, député résolu "
          f"{compte['resolus']}, non résolu {compte['non_resolus']}")


if __name__ == "__main__":
    main()
