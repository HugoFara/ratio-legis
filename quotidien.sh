#!/usr/bin/env bash
# Réincrémentation quotidienne — § 4.1 de la feuille de route.
#
# La base de travail était construite depuis l'archive **globale** de la DILA,
# datée du 13 juillet 2025, alors que le miroir recevait un incrément par jour
# ouvré. Elle avait un an de retard, et rien ne le disait. Ce script ferme
# l'écart et le maintient fermé.
#
# Ce qu'il fait, dans l'ordre, et pourquoi cet ordre :
#   1. miroir DILA        — seule étape qui a besoin du réseau ; idempotente
#   2. incréments LEGI    — appliqués au fonds extrait, journalisés un par un
#   3. arrêt anticipé     — si rien n'a bougé, ne rien reconstruire
#   4. reconstruction     — le graphe entier ; voir la note ci-dessous
#   5. dump ouvert        — ce qui est publié suit ce qui est construit
#   6. ce qui a changé    — un rapport quotidien vaut mieux qu'un rebuild muet
#
# **La reconstruction est complète, non incrémentale, et c'est délibéré.** Presque
# toutes les arêtes dépendent de LEGI : segments, `repris_de`, `renumerote_de`, et
# par ricochet `motive`, `resulte_de`, `porte_sur`, le verdict. Reconstruire coûte
# quelques minutes ; patcher le graphe coûterait une classe entière de bogues
# d'incohérence, pour un gain que personne n'attend sur un rythme quotidien.
# L'incrément porte sur la **source**, pas sur le graphe.
#
# Usage : quotidien.sh [répertoire de travail] [base.sqlite]
set -uo pipefail
RACINE="$(cd "$(dirname "$0")" && pwd)"
TRAVAIL="${1:-$RACINE/travail}"
BASE="${2:-$TRAVAIL/ratio-legis.sqlite}"
MIROIR="$RACINE/data/raw/dila"
CODE=LEGITEXT000006069565
JOURNAL="$RACINE/data/mesures/journal-quotidien.tsv"
COURSE="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$(dirname "$JOURNAL")"
[ -s "$JOURNAL" ] || printf 'course\tetape\tetat\tsecondes\tdetail\n' > "$JOURNAL"

noter() {  # noter <étape> <état> <secondes> <détail>
  printf '%s\t%s\t%s\t%s\t%s\n' "$COURSE" "$1" "$2" "$3" "$4" >> "$JOURNAL"
  printf '\033[1m[%s]\033[0m %s — %s (%ss)\n' "$1" "$2" "$4" "$3"
}

etape() {  # etape <nom> <commande…> : chronomètre, journalise, propage l'échec
  local nom="$1"; shift
  local debut; debut=$(date +%s)
  local sortie; sortie=$("$@" 2>&1); local code=$?
  local duree=$(( $(date +%s) - debut ))
  # Le journal est versionné. Il ne doit donc pas emporter l'arborescence de la
  # machine qui l'a écrit : les chemins sont ramenés à la racine du dépôt, et ce
  # qui reste de $HOME à un tilde. Sans cela un dépôt public publie un nom
  # d'utilisateur et un plan de disque, chaque matin, sans que personne le relise.
  local resume; resume=$(printf '%s' "$sortie" | tail -1 | tr '\t\n' '  ')
  resume=${resume//"$RACINE"\//}
  resume=${resume//"$HOME"/\~}
  resume=$(printf '%s' "$resume" | cut -c1-160)
  if [ $code -ne 0 ]; then
    noter "$nom" ECHEC "$duree" "$resume"
    printf '%s\n' "$sortie" | tail -20
    return 1
  fi
  noter "$nom" OK "$duree" "$resume"
  printf '%s\n' "$sortie" | tail -6
}

# --------------------------------------------------------------- 1. le miroir
etape miroir bash "$RACINE/tools/phase0/miroir_dila.sh" "$MIROIR" || exit 1

# ------------------------------------------------------------ 2. les incréments
etape increments python3 "$RACINE/tools/dila/increments.py" \
      "$MIROIR" "$TRAVAIL/conso" "$CODE" || exit 1

# --------------------------------------------------- 3. y a-t-il eu du nouveau ?
# La question se pose au fonds, pas à git : « un fichier source est-il plus récent
# que la base construite ? ». Un test qui dépend du dépôt répondrait « non » hors
# dépôt, c'est-à-dire exactement là où personne ne le vérifierait.
NOUVEAU=$(find "$TRAVAIL/conso" -name '*.xml' -newer "$BASE" -print -quit 2>/dev/null)
if [ -s "$BASE" ] && [ -z "$NOUVEAU" ]; then
  noter reconstruction IGNOREE 0 "aucun fichier du fonds plus récent que la base"
  noter course TERMINEE 0 "rien à faire"
  exit 0
fi

# --------------------------------------------------------- 4. reconstruction
etape reconstruction bash "$RACINE/pipeline.sh" "$TRAVAIL" "$BASE" || exit 1

# ------------------------------------------------------------------ 5. dump
etape dump python3 "$RACINE/tools/diffusion/dump.py" "$BASE" "$RACINE/data/diffusion" \
  || exit 1

# --------------------------------------------------------- 6. ce qui a changé
etape rapport python3 "$RACINE/tools/mesures/quoi_de_neuf.py" "$BASE" "$JOURNAL" \
      "$COURSE" || exit 1

noter course TERMINEE 0 "fonds plus récent que la base : reconstruit"
