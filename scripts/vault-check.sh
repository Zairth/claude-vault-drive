#!/usr/bin/env bash
# claude-vault/scripts/vault-check.sh
# Vérifie que le vault Obsidian est accessible et initialisé, puis imprime son
# chemin sur stdout. Échec explicite sinon — jamais de vault vide silencieux.
# Consommé par les commandes /doc-ingest, /doc-query, /doc-lint.
# La config vit dans le PROJET, pas dans le plugin : chaque projet a son
# propre vault.
#
# Le projet est désigné par CLAUDE_PROJECT_DIR, jamais par $PWD. Ce script est
# appelé depuis des sub-agents et des wrappers qui changent de dossier — un
# `cd` dans le moteur, une commande lancée depuis un autre chemin — et se
# fier au répertoire courant le faisait échouer alors que le vault était
# parfaitement accessible. Repli sur $PWD hors de Claude Code (appel manuel).
set -euo pipefail

# Recherche ASCENDANTE depuis le point de départ. CLAUDE_PROJECT_DIR n'est pas
# toujours défini — certains sub-agents ne le propagent pas — et le répertoire
# courant peut être un sous-dossier du projet. Remonter jusqu'à la racine règle
# les deux cas d'un coup, et coûte quelques `test -f`.
find_vault_path_file() {
    local directory="$1"
    while [[ -n "$directory" && "$directory" != "/" ]]; do
        if [[ -f "$directory/.claude/vault-path.local" ]]; then
            printf '%s\n' "$directory/.claude/vault-path.local"
            return 0
        fi
        directory="$(dirname "$directory")"
    done
    return 1
}

start_directory="${CLAUDE_PROJECT_DIR:-$PWD}"
if ! vault_path_file="$(find_vault_path_file "$start_directory")"; then
    echo "ERREUR : fichier de config introuvable : aucun .claude/vault-path.local depuis $start_directory ni au-dessus. Ce projet n'a pas de vault (lancer vault-init.sh), ou l'appel vient d'un dossier étranger au projet — définir CLAUDE_PROJECT_DIR, ou appeler depuis le projet." >&2
    exit 1
fi

# Nettoie BOM UTF-8 en tête et CR/espaces en fin : le fichier peut être édité depuis Windows.
vault_path="$(head -n 1 "$vault_path_file" | sed -e 's/^\xEF\xBB\xBF//' -e 's/[[:space:]]*$//')"

if [[ -z "$vault_path" ]]; then
    echo "ERREUR : .claude/vault-path.local est vide — y écrire le chemin du vault (une seule ligne)." >&2
    exit 1
fi

if [[ ! -d "$vault_path" ]]; then
    echo "ERREUR : vault introuvable : $vault_path" >&2
    # C'est ce portier-là qui parle après un redémarrage de WSL : le lecteur
    # n'est plus monté, et il rejette TOUTES les commandes jusqu'à ce qu'on le
    # remonte. Autant rendre la commande copiable telle quelle, avec la bonne
    # lettre, plutôt qu'un modèle à compléter.
    # Le montage exige root : ce script ne le fait pas, il ne peut pas — pas de
    # terminal pour un mot de passe — et ce n'est pas son rôle. Il diagnostique.
    if [[ "$vault_path" =~ ^/mnt/([a-z])(/|$) ]]; then
        mount_point="/mnt/${BASH_REMATCH[1]}"
        drive="$(printf '%s' "${BASH_REMATCH[1]}" | tr 'a-z' 'A-Z'):"
        if ! grep -q " $mount_point " /proc/mounts 2>/dev/null; then
            echo "  → $mount_point n'est pas monté (le montage ne survit pas à un redémarrage de WSL)." >&2
            if grep -qE "^[^#]*[[:space:]]$mount_point[[:space:]]" /etc/fstab 2>/dev/null; then
                echo "     sudo mount -a        ($mount_point est dans /etc/fstab : le montage a échoué au démarrage, souvent parce que le lecteur n'était pas encore lancé)" >&2
            else
                echo "     sudo mount -t drvfs $drive $mount_point" >&2
            fi
        else
            echo "  → $mount_point est monté : vérifier que le dossier du vault existe toujours (déplacé, renommé, synchronisation en cours ?)." >&2
        fi
    else
        echo "  → le lecteur du vault est-il monté et le dossier toujours en place ?" >&2
    fi
    exit 1
fi

# Toujours imprimer un chemin ABSOLU : les consommateurs (wrappers sémantiques)
# changent de dossier avant de s'en servir — un chemin relatif les casserait.
vault_path="$(cd "$vault_path" && pwd)"

if [[ ! -f "$vault_path/INSTRUCTIONS-CLAUDE.md" ]]; then
    echo "ERREUR : vault non initialisé : $vault_path ne contient pas INSTRUCTIONS-CLAUDE.md (lancer vault-init.sh, ou synchronisation incomplète)." >&2
    exit 1
fi

echo "$vault_path"
