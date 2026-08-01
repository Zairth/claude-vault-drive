#!/usr/bin/env bash
# claude-vault-drive/scripts/hook-prompt-context.sh
# Hook UserPromptSubmit : recherche LEXICALE (BM25) sur le prompt de
# l'utilisateur, quelques pistes injectées comme contexte. Ce sont des PISTES,
# pas une réponse — /doc-query reste la vraie recherche.
#
# Pourquoi le lexical et non le sémantique ici : ce hook se déclenche à CHAQUE
# prompt. Une recherche sémantique y coûterait un embedding à chaque fois, donc
# un poste de dépense permanent, et exigerait qu'un index ait déjà été
# construit. BM25 ne coûte rien, n'appelle aucune API, ne demande aucune clé et
# fonctionne dès le premier prompt d'un vault neuf. La contrepartie est connue
# et acceptée : il trouve le terme exact, pas la reformulation — c'est le métier
# de /doc-query, qui fait les deux.
#
# Toute condition manquante = sortie 0 silencieuse : projet sans vault, vault
# inaccessible, prompt court ou commande slash, moteur absent. Le hook ne doit
# jamais retarder ni polluer un prompt qu'il ne peut pas servir.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-.}"

[[ -f .claude/vault-path.local ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# Le prompt arrive dans le JSON du hook sur stdin (champ "prompt").
prompt="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("prompt",""))' 2>/dev/null)" || exit 0

# Filtres : commandes slash (/doc-query fait sa propre recherche), commandes
# shell (!), mémos (#), et prompts trop courts pour porter une intention
# cherchable (« oui », « vas-y », …).
case "$prompt" in
    /* | !* | \#* ) exit 0 ;;
esac
(( ${#prompt} >= 12 )) || exit 0

vault="$(bash "$script_directory/vault-check.sh" 2>/dev/null)" || exit 0

# Porte de vocabulaire, AVANT d'appeler le moteur — et c'est le seul filtre
# qui marche. Mesuré : le score BM25 ne distingue PAS une question sur le vault
# d'une phrase de conversation. « je fais quoi maintenant du coup » y score plus
# haut que « qui détient quelle part du capital », parce qu'un mot rare et hors
# sujet pèse autant qu'un mot rare et pertinent. Aucun seuil, aucun rapport de
# scores ne sépare les deux — vérifié sur un corpus réel.
#
# Ce qui les sépare, c'est le VOCABULAIRE : une question sur le vault emploie
# les mots de ses notes. On exige donc qu'au moins un mot long du prompt
# figure dans `INDEX.md` ET y soit CARACTÉRISTIQUE — présent dans au plus un
# dixième des entrées. Ce plafond relatif se recalcule sur l'INDEX du moment :
# rien à régler, et il écarte les mots que le vault emploie partout (« travail »
# dans un vault de travail) sans écarter ceux qui le désignent (« leaver »).
# Local, gratuit, et exécuté avant tout appel au moteur.
index_file="$vault/INDEX.md"
[[ -f "$index_file" ]] || exit 0
INDEX_FILE="$index_file" PROMPT="$prompt" python3 -c '
import collections, os, re, sys, unicodedata

def fold(text):
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")

def long_words(text):
    return set(re.findall(r"[a-z0-9]{5,}", fold(text)))

entries = [line for line in open(os.environ["INDEX_FILE"], encoding="utf-8").read().splitlines()
           if line.startswith("- [[")]
if not entries:
    sys.exit(1)
frequency = collections.Counter()
for entry in entries:
    frequency.update(long_words(entry))
ceiling = max(1, len(entries) // 10)
sys.exit(0 if any(0 < frequency[w] <= ceiling for w in long_words(os.environ["PROMPT"])) else 1)
' 2>/dev/null || exit 0

results="$(bash "$script_directory/vault-lexical.sh" "$prompt" "" 3 2>/dev/null)" || exit 0

printf '%s' "$results" | python3 -c '
import json, sys
try:
    groups = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(groups, list):
    sys.exit(0)

hits = []
for group in groups:
    layer = str(group.get("directory", "")).rstrip("/").rsplit("/", 1)[-1]
    for hit in (group.get("results") or []):
        score = hit.get("score")
        if isinstance(score, (int, float)):
            hits.append((float(score), layer, hit))
if not hits:
    sys.exit(0)
hits.sort(key=lambda h: h[0], reverse=True)

# Trois pistes au plus : ce hook propose, il ne repond pas. Le score BM25 sert
# a ordonner, jamais a filtrer — mesure : il ne distingue pas une question
# pertinente dune phrase de conversation.
lines = []
for score, layer, hit in hits[:3]:
    excerpt = " ".join(str(hit.get("excerpt", "")).split())
    if len(excerpt) > 160:
        excerpt = excerpt[:160] + "\u2026"
    lines.append("- wiki/" + layer + "/" + str(hit.get("relative_path", "?")) + " : " + excerpt)

print("Pistes du vault (mots-cles, automatique — des extraits, pas une reponse ; /doc-query pour une recherche complete et citee) :")
print("\n".join(lines))
'
