#!/usr/bin/env bash
# Miroir des fonds DILA. Le dump global est le seul point de reconstruction
# existant et les incréments ne remontent pas au-delà de sa date : si la DILA
# publie un nouveau global et purge, la reconstruction depuis zéro devient
# impossible. Ce script est à relancer quotidiennement.
#
# Usage : miroir_dila.sh <repertoire_destination>
set -uo pipefail
DEST="${1:?répertoire de destination requis}"
BASE=https://echanges.dila.gouv.fr/OPENDATA
MANIFESTE="$DEST/manifeste-$(date -u +%Y%m%dT%H%M%SZ).tsv"

printf 'fonds\tfichier\toctets\tsha256\trecupere_le\n' > "$MANIFESTE"
for FONDS in LEGI JORF DOLE; do
  mkdir -p "$DEST/$FONDS"
  curl -sS --fail --max-time 120 "$BASE/$FONDS/" \
    | grep -oE 'href="[^"]+\.tar\.gz"' | sed 's/href="//;s/"//' | sort -u \
    | while read -r F; do
        CIBLE="$DEST/$FONDS/$F"
        if [ ! -s "$CIBLE" ]; then
          curl -sS --fail --max-time 3000 -o "$CIBLE" "$BASE/$FONDS/$F" || { rm -f "$CIBLE"; continue; }
        fi
        printf '%s\t%s\t%s\t%s\t%s\n' "$FONDS" "$F" "$(stat -c%s "$CIBLE")" \
          "$(sha256sum "$CIBLE" | cut -d' ' -f1)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$MANIFESTE"
      done
done
echo "manifeste : $MANIFESTE"
wc -l < "$MANIFESTE"
