#!/usr/bin/env bash
# Refait les rendus d'exemple versionnés, tels que la base du jour les produit,
# et la page d'entrée qui les liste. À relancer quand la feuille de style, un
# module de restitution ou la base change — un rendu versionné qui ne
# correspond plus à ce que le code produit est un chiffre périmé.
#
#     restitution/regenerer_les_exemples.sh [base.sqlite]
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="${1:-travail/ratio-legis.sqlite}"
EX=restitution/exemples

for n in L224-43 L111-1 L511-7 L112-1-1 L122-23 L521-2 L722-10 L411-1 R121-1 D824-3 R512-31 D120-7; do
    python3 restitution/graphe.py "$BASE" "$n" --html "$EX/$n.html"
done
for n in L224-43 L122-23 L112-1-1 L722-10 L411-1 D824-3 R512-31; do
    python3 restitution/note.py "$BASE" "$n" --html "$EX/notes/$n.html"
done
for n in L111-1 L112-1-1 L224-43 L722-10 R121-1; do
    python3 restitution/surlignage.py "$BASE" "$n" --html "$EX/surlignage/$n.html"
done
for n in L732-3 L312-9 L113-3 L224-43 L111-3; do
    python3 restitution/tentatives.py "$BASE" "$n" --html "$EX/tentatives/$n.html"
done
python3 restitution/tentatives.py "$BASE" --sommet --html "$EX/tentatives/sommet.html"
for n in L111-1 L221-5 R512-31 D412-51; do
    python3 restitution/retentissement.py "$BASE" "$n" --html "$EX/retentissement/$n.html"
done
python3 restitution/retentissement.py "$BASE" --sommet --html "$EX/retentissement/sommet.html"
python3 restitution/index_des_exemples.py "$EX" data/mesures/hygiene.tsv
