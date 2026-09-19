#!/usr/bin/env python3
"""Phase 1, première tranche : LEGI → articles, versions, segments, arêtes déclarées.

Peuple les tables du schéma `schema/001-graphe-provenance.sql` et construit
l'arête `repris_de`, qui porte la continuité d'un alinéa d'une version à l'autre.

Cette tranche est volontairement la première parce que `repris_de` est la
dépendance dure de `resulte_de` : sur un corpus recodifié, un amendement ne peut
être relié à l'article en vigueur qu'en passant par la version historique qu'il a
réellement produite (`docs/06-modele-de-donnees.md` § 4).

Trois pièges de la donnée LEGI sont traités ici, tous mesurés en phase 0 et
documentés dans `docs/01-rapport-verification-sources.md` § 2.3 bis :

  - l'attribut `sens` des liens n'est pas fiable, les vocabulaires ancien et
    récent lui donnant des valeurs opposées pour la même relation ;
  - les liens de concordance se résolvent par identifiant `LEGIARTI`, jamais par
    numéro d'article : le même numéro peut désigner deux dispositions sans
    rapport à deux époques ;
  - l'alinéa n'est pas porté par la seule balise `<p>` — 26,5 % des articles n'en
    ont aucune — mais aussi par `<br/>`.

Usage :
    legi_vers_graphe.py <racine_extraction_legi> <base.sqlite> [<schema.sql>]
"""

from __future__ import annotations

import hashlib
import html
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Vocabulaires de liens. Les deux séries coexistent dans le fonds avec des
# volumes très différents ; n'en connaître qu'une fait perdre l'essentiel.
CREATION = {"CREE", "CREATION"}
MODIFICATION = {"MODIFIE", "MODIFICATION", "RECTIFICATION"}
ABROGATION = {"ABROGE", "ABROGATION"}
RENUMEROTATION = {"CONCORDANCE", "CONCORDE", "TRANSFERE", "TRANSFERT", "DEPLACE"}
TEXTES_NORMATIFS = {"LOI", "ORDONNANCE", "DECRET", "ARRETE"}

NATURE_SQL = {"LOI": "loi", "ORDONNANCE": "ordonnance",
              "DECRET": "decret", "ARRETE": "arrete"}

# Longueur minimale d'une preuve textuelle, imposée par le schéma. En deçà, un
# fragment n'a aucun pouvoir discriminant.
FENETRE = 60

MOIS = {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "août": 8, "septembre": 9, "octobre": 10,
        "novembre": 11, "décembre": 12}


@dataclass
class Version:
    id_legi: str
    numero: str
    code: str
    etat: str
    date_debut: str
    date_fin: str
    segments: list[str] = field(default_factory=list)
    producteurs: list[tuple] = field(default_factory=list)   # (cid, nature, titre, type)
    predecesseurs: list[str] = field(default_factory=list)   # identifiants LEGIARTI

    @property
    def texte(self) -> str:
        return "\n".join(self.segments)


def balise(xml: str, nom: str) -> str:
    trouve = re.search(rf"<{nom}>(.*?)</{nom}>", xml, re.S)
    return trouve.group(1).strip() if trouve else ""


def decouper_en_alineas(bloc: str) -> list[str]:
    """Alinéas d'un BLOC_TEXTUEL.

    L'alinéa est porté par `</p>` **et** par `<br/>` : 26,5 % des articles du
    Code de la consommation n'ont aucune balise `<p>`, et le fonds compte deux
    fois plus de `<br/>`. Ne couper que sur `<p>` laisse un article entier en un
    seul segment et ruine le grain de provenance.
    """
    texte = re.sub(r"</p\s*>|<br\s*/?>", "\n", bloc, flags=re.I)
    texte = html.unescape(re.sub(r"<[^>]+>", " ", texte))
    alineas = (re.sub(r"\s+", " ", ligne).strip() for ligne in texte.split("\n"))
    return [a for a in alineas if len(a) >= 15]


def normalise(texte: str) -> str:
    """Forme comparable, pour l'appariement seulement — jamais pour le stockage."""
    forme = unicodedata.normalize("NFKC", texte).lower()
    forme = forme.replace("’", "'").replace("‘", "'")
    forme = re.sub(r"[«»\"“”]", " ", forme)
    return re.sub(r"\s+", " ", forme).strip()


def fenetres(texte: str, pas: int = 1) -> set[str]:
    if len(texte) < FENETRE:
        return set()
    return {texte[d:d + FENETRE] for d in range(0, len(texte) - FENETRE + 1, pas)}


def empreinte(texte: str) -> str:
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def date_du_libelle(libelle: str) -> str:
    """Date du texte producteur, lue dans le libellé du lien."""
    trouve = re.search(r"(\d{1,2})(?:er)?\s+(\w+)\s+(\d{4})", libelle)
    if trouve and trouve.group(2).lower() in MOIS:
        return (f"{trouve.group(3)}-{MOIS[trouve.group(2).lower()]:02d}"
                f"-{int(trouve.group(1)):02d}")
    trouve = re.search(r"(\d{4})-(\d{2})-(\d{2})", libelle)
    return trouve.group(0) if trouve else ""


def lire_version(chemin: Path) -> Version | None:
    xml = chemin.read_text(encoding="utf-8", errors="replace")
    identifiant, numero = balise(xml, "ID"), balise(xml, "NUM")
    if not identifiant or not numero:
        return None

    contexte = re.search(r"<CONTEXTE>(.*?)</CONTEXTE>", xml, re.S)
    code = ""
    if contexte:
        attrs = re.search(r'<TEXTE\s+[^>]*cid="([^"]*)"', contexte.group(1))
        code = attrs.group(1) if attrs else ""

    version = Version(
        id_legi=identifiant,
        numero=numero,
        code=code,
        etat=balise(xml, "ETAT"),
        date_debut=balise(xml, "DATE_DEBUT"),
        date_fin=balise(xml, "DATE_FIN"),
        segments=decouper_en_alineas(balise(xml, "BLOC_TEXTUEL")),
    )

    liens = re.search(r"<LIENS>(.*?)</LIENS>", xml, re.S)
    for lien in re.finditer(r"<LIEN ([^>]*)>(.*?)</LIEN>",
                            liens.group(1) if liens else "", re.S):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', lien.group(1)))
        libelle = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lien.group(2))).strip()
        type_lien = attrs.get("typelien", "")
        nature = attrs.get("naturetexte", "")
        # `sens` est délibérément ignoré : le vocabulaire ancien l'inverse.
        if type_lien in CREATION | MODIFICATION | ABROGATION and nature in TEXTES_NORMATIFS:
            version.producteurs.append((attrs.get("cidtexte", ""), nature,
                                        libelle.split(" - art")[0].strip(), type_lien))
        elif type_lien in RENUMEROTATION and nature == "CODE" and attrs.get("id"):
            # Résolution par identifiant : le numéro d'article ne suffit pas, le
            # même numéro pouvant désigner deux dispositions à deux époques.
            version.predecesseurs.append(attrs["id"])
    return version


def charger_versions(racine: Path) -> dict[str, Version]:
    versions: dict[str, Version] = {}
    for fichier in racine.rglob("LEGIARTI*.xml"):
        version = lire_version(fichier)
        if version and version.segments:
            versions[version.id_legi] = version
    return versions


def anterieurs(version: Version, versions: dict[str, Version]) -> list[Version]:
    """Prédécesseurs d'une version, restreints à ceux qui la précèdent dans le temps.

    LEGI déclare le lien de renumérotation sur les deux versions concernées, et
    l'attribut `sens` qui devrait les départager est inexploitable (voir
    `docs/01-rapport-verification-sources.md` § 2.3 bis). Pris tels quels, ces
    liens forment une relation symétrique et non une ascendance : 3 848 des 3 849
    arêtes `renumerote_de` avaient leur réciproque, et remonter la chaîne d'un
    article bouclait indéfiniment entre L224-65 et L121-105.

    Le sens est donc rétabli par la chronologie, qui est un fait observable dans le
    fonds et non une déclaration. À date de début égale, la direction n'est pas
    décidable : l'arête est abandonnée plutôt que devinée (règle § 5.1).
    """
    retenus = []
    for identifiant in version.predecesseurs:
        precedent = versions.get(identifiant)
        if precedent is not None and precedent.date_debut < version.date_debut:
            retenus.append(precedent)
    return retenus


# Deux textes qui partagent moins de la moitié de leur vocabulaire ne sont pas
# la même disposition. Mesuré sur les 289 numéros en vigueur qui ont eu une
# version abrogée avant le 1er juillet 2016 : 285 sont sous 0,15, quatre au-dessus
# de 0,5, aucun entre les deux — le seuil ne tranche rien de discutable.
SEUIL_MEME_DISPOSITION = 0.5
MOT = re.compile(r"\w{4,}")


def similarite(a: str, b: str) -> float:
    """Part du vocabulaire commun (Jaccard sur les mots de quatre lettres et plus)."""
    ma, mb = set(MOT.findall(a.lower())), set(MOT.findall(b.lower()))
    return len(ma & mb) / len(ma | mb) if ma | mb else 1.0


def lignees(chronologie: list[Version]) -> list[int]:
    """Rang de lignée de chaque version d'un même numéro, dans l'ordre chronologique.

    Un numéro change de disposition quand sa version en cours est **abrogée** et
    que la version qui reprend le numéro n'a pas le même texte. La recodification
    de 2016 l'a fait 285 fois sur le code en vigueur ; le nœud clé par numéro
    faisait de l'ancienne disposition l'historique de la nouvelle.

    Les versions mort-nées ou annulées ne portent pas de lignée propre : elles
    suivent la version vivante qui entre en vigueur à la même date — c'est celle
    qu'elles devaient être —, à défaut la disposition en cours à leur date.
    """
    vivantes = [v for v in chronologie if v.etat not in ("MODIFIE_MORT_NE", "ANNULE")]
    rang_vivante: dict[str, int] = {}
    rang, derniere = 1, None
    for version in vivantes:
        if derniere is not None and derniere.etat in ABROGATION \
                and similarite(derniere.texte, version.texte) < SEUIL_MEME_DISPOSITION:
            rang += 1
        rang_vivante[version.id_legi] = rang
        derniere = version

    # Une version mort-née rejoint la vivante qui entre en vigueur à sa date si
    # elle en est la rédaction — même texte à peu près — ; sinon la disposition
    # en cours, au même critère ; sinon elle fait lignée à part. L313-8 en 2016 :
    # la version mort-née de l'ordonnance de mars (la fiche standardisée,
    # renumérotée L313-10 en juillet) n'a rien à voir avec le L313-8 vivant
    # (l'information sur l'assurance emprunteur) ; les fondre faisait remonter
    # à L313-10, par la concordance, le rapport de 2022 sur L313-8.
    rangs, rang_suivant = [], rang + 1
    for version in chronologie:
        if version.id_legi in rang_vivante:
            rangs.append(rang_vivante[version.id_legi])
            continue
        meme_date = [v for v in vivantes if v.date_debut == version.date_debut]
        en_cours = [v for v in reversed(vivantes) if v.date_debut <= version.date_debut]
        repere = next((v for v in meme_date + en_cours
                       if similarite(v.texte, version.texte) >= SEUIL_MEME_DISPOSITION),
                      None)
        if repere is not None:
            rangs.append(rang_vivante[repere.id_legi])
        else:
            rangs.append(rang_suivant)
            rang_suivant += 1
    return rangs


def inserer_noeuds(base: sqlite3.Connection, versions: dict[str, Version]) -> dict:
    """Un nœud `article` par lignée ; `articles` rend l'identifiant de chaque version."""
    par_numero: dict[tuple[str, str], list[Version]] = defaultdict(list)
    for version in versions.values():
        par_numero[(version.code, version.numero)].append(version)

    articles: dict[str, int] = {}          # id_legi → article.id
    noeuds: list[tuple[int, str, str, int]] = []
    for (code, numero), groupe in sorted(par_numero.items()):
        chronologie = sorted(groupe, key=lambda v: (v.date_debut, v.id_legi))
        ids: dict[int, int] = {}
        for version, rang in zip(chronologie, lignees(chronologie)):
            if rang not in ids:
                ids[rang] = len(noeuds) + 1
                noeuds.append((ids[rang], code, numero, rang))
            articles[version.id_legi] = ids[rang]
    base.executemany("INSERT INTO article (id, code, numero, lignee) VALUES (?, ?, ?, ?)",
                     noeuds)
    scindes = sum(1 for n in noeuds if n[3] > 1)

    textes: dict[str, tuple] = {}
    for version in versions.values():
        for cid, nature, titre, _ in version.producteurs:
            if cid and cid not in textes:
                textes[cid] = (cid, NATURE_SQL.get(nature, "loi"),
                               date_du_libelle(titre) or "1900-01-01", titre)
    base.executemany("INSERT INTO texte_normatif VALUES (?, ?, ?, ?)", list(textes.values()))

    base.executemany(
        "INSERT INTO version_article VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(v.id_legi, articles[v.id_legi], v.date_debut, v.date_fin or None,
          v.etat, v.texte, empreinte(v.texte)) for v in versions.values()])

    lignes_segments = []
    for version in versions.values():
        position = 0
        for ordre, segment in enumerate(version.segments):
            lignes_segments.append((f"{version.id_legi}:{ordre}", version.id_legi, ordre,
                                    segment, position, position + len(segment),
                                    empreinte(segment)))
            position += len(segment) + 1  # le séparateur inséré dans version.texte
    base.executemany("INSERT INTO segment VALUES (?, ?, ?, ?, ?, ?, ?)", lignes_segments)
    base.execute("INSERT INTO segment_fts (rowid, texte) SELECT rowid, texte FROM segment")
    return {"articles": articles, "noeuds": len(noeuds), "scindes": scindes,
            "textes": textes, "segments": len(lignes_segments)}


def inserer_aretes_declarees(base: sqlite3.Connection, versions: dict[str, Version],
                             articles: dict[str, int]) -> dict:
    produite_par = {(v.id_legi, cid, type_lien)
                    for v in versions.values()
                    for cid, _, _, type_lien in v.producteurs if cid}
    base.executemany(
        "INSERT INTO produite_par (version_id, texte_id, type_lien) VALUES (?, ?, ?)",
        sorted(produite_par))

    renumerote = set()
    for version in versions.values():
        cible = articles[version.id_legi]
        for precedent in anterieurs(version, versions):
            source = articles[precedent.id_legi]
            if source != cible:
                renumerote.add((cible, source))
    base.executemany(
        "INSERT INTO renumerote_de (article_id, ancien_id) VALUES (?, ?)",
        sorted(renumerote))
    return {"produite_par": len(produite_par), "renumerote_de": len(renumerote)}


def construire_repris_de(base: sqlite3.Connection, versions: dict[str, Version]) -> dict:
    """Continuité d'un alinéa entre une version et son prédécesseur renuméroté.

    Pour chaque segment, on cherche le segment du prédécesseur qui partage le plus
    de texte, et on mesure la part reprise. C'est cette part qui distingue un
    alinéa repris tel quel d'un alinéa retouché — distinction sans laquelle la
    provenance au grain de l'article reste ininterprétable
    (`docs/06-modele-de-donnees.md` § 1).
    """
    aretes, preuves = [], []
    for version in versions.values():
        for precedent in anterieurs(version, versions):
            # Le prédécesseur est indexé à toutes les positions, et non par
            # échantillonnage : sinon les grilles d'offsets des deux côtés ne
            # coïncident pas et un alinéa repris à l'identique ressort à 10 % de
            # reprise au lieu de 100 %. C'est l'erreur qui avait fait tomber C1
            # de 29 % à 5 % en phase 0 sans qu'aucune donnée ne change.
            index: dict[str, set[int]] = defaultdict(set)
            for rang, segment in enumerate(precedent.segments):
                for fenetre in fenetres(normalise(segment), pas=1):
                    index[fenetre].add(rang)

            for ordre, segment in enumerate(version.segments):
                candidates = fenetres(normalise(segment), pas=1)
                if not candidates:
                    continue  # segment trop court : aucune preuve possible
                partages: dict[int, set[str]] = defaultdict(set)
                for fenetre in candidates:
                    for rang in index.get(fenetre, ()):
                        partages[rang].add(fenetre)
                if not partages:
                    continue
                rang, communes = max(partages.items(), key=lambda kv: len(kv[1]))
                preuves.append(("appariement_exact", sorted(communes)[0]))
                aretes.append((f"{version.id_legi}:{ordre}",
                               f"{precedent.id_legi}:{rang}",
                               round(len(communes) / len(candidates), 4),
                               len(preuves)))

    base.executemany("INSERT INTO preuve (id, methode, fenetre) VALUES (?, ?, ?)",
                     [(i + 1, m, f) for i, (m, f) in enumerate(preuves)])
    base.executemany(
        "INSERT OR IGNORE INTO repris_de "
        "(segment_id, segment_source_id, part_reprise, preuve_id) VALUES (?, ?, ?, ?)",
        aretes)
    return {
        "repris_de": len(aretes),
        "integrales": sum(1 for a in aretes if a[2] >= 0.9),
        "retouchees": sum(1 for a in aretes if 0.1 <= a[2] < 0.9),
    }


def main() -> None:
    if not 3 <= len(sys.argv) <= 4:
        sys.exit(__doc__)
    racine, chemin_base = Path(sys.argv[1]), Path(sys.argv[2])
    schema = Path(sys.argv[3]) if len(sys.argv) == 4 else \
        Path(__file__).resolve().parent.parent / "schema" / "001-graphe-provenance.sql"

    if chemin_base.exists():
        chemin_base.unlink()
    base = sqlite3.connect(chemin_base)
    base.executescript(schema.read_text(encoding="utf-8"))
    # Une seule définition de « en vigueur aujourd'hui », au lieu de dix-sept
    # tests éparpillés — voir l'en-tête de `schema/009-en-vigueur.sql`.
    base.executescript((schema.parent / "009-en-vigueur.sql").read_text(encoding="utf-8"))
    base.execute("PRAGMA foreign_keys = ON")

    versions = charger_versions(racine)
    noeuds = inserer_noeuds(base, versions)
    aretes = inserer_aretes_declarees(base, versions, noeuds["articles"])
    reprises = construire_repris_de(base, versions)
    base.commit()

    # Le schéma pose les contraintes ; encore faut-il vérifier qu'elles tiennent
    # sur la donnée réelle plutôt que de faire confiance au chargement.
    violations = list(base.execute("PRAGMA foreign_key_check"))
    orphelines = base.execute(
        "SELECT count(*) FROM repris_de WHERE preuve_id IS NULL").fetchone()[0]

    print(f"versions d'articles       : {len(versions)}")
    print(f"articles distincts        : {noeuds['noeuds']} "
          f"(dont {noeuds['scindes']} lignées nouvelles d'un numéro réutilisé)")
    print(f"segments                  : {noeuds['segments']} "
          f"({noeuds['segments'] / len(versions):.1f} par version)")
    print(f"  non appariables (<60 c.) : "
          f"{base.execute('SELECT count(*) FROM segment_non_appariable').fetchone()[0]}")
    print(f"textes normatifs          : {len(noeuds['textes'])}")
    print(f"arêtes produite_par       : {aretes['produite_par']}")
    print(f"arêtes renumerote_de      : {aretes['renumerote_de']}")
    print(f"arêtes repris_de          : {reprises['repris_de']}")
    print(f"  reprises intégrales     : {reprises['integrales']}")
    print(f"  retouchées              : {reprises['retouchees']}")
    print(f"\nintégrité : {len(violations)} violation(s) de clef étrangère, "
          f"{orphelines} arête(s) dérivée(s) sans preuve")
    if violations or orphelines:
        sys.exit("intégrité non satisfaite")


if __name__ == "__main__":
    main()
