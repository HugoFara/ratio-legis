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
#   - les plans de récupération  data/corpus/*.tsv
#
# **Le périmètre n'est plus une entrée, c'est une sortie.** Il était figé en
# phase 0 sur la seule partie législative, sans le code qui l'avait produit, et
# `docs/27` montre ce que cela a coûté : la raison écrite de l'exclusion des
# parties R et D — « rattachement à DOLE mesuré à 0 % » — est fausse, et rien ne
# pouvait la démentir tant que le fichier ne se recalculait pas. Il est désormais
# dérivé du fonds, à l'étape 1 bis, avant tout ce qui en dépend.
#
# Usage : pipeline.sh [répertoire de travail] [base.sqlite]
set -uo pipefail
RACINE="$(cd "$(dirname "$0")" && pwd)"

# Une étape d'ingestion qui échoue arrête le pipeline. Sans cela — vu le
# 19 septembre 2026 — `texte_discute` s'est chargé à zéro sur une collision
# d'identifiants, les tranches suivantes ont tourné sur le trou, et l'hygiène a
# publié « 0 texte en discussion » comme un chiffre. Un téléchargement peut
# échouer, le pipeline le compte ; une ingestion, non.
ingere() { python3 "$@" || { echo "ÉCHEC : ${1##*/} — pipeline arrêté" >&2; exit 1; }; }

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
PERIMETRE="$RACINE/data/perimetre-v2.csv"
IMPACTS="$RACINE/data/corpus/plan-impacts.tsv"
TEXTES="$RACINE/data/corpus/plan-textes.tsv"
DOSSIERS="$RACINE/data/dossiers-du-perimetre.tsv"
RAPPORTS="$RACINE/data/corpus/plan-rapports.tsv"

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

# ------------------------------------- 1 bis. le graphe LEGI, puis le périmètre
etape "1 bis. Fonds LEGI en base, dossiers DOLE, périmètre"
# Le périmètre se déduit du fonds : il lui faut donc la base, et à la base il ne
# faut que le fonds. `dossiers_des_textes` complète `issu_de`, sans quoi le
# périmètre ne saurait pas quels articles ont un dossier dans leur ascendance —
# c'est-à-dire exactement ce que l'exclusion des parties R et D avait supposé nul.
rm -f "$BASE"
ingere "$RACINE/ingestion/legi_vers_graphe.py" "$TRAVAIL/conso" "$BASE"
ingere "$RACINE/ingestion/dossiers_des_textes.py" "$MIROIR" "$BASE"
python3 "$RACINE/tools/phase0/perimetre.py" "$BASE" \
        "$RACINE/data/perimetre-v1.csv" "$PERIMETRE"
# Les dossiers à récupérer sont ceux de tout l'historique des articles en
# vigueur, pas le seul dossier d'origine que porte le périmètre : un texte qui
# modifie un article a un dossier, et ce dossier motive ce qu'il a réécrit. La
# liste est versionnée ; quand elle bouge, les plans se régénèrent.
python3 "$RACINE/tools/dila/dossiers_du_perimetre.py" "$BASE" "$DOSSIERS.new"
if ! cmp -s "$DOSSIERS" "$DOSSIERS.new"; then
  mv "$DOSSIERS.new" "$DOSSIERS"
  rm -f "$RAPPORTS" "$IMPACTS" "$TEXTES" "$RACINE/data/corpus/plan-ameli.tsv"
  echo "   liste des dossiers modifiée : plans à régénérer"
else
  rm -f "$DOSSIERS.new"
fi

# ------------------------------------------------------- 2. rapports et textes
etape "2. Rapports de commission"
# Les plans se régénèrent quand ils manquent, et les téléchargeurs sautent ce qui
# est déjà là. Les garde-fous par comptage — « plus de 200 fichiers, on passe » —
# ont été retirés : ils faisaient exactement l'inverse de leur objet le jour où le
# périmètre a bougé, en déclarant le corpus complet alors qu'il manquait les
# dossiers nouveaux.
[ -s "$RAPPORTS" ] || python3 "$RACINE/tools/dila/plan_rapports.py" "$MIROIR" \
        "$DOSSIERS" "$RAPPORTS"
bash "$RACINE/tools/prototype/telecharger_rapports.sh" \
     "$RAPPORTS" "$TRAVAIL/corpus/rapports"

# Une ordonnance n'a ni exposé des motifs, ni rapport de commission : sa seule
# motivation publiée est le rapport au Président de la République. Il est au
# Journal officiel, donc dans le miroir — aucun accès réseau.
python3 "$RACINE/tools/dila/rapports_president.py" "$MIROIR" \
        "$DOSSIERS" "$TRAVAIL/corpus/rapports"

# L'exposé des motifs est dans le XML DOLE lui-même, sous <EXPOSE_MOTIF> : ni
# téléchargement, ni PDF, ni OCR. C'est la colonne « ce que le Gouvernement a
# déclaré vouloir » du § 4.3.
python3 "$RACINE/tools/dila/exposes_motifs.py" "$MIROIR" \
        "$DOSSIERS" "$TRAVAIL/corpus/rapports"

etape "2 bis. Études d'impact et avis du Conseil d'État"
# Les seuls documents du corpus qui n'existent qu'en PDF. DOLE n'en porte que le
# lien ; le plan est versionné pour retélécharger sans retraverser l'archive.
[ -s "$IMPACTS" ] || python3 "$RACINE/tools/dila/plan_impacts.py" "$MIROIR" \
        "$DOSSIERS" "$IMPACTS"
python3 "$RACINE/tools/dila/telecharger_impacts.py" "$IMPACTS" \
        "$TRAVAIL/corpus/impacts" "$TRAVAIL/corpus/rapports"

etape "2 ter. Textes en discussion"
# Le chaînon « article du texte → article du code ». DOLE n'en porte que les
# liens ; les pages sont sur les sites des deux chambres, en HTML pour les
# anciennes et en PDF pour les récentes de l'Assemblée.
[ -s "$TEXTES" ] || python3 "$RACINE/tools/dila/plan_textes.py" "$MIROIR" \
        "$DOSSIERS" "$TEXTES"
python3 "$RACINE/tools/dila/telecharger_textes.py" "$TEXTES" "$TRAVAIL/corpus/textes"

# ------------------------------------------------------- 3. amendements Sénat
etape "3. Jeux d'amendements Améli (Sénat)"
AMELI="$RACINE/data/corpus/plan-ameli.tsv"
[ -s "$AMELI" ] || python3 "$RACINE/tools/senat/plan_ameli.py" "$MIROIR" \
        "$DOSSIERS" "$AMELI"
while IFS=$'\t' read -r dossier session texte; do
  [ -z "${texte:-}" ] && continue
  url="https://www.senat.fr/amendements/${session}/${texte}/jeu_complet_${session}_${texte}.csv"
  dest="$TRAVAIL/corpus/ameli/${dossier}__${session}_${texte}.csv"
  [ -s "$dest" ] && continue
  code=$(curl -sSL --max-time 120 -o "$dest" -w '%{http_code}' "$url" 2>/dev/null)
  { [ "$code" != "200" ] || [ ! -s "$dest" ]; } && rm -f "$dest"
done < "$AMELI"
echo "   $(ls "$TRAVAIL/corpus/ameli" | wc -l) jeux présents"

# -------------------------------------------------- 4. amendements Assemblée
etape "4. Amendements de l'Assemblée, XIIIe à XVIIe législature"
AN=https://data.assemblee-nationale.fr/static/openData/repository
# Le chemin est `amendements_legis_XIV`, non `amendements_legis` : la page
# d'archives de l'Assemblée publie une URL périmée, qui avait fait conclure à
# tort que ces données n'existaient pas (docs/10 § 4). Depuis la XVe, le jeu
# est en JSON, et son chemin change encore d'une législature à l'autre.
for couple in \
  "14/loi/amendements_legis_XIV/Amendements_XIV.csv.zip|Amendements_XIV.csv.zip" \
  "15/loi/amendements_legis/Amendements_XV.json.zip|Amendements_XV.json.zip" \
  "16/loi/amendements_div_legis/Amendements.json.zip|Amendements_XVI.json.zip" \
  "17/loi/amendements_div_legis/Amendements.json.zip|Amendements_XVII.json.zip" \
  "17/amo/tous_acteurs_mandats_organes_xi_legislature/AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip|acteurs_historique.json.zip"
do
  chemin="${couple%%|*}"; nom="${couple##*|}"
  [ -s "$TRAVAIL/an/$nom" ] && { echo "   $nom déjà présent"; continue; }
  # --http1.1 : le serveur coupe le flux HTTP/2 sur les gros fichiers. Il coupe
  # aussi, par moments, le HTTP/1.1, sans accepter de reprise par plage : on
  # recommence du début, et seule une archive dont `unzip -t` répond est gardée.
  for essai in 1 2 3 4 5 6 7 8 9 10; do
    curl -sSL --http1.1 --max-time 1800 -o "$TRAVAIL/an/$nom.part" "$AN/$chemin" \
      && unzip -tqq "$TRAVAIL/an/$nom.part" 2>/dev/null \
      && mv "$TRAVAIL/an/$nom.part" "$TRAVAIL/an/$nom" && break
    sleep 20
  done
  rm -f "$TRAVAIL/an/$nom.part"
  [ -s "$TRAVAIL/an/$nom" ] && echo "   $nom : $(du -h "$TRAVAIL/an/$nom" | cut -f1)"
done
# Le plan « dossier → numéros de texte » est dérivé des liens DOLE et des textes
# déposés ; celui de la XIVe, écrit à la main, en est un sous-ensemble strict
# (tools/an/plan_textes_an.py). Le plan des textes déposés se reconstruit à
# l'étape 5, à partir des amendements : c'est sa version versionnée qu'on lit
# ici, avec au pire une exécution de retard sur un dossier nouveau.
# La XIIIe n'a pas de jeu open data : ses amendements de séance sont lus page
# par page sur le site de l'Assemblée, qui les sert encore (docs/57). Les pages
# sont gardées dans `travail/an/13/` ; une reconstruction ne les redemande pas.
python3 "$RACINE/tools/an/plan_textes_an.py" 13 \
        "$RACINE/data/corpus/plan-textes-an-13.tsv" "$RAPPORTS" "$TEXTES" \
        "$RACINE/data/corpus/plan-textes-deposes-an.tsv"
python3 "$RACINE/tools/an/moissonner_amendements_13.py" \
        "$RACINE/data/corpus/plan-textes-an-13.tsv" "$RAPPORTS" \
        "$TRAVAIL/an/acteurs_historique.json.zip" "$TRAVAIL/an/13" \
        "$TRAVAIL/an/amendements_13.csv"
for legislature in 14 15 16 17; do
  case $legislature in 14) jeu=XIV.csv;; 15) jeu=XV.json;; 16) jeu=XVI.json;; 17) jeu=XVII.json;; esac
  [ -s "$TRAVAIL/an/Amendements_$jeu.zip" ] || { echo "   $jeu absent"; continue; }
  python3 "$RACINE/tools/an/plan_textes_an.py" "$legislature" \
          "$RACINE/data/corpus/plan-textes-an-$legislature.tsv" "$RAPPORTS" "$TEXTES" \
          "$RACINE/data/corpus/plan-textes-deposes-an.tsv"
  python3 "$RACINE/tools/an/extraire_amendements_an.py" \
          "$TRAVAIL/an/Amendements_$jeu.zip" \
          "$RACINE/data/corpus/plan-textes-an-$legislature.tsv" \
          "$TRAVAIL/an/amendements_$legislature.csv"
done

# ------------------------------------------------------------- 5. ingestion
etape "5. Ingestion"
# `legi_vers_graphe` et `dossiers_des_textes` sont passés à l'étape 1 bis : le
# périmètre en dépend, et le corpus dépend du périmètre.
ingere "$RACINE/ingestion/rapports_vers_motive.py" "$TRAVAIL/corpus/rapports" \
        "$PERIMETRE" "$RAPPORTS" "$BASE" "$IMPACTS"
ingere "$RACINE/ingestion/renvois.py" "$BASE"
for extrait in "$TRAVAIL"/an/amendements_1[3-7].csv; do
  ingere "$RACINE/ingestion/an_vers_amendements.py" "$extrait" \
          "$TRAVAIL/an/acteurs_historique.json.zip" "$BASE"
done
# Les nœuds seulement : l'arête `resulte_de` se construit plus bas, après
# `porte_sur` et `depose_sur`, dont elle lit l'hôte de l'alinéa que
# l'amendement nomme (docs/49).
ingere "$RACINE/ingestion/amendements_vers_resulte_de.py" "$TRAVAIL/corpus/ameli" "$BASE" --noeuds
# DOLE ne lie pas le texte déposé d'un projet de loi ; son numéro se lit dans le
# rapport qui le rapporte, et les textes de commission dans la référence des
# amendements. Les deux plans sont chargés en une seule passe : ce script
# reconstruit `texte_discute`, une seconde passe effacerait la première.
DEPOSES="$RACINE/data/corpus/plan-textes-deposes-an.tsv"
python3 "$RACINE/tools/an/plan_textes_deposes.py" "$BASE" \
        "$TRAVAIL/corpus/rapports" "$DEPOSES"
python3 "$RACINE/tools/dila/telecharger_textes.py" "$DEPOSES" "$TRAVAIL/corpus/textes"
ingere "$RACINE/ingestion/textes_deposes.py" "$TRAVAIL/corpus/textes" "$TEXTES" \
        "$BASE" "$DEPOSES"
# `visees` vient après `porte_sur` depuis docs/43 : un numéro que le dispositif
# ne qualifie pas hérite du code hôte de l'article du texte, et c'est
# `porte_sur` qui le sait.
ingere "$RACINE/ingestion/visees.py" "$BASE"
# Après les deux chargeurs d'amendements et après `visees` : il lit les deux
# colonnes de sort des deux chambres, et la vue `tentative_sur_article` qu'il
# crée s'appuie sur `vise`.
ingere "$RACINE/ingestion/sort_des_amendements.py" "$BASE"
# Doit suivre `textes_deposes` — il lui faut `porte_sur` —, `visees` et
# `sort_des_amendements`, dont sa vue reprend les familles.
ingere "$RACINE/ingestion/textes_des_amendements.py" "$BASE"
# L'arête critique, en dernier des amendements : un amendement de l'Assemblée
# ne nomme pas le code, il nomme un alinéa du texte, et c'est `porte_sur` qui
# sait sous quel code cet alinéa est écrit.
ingere "$RACINE/ingestion/amendements_vers_resulte_de.py" "$TRAVAIL/corpus/ameli" "$BASE" --aretes
# Doit suivre les deux précédents : il lui faut les documents et `porte_sur`.
ingere "$RACINE/ingestion/sections_vers_motive.py" "$TRAVAIL/corpus/rapports" \
        "$PERIMETRE" "$RAPPORTS" "$BASE" "$IMPACTS"

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

ingere "$RACINE/ingestion/union_europeenne.py" "$BASE" "$CELEX" "$TITRES"

# Le « pourquoi » du droit de l'Union est dans ses considérants, publiés avec
# l'acte. EUR-Lex les rend en HTML structuré selon ELI ; le miroir est hors dépôt
# comme celui de la DILA, seul son manifeste est versionné.
EURLEX="$RACINE/data/raw/eurlex"
python3 "$RACINE/tools/ue/recuperer_actes.py" "$BASE" "$EURLEX"
ingere "$RACINE/ingestion/considerants.py" "$BASE" "$EURLEX"

# L'article de la directive que l'article du code transpose : les tableaux de
# concordance annexés aux études d'impact (docs/54). Après les considérants,
# qui chargent les articles des actes contre lesquels chaque ligne se vérifie.
ingere "$RACINE/ingestion/concordances.py" "$TRAVAIL/corpus/impacts" "$IMPACTS" "$BASE"

# --------------------------------------------------- 7. verdict et métriques
etape "7. Verdict et métriques d'hygiène"
ingere "$RACINE/ingestion/verdict.py" "$BASE"
ingere "$RACINE/tools/mesures/hygiene.py" "$BASE" "$PERIMETRE" \
        "$RACINE/data/mesures/hygiene.tsv"
# Les deux tableaux « au grain » du README, avec les définitions du verdict.
ingere "$RACINE/tools/mesures/grain.py" "$BASE" "$RACINE/data/mesures/grain.tsv"

# ------------------------------------------- 8. préparation de la lecture
etape "8. Index de lecture"
# En dernier, après toute écriture : ce sont les statistiques du planificateur
# qui font l'essentiel, et elles décrivent la base telle qu'elle est à la fin.
ingere "$RACINE/ingestion/index_de_lecture.py" "$BASE"

etape "Terminé"
echo "base : $BASE ($(du -h "$BASE" | cut -f1))"
echo "essai : python3 restitution/graphe.py $BASE L224-43"
