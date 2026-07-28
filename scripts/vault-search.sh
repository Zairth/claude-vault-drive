#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-search.sh
# Recherche sémantique dans un ou plusieurs dossiers déjà indexés, via le venv
# d'agentic-toolbox.
#
# Usage : vault-search.sh "question" [dossier] [top_k]
#   - dossier omis ou vide : chaque cible de vault-index-targets.sh est
#     interrogée dans SON index, et la sortie est une suite de blocs
#     `## <cible>` suivis du JSON [{relative_path, section, score, excerpt}] ;
#     `relative_path` est relatif à la cible, pas à wiki/ — le préfixer par
#     `wiki/<cible>/` pour ouvrir et citer la note ;
#   - dossier fourni : ce dossier seul, JSON brut sur stdout (cible `dans:`,
#     ou recherche volontairement restreinte à une catégorie).
#
# Une recherche coûte un embedding de la question PAR index interrogé : c'est
# le prix de la séparation des espaces vectoriels. Balayer tout le wiki est
# donc un geste délibéré, pas un réflexe.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/toolbox-env.sh"

question="${1:?Usage : vault-search.sh \"question\" [dossier] [top_k]}"
requested_directory="${2:-}"
top_k="${3:-5}"

search_directory() {
    local target_directory
    target_directory="$(cd "$1" && pwd)"  # absolu : on change de dossier juste après
    (cd "$toolbox_directory" && "$toolbox_python" -m services.semantic_index.cli_parser search "$question" --dir "$target_directory" --top-k "$top_k")
}

if [[ -n "$requested_directory" ]]; then
    if [[ ! -d "$requested_directory" ]]; then
        echo "ERREUR : dossier de recherche introuvable : $requested_directory" >&2
        exit 1
    fi
    search_directory "$requested_directory"
    exit 0
fi

wiki_directory="$(bash "$script_directory/vault-check.sh")/wiki"
targets="$(bash "$script_directory/vault-index-targets.sh" "$wiki_directory")"
if [[ -z "$targets" ]]; then
    echo "ERREUR : aucun dossier indexable sous $wiki_directory (wiki vide ?)" >&2
    exit 1
fi

# Une cible sans index (jamais indexée, ou indexation partielle) est sautée en
# silence : la recherche reste utile sur les autres.
searched_targets=0
while IFS= read -r target; do
    [[ -f "$wiki_directory/$target/.index/embeddings.jsonl" ]] || continue
    printf '## %s\n' "$target"
    search_directory "$wiki_directory/$target" || echo "[]"
    searched_targets=$((searched_targets + 1))
done <<< "$targets"

if (( searched_targets == 0 )); then
    echo "ERREUR : aucun index sous $wiki_directory — lancer l'indexation d'abord." >&2
    exit 1
fi
