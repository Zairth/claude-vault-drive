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

# Blocs de callout tenus hors du texte vectorisé. `source` porte l'attribution
# d'une citation — auteur, pièce, ligne : de la plomberie, indispensable pour
# remonter à l'original et sans valeur sémantique. Mesuré sur un corpus réel :
# section médiane 221 caractères, bloc d'attribution 110, soit la moitié du
# vecteur en chemins et en chiffres. Un vecteur étant une moyenne, ce bloc tire
# tous les chunks d'une note vers une même direction et abîme la discrimination.
#
# Le moteur ne l'accepte que depuis sa 4.7.0. Plus ancien : l'option est retirée
# de l'appel plutôt que de le faire échouer — l'indexation reste correcte, les
# blocs sont simplement vectorisés avec le reste. Une dégradation de qualité se
# rattrape en mettant le moteur à jour ; un index qu'on n'a pas pu construire,
# non.
excluded_callouts=(source)

# Détection UNE fois, pas à chaque dossier : chaque appel au moteur relance son
# environnement, et l'indexation en traite cinq à six.
exclusion_options=()
if (cd "$toolbox_directory" && "${toolbox_run[@]}" index --help 2>/dev/null \
        | grep -q -- "--exclude-callout"); then
    for callout in "${excluded_callouts[@]}"; do
        exclusion_options+=(--exclude-callout "$callout")
    done
else
    echo "NOTE : moteur antérieur à la 4.7.0 — les blocs d'attribution seront" >&2
    echo "       vectorisés avec le texte. L'index reste correct, la recherche" >&2
    echo "       un peu moins fine. Mettre à jour le plugin agentic-toolbox." >&2
fi

index_directory() {
    local target_directory
    target_directory="$(cd "$1" && pwd)"  # absolu : on change de dossier juste après
    (cd "$toolbox_directory" && "${toolbox_run[@]}" index --dir "$target_directory" \
        "${exclusion_options[@]}")
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
