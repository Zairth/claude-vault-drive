#!/usr/bin/env bash
# claude-vault-drive/scripts/vault-init.sh
# Initialise tout en un appel, POUR LE PROJET COURANT ($PWD) : config locale
# dans son .claude/, .gitignore complété, structure du vault + fichiers du
# template (embarqué dans le plugin). Idempotent : ne remplace jamais un
# fichier déjà présent.
# Usage (depuis la racine du projet) : bash <ce script> "/chemin/du/vault"
set -euo pipefail

if [[ $# -ne 1 || -z "${1:-}" ]]; then
    echo "Usage : bash vault-init.sh \"/chemin/du/vault\" (depuis la racine du projet)" >&2
    exit 1
fi

vault_path="$1"

# Chemin Windows collé tel quel (`G:\Mon Drive\...`) → forme POSIX. C'est le
# geste naturel de qui lit le chemin dans l'explorateur, et sans conversion il
# ne produit AUCUNE erreur : la chaîne ne contient pas un seul `/`, donc
# `dirname` rend `.`, le contrôle du dossier parent passe, et `mkdir -p` crée
# un dossier dont le NOM contient les antislashs, au milieu du projet. Le
# script annonce alors « vault initialisé » sur un vault qui n'est pas là où
# l'utilisateur croit.
if [[ "$vault_path" =~ ^([A-Za-z]):[\\/](.*)$ ]]; then
    drive_letter="$(printf '%s' "${BASH_REMATCH[1]}" | tr 'A-Z' 'a-z')"
    windows_path="$vault_path"
    vault_path="/mnt/$drive_letter/${BASH_REMATCH[2]//\\//}"
    echo "Note : chemin Windows converti — $windows_path → $vault_path"
fi

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_directory/.." && pwd)"
template_directory="$plugin_root/vault-template"
project_claude_directory="$PWD/.claude"

# Le projet et le vault confondus : ça fonctionne — le portier remonte
# l'arborescence pour trouver `vault-path.local` —, mais la config locale part
# alors sur le dossier synchronisé. Or elle ne contient QUE des chemins propres
# à cette machine : l'emplacement du vault, et celui du cache des plugins. Un
# second poste synchronisant ce vault les recevrait faux, et les deux machines
# se disputeraient le même fichier. Prévenir, sans rien empêcher : le montage
# est légitime pour qui travaille seul.
if [[ "$(cd "$PWD" && pwd -P)" == "$(cd "$vault_path" 2>/dev/null && pwd -P || echo '')" ]]; then
    echo "Note : le projet EST le vault — la config locale (.claude/) vivra donc dans le dossier synchronisé." >&2
    echo "  Elle ne porte que des chemins propres à cette machine : un autre poste les recevrait faux." >&2
    echo "  Sans conséquence si vous êtes seul dessus ; sinon, initialiser depuis un dossier de projet distinct." >&2
fi

if [[ ! -d "$template_directory" ]]; then
    echo "ERREUR : vault-template/ introuvable dans le plugin ($plugin_root) — installation du plugin incomplète." >&2
    exit 1
fi

parent_directory="$(dirname "$vault_path")"
if [[ ! -d "$parent_directory" ]]; then
    echo "ERREUR : dossier parent introuvable : $parent_directory" >&2
    # Cas de loin le plus fréquent : le vault vit sur un lecteur Windows que
    # WSL n'a pas monté. Le diagnostic est mécanique, autant le poser et
    # rendre les commandes copiables telles quelles plutôt que de laisser un
    # `<lettre>` à compléter.
    # Ce script n'écrit JAMAIS hors du projet et du vault : monter un lecteur
    # et éditer /etc/fstab demandent root, touchent toute la machine et ne
    # concernent que WSL. C'est une décision d'administration, elle revient à
    # l'utilisateur — on la lui prépare, on ne la prend pas à sa place.
    if [[ "$vault_path" =~ ^/mnt/([a-z])(/|$) ]]; then
        mount_letter="${BASH_REMATCH[1]}"
        mount_point="/mnt/$mount_letter"
        drive="$(printf '%s' "$mount_letter" | tr 'a-z' 'A-Z'):"
        if ! mountpoint -q "$mount_point" 2>/dev/null && ! grep -q " $mount_point " /proc/mounts 2>/dev/null; then
            echo "  → $mount_point n'est pas monté. Le lecteur $drive est-il lancé côté Windows ?" >&2
            if grep -qE "^[^#]*[[:space:]]$mount_point[[:space:]]" /etc/fstab 2>/dev/null; then
                echo "     $mount_point figure déjà dans /etc/fstab — le montage a dû échouer au démarrage :" >&2
                echo "       sudo mount -a" >&2
            else
                # Le point de montage est un dossier ordinaire du disque WSL :
                # créé une fois, il persiste. Ne proposer `mkdir` que s'il
                # manque vraiment — après un redémarrage, seul le montage est
                # à refaire, et une commande superflue fait douter de tout le
                # reste du diagnostic.
                if [[ -d "$mount_point" ]]; then
                    echo "     Monter maintenant :   sudo mount -t drvfs $drive $mount_point" >&2
                else
                    echo "     Monter maintenant :   sudo mkdir -p $mount_point && sudo mount -t drvfs $drive $mount_point" >&2
                fi
                echo "     Rendre permanent :    echo '$drive $mount_point drvfs defaults 0 0' | sudo tee -a /etc/fstab" >&2
                echo "     (root requis : à lancer vous-même — ce script n'écrit que dans le projet et le vault.)" >&2
            fi
            echo "  Puis relancer cette commande." >&2
            exit 1
        fi
    fi
    echo "  → vérifier le chemin, ou créer le dossier parent." >&2
    exit 1
fi

# Config locale du projet — jamais écrasée si présente.
mkdir -p "$project_claude_directory"

config_file="$project_claude_directory/vault-path.local"
if [[ ! -f "$config_file" ]]; then
    printf '%s\n' "$vault_path" > "$config_file"
    echo "OK : .claude/vault-path.local créé."
else
    # « Ne jamais écraser » protège une config valide. Appliqué à une config
    # CASSÉE, ça interdit de la réparer : relancer la commande avec le bon
    # chemin conservait l'ancien et échouait sur « vault introuvable », sans
    # dire que le chemin conservé était le coupable. Un chemin enregistré qui
    # ne désigne aucun dossier n'est pas une préférence à respecter.
    recorded_path="$(tr -d '\r' < "$config_file" | head -1 | sed 's/[[:space:]]*$//')"
    if [[ "$recorded_path" == "$vault_path" ]]; then
        echo "Conservé (identique) : .claude/vault-path.local"
    elif [[ -d "$recorded_path" ]]; then
        echo "Conservé (déjà présent, et le dossier existe) : .claude/vault-path.local → $recorded_path" >&2
        echo "  Pour le remplacer par $vault_path, supprimer ce fichier et relancer." >&2
    else
        printf '%s\n' "$vault_path" > "$config_file"
        echo "OK : .claude/vault-path.local corrigé — l'ancien chemin ne désignait aucun dossier ($recorded_path)."
    fi
fi

# Deux permissions, dans le fichier LOCAL (jamais versionné, et le chemin du
# plugin dépend de la machine) :
#   - additionalDirectories : l'accès au vault, hors du projet ;
#   - allow : les scripts du plugin, sans quoi chaque commande se fait refuser
#     ses appels un par un et dégrade au lieu de tourner. Le joker sur la
#     version évite d'avoir à refaire ça à chaque mise à jour.
# Périmètre volontairement étroit : ce dossier de scripts, rien d'autre. Ils
# lisent le vault ; seul vault-index.sh y écrit, dans les `.index/`, qui sont
# des dérivés régénérables.
settings_file="$project_claude_directory/settings.local.json"
# Racine du plugin déduite de l'emplacement de CE script, jamais de
# `CLAUDE_PLUGIN_ROOT` seule. La commande invoque
# `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-init.sh"` : le chemin est
# **substitué dans la ligne de commande**, donc le script le reçoit en
# argument — mais la variable, elle, n'est PAS dans son environnement. S'y fier
# faisait sauter les règles `allow` sans le moindre message, et laissait les
# commandes se faire refuser leurs scripts un par un.
# `$script_directory` est calculé depuis `BASH_SOURCE`, donc toujours juste.
plugin_root="${CLAUDE_PLUGIN_ROOT:-$(dirname "$script_directory")}"
# .../<plugin>/<version>/scripts → .../<plugin>/*/scripts, pour survivre aux
# mises à jour. Hors cache versionné, on garde le chemin tel quel.
if [[ "$(basename "$plugin_root")" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    plugin_scripts_glob="$(dirname "$plugin_root")/*/scripts/*"
else
    plugin_scripts_glob="$plugin_root/scripts/*"
fi

if command -v python3 >/dev/null 2>&1 \
   && SETTINGS_FILE="$settings_file" VAULT_PATH="$vault_path" \
      SCRIPTS_GLOB="$plugin_scripts_glob" python3 "$script_directory/merge-permissions.py"; then
    echo "OK : .claude/settings.local.json — accès au vault et scripts du plugin autorisés (relancer la session Claude Code pour les charger)."
elif [[ ! -f "$settings_file" ]]; then
    printf '{\n  "permissions": {\n    "additionalDirectories": [\n      "%s"\n    ]\n  }\n}\n' "$vault_path" > "$settings_file"
    echo "OK : .claude/settings.local.json créé (fusion indisponible : autoriser à la main les scripts du plugin si les commandes se font refuser leurs appels)."
else
    echo "Conservé (déjà présent) : .claude/settings.local.json — y autoriser à la main : $vault_path, et les scripts du plugin." >&2
fi

# .gitignore du projet : les fichiers locaux ne sont jamais versionnés.
gitignore_file="$PWD/.gitignore"
for ignore_line in ".claude/settings.local.json" ".claude/vault-path.local" ".claude/toolbox-path.local"; do
    if [[ ! -f "$gitignore_file" ]] || ! grep -qxF "$ignore_line" "$gitignore_file"; then
        printf '%s\n' "$ignore_line" >> "$gitignore_file"
        echo "OK : $ignore_line ajouté au .gitignore."
    fi
done

# Structure du vault.
# Chaque dossier de wiki/ porte son propre index (`<dossier>/.index/`) — il est
# créé par le moteur à la première indexation, pas ici.
mkdir -p "$vault_path/inbox" "$vault_path/archives" "$vault_path/LOG" \
         "$vault_path/wiki/sources" "$vault_path/wiki/enseignements" \
         "$vault_path/wiki/concepts" "$vault_path/wiki/entites" \
         "$vault_path/wiki/syntheses"
echo "OK : arborescence du vault en place."

# Fichiers racine — jamais écrasés (un vault déjà vivant n'est pas touché).
for template_file in "$template_directory"/*.md; do
    target_file="$vault_path/$(basename "$template_file")"
    if [[ ! -f "$target_file" ]]; then
        cp "$template_file" "$target_file"
        echo "OK : $(basename "$template_file") copié."
    else
        echo "Conservé (déjà présent) : $(basename "$template_file")"
    fi
done

# Journal : un fichier par jour dans LOG/. Entrée init écrite une seule fois,
# jamais dans un vault déjà vivant (LOG/ non vide, ou LOG.md hérité — gelé).
if [[ -z "$(ls -A "$vault_path/LOG")" && ! -f "$vault_path/LOG.md" ]]; then
    today="$(date +%F)"
    printf '## [%s] init | création du vault\n\nStructure initiale : INSTRUCTIONS-CLAUDE.md, INDEX.md, LOG/, inbox/, archives/,\nwiki/{sources,enseignements,concepts,entites,syntheses}/ — un index sémantique\npar dossier de wiki/, construit à la première indexation.\n' \
        "$today" > "$vault_path/LOG/$today.md"
    echo "OK : LOG/$today.md créé (entrée init)."
fi

# Obsidian : exclure archives/ ET inbox/ de son index. Obsidian avale TOUS les
# .md du vault (contrairement à l'index sémantique, limité à wiki/), or ces
# deux dossiers ne contiennent pas de savoir : `archives/` garde les pièces
# d'origine — dont des markdown OCR qui référencent des images non extraites,
# lesquelles apparaissent en nœuds fantômes dans le graphe, et un clic dessus
# crée une note vide à la racine — et `inbox/` n'est qu'un sas de matière brute
# en attente, y compris les dépôts automatiques de fin de session. Les laisser
# indexés fait apparaître dans le graphe des nœuds qui ne sont pas des notes.
# Fusion sans écrasement : les autres réglages sont préservés, et un filtre
# déjà présent n'est pas dupliqué.
# Le fichier est pris en compte même si Obsidian n'a jamais ouvert ce vault :
# il préserve un .obsidian/ existant à la première ouverture. Sans Obsidian,
# ces quelques octets sont inertes — le vault reste auto-porteur.
obsidian_config="$vault_path/.obsidian/app.json"
mkdir -p "$vault_path/.obsidian"
if [[ ! -f "$obsidian_config" ]]; then
    # Rien à préserver : écriture directe, sans dépendre de python3.
    printf '{\n  "userIgnoreFilters": [\n    "archives/",\n    "inbox/"\n  ]\n}\n' > "$obsidian_config"
    echo "OK : archives/ et inbox/ exclus de l'index Obsidian (.obsidian/app.json créé)."
elif command -v python3 >/dev/null 2>&1; then
    if OBSIDIAN_CONFIG="$obsidian_config" python3 - <<'PY'
import json, os, sys
path = os.environ["OBSIDIAN_CONFIG"]
try:
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    if not isinstance(config, dict):
        sys.exit(1)
except Exception:
    sys.exit(1)  # config illisible ou personnalisée : ne rien toucher
filters = config.get("userIgnoreFilters", [])
if not isinstance(filters, list):
    sys.exit(1)
missing = [wanted for wanted in ("archives/", "inbox/") if wanted not in filters]
if not missing:
    sys.exit(2)  # déjà exclus
filters.extend(missing)
config["userIgnoreFilters"] = filters
with open(path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
PY
    then
        echo "OK : archives/ et inbox/ exclus de l'index Obsidian (.obsidian/app.json) — si Obsidian est ouvert, le redémarrer."
    else
        status=$?
        (( status == 2 )) && echo "Conservé (déjà présent) : archives/ et inbox/ dans les exclusions Obsidian." \
                          || echo "Ignoré : .obsidian/app.json existant et non fusionnable — exclure archives/ et inbox/ à la main (Paramètres → Fichiers et liens → Fichiers exclus)."
    fi
else
    echo "Ignoré : .obsidian/app.json existant et python3 absent — exclure archives/ et inbox/ à la main (Paramètres → Fichiers et liens → Fichiers exclus)."
fi

# Couleurs du graphe : une par dossier de wiki/. Sans ça, tous les nœuds se
# ressemblent et le graphe ne dit rien — c'est le seul réglage d'Obsidian qui
# rende la structure du vault visible d'un coup d'œil.
# `graph.json` porte AUSSI les réglages personnels (zoom, forces, filtres) :
# on n'y touche que si `colorGroups` est vide. Des groupes déjà définis sont
# un choix de l'utilisateur, pas un défaut à écraser.
graph_config="$vault_path/.obsidian/graph.json"
if command -v python3 >/dev/null 2>&1; then
    if GRAPH_CONFIG="$graph_config" python3 - <<'PY'
import json, os, sys
path = os.environ["GRAPH_CONFIG"]
groups = [
    ("path:wiki/sources",       0x5B8DEF),  # bleu    — texte intégral
    ("path:wiki/enseignements", 0x3DA35D),  # vert    — ce qu'on retient
    ("path:wiki/concepts",      0xE8A33D),  # ambre   — notions
    ("path:wiki/entites",       0xA45BD6),  # violet  — personnes, outils
    ("path:wiki/syntheses",     0xE05C5C),  # rouge   — réponses
]
config = {}
if os.path.exists(path):
    try:
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
        if not isinstance(config, dict):
            sys.exit(1)
    except Exception:
        sys.exit(1)  # illisible : ne rien toucher
    if config.get("colorGroups"):
        sys.exit(2)  # l'utilisateur a ses propres groupes
config["colorGroups"] = [{"query": q, "color": {"a": 1, "rgb": c}} for q, c in groups]
with open(path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
PY
    then
        echo "OK : graphe Obsidian coloré par dossier (.obsidian/graph.json) — si Obsidian est ouvert, le redémarrer."
    else
        status=$?
        (( status == 2 )) && echo "Conservé (déjà présent) : groupes de couleurs du graphe Obsidian." \
                          || echo "Ignoré : .obsidian/graph.json illisible — colorer à la main (Paramètres du graphe → Groupes)."
    fi
else
    echo "Ignoré : python3 absent — colorer le graphe à la main (Paramètres du graphe → Groupes, une requête path:wiki/<dossier> par dossier)."
fi

# Vérification finale par le portier officiel.
bash "$script_directory/vault-check.sh" >/dev/null
echo ""
echo "✅ Vault initialisé et vérifié : $vault_path"
echo "→ Facultatif : ouvrir ce dossier comme coffre dans Obsidian (vitrine humaine)."
echo "→ Commandes disponibles : /doc-ingest, /doc-query, /doc-lint, /doc-repair."
echo "→ Instrument facultatif : /doc-bench (mesurer la qualité de recherche — rien ne l'exige)."
