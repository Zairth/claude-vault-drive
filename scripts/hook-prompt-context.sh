#!/usr/bin/env bash
# claude-vault/scripts/hook-prompt-context.sh
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

# Le payload du hook n'arrive qu'UNE FOIS sur stdin : on en tire le prompt et
# l'identifiant de session en une seule lecture, séparés par une tabulation.
payload="$(python3 -c 'import json,re,sys
d = json.load(sys.stdin)
session = re.sub(r"[^A-Za-z0-9-]", "", str(d.get("session_id", "")))[:16]
print(session + "\t" + str(d.get("prompt", "")).replace("\t", " "))' 2>/dev/null)" || exit 0
session_id="${payload%%$'\t'*}"
prompt="${payload#*$'\t'}"

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

# Mémoire de session : une note déjà proposée ne l'est plus. Ce hook se
# déclenche à chaque prompt, et sur un sujet suivi il remonte les mêmes trois
# notes à chaque fois — trois questions sur la même pièce réinjectaient trois
# fois les mêmes extraits. Ce n'est pas le volume qui gêne (200 jetons par
# déclenchement, sous le bruit) mais la redondance : du contexte périmé qui
# reste et concurrence le reste pour l'attention.
# Fichier hors du projet et hors du vault — il n'a aucune valeur au delà de la
# session et ne doit polluer ni l'un ni l'autre.
#
# Il se nettoie lui-même : à chaque passage, les mémoires de plus de sept jours
# sont supprimées. Pas de hook de fin de session pour ça — il n'y en a pas qui
# se déclenche de façon fiable à la fermeture, et compter sur le nettoyage de
# /tmp par le système reviendrait à ne rien garantir du tout. Sept jours et non
# un : une session peut être reprise le lendemain, et retrouver sa mémoire est
# le comportement voulu. Purge silencieuse, jamais bloquante.
seen_file=""
if [[ -n "$session_id" ]]; then
    seen_directory="${TMPDIR:-/tmp}"
    # Deux familles de résidus : les mémoires de pistes (celles de ce hook) et
    # les fichiers de suite écrits par les commandes en fork. Même règle, même
    # raison — aucun hook ne se déclenche de façon fiable à la fermeture d'une
    # session, donc c'est le prochain usage qui balaie.
    find "$seen_directory" -maxdepth 1 -type f \
        \( -name 'claude-vault-pistes-*' -o -name 'claude-vault-suite-*' \) \
        -mtime +7 -delete 2>/dev/null || true
    seen_file="$seen_directory/claude-vault-pistes-$session_id"
fi

printf '%s' "$results" | SEEN_FILE="$seen_file" python3 -c '
import json, os, sys
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

# Les trois meilleures, et elles seules. Puis on retire celles deja proposees
# dans cette session. Si les trois sont deja connues, on SE TAIT — descendre
# au rang 4 ou 7 pour avoir quelque chose a dire reviendrait a proposer du
# bruit sous pretexte de ne pas rester muet. Ce hook propose, il ne comble pas.
seen_file = os.environ.get("SEEN_FILE") or ""
seen = set()
if seen_file and os.path.isfile(seen_file):
    try:
        seen = set(open(seen_file, encoding="utf-8").read().split("\n"))
    except Exception:
        seen = set()
hits = [h for h in hits[:3]
        if (h[1] + "/" + str(h[2].get("relative_path", "?"))) not in seen]
if not hits:
    sys.exit(0)

# Trois pistes au plus : ce hook propose, il ne repond pas. Le score BM25 sert
# a ordonner, jamais a filtrer — mesure : il ne distingue pas une question
# pertinente dune phrase de conversation.
lines = []
retenues = []
for score, layer, hit in hits[:3]:
    retenues.append(layer + "/" + str(hit.get("relative_path", "?")))
    excerpt = " ".join(str(hit.get("excerpt", "")).split())
    if len(excerpt) > 160:
        excerpt = excerpt[:160] + "\u2026"
    lines.append("- wiki/" + layer + "/" + str(hit.get("relative_path", "?")) + " : " + excerpt)

if seen_file:
    try:
        with open(seen_file, "a", encoding="utf-8") as f:
            f.write("\n".join(retenues) + "\n")
    except Exception:
        pass

print("Pistes du vault (mots-cles, automatique — des extraits, pas une reponse ; /doc-query pour une recherche complete et citee) :")
print("\n".join(lines))
'
