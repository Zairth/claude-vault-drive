#!/usr/bin/env bash
# claude-vault-drive/.claude/scripts/vault-check.sh
# Vérifie que le vault Obsidian est accessible et initialisé, puis imprime son
# chemin sur stdout. Échec explicite sinon — jamais de vault vide silencieux.
# Consommé par les commandes /doc-ingest, /doc-query, /doc-lint.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
vault_path_file="$script_directory/../vault-path.local"

if [[ ! -f "$vault_path_file" ]]; then
    echo "ERREUR : fichier de config absent : .claude/vault-path.local — y écrire le chemin du vault (une seule ligne)." >&2
    exit 1
fi

# Nettoie BOM UTF-8 en tête et CR/espaces en fin : le fichier peut être édité depuis Windows.
vault_path="$(head -n 1 "$vault_path_file" | sed -e 's/^\xEF\xBB\xBF//' -e 's/[[:space:]]*$//')"

if [[ -z "$vault_path" ]]; then
    echo "ERREUR : .claude/vault-path.local est vide — y écrire le chemin du vault (une seule ligne)." >&2
    exit 1
fi

if [[ ! -d "$vault_path" ]]; then
    echo "ERREUR : vault introuvable : $vault_path — le lecteur du vault est-il monté ? (Google Drive lancé ? sous WSL : sudo mount -t drvfs <lettre>: /mnt/<lettre>)" >&2
    exit 1
fi

if [[ ! -f "$vault_path/INSTRUCTIONS-CLAUDE.md" ]]; then
    echo "ERREUR : vault non initialisé : $vault_path ne contient pas INSTRUCTIONS-CLAUDE.md (copier les fichiers de vault-template/ à la racine du vault, ou synchronisation incomplète)." >&2
    exit 1
fi

echo "$vault_path"
