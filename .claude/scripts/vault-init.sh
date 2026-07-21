#!/usr/bin/env bash
# claude-vault-drive/.claude/scripts/vault-init.sh
# Initialise tout en un appel : config locale + structure du vault + fichiers
# du template. Idempotent : ne remplace jamais un fichier déjà présent.
# Usage : bash .claude/scripts/vault-init.sh "/chemin/du/vault"
set -euo pipefail

if [[ $# -ne 1 || -z "${1:-}" ]]; then
    echo "Usage : bash .claude/scripts/vault-init.sh \"/chemin/du/vault\"" >&2
    exit 1
fi

vault_path="$1"
script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude_directory="$(cd "$script_directory/.." && pwd)"
project_root="$(cd "$claude_directory/.." && pwd)"
template_directory="$project_root/vault-template"

if [[ ! -d "$template_directory" ]]; then
    echo "ERREUR : vault-template/ introuvable à la racine du projet ($project_root) — lancer ce script depuis un clone de claude-vault-drive." >&2
    exit 1
fi

parent_directory="$(dirname "$vault_path")"
if [[ ! -d "$parent_directory" ]]; then
    echo "ERREUR : dossier parent introuvable : $parent_directory — Google Drive est-il lancé et monté ? (WSL : sudo mount -t drvfs <lettre>: /mnt/<lettre>)" >&2
    exit 1
fi

# Config locale — jamais écrasée si présente.
config_file="$claude_directory/vault-path.local"
if [[ ! -f "$config_file" ]]; then
    printf '%s\n' "$vault_path" > "$config_file"
    echo "OK : .claude/vault-path.local créé."
else
    echo "Conservé (déjà présent) : .claude/vault-path.local"
fi

settings_file="$claude_directory/settings.local.json"
if [[ ! -f "$settings_file" ]]; then
    printf '{\n  "permissions": {\n    "additionalDirectories": [\n      "%s"\n    ]\n  }\n}\n' "$vault_path" > "$settings_file"
    echo "OK : .claude/settings.local.json créé (relancer la session Claude Code pour charger la permission)."
else
    echo "Conservé (déjà présent) : .claude/settings.local.json — vérifier qu'il autorise bien : $vault_path"
fi

# Structure du vault.
mkdir -p "$vault_path/inbox" "$vault_path/wiki/sources" "$vault_path/wiki/concepts" \
         "$vault_path/wiki/entites" "$vault_path/wiki/syntheses" "$vault_path/.index"
echo "OK : arborescence du vault en place."

# Fichiers racine — jamais écrasés (un vault déjà vivant n'est pas touché).
for template_file in "$template_directory"/*.md; do
    target_file="$vault_path/$(basename "$template_file")"
    if [[ ! -f "$target_file" ]]; then
        cp "$template_file" "$target_file"
        echo "OK : $(basename "$template_file") copié."
    else
        echo "Conservé (déjà présent) : $(basename "$template_file")"
    fi
done

# Date du jour dans l'entrée init du LOG, si le placeholder est encore là.
log_file="$vault_path/LOG.md"
if grep -q '\[YYYY-MM-DD\] init' "$log_file"; then
    sed -i "s/\[YYYY-MM-DD\] init/[$(date +%F)] init/" "$log_file"
fi

# Vérification finale par le portier officiel.
bash "$script_directory/vault-check.sh" >/dev/null
echo ""
echo "✅ Vault initialisé et vérifié : $vault_path"
echo "→ Facultatif : ouvrir ce dossier comme coffre dans Obsidian (vitrine humaine)."
echo "→ Commandes disponibles : /doc-ingest, /doc-query, /doc-lint."
