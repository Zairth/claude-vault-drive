#!/usr/bin/env bash
# claude-vault-drive/scripts/hook-session-start.sh
# Hook SessionStart : injecte la carte du vault (INDEX.md) dans le contexte à
# l'ouverture de session — Claude sait d'emblée ce que le vault contient.
# Projet sans vault (.claude/vault-path.local absent) : sortie 0 silencieuse,
# le hook est invisible. Vault configuré mais inaccessible : une ligne
# d'avertissement (utile en début de session : Drive pas monté ?).
#
# Budget : au-delà d'environ 2 Ko, une sortie de hook n'est plus injectée
# telle quelle (le harnais n'en passe qu'un aperçu) — une troncature brute
# livrerait un fragment alphabétique arbitraire. Un INDEX volumineux est donc
# CONDENSÉ (les slugs seuls, sans les descriptions, équitablement répartis
# entre sections) : une carte complète vaut mieux qu'un début de carte.
set -euo pipefail

budget=1400

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-.}"

[[ -f .claude/vault-path.local ]] || exit 0

if ! vault="$(bash "$script_directory/vault-check.sh" 2>&1)"; then
    printf 'Vault du projet (plugin claude-vault-drive) : configuré mais inaccessible — %s\n' "$vault"
    exit 0
fi

index_file="$vault/INDEX.md"
[[ -f "$index_file" ]] || exit 0

printf 'Vault du projet (plugin claude-vault-drive) : %s\n' "$vault"
printf 'Sa carte ci-dessous — interroger via /doc-query, alimenter via /doc-ingest, maintenir via /doc-lint.\n\n'

if (( $(wc -c < "$index_file") <= budget )) || ! command -v python3 >/dev/null 2>&1; then
    head -c "$budget" "$index_file"
    if (( $(wc -c < "$index_file") > budget )); then
        printf '\n[carte tronquée — lire %s/INDEX.md en entier]\n' "$vault"
    fi
    exit 0
fi

INDEX_FILE="$index_file" VAULT="$vault" BUDGET="$budget" python3 -c "$(cat <<'PY'
import os, re, sys

budget = int(os.environ["BUDGET"])
sections, current = [], None
with open(os.environ["INDEX_FILE"], encoding="utf-8", errors="replace") as f:
    for line in f:
        heading = re.match(r"##\s+(.+)", line)
        if heading:
            current = (heading.group(1).strip(), [])
            sections.append(current)
            continue
        entry = re.match(r"\s*-\s*\[\[([^\]|#]+)", line)
        if entry and current is not None:
            current[1].append(entry.group(1).strip())

sections = [(title, slugs) for title, slugs in sections if slugs]
if not sections:
    sys.exit(1)  # structure inattendue : le shell reprend la main (troncature brute)

# Part égale par section, non consommée redistribuée aux suivantes.
out, remaining = [], budget - sum(len(t) + 4 for t, _ in sections)
for position, (title, slugs) in enumerate(sections):
    share = max(0, remaining // (len(sections) - position))
    kept, used = [], 0
    for slug in slugs:
        cost = len(slug) + 2
        if used + cost > share:
            break
        kept.append(slug)
        used += cost
    line = ", ".join(kept)
    hidden = len(slugs) - len(kept)
    if hidden:
        line = (line + ", " if kept else "") + f"(+{hidden} autres)"
    out.append(f"## {title}\n{line}")
    remaining -= used

print("\n".join(out))
print(f"\n[carte condensée : les titres seuls — descriptions et détail dans {os.environ['VAULT']}/INDEX.md]")
PY
)" || {
    head -c "$budget" "$index_file"
    printf '\n[carte tronquée — lire %s/INDEX.md en entier]\n' "$vault"
}
