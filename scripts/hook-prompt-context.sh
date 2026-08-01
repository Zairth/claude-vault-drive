#!/usr/bin/env bash
# claude-vault-drive/scripts/hook-prompt-context.sh
# Hook UserPromptSubmit : recherche LEXICALE (BM25) sur le prompt de
# l'utilisateur, quelques pistes injectées comme contexte. Ce sont des PISTES,
# pas une réponse — /doc-query reste la vraie recherche.
#
# Pourquoi le lexical et non le sémantique ici : ce hook se déclenche à CHAQUE
# prompt. Une recherche sémantique y coûterait un embedding à chaque fois, donc
# un poste de dépense permanent, et exigerait qu'un index ait déjà été
# construit. BM25 ne coûte rien, n'appelle aucune API, ne demande aucune clé et
# fonctionne dès le premier prompt d'un vault neuf. La contrepartie est connue
# et acceptée : il trouve le terme exact, pas la reformulation — c'est le métier
# de /doc-query, qui fait les deux.
#
# Toute condition manquante = sortie 0 silencieuse : projet sans vault, vault
# inaccessible, prompt court ou commande slash, moteur absent. Le hook ne doit
# jamais retarder ni polluer un prompt qu'il ne peut pas servir.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-.}"

[[ -f .claude/vault-path.local ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# Le prompt arrive dans le JSON du hook sur stdin (champ "prompt").
prompt="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("prompt",""))' 2>/dev/null)" || exit 0

# Filtres : commandes slash (/doc-query fait sa propre recherche), commandes
# shell (!), mémos (#), et prompts trop courts pour porter une intention
# cherchable (« oui », « vas-y », …).
case "$prompt" in
    /* | !* | \#* ) exit 0 ;;
esac
(( ${#prompt} >= 12 )) || exit 0

results="$(bash "$script_directory/vault-lexical.sh" "$prompt" "" 3 2>/dev/null)" || exit 0

printf '%s' "$results" | python3 -c '
import json, sys
try:
    groups = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(groups, list):
    sys.exit(0)

lines = []
for group in groups:
    layer = str(group.get("directory", "")).rstrip("/").rsplit("/", 1)[-1]
    for hit in (group.get("results") or [])[:2]:
        path = hit.get("relative_path", "?")
        excerpt = " ".join(str(hit.get("excerpt", "")).split())
        if len(excerpt) > 200:
            excerpt = excerpt[:200] + "\u2026"
        lines.append("- wiki/" + layer + "/" + str(path) + " : " + excerpt)

# Rien de pertinent, ou un corpus trop petit pour que BM25 discrimine : mieux
# vaut se taire que dinjecter du bruit sous chaque prompt.
if not lines:
    sys.exit(0)
print("Pistes du vault (recherche par mots-cles automatique sur ce prompt - des extraits, pas une reponse ; /doc-query pour une recherche complete et citee) :")
print("\n".join(lines[:6]))
'
