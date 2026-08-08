# claude-vault/scripts/engine-env.sh
# Résolution du moteur sémantique/OCR embarqué : son dossier, et la façon de
# l'invoquer. Sourcé par vault-index.sh, vault-search.sh et vault-lexical.sh —
# définit `engine_directory` et le tableau `engine_run`, ou sort en échec
# explicite (l'appelant dégrade alors vers grep).
#
# Pourquoi une porte en ligne de commande alors que le moteur expose déjà un
# serveur MCP : un hook Claude Code est un script shell. Pas de session, pas de
# client MCP — cette catégorie d'appelants ne peut structurellement pas passer
# par là. Le moteur expose `python -m cli` pour elle.

engine_env_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Le moteur vit DANS le plugin (engine/). Deux façons d'y arriver, et deux
# seulement : le plugin installé, ou un clone du dépôt — dans les deux cas le
# moteur est au même endroit relativement à ce script, donc une seule ligne
# suffit. `CLAUDE_PLUGIN_ROOT` reste préféré quand il est là : c'est la racine
# que Claude Code affirme, plutôt qu'une déduction depuis le chemin du script.
if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" && -f "$CLAUDE_PLUGIN_ROOT/engine/cli/__main__.py" ]]; then
    engine_directory="$CLAUDE_PLUGIN_ROOT/engine"
else
    engine_directory="$(cd "$engine_env_directory/../engine" 2>/dev/null && pwd)" || engine_directory=""
fi

if [[ -z "$engine_directory" || ! -f "$engine_directory/cli/__main__.py" ]]; then
    echo "ERREUR : moteur introuvable (attendu : <plugin>/engine/cli/__main__.py) — installation du plugin incomplète, réinstaller claude-vault." >&2
    exit 1
fi

# Invocation : `uv` résout les dépendances depuis requirements.txt et les met en
# cache — aucun venv à créer ni à maintenir dans le dossier du moteur, qui est
# de toute façon un cache que Claude Code réécrit à chaque mise à jour du
# plugin. C'est aussi la façon dont le plugin lance son serveur MCP.
if ! command -v uv >/dev/null 2>&1; then
    echo "ERREUR : 'uv' introuvable — nécessaire pour exécuter le moteur (voir PREREQUIS.md). Installation : curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# `PYTHONPATH` plutôt qu'un `cd` dans le moteur : `python -m cli` a besoin que le
# paquet `cli` soit importable, pas que le processus travaille depuis là. Se
# déplacer résoudrait les chemins RELATIFS reçus de l'appelant (un dossier à
# indexer, un `--out`) depuis le dossier du moteur — c'est-à-dire depuis le cache
# des plugins, que Claude Code réécrit à chaque mise à jour. Ainsi, le répertoire
# courant reste celui de l'appelant et ses chemins veulent dire ce qu'il croit.
engine_run=(env "PYTHONPATH=$engine_directory${PYTHONPATH:+:$PYTHONPATH}"
            uv run --quiet --with-requirements "$engine_directory/requirements.txt" python -m cli)
