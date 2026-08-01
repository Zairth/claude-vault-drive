# claude-vault-drive/scripts/toolbox-env.sh
# Résolution partagée du moteur agentic-toolbox : son dossier, et la façon de
# l'invoquer. Sourcé par vault-index.sh, vault-search.sh et vault-lexical.sh —
# définit `toolbox_directory` et le tableau `toolbox_run`, ou sort en échec
# explicite (l'appelant dégrade alors vers grep).
#
# Pourquoi une porte en ligne de commande alors que le moteur est un serveur
# MCP : un hook Claude Code est un script shell. Pas de session, pas de client
# MCP — cette catégorie d'appelants ne peut structurellement pas passer par là.
# Le moteur expose `python -m cli` pour elle depuis sa 4.1.0.

# Ordre de résolution, du plus explicite au plus implicite.
_resolve_toolbox_directory() {
    # 1. Chemin imposé par le projet (une ligne, non versionné).
    local path_file="$PWD/.claude/toolbox-path.local"
    if [[ -f "$path_file" ]]; then
        # Nettoie BOM UTF-8 en tête et CR/espaces en fin (fichier éditable depuis Windows).
        local declared
        declared="$(head -n 1 "$path_file" | sed -e 's/^\xEF\xBB\xBF//' -e 's/[[:space:]]*$//')"
        [[ -n "$declared" ]] && { printf '%s\n' "$declared"; return 0; }
    fi

    local marketplace_root cache_root newest candidate
    if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
        # 2. Le plugin agentic-toolbox installé À CÔTÉ de celui-ci dans le cache
        #    des plugins — le cas normal. Déduit de CLAUDE_PLUGIN_ROOT plutôt que
        #    codé en dur sur ~/.claude : si Claude Code déplace son cache, ceci
        #    suit. Plusieurs versions y cohabitent, on prend la plus haute.
        marketplace_root="$(cd "$CLAUDE_PLUGIN_ROOT/../.." 2>/dev/null && pwd)" || marketplace_root=""
        if [[ -n "$marketplace_root" && -d "$marketplace_root/agentic-toolbox" ]]; then
            newest="$(ls -1 "$marketplace_root/agentic-toolbox" 2>/dev/null | sort -V | tail -n 1)"
            [[ -n "$newest" ]] && { printf '%s\n' "$marketplace_root/agentic-toolbox/$newest"; return 0; }
        fi
        # 3. Installé depuis une AUTRE place de marché que celle-ci.
        cache_root="$(cd "$CLAUDE_PLUGIN_ROOT/../../.." 2>/dev/null && pwd)" || cache_root=""
        if [[ -n "$cache_root" ]]; then
            candidate="$(ls -1d "$cache_root"/*/agentic-toolbox/*/ 2>/dev/null | sort -V | tail -n 1)"
            [[ -n "$candidate" ]] && { printf '%s\n' "${candidate%/}"; return 0; }
        fi
    fi

    # 4. Clone local, pour qui développe le moteur.
    printf '%s\n' "$HOME/projects/agentic-toolbox"
}

toolbox_directory="$(_resolve_toolbox_directory)"

if [[ ! -f "$toolbox_directory/cli/__main__.py" ]]; then
    echo "ERREUR : moteur agentic-toolbox introuvable ou trop ancien (attendu : $toolbox_directory/cli/__main__.py) — installer le plugin agentic-toolbox en 4.1.0 ou plus, ou écrire le chemin de son clone dans .claude/toolbox-path.local." >&2
    exit 1
fi

# Invocation : `uv` résout les dépendances depuis requirements.txt et les met en
# cache — aucun venv à créer ni à maintenir dans le dossier du moteur, qui est
# de toute façon un cache que Claude Code réécrit à chaque mise à jour du
# plugin. C'est aussi la façon dont le moteur lance son propre serveur MCP.
if ! command -v uv >/dev/null 2>&1; then
    echo "ERREUR : 'uv' introuvable — nécessaire pour exécuter le moteur agentic-toolbox (voir PREREQUIS.md). Installation : curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

toolbox_run=(uv run --quiet --with-requirements "$toolbox_directory/requirements.txt" python -m cli)
