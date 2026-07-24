# claude-vault-drive/scripts/toolbox-env.sh
# Résolution partagée du moteur sémantique agentic-toolbox : dossier + venv.
# Sourcé par vault-index.sh et vault-search.sh — définit `toolbox_directory`
# et `toolbox_python`, ou sort en échec explicite (l'appelant dégrade vers grep).
# Le dossier vient de $PWD/.claude/toolbox-path.local du projet courant
# (une ligne, non versionné), à défaut ~/projects/agentic-toolbox.

toolbox_path_file="$PWD/.claude/toolbox-path.local"
toolbox_directory="$HOME/projects/agentic-toolbox"
if [[ -f "$toolbox_path_file" ]]; then
    # Nettoie BOM UTF-8 en tête et CR/espaces en fin (fichier éditable depuis Windows).
    toolbox_directory="$(head -n 1 "$toolbox_path_file" | sed -e 's/^\xEF\xBB\xBF//' -e 's/[[:space:]]*$//')"
    if [[ -z "$toolbox_directory" ]]; then
        echo "ERREUR : .claude/toolbox-path.local est vide — y écrire le chemin d'agentic-toolbox (une seule ligne), ou supprimer le fichier pour utiliser ~/projects/agentic-toolbox." >&2
        exit 1
    fi
fi

toolbox_python="$toolbox_directory/.venv/bin/python"
if [[ ! -x "$toolbox_python" ]]; then
    echo "ERREUR : recherche sémantique indisponible — venv introuvable : $toolbox_python (cloner agentic-toolbox et créer son venv, ou écrire son chemin dans .claude/toolbox-path.local)." >&2
    exit 1
fi
