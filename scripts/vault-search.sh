#!/usr/bin/env bash
# claude-vault/scripts/vault-search.sh
# Recherche SÉMANTIQUE dans un ou tous les dossiers indexés de wiki/, via la
# porte en ligne de commande du moteur embarqué.
#
# Usage : vault-search.sh "question" [dossier] [top_k]
#   - dossier omis ou vide : toutes les cibles de vault-index-targets.sh, en UN
#     SEUL appel — la question n'est vectorisée qu'une fois quel que soit leur
#     nombre. C'est le seul coût API d'une recherche ;
#   - dossier fourni : ce dossier seul (cible `dans:`, ou périmètre restreint).
#
# Sortie : JSON [{directory, results: [{relative_path, section, score, excerpt}]}],
# un groupe par dossier, dans l'ordre demandé. `relative_path` est relatif au
# dossier de son groupe, pas à wiki/.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/engine-env.sh"

question="${1:?Usage : vault-search.sh \"question\" [dossier] [top_k]}"
requested_directory="${2:-}"
top_k="${3:-5}"

directory_arguments=()
if [[ -n "$requested_directory" ]]; then
    if [[ ! -d "$requested_directory" ]]; then
        echo "ERREUR : dossier de recherche introuvable : $requested_directory" >&2
        exit 1
    fi
    directory_arguments=(--dir "$requested_directory")
else
    wiki_directory="$(bash "$script_directory/vault-check.sh")/wiki"
    while IFS= read -r target; do
        [[ -n "$target" ]] || continue
        # Un dossier jamais indexé ferait échouer la recherche ENTIÈRE côté
        # moteur (il refuse un résultat partiel silencieux) : on ne lui passe
        # que les cibles qui ont bien leur index.
        [[ -f "$wiki_directory/$target/.index/embeddings.jsonl" ]] || continue
        directory_arguments+=(--dir "$wiki_directory/$target")
    done < <(bash "$script_directory/vault-index-targets.sh" "$wiki_directory")
    if (( ${#directory_arguments[@]} == 0 )); then
        echo "ERREUR : aucun index sous $wiki_directory — lancer l'indexation d'abord." >&2
        exit 1
    fi
fi

exec "${engine_run[@]}" search "$question" "${directory_arguments[@]}" --top-k "$top_k"
