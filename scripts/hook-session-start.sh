#!/usr/bin/env bash
# claude-vault-drive/scripts/hook-session-start.sh
# Hook SessionStart : injecte INDEX.md (la carte du vault) dans le contexte à
# l'ouverture de session — Claude sait d'emblée ce que le vault contient.
# Projet sans vault (.claude/vault-path.local absent) : sortie 0 silencieuse,
# le hook est invisible. Vault configuré mais inaccessible : une ligne
# d'avertissement (utile en début de session : Drive pas monté ?).
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-.}"

[[ -f .claude/vault-path.local ]] || exit 0

if ! vault="$(bash "$script_directory/vault-check.sh" 2>&1)"; then
    printf 'Vault du projet (plugin claude-vault-drive) : configuré mais inaccessible — %s\n' "$vault"
    exit 0
fi

index_file="$vault/INDEX.md"
[[ -f "$index_file" ]] || exit 0

printf 'Vault du projet (plugin claude-vault-drive) : %s\n' "$vault"
printf 'Sa carte INDEX.md ci-dessous — interroger via /doc-query, alimenter via /doc-ingest, maintenir via /doc-lint.\n\n'
# Garde-fou taille : l'INDEX est une ligne par note, il tient normalement très
# en dessous de 16 Ko — au-delà, tronquer plutôt que gonfler chaque session.
head -c 16384 "$index_file"
if (( $(wc -c < "$index_file") > 16384 )); then
    printf '\n[INDEX.md tronqué à 16 Ko — lire %s/INDEX.md pour la suite]\n' "$vault"
fi
