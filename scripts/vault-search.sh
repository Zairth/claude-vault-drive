#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-search.sh
# Recherche sémantique dans un dossier déjà indexé (défaut : le vault) via le
# venv d'agentic-toolbox. Usage : vault-search.sh "question" [dossier] [top_k]
# Sortie : JSON [{relative_path, section, score, excerpt}] sur stdout.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/toolbox-env.sh"

question="${1:?Usage : vault-search.sh \"question\" [dossier] [top_k]}"
target_directory="${2:-$(bash "$script_directory/vault-check.sh")/wiki}"
if [[ ! -d "$target_directory" ]]; then
    echo "ERREUR : dossier de recherche introuvable : $target_directory" >&2
    exit 1
fi
# Chemin absolu obligatoire : on change de dossier juste après.
target_directory="$(cd "$target_directory" && pwd)"
top_k="${3:-5}"

cd "$toolbox_directory"
exec "$toolbox_python" -m services.semantic_index.cli_parser search "$question" --dir "$target_directory" --top-k "$top_k"
