#!/usr/bin/env bash
# Ratio Legis — reconstruction complète du graphe depuis les sources versionnées.
#
# Écrit après avoir perdu tous les corpus dérivés : ils ne vivaient que dans un
# répertoire temporaire, effacé au vidage de /tmp. Le miroir DILA, lui, a survécu
# parce qu'il est dans l'arbre du dépôt. La règle « la donnée brute est sacrée »
# du § 5.2 ne vaut que si l'on sait aussi la retrouver : ce script est la
# vérification que tout est reconstructible à partir de ce qui est versionné.
#
# Ce dont il a besoin, et rien d'autre :
#   - le miroir DILA          data/raw/dila/          (non versionné, 6,4 Go)
#   - le périmètre            data/perimetre-v1.csv
#   - les plans de récupération  data/corpus/*.tsv
#
# Usage : pipeline.sh [répertoire de travail] [base.sqlite]
set -uo pipefail
RACINE="$(cd "$(dirname "$0")" && pwd)"

# L'interpréteur fait partie de ce qu'il faut pour rejouer le pipeline, au même
# titre que le miroir et les plans. Le laisser implicite, c'est accepter que
# « rejouable » veuille dire « rejouable ici » — l'inverse de la règle § 5.2.
python3 - <<'FIN' || exit 1
import sys
if sys.version_info < (3, 14):
    sys.exit(f"Python 3.14 est requis (voir pyproject.toml) ; "
             f"celui-ci est {'.'.join(map(str, sys.version_info[:3]))}.")
FIN
TRAVAIL="${1:-$RACINE/travail}"
BASE="${2:-$TRAVAIL/ratio-legis.sqlite}"
MIROIR="$RACINE/data/raw/dila"
CODE=LEGITEXT000006069565          # code de la consommation

etape() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

mkdir -p "$TRAVAIL"/{conso,corpus/rapports,corpus/ameli,corpus/impacts,corpus/textes,an}

# --------------------------------------------------------------- 1. fonds LEGI
etape "1. Extraction du code depuis le miroir LEGI"
if [ -z "$(ls -A "$TRAVAIL/conso" 2>/dev/null)" ]; then
  ARCHIVE=$(ls -t "$MIROIR"/LEGI/Freemium_legi_global_*.tar.gz 2>/dev/null | head -1)
  [ -n "$ARCHIVE" ] || { echo "miroir LEGI absent : lancer tools/phase0/miroir_dila.sh"; exit 1; }
  # Extraction ciblée : l'archive globale fait 1,2 Go compressés et son
  # déploiement complet avait saturé le disque en phase 0.
  tar xzf "$ARCHIVE" -C "$TRAVAIL/conso" --strip-components=9 --wildcards \
      "*/$CODE/*" 2>/dev/null
  echo "   $(find "$TRAVAIL/conso" -name 'LEGIARTI*.xml' | wc -l) versions d'articles"
else
  echo "   déjà extrait"
fi

# L'archive globale date du 13 juillet 2025 ; la DILA publie un incrément par jour
# ouvré. Sans cette étape, le fonds extrait avait un an de retard sur le miroir et
# rien ne le disait — 200 des 406 incréments publiés depuis touchent ce code.
python3 "$RACINE/tools/dila/increments.py" "$MIROIR" "$TRAVAIL/conso" "$CODE"

# ------------------------------------------------------- 2. rapports et textes
etape "2. Rapports de commission"
if [ "$(ls "$TRAVAIL/corpus/rapports" | wc -l)" -lt 200 ]; then
  bash "$RACINE/tools/prototype/telecharger_rapports.sh" \
       "$RACINE/data/corpus/plan-rapports.tsv" "$TRAVAIL/corpus/rapports"
else
  echo "   $(ls "$TRAVAIL/corpus/rapports" | wc -l) rapports déjà présents"
fi

# Une ordonnance n'a ni exposé des motifs, ni rapport de commission : sa seule
# motivation publiée est le rapport au Président de la République. Il est au
# Journal officiel, donc dans le miroir — aucun accès réseau.
if [ "$(ls "$TRAVAIL/corpus/rapports" | grep -c rapport-pr)" -lt 30 ]; then
  python3 "$RACINE/tools/dila/rapports_president.py" "$MIROIR" \
          "$RACINE/data/perimetre-v1.csv" "$TRAVAIL/corpus/rapports"
else
  echo "   $(ls "$TRAVAIL/corpus/rapports" | grep -c rapport-pr) rapports au Président déjà présents"
fi

# L'exposé des motifs est dans le XML DOLE lui-même, sous <EXPOSE_MOTIF> : ni
# téléchargement, ni PDF, ni OCR. C'est la colonne « ce que le Gouvernement a
# déclaré vouloir » du § 4.3.
if [ "$(ls "$TRAVAIL/corpus/rapports" | grep -c expose-motifs)" -lt 30 ]; then
  python3 "$RACINE/tools/dila/exposes_motifs.py" "$MIROIR" \
          "$RACINE/data/perimetre-v1.csv" "$TRAVAIL/corpus/rapports"
else
  echo "   $(ls "$TRAVAIL/corpus/rapports" | grep -c expose-motifs) exposés déjà présents"
fi

etape "2 bis. Études d'impact et avis du Conseil d'État"
# Les seuls documents du corpus qui n'existent qu'en PDF. DOLE n'en porte que le
# lien ; le plan est versionné pour retélécharger sans retraverser l'archive.
IMPACTS="$RACINE/data/corpus/plan-impacts.tsv"
[ -s "$IMPACTS" ] || python3 "$RACINE/tools/dila/plan_impacts.py" "$MIROIR" \
        "$RACINE/data/perimetre-v1.csv" "$IMPACTS"
python3 "$RACINE/tools/dila/telecharger_impacts.py" "$IMPACTS" \
        "$TRAVAIL/corpus/impacts" "$TRAVAIL/corpus/rapports"

etape "2 ter. Textes en discussion"
# Le chaînon « article du texte → article du code ». DOLE n'en porte que les
# liens ; les pages sont sur les sites des deux chambres, en HTML pour les
# anciennes et en PDF pour les récentes de l'Assemblée.
TEXTES="$RACINE/data/corpus/plan-textes.tsv"
[ -s "$TEXTES" ] || python3 "$RACINE/tools/dila/plan_textes.py" "$MIROIR" \
        "$RACINE/data/perimetre-v1.csv" "$TEXTES"
python3 "$RACINE/tools/dila/telecharger_textes.py" "$TEXTES" "$TRAVAIL/corpus/textes"

# ------------------------------------------------------- 3. amendements Sénat
etape "3. Jeux d'amendements Améli (Sénat)"
if [ "$(ls "$TRAVAIL/corpus/ameli" | wc -l)" -lt 50 ]; then
  python3 "$RACINE/tools/senat/plan_ameli.py" "$MIROIR" "$RACINE/data/perimetre-v1.csv" \
          "$RACINE/data/corpus/plan-ameli.tsv"
  while IFS=$'\t' read -r dossier session texte; do
    [ -z "${texte:-}" ] && continue
    url="https://www.senat.fr/amendements/${session}/${texte}/jeu_complet_${session}_${texte}.csv"
    dest="$TRAVAIL/corpus/ameli/${dossier}__${session}_${texte}.csv"
    [ -s "$dest" ] && continue
    code=$(curl -sSL --max-time 120 -o "$dest" -w '%{http_code}' "$url" 2>/dev/null)
    { [ "$code" != "200" ] || [ ! -s "$dest" ]; } && rm -f "$dest"
  done < "$RACINE/data/corpus/plan-ameli.tsv"
  echo "   $(ls "$TRAVAIL/corpus/ameli" | wc -l) jeux récupérés"
else
  echo "   $(ls "$TRAVAIL/corpus/ameli" | wc -l) jeux déjà présents"
fi

# -------------------------------------------------- 4. amendements Assemblée
etape "4. Amendements de l'Assemblée, XIVe législature"
AN=https://data.assemblee-nationale.fr/static/openData/repository
# Le chemin est `amendements_legis_XIV`, non `amendements_legis` : la page
# d'archives de l'Assemblée publie une URL périmée, qui avait fait conclure à
# tort que ces données n'existaient pas (docs/10 § 4).
for couple in \
  "14/loi/amendements_legis_XIV/Amendements_XIV.csv.zip|Amendements_XIV.csv.zip" \
  "17/amo/tous_acteurs_mandats_organes_xi_legislature/AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip|acteurs_historique.json.zip"
do
  chemin="${couple%%|*}"; nom="${couple##*|}"
  [ -s "$TRAVAIL/an/$nom" ] && { echo "   $nom déjà présent"; continue; }
  # --http1.1 : le serveur coupe le flux HTTP/2 sur les gros fichiers.
  curl -sSL --http1.1 --retry 3 -C - --max-time 1800 -o "$TRAVAIL/an/$nom" "$AN/$chemin" \
    && echo "   $nom : $(du -h "$TRAVAIL/an/$nom" | cut -f1)"
done
python3 "$RACINE/tools/an/extraire_amendements_an.py" \
        "$TRAVAIL/an/Amendements_XIV.csv.zip" \
        "$RACINE/data/corpus/plan-textes-an-14.tsv" "$TRAVAIL/an/amendements_14.csv"

# ------------------------------------------------------------- 5. ingestion
etape "5. Ingestion"
rm -f "$BASE"
python3 "$RACINE/ingestion/legi_vers_graphe.py" "$TRAVAIL/conso" "$BASE"
python3 "$RACINE/ingestion/rapports_vers_motive.py" "$TRAVAIL/corpus/rapports" \
        "$RACINE/data/perimetre-v1.csv" "$RACINE/data/corpus/plan-rapports.tsv" \
        "$BASE" "$IMPACTS"
# Le dossier législatif de chaque texte, déclaré par DOLE. Doit précéder les
# amendements et les visées : tous deux ne considèrent que les dossiers ayant
# produit un article du code, et cette liste dépend de `issu_de`.
python3 "$RACINE/ingestion/dossiers_des_textes.py" "$MIROIR" "$BASE"
python3 "$RACINE/ingestion/renvois.py" "$BASE"
python3 "$RACINE/ingestion/an_vers_amendements.py" "$TRAVAIL/an/amendements_14.csv" \
        "$TRAVAIL/an/acteurs_historique.json.zip" "$BASE"
python3 "$RACINE/ingestion/amendements_vers_resulte_de.py" "$TRAVAIL/corpus/ameli" "$BASE"
python3 "$RACINE/ingestion/visees.py" "$BASE"
python3 "$RACINE/ingestion/textes_deposes.py" "$TRAVAIL/corpus/textes" "$TEXTES" "$BASE"
# Doit suivre les deux précédents : il lui faut les documents et `porte_sur`.
python3 "$RACINE/ingestion/sections_vers_motive.py" "$TRAVAIL/corpus/rapports" \
        "$RACINE/data/perimetre-v1.csv" "$RACINE/data/corpus/plan-rapports.tsv" \
        "$BASE" "$IMPACTS"

# ------------------------------------------------------- 6. couche européenne
etape "6. Droit de l'Union"
# L'intitulé complet d'un texte est au Journal officiel, pas dans LEGI : c'est
# lui qui déclare une transposition. Le plan est versionné, donc régénéré
# seulement s'il manque — l'extraction traverse une archive de 1,6 Go.
TITRES="$RACINE/data/corpus/titres-jorf.tsv"
[ -s "$TITRES" ] || python3 "$RACINE/tools/dila/titres_jorf.py" "$MIROIR" "$BASE" "$TITRES"

# Les CELEX sont construits depuis le texte français, donc vérifiés un à un
# auprès de Cellar. Seule étape du projet qui demande le réseau ; son résultat
# est versionné pour que tout le reste reste rejouable hors ligne.
CELEX="$RACINE/data/corpus/celex-verifies.tsv"
[ -s "$CELEX" ] || python3 "$RACINE/tools/ue/verifier_celex.py" "$BASE" "$CELEX"

python3 "$RACINE/ingestion/union_europeenne.py" "$BASE" "$CELEX" "$TITRES"

# Le « pourquoi » du droit de l'Union est dans ses considérants, publiés avec
# l'acte. EUR-Lex les rend en HTML structuré selon ELI ; le miroir est hors dépôt
# comme celui de la DILA, seul son manifeste est versionné.
EURLEX="$RACINE/data/raw/eurlex"
python3 "$RACINE/tools/ue/recuperer_actes.py" "$BASE" "$EURLEX"
python3 "$RACINE/ingestion/considerants.py" "$BASE" "$EURLEX"

# --------------------------------------------------- 7. verdict et métriques
etape "7. Verdict et métriques d'hygiène"
python3 "$RACINE/ingestion/verdict.py" "$BASE"
python3 "$RACINE/tools/mesures/hygiene.py" "$BASE" "$RACINE/data/perimetre-v1.csv" \
        "$RACINE/data/mesures/hygiene.tsv"

# ------------------------------------------- 8. préparation de la lecture
etape "8. Index de lecture"
# En dernier, après toute écriture : ce sont les statistiques du planificateur
# qui font l'essentiel, et elles décrivent la base telle qu'elle est à la fin.
python3 "$RACINE/ingestion/index_de_lecture.py" "$BASE"

etape "Terminé"
echo "base : $BASE ($(du -h "$BASE" | cut -f1))"
echo "essai : python3 restitution/graphe.py $BASE L224-43"
