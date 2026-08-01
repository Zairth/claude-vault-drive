#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-lexical.sh
# Recherche LEXICALE (BM25) dans un ou tous les dossiers de wiki/, via la porte
# en ligne de commande d'agentic-toolbox.
#
# Usage : vault-lexical.sh "question" [dossier] [top_k]
#
# Complémentaire du sémantique, pas concurrent : celui-ci trouve le terme exact
# — nom propre, référence, identifiant — et pondère par IDF, donc un mot présent
# dans la moitié du corpus n'y pèse presque rien. Le sémantique, lui, trouve les
# reformulations.
#
# Trois propriétés qui le rendent utilisable là où le sémantique ne l'est pas :
# **aucun appel API**, **aucun index préalable** (il se construit en mémoire à
# la requête et se jette), et il fonctionne sur un dossier en lecture seule.
# C'est ce qui en fait la couche des appelants déclenchés souvent.
#
# Réserve : BM25 a besoin d'un corpus pour vouloir dire quelque chose. Sur
# quelques fichiers, l'IDF s'écrase et le classement ne discrimine plus rien.
#
# Sortie : JSON [{directory, results: [{relative_path, score, excerpt}]}].
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_directory/toolbox-env.sh"

question="${1:?Usage : vault-lexical.sh \"question\" [dossier] [top_k]}"
requested_directory="${2:-}"
top_k="${3:-5}"

directory_arguments=()
if [[ -n "$requested_directory" ]]; then
    if [[ ! -d "$requested_directory" ]]; then
        echo "ERREUR : dossier de recherche introuvable : $requested_directory" >&2
        exit 1
    fi
    directory_arguments=(--dir "$requested_directory")
else
    wiki_directory="$(bash "$script_directory/vault-check.sh")/wiki"
    while IFS= read -r target; do
        [[ -n "$target" ]] || continue
        directory_arguments+=(--dir "$wiki_directory/$target")
    done < <(bash "$script_directory/vault-index-targets.sh" "$wiki_directory")
    if (( ${#directory_arguments[@]} == 0 )); then
        echo "ERREUR : aucune note sous $wiki_directory — rien à chercher." >&2
        exit 1
    fi
fi

cd "$toolbox_directory"
exec "${toolbox_run[@]}" lexical "$question" "${directory_arguments[@]}" --top-k "$top_k"
