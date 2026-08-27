#!/usr/bin/env python3
"""Tire un échantillon reproductible d'arêtes `porte_sur`, et en fait le bilan.

`porte_sur` est devenue la colonne vertébrale du produit : 43 786 arêtes, 964
articles en vigueur reliés à un article de texte, et deux arêtes construites
par-dessus — `depose_sur` (`docs/31`) et le rattachement de l'étude d'impact
(`docs/33`). Sa précision n'a pourtant été mesurée qu'une fois, sur vingt
rattachements tirés de la population entière (`docs/16` § 4).

Deux contrôles à la main l'ont depuis prise en défaut, chacun sur la même cause
et chacun dans un autre module : `docs/31` § 4 — deux fausses sur quinze — et
`docs/33` § 3 — huit sur quinze. **Le code hôte est implicite.** Un texte le
nomme une fois, en tête du bloc modificateur, puis dit « du même code » ; un
texte qui modifie plusieurs codes à la suite fait dériver cette dernière mention,
et une référence qui existe dans deux codes tombe dans le mauvais.

Chaque fois, la réponse a été une garde sur l'arête **nouvelle**. Cet outil sert
à mesurer, puis à réparer, l'arête ancienne — ce qui suppose de distinguer les
populations, parce qu'elles ne valent pas la même chose :

- `hote` : le code est-il nommé **dans la fenêtre de preuve**, ou seulement
  supposé par report d'une mention lointaine ? C'est la distinction que
  `docs/31` § 4 a isolée.
- `legi` : la loi issue de ce dossier a-t-elle produit une version de cet
  article ? Source indépendante du texte en discussion, celle de `docs/33` § 4.
- `voie` : l'instruction déclare la cible (`texte_en_discussion`), ou c'est
  l'en-tête d'un alinéa cité qui la désigne (`article_cree`).

Ces colonnes **n'établissent rien**, elles orientent l'examen. La colonne
`verdict` reste vide et se remplit à la main — `juste`, `faux` ou `douteux`.

**Un tirage reproductible, pas aléatoire**, comme pour `resulte_de` : la clef de
tri est le SHA-256 du triplet (texte, article du texte, numéro cité). L'ordre est
sans rapport avec la structure du corpus et le même à chaque exécution.
`--sauf` écarte les arêtes d'une fiche déjà examinée : un correctif tiré d'un
échantillon ne se mesure pas sur ce même échantillon.

Usage :
    precision_porte_sur.py <base.sqlite> <corpus/textes/> <fiche.tsv> [effectif]
        [--voie declaree|citation] [--hote nomme|suppose] [--legi oui|non]
        [--sauf <fiche.tsv>]
    precision_porte_sur.py --bilan <fiche.tsv>
"""

from __future__ import annotations

import csv
import hashlib
import math
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ingestion"))
from textes_deposes import bornes, texte_brut   # noqa: E402

EFFECTIF = 20
CONTEXTE = 500
COLONNES = ["verdict", "cle", "voie", "hote", "legi", "distance_hote", "texte",
            "article_du_texte", "numero_cite", "code_cite", "article_du_fonds",
            "mention_hote", "contexte", "url"]


def hote_nomme(texte: str, nom: str | None, gauche: int, droite: int) -> bool:
    """Le code est-il **nommé** dans la fenêtre de preuve, ou seulement supposé ?

    Le report du « même code » est une convention légistique juste, et elle est
    conservée : elle porte la moitié des rattachements. Mais elle dérive — un
    texte qui modifie plusieurs codes à la suite laisse la dernière mention
    valoir pour un bloc qu'elle ne gouverne pas (`docs/31` § 4, `docs/33` § 3).
    Le nom lu dans la fenêtre distingue donc ce que le passage **dit** de ce
    qu'on lui a **reporté** ; le second demande une corroboration, le premier non.

    La comparaison se fait sur le texte réespacé, comme la preuve stockée : un
    nom de code coupé par un retour à la ligne est le même nom.
    """
    if not nom:
        return False
    lue = re.sub(r"\s+", " ", texte[gauche:droite]).lower()
    return re.sub(r"\s+", " ", nom).strip().lower() in lue


def wilson(succes: int, total: int, z: float = 1.96) -> float:
    """Borne inférieure de Wilson à 95 %, la convention de confiance du § 5.4."""
    if total == 0:
        return 0.0
    p = succes / total
    denominateur = 1 + z * z / total
    centre = p + z * z / (2 * total)
    ecart = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return (centre - ecart) / denominateur


def coupe(texte: str, limite: int = 400) -> str:
    texte = " ".join((texte or "").split())
    return texte if len(texte) <= limite else texte[:limite] + " […]"


def articles_produits(base: sqlite3.Connection) -> set[tuple[str, int]]:
    """(dossier, article) que la loi issue du dossier a effectivement produits."""
    return {(d, a) for d, a in base.execute(
        "SELECT i.dossier_id, v.article_id FROM issu_de i "
        "JOIN produite_par p ON p.texte_id = i.texte_id "
        "JOIN version_article v ON v.id_legi = p.version_id")}


def echantillon(base: sqlite3.Connection, corpus: Path, filtres: dict,
                sauf: set[tuple[str, str, str]], effectif: int) -> list[dict]:
    produits = articles_produits(base)
    aretes = base.execute("""
        SELECT p.texte_id, p.article_du_texte, p.numero_cite, p.code_cite,
               p.article_id, e.methode, e.source_offset, t.dossier_id, t.url
        FROM porte_sur p
        JOIN preuve e          ON e.id = p.preuve_id
        JOIN texte_discute t   ON t.id = p.texte_id
        WHERE p.portee = 'interne'
        ORDER BY p.id""").fetchall()

    # Le premier état connu de l'article dans le fonds. C'est lui qui tranche :
    # si le texte dit réécrire L. 332-2 « Dans un délai fixé par voie
    # réglementaire, le saisi… » et que L. 332-2 de ce code-ci traite du
    # surendettement, l'hôte a dérivé — et cela se lit, au lieu de se supposer.
    fonds = {}
    for article_id, numero, date, texte in base.execute(
            "SELECT v.article_id, a.numero, min(v.date_debut), v.texte "
            "FROM version_article v JOIN article a ON a.id = v.article_id "
            "GROUP BY v.article_id"):
        fonds[article_id] = (numero, date, texte)

    lignes, contenus = [], {}
    for (texte_id, article_du_texte, numero_cite, code_cite, article_id,
         methode, offset, dossier, url) in aretes:
        voie = "citation" if methode == "article_cree" else "declaree"
        if filtres.get("voie") and filtres["voie"] != voie:
            continue
        legi = "oui" if (dossier, article_id) in produits else "non"
        if filtres.get("legi") and filtres["legi"] != legi:
            continue
        if texte_id not in contenus:
            fichier = corpus / f"{dossier}__{texte_id.split('/', 1)[1]}"
            contenus[texte_id] = texte_brut(fichier) if fichier.exists() else ""
        contenu = contenus[texte_id]
        # La mention d'hôte retenue est la dernière avant la référence, ou celle
        # qui la suit dans la phrase : on la retrouve par le nom que l'ingestion
        # a stocké, ce qui évite de recalculer les repères et de diverger d'eux.
        nom = (code_cite or "").rstrip(" »«\"").strip()
        place = contenu.lower().rfind(nom.lower(), 0, offset + 200) if nom else -1
        gauche, droite = bornes(contenu, offset, offset + len(numero_cite) + 2)
        hote = "nomme" if hote_nomme(contenu, nom, gauche, droite) else "suppose"
        if filtres.get("hote") and filtres["hote"] != hote:
            continue
        lignes.append({
            "verdict": "", "cle": hashlib.sha256(
                f"{texte_id}|{article_du_texte}|{numero_cite}".encode()
            ).hexdigest()[:16],
            "voie": voie, "hote": hote, "legi": legi,
            "distance_hote": str(offset - place) if place >= 0 else "",
            "texte": texte_id, "article_du_texte": article_du_texte,
            "numero_cite": numero_cite, "code_cite": code_cite or "",
            "article_du_fonds": coupe(
                f"{fonds[article_id][0]} ({fonds[article_id][1]}) "
                f"{fonds[article_id][2]}", 320) if article_id in fonds else "",
            "mention_hote": coupe(contenu[max(0, place - 120):place + 160], 280)
                            if place >= 0 else "",
            "contexte": coupe(contenu[max(0, offset - CONTEXTE):
                                      offset + CONTEXTE], 2 * CONTEXTE),
            "url": url or "",
        })
    lignes = [l for l in lignes
              if (l["texte"], l["article_du_texte"], l["numero_cite"]) not in sauf]
    lignes.sort(key=lambda l: l["cle"])
    return lignes[:effectif]


def bilan(fiche: Path) -> None:
    lignes = list(csv.DictReader(fiche.open(encoding="utf-8"), delimiter="\t"))
    examinees = [l for l in lignes if l["verdict"]]
    justes = [l for l in examinees if l["verdict"] == "juste"]
    doutes = [l for l in examinees if l["verdict"] == "douteux"]
    print(f"arêtes tirées      : {len(lignes)}")
    print(f"arêtes examinées   : {len(examinees)}")
    print(f"  justes           : {len(justes)}")
    print(f"  douteuses        : {len(doutes)}")
    print(f"  fausses          : {len(examinees) - len(justes) - len(doutes)}")
    if not examinees:
        return
    # Le douteux compte comme un échec : le § 5.3 met la précision au-dessus du
    # rappel, une arête dont on n'est pas sûr n'est pas une arête juste.
    print(f"précision ponctuelle : {len(justes) / len(examinees):.3f}")
    print(f"borne de Wilson 95 % : {wilson(len(justes), len(examinees)):.4f}")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--bilan":
        return bilan(Path(sys.argv[2]))
    arguments, filtres, sauf = sys.argv[1:], {}, set()
    for option in ("voie", "hote", "legi"):
        if f"--{option}" in arguments:
            place = arguments.index(f"--{option}")
            filtres[option] = arguments[place + 1]
            arguments = arguments[:place] + arguments[place + 2:]
    if "--sauf" in arguments:
        place = arguments.index("--sauf")
        deja = Path(arguments[place + 1])
        sauf = {(l["texte"], l["article_du_texte"], l["numero_cite"]) for l in
                csv.DictReader(deja.open(encoding="utf-8"), delimiter="\t")}
        arguments = arguments[:place] + arguments[place + 2:]
    if len(arguments) not in (3, 4):
        sys.exit(__doc__)
    chemin_base, corpus, fiche = (Path(a) for a in arguments[:3])
    effectif = int(arguments[3]) if len(arguments) == 4 else EFFECTIF
    base = sqlite3.connect(chemin_base)
    lignes = echantillon(base, corpus, filtres, sauf, effectif)
    with fiche.open("w", encoding="utf-8", newline="") as sortie:
        graveur = csv.DictWriter(sortie, COLONNES, delimiter="\t",
                                 lineterminator="\n")
        graveur.writeheader()
        graveur.writerows(lignes)
    print(f"{len(lignes)} arêtes tirées → {fiche}")
    base.close()


if __name__ == "__main__":
    main()
