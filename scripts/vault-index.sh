#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-index.sh
# Indexation sémantique incrémentale via la porte en ligne de commande
# d'agentic-toolbox.
#
# Sans argument : chaque dossier listé par vault-index-targets.sh est indexé
# dans SON propre `.index/embeddings.jsonl`. Sortie : un bloc `## <cible>` par
# dossier, suivi du rapport JSON du moteur.
# Avec un argument : ce dossier seul, rapport JSON brut.
#
# Ne revectorise que les chunks au hash inconnu ; réécrit l'index complet de
# chaque cible (la purge des vecteurs orphelins est automatique).
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/toolbox-env.sh"

index_directory() {
    local target_directory
    target_directory="$(cd "$1" && pwd)"  # absolu : on change de dossier juste après
    (cd "$toolbox_directory" && "${toolbox_run[@]}" index --dir "$target_directory")
}

if [[ $# -ge 1 && -n "${1:-}" ]]; then
    if [[ ! -d "$1" ]]; then
        echo "ERREUR : dossier à indexer introuvable : $1" >&2
        exit 1
    fi
    index_directory "$1"
    exit 0
fi

wiki_directory="$(bash "$script_directory/vault-check.sh")/wiki"
targets="$(bash "$script_directory/vault-index-targets.sh" "$wiki_directory")"
if [[ -z "$targets" ]]; then
    echo "ERREUR : aucun dossier à indexer sous $wiki_directory (wiki vide ?)" >&2
    exit 1
fi

# Une cible en échec n'annule pas les autres : on indexe tout ce qui peut
# l'être, puis on sort en échec — l'appelant sait alors que l'index est partiel
# (et /doc-query bascule sur son repli grep explicite).
failed_targets=0
while IFS= read -r target; do
    printf '## %s\n' "$target"
    index_directory "$wiki_directory/$target" || { failed_targets=$((failed_targets + 1)); echo "ERREUR : indexation échouée pour $target" >&2; }
done <<< "$targets"

(( failed_targets == 0 ))
