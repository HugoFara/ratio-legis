#!/usr/bin/env bash
# Récupère les rapports de commission des dossiers d'un jeu d'annotation, depuis
# les liens de l'ARBORESCENCE de DOLE.
#
# Les fichiers sont nommés <ID_DOLE>__<fichier> : le rattachement au dossier doit
# survivre au téléchargement, sinon l'extraction ne sait plus à quel texte un
# rapport se rapporte.
#
# Deux particularités des sources :
#   - les rapports du Sénat sont paginés ; seule la version `_mono.html` porte le
#     texte, et son URL se déduit mécaniquement de celle de la page d'index ;
#   - depuis la XVIe législature, l'Assemblée publie ses rapports sous
#     `/dyn/<lég>/rapports/<commission>/l<lég>b<n°>_rapport-fond` — une page de
#     garde de 75 ko, sans le corps. Le texte intégral est sous
#     `/dyn/opendata/RAPPANR5L<lég>B<n°>.html`, et l'URL s'en déduit aussi ;
#     sans cette règle, la XVIe et la XVIIe législature entraient en base sans
#     un seul commentaire d'article ;
#   - une page d'index du Sénat fait moins de 20 ko, ce qui sert de test de rejet —
#     mais seulement pour les rapports : un texte de loi court est légitimement
#     petit, et lui appliquer le même seuil fait perdre les petits dossiers ;
#   - les deux sites redirigent http vers https : sans -L, --fail rejette la
#     redirection et fait perdre les deux tiers du corpus, silencieusement ;
#   - le serveur du Sénat ferme la connexion TLS sans close_notify. curl sort
#     alors en erreur 56 alors que le corps est complet : se fier au code HTTP et
#     à la taille, jamais au code de sortie de curl.
#
# Usage : telecharger_rapports.sh <plan.tsv> <destination>
#         plan.tsv : deux colonnes, ID_DOLE <TAB> URL
set -uo pipefail
PLAN="${1:?plan tsv requis}"
DEST="${2:?répertoire de destination requis}"
mkdir -p "$DEST"

# Texte intégral d'un rapport de l'Assemblée publié sous /dyn/, ou rien.
texte_integral_an() {
  local url="${1%%#*}" leg num
  case "$url" in
    *assemblee-nationale.fr/dyn/*/rapports/*_rapport-fond)
      leg="${url##*/l}"; leg="${leg%%b*}"
      num="${url##*b}"; num="${num%_rapport-fond}"
      echo "https://www.assemblee-nationale.fr/dyn/opendata/RAPPANR5L${leg}B${num}.html" ;;
  esac
}

recuperer() {
  local dossier="$1" url="${2%%#*}" nom code
  nom="${dossier}__$(basename "$url")"
  [ -s "$DEST/$nom" ] && return 0
  code=$(curl -sSL --max-time 120 -o "$DEST/$nom" -w '%{http_code}' "$url" 2>/dev/null)
  if [ "$code" != "200" ] || [ ! -s "$DEST/$nom" ]; then
    rm -f "$DEST/$nom"
    return 1
  fi
  case "$url" in
    *senat.fr/rap/*) [ "$(stat -c%s "$DEST/$nom")" -lt 20000 ] && rm -f "$DEST/$nom" ;;
  esac
  return 0
}

while IFS=$'\t' read -r dossier url; do
  [ -z "${url:-}" ] && continue
  recuperer "$dossier" "$url"
  case "$url" in
    *senat.fr/rap/*.html) recuperer "$dossier" "${url%.html}_mono.html" ;;
  esac
  integral=$(texte_integral_an "$url")
  [ -n "$integral" ] && recuperer "$dossier" "$integral"
done < "$PLAN"

echo "rapports récupérés : $(ls "$DEST" | wc -l)"
