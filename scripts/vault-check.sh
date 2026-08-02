#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-check.sh
# Vérifie que le vault Obsidian est accessible et initialisé, puis imprime son
# chemin sur stdout. Échec explicite sinon — jamais de vault vide silencieux.
# Consommé par les commandes /doc-ingest, /doc-query, /doc-lint.
# La config vit dans le PROJET, pas dans le plugin : chaque projet a son
# propre vault.
#
# Le projet est désigné par CLAUDE_PROJECT_DIR, jamais par $PWD. Ce script est
# appelé depuis des sub-agents et des wrappers qui changent de dossier — un
# `cd` dans le moteur, une commande lancée depuis un autre chemin — et se
# fier au répertoire courant le faisait échouer alors que le vault était
# parfaitement accessible. Repli sur $PWD hors de Claude Code (appel manuel).
set -euo pipefail

vault_path_file="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/vault-path.local"

if [[ ! -f "$vault_path_file" ]]; then
    echo "ERREUR : fichier de config absent : ${CLAUDE_PROJECT_DIR:-$PWD}/.claude/vault-path.local — lancer vault-init.sh, ou y écrire le chemin du vault (une seule ligne)." >&2
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

# Toujours imprimer un chemin ABSOLU : les consommateurs (wrappers sémantiques)
# changent de dossier avant de s'en servir — un chemin relatif les casserait.
vault_path="$(cd "$vault_path" && pwd)"

if [[ ! -f "$vault_path/INSTRUCTIONS-CLAUDE.md" ]]; then
    echo "ERREUR : vault non initialisé : $vault_path ne contient pas INSTRUCTIONS-CLAUDE.md (lancer vault-init.sh, ou synchronisation incomplète)." >&2
    exit 1
fi

echo "$vault_path"
