#!/usr/bin/env bash
# claude-vault-drive/scripts/hook-prompt-context.sh
# Hook UserPromptSubmit : recherche sémantique directe (vault-search.sh, pas de
# fork) sur le prompt de l'utilisateur, top 3 injecté comme pistes de contexte.
# Ce sont des PISTES, pas une réponse — /doc-query reste la vraie recherche.
# Toute condition manquante = sortie 0 silencieuse : projet sans vault, vault
# inaccessible, prompt court ou commande slash, index jamais construit, moteur
# absent (pas de clone toolbox). Le hook ne doit jamais retarder ni polluer un
# prompt qu'il ne peut pas servir.
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

vault="$(bash "$script_directory/vault-check.sh" 2>/dev/null)" || exit 0
# Recherche seule, jamais d'indexation ici : un index absent signifie qu'aucun
# /doc-query n'a encore tourné — pas au hook de payer la construction.
[[ -f "$vault/wiki/.index/embeddings.jsonl" ]] || exit 0

results="$(bash "$script_directory/vault-search.sh" "$prompt" "$vault/wiki" 3 2>/dev/null)" || exit 0

printf '%s' "$results" | python3 -c '
import json, sys
try:
    hits = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(hits, list) or not hits:
    sys.exit(0)
print("Pistes du vault (recherche sémantique automatique sur ce prompt — des extraits, pas une réponse ; /doc-query pour une recherche complète et citée) :")
for hit in hits[:3]:
    path = hit.get("relative_path", "?")
    section = hit.get("section") or ""
    score = hit.get("score")
    excerpt = " ".join(str(hit.get("excerpt", "")).split())
    if len(excerpt) > 200:
        excerpt = excerpt[:200] + "…"
    where = f"wiki/{path}" + (f" § {section}" if section else "")
    note = f" ({score:.2f})" if isinstance(score, (int, float)) else ""
    print(f"- {where}{note} : {excerpt}")
'
