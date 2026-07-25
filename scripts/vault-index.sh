#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-index.sh
# Indexation sémantique incrémentale d'un dossier de notes (défaut : le vault)
# via le venv d'agentic-toolbox. Ne revectorise que les chunks au hash inconnu ;
# réécrit l'index complet (la purge des vecteurs orphelins est automatique).
# Sortie : rapport JSON du moteur sur stdout. Échec explicite sinon.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/toolbox-env.sh"

target_directory="${1:-$(bash "$script_directory/vault-check.sh")}"
if [[ ! -d "$target_directory" ]]; then
    echo "ERREUR : dossier à indexer introuvable : $target_directory" >&2
    exit 1
fi
# Chemin absolu obligatoire : on change de dossier juste après.
target_directory="$(cd "$target_directory" && pwd)"

cd "$toolbox_directory"
exec "$toolbox_python" -m services.semantic_index.cli_parser index "$target_directory"
