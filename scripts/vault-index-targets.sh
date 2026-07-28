#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-index-targets.sh
# Liste les dossiers de wiki/ à indexer SÉPARÉMENT, un par ligne, en chemin
# relatif à wiki/. Usage : vault-index-targets.sh [chemin de wiki]
#
# Règle : un dossier de savoir = un index (`<dossier>/.index/embeddings.jsonl`),
# donc un espace vectoriel à lui. Les notes ne concourent qu'entre semblables :
# une entité de dix lignes n'est plus écrasée par un extrait d'une source de
# trois cents. C'est une séparation structurelle, pas un réglage de score.
#
# `transcriptions/` est VOLONTAIREMENT absent — ses notes ne sont pas
# vectorisées. Raison : ce qu'on demande à un corpus de messages est presque
# toujours exhaustif (« tous les messages qui… »), or un index rend les K
# meilleurs résultats, jamais l'ensemble des résultats qualifiants. Il faut
# donc lire les conversations en entier — et dès lors qu'on lit tout, l'ordre
# de lecture ne change plus le résultat : les vecteurs ne garantissent rien
# que la lecture ne garantisse déjà. On les atteint autrement, sans coût ni
# envoi de l'intégralité des conversations au fournisseur d'embeddings :
#   - le condensé de `sources/`, lui vectorisé, désigne quelle conversation
#     ouvrir et pointe dessus en wikilink ;
#   - le grep, exact et local, sur ce qu'on cherche vraiment dans des messages
#     (un nom, une date, un terme) ;
#   - la lecture intégrale du dossier, seule garantie d'exhaustivité.
# Réversible : la structure en un dossier par conversation supporte les deux,
# il suffirait d'ajouter ces dossiers ici pour les indexer.
#
# Ordre = ordre de présentation des pistes : le synthétisé d'abord, le brut
# ensuite.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
wiki_directory="${1:-$(bash "$script_directory/vault-check.sh")/wiki}"
[[ -d "$wiki_directory" ]] || exit 0

for category in concepts entites syntheses sources; do
    compgen -G "$wiki_directory/$category/*.md" >/dev/null 2>&1 && printf '%s\n' "$category"
done

exit 0
