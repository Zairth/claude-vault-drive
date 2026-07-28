#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-init.sh
# Initialise tout en un appel, POUR LE PROJET COURANT ($PWD) : config locale
# dans son .claude/, .gitignore complété, structure du vault + fichiers du
# template (embarqué dans le plugin). Idempotent : ne remplace jamais un
# fichier déjà présent.
# Usage (depuis la racine du projet) : bash <ce script> "/chemin/du/vault"
set -euo pipefail

if [[ $# -ne 1 || -z "${1:-}" ]]; then
    echo "Usage : bash vault-init.sh \"/chemin/du/vault\" (depuis la racine du projet)" >&2
    exit 1
fi

vault_path="$1"
script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_directory/.." && pwd)"
template_directory="$plugin_root/vault-template"
project_claude_directory="$PWD/.claude"

if [[ ! -d "$template_directory" ]]; then
    echo "ERREUR : vault-template/ introuvable dans le plugin ($plugin_root) — installation du plugin incomplète." >&2
    exit 1
fi

parent_directory="$(dirname "$vault_path")"
if [[ ! -d "$parent_directory" ]]; then
    echo "ERREUR : dossier parent introuvable : $parent_directory — Google Drive est-il lancé et monté ? (WSL : sudo mount -t drvfs <lettre>: /mnt/<lettre>)" >&2
    exit 1
fi

# Config locale du projet — jamais écrasée si présente.
mkdir -p "$project_claude_directory"

config_file="$project_claude_directory/vault-path.local"
if [[ ! -f "$config_file" ]]; then
    printf '%s\n' "$vault_path" > "$config_file"
    echo "OK : .claude/vault-path.local créé."
else
    echo "Conservé (déjà présent) : .claude/vault-path.local"
fi

settings_file="$project_claude_directory/settings.local.json"
if [[ ! -f "$settings_file" ]]; then
    printf '{\n  "permissions": {\n    "additionalDirectories": [\n      "%s"\n    ]\n  }\n}\n' "$vault_path" > "$settings_file"
    echo "OK : .claude/settings.local.json créé (relancer la session Claude Code pour charger la permission)."
else
    echo "Conservé (déjà présent) : .claude/settings.local.json — vérifier qu'il autorise bien : $vault_path"
fi

# .gitignore du projet : les fichiers locaux ne sont jamais versionnés.
gitignore_file="$PWD/.gitignore"
for ignore_line in ".claude/settings.local.json" ".claude/vault-path.local" ".claude/toolbox-path.local"; do
    if [[ ! -f "$gitignore_file" ]] || ! grep -qxF "$ignore_line" "$gitignore_file"; then
        printf '%s\n' "$ignore_line" >> "$gitignore_file"
        echo "OK : $ignore_line ajouté au .gitignore."
    fi
done

# Structure du vault.
# Chaque dossier de wiki/ porte son propre index (`<dossier>/.index/`) — il est
# créé par le moteur à la première indexation, pas ici. `transcriptions/` reste
# vide : ses notes vivent dans un sous-dossier par conversation, créé à
# l'ingestion.
mkdir -p "$vault_path/inbox" "$vault_path/archives" "$vault_path/LOG" \
         "$vault_path/wiki/sources" "$vault_path/wiki/transcriptions" \
         "$vault_path/wiki/concepts" "$vault_path/wiki/entites" \
         "$vault_path/wiki/syntheses"
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

# Journal : un fichier par jour dans LOG/. Entrée init écrite une seule fois,
# jamais dans un vault déjà vivant (LOG/ non vide, ou LOG.md hérité — gelé).
if [[ -z "$(ls -A "$vault_path/LOG")" && ! -f "$vault_path/LOG.md" ]]; then
    today="$(date +%F)"
    printf '## [%s] init | création du vault\n\nStructure initiale : INSTRUCTIONS-CLAUDE.md, INDEX.md, LOG/, inbox/, archives/,\nwiki/{sources,transcriptions,concepts,entites,syntheses}/ — un index sémantique\npar dossier de wiki/, construit à la première indexation.\n' \
        "$today" > "$vault_path/LOG/$today.md"
    echo "OK : LOG/$today.md créé (entrée init)."
fi

# Obsidian : exclure archives/ de son index. Obsidian avale TOUS les .md du
# vault (contrairement à l'index sémantique, limité à wiki/) — les markdown
# OCR archivés y référencent des images non extraites, qui apparaissent en
# nœuds fantômes dans le graphe ; un clic dessus crée une note vide à la
# racine. Fusion sans écrasement : les autres réglages sont préservés, et un
# `archives/` déjà présent n'est pas dupliqué.
# Le fichier est pris en compte même si Obsidian n'a jamais ouvert ce vault :
# il préserve un .obsidian/ existant à la première ouverture. Sans Obsidian,
# ces quelques octets sont inertes — le vault reste auto-porteur.
obsidian_config="$vault_path/.obsidian/app.json"
mkdir -p "$vault_path/.obsidian"
if [[ ! -f "$obsidian_config" ]]; then
    # Rien à préserver : écriture directe, sans dépendre de python3.
    printf '{\n  "userIgnoreFilters": [\n    "archives/"\n  ]\n}\n' > "$obsidian_config"
    echo "OK : archives/ exclu de l'index Obsidian (.obsidian/app.json créé)."
elif command -v python3 >/dev/null 2>&1; then
    if OBSIDIAN_CONFIG="$obsidian_config" python3 - <<'PY'
import json, os, sys
path = os.environ["OBSIDIAN_CONFIG"]
try:
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    if not isinstance(config, dict):
        sys.exit(1)
except Exception:
    sys.exit(1)  # config illisible ou personnalisée : ne rien toucher
filters = config.get("userIgnoreFilters", [])
if not isinstance(filters, list):
    sys.exit(1)
if "archives/" in filters:
    sys.exit(2)  # déjà exclu
filters.append("archives/")
config["userIgnoreFilters"] = filters
with open(path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
PY
    then
        echo "OK : archives/ exclu de l'index Obsidian (.obsidian/app.json) — si Obsidian est ouvert, le redémarrer."
    else
        status=$?
        (( status == 2 )) && echo "Conservé (déjà présent) : archives/ dans les exclusions Obsidian." \
                          || echo "Ignoré : .obsidian/app.json existant et non fusionnable — exclure archives/ à la main (Paramètres → Fichiers et liens → Fichiers exclus)."
    fi
else
    echo "Ignoré : .obsidian/app.json existant et python3 absent — exclure archives/ à la main (Paramètres → Fichiers et liens → Fichiers exclus)."
fi

# Vérification finale par le portier officiel.
bash "$script_directory/vault-check.sh" >/dev/null
echo ""
echo "✅ Vault initialisé et vérifié : $vault_path"
echo "→ Facultatif : ouvrir ce dossier comme coffre dans Obsidian (vitrine humaine)."
echo "→ Commandes disponibles : /doc-ingest, /doc-query, /doc-lint."
