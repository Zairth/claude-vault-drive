#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-ocr.sh
# Conversion OCR d'un document en markdown, via la porte en ligne de commande
# d'agentic-toolbox — le repli quand l'outil MCP `ocr_convert` n'est pas
# disponible dans la session.
#
# Usage : vault-ocr.sh <fichier> [<markdown de sortie>]
# Sortie : le rapport JSON du moteur sur stdout.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/toolbox-env.sh"

document="${1:?Usage : vault-ocr.sh <fichier> [<markdown de sortie>]}"
if [[ ! -f "$document" ]]; then
    echo "ERREUR : fichier introuvable : $document" >&2
    exit 1
fi
document="$(cd "$(dirname "$document")" && pwd)/$(basename "$document")"  # absolu

output_arguments=()
[[ -n "${2:-}" ]] && output_arguments=(--out "$2")

cd "$toolbox_directory"
exec "${toolbox_run[@]}" convert "$document" "${output_arguments[@]}"
