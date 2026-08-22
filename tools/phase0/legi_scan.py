#!/usr/bin/env python3
"""Phase 0 — mesure du périmètre sur un code du fonds LEGI.

Ne fait partie d'aucun pipeline et n'a pas vocation à être maintenu. Sert
uniquement à produire, de façon reproductible, les chiffres de la note de cadrage
et la liste figée des articles cibles.

Le dump LEGI se décompresse en plus de 200 000 fichiers. Extraire par filtre :

    tar xzf Freemium_legi_global_<date>.tar.gz -C <dir> \
        --wildcards '*LEGITEXT000006069565*'

Usage :
    legi_scan.py <racine_extraction> <sortie.json>
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ARTICLE_FILE = re.compile(r"^LEGIARTI\d+\.xml$")

LIEN_RE = re.compile(
    r"<LIEN\s+(?P<attrs>[^>]*?)>(?P<libelle>.*?)</LIEN>", re.S
)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def tag(xml: str, name: str) -> str:
    m = re.search(rf"<{name}>(.*?)</{name}>", xml, re.S)
    return m.group(1).strip() if m else ""


def plain(fragment: str) -> str:
    """Texte brut d'un bloc XML, balises retirées, espaces normalisés."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def parse_article(path: Path) -> dict:
    xml = path.read_text(encoding="utf-8", errors="replace")

    liens = []
    bloc_liens = re.search(r"<LIENS>(.*?)</LIENS>", xml, re.S)
    if bloc_liens:
        for m in LIEN_RE.finditer(bloc_liens.group(1)):
            attrs = dict(ATTR_RE.findall(m.group("attrs")))
            liens.append(
                {
                    "typelien": attrs.get("typelien", ""),
                    "sens": attrs.get("sens", ""),
                    "cidtexte": attrs.get("cidtexte", ""),
                    "naturetexte": attrs.get("naturetexte", ""),
                    "num": attrs.get("num", ""),
                    "id": attrs.get("id", ""),
                    "libelle": plain(m.group("libelle")),
                }
            )

    contexte = re.search(r"<CONTEXTE>(.*?)</CONTEXTE>", xml, re.S)
    contexte_xml = contexte.group(1) if contexte else ""
    texte_attrs = dict(ATTR_RE.findall(re.search(r"<TEXTE\s+([^>]*)>", contexte_xml).group(1))) \
        if re.search(r"<TEXTE\s+([^>]*)>", contexte_xml) else {}

    return {
        "id": tag(xml, "ID"),
        "num": tag(xml, "NUM"),
        "etat": tag(xml, "ETAT"),
        "date_debut": tag(xml, "DATE_DEBUT"),
        "date_fin": tag(xml, "DATE_FIN"),
        "cid_texte": texte_attrs.get("cid", ""),
        "nature_texte": texte_attrs.get("nature", ""),
        "sections": [plain(s) for s in re.findall(r"<TITRE_TM[^>]*>(.*?)</TITRE_TM>", contexte_xml, re.S)],
        "texte": plain(tag(xml, "BLOC_TEXTUEL")),
        "nota": plain(tag(xml, "NOTA")),
        "liens": liens,
        "source": str(path),
    }


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    root, out = Path(sys.argv[1]), Path(sys.argv[2])

    articles = [
        parse_article(p) for p in root.rglob("*.xml") if ARTICLE_FILE.match(p.name)
    ]
    out.write_text(json.dumps(articles, ensure_ascii=False), encoding="utf-8")

    etats = Counter(a["etat"] for a in articles)
    en_vigueur = [a for a in articles if a["etat"] == "VIGUEUR"]
    types = Counter(l["typelien"] for a in articles for l in a["liens"])

    print(f"versions d'articles : {len(articles)}")
    print(f"états               : {etats.most_common()}")
    print(f"en vigueur          : {len(en_vigueur)}")
    print(f"numéros distincts   : {len({a['num'] for a in en_vigueur})}")
    print(f"types de liens      : {types.most_common(20)}")


if __name__ == "__main__":
    main()
