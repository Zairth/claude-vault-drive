#!/usr/bin/env bash
# claude-vault/scripts/vault-index.sh
# Indexation sémantique incrémentale via la porte en ligne de commande du
# moteur embarqué.
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
source "$script_directory/engine-env.sh"

# Blocs de callout tenus hors du texte vectorisé. `source` porte l'attribution
# d'une citation — auteur, pièce, ligne : de la plomberie, indispensable pour
# remonter à l'original et sans valeur sémantique. Mesuré sur un corpus réel :
# section médiane 221 caractères, bloc d'attribution 110, soit la moitié du
# vecteur en chemins et en chiffres. Un vecteur étant une moyenne, ce bloc tire
# tous les chunks d'une note vers une même direction et abîme la discrimination.
#
# Le moteur étant livré avec le plugin, l'option est toujours là : plus de
# sondage de capacité ni de repli — ce sont deux versions qui avancent
# ensemble, pas deux composants à accorder.
exclusion_options=(--exclude-callout source)

index_directory() {
    "${engine_run[@]}" index --dir "$1" "${exclusion_options[@]}"
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
