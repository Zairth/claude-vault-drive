#!/usr/bin/env bash
# claude-vault/scripts/vault-index-targets.sh
# Liste les dossiers de wiki/ à indexer SÉPARÉMENT, un par ligne, en chemin
# relatif à wiki/. Usage : vault-index-targets.sh [chemin de wiki]
#
# Règle : un dossier = un index (`<dossier>/.index/embeddings.jsonl`), donc un
# espace vectoriel à lui. Les notes ne concourent qu'entre semblables : une
# note d'entité de dix lignes n'est plus écrasée par un extrait d'un texte
# intégral de trois cents. C'est une séparation structurelle, pas un réglage
# de score — et c'est ce qui permet de chercher dans une couche sans l'autre.
#
# Le nombre d'index ne dépend PAS du nombre de sources : trois couches de
# provenance (concepts, entites, syntheses) plus deux couches d'origine
# (enseignements, sources), constantes quelle que soit la taille du vault.
#
# Ordre = ordre de présentation des pistes : le synthétisé d'abord, le texte
# d'origine en dernier.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
wiki_directory="${1:-$(bash "$script_directory/vault-check.sh")/wiki}"
[[ -d "$wiki_directory" ]] || exit 0

for category in concepts entites syntheses enseignements sources; do
    compgen -G "$wiki_directory/$category/*.md" >/dev/null 2>&1 && printf '%s\n' "$category"
done

exit 0
