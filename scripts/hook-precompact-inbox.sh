#!/usr/bin/env bash
# claude-vault-drive/scripts/hook-precompact-inbox.sh
# Hook PreCompact : avant que le compactage n'écrase la conversation, dépose sa
# partie textuelle (tours utilisateur/assistant, jamais les sorties d'outils)
# dans le sas inbox/ du vault, en note `type: session`. L'ingestion se fait
# plus tard, à froid, par /doc-ingest (extraire les décisions, brut archivé).
# Même session compactée plusieurs fois → même fichier, réécrit avec le
# transcript le plus complet. Toute condition manquante = sortie 0 silencieuse.
#
# Sécurité : le payload du hook reste sur stdin (jamais dans l'environnement ni
# en argument — argv est lisible par les autres processus) ; tout champ du
# payload servant au nom de fichier ou au frontmatter est filtré, et le chemin
# d'écriture est vérifié confiné à inbox/.
set -euo pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-.}"

[[ -f .claude/vault-path.local ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
vault="$(bash "$script_directory/vault-check.sh" 2>/dev/null)" || exit 0
[[ -d "$vault/inbox" ]] || exit 0

VAULT="$vault" PROJECT_NAME="$(basename "$PWD")" python3 -c "$(cat <<'PY'
import datetime, json, os, re, sys

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
transcript_path = payload.get("transcript_path", "")
if not isinstance(transcript_path, str) or not os.path.isfile(transcript_path):
    sys.exit(0)
# Le session_id sert au nom de fichier : ne garder que [A-Za-z0-9-].
session_id = re.sub(r"[^A-Za-z0-9-]", "", str(payload.get("session_id", "")))[:8] or "session"
trigger = "manuel" if payload.get("trigger") == "manual" else "auto"
# Une seule ligne propre dans le frontmatter, quel que soit le nom du dossier.
project_name = " ".join(str(os.environ.get("PROJECT_NAME", "?")).split())[:80] or "?"

turns = []
with open(transcript_path, encoding="utf-8", errors="replace") as f:
    for line in f:
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") not in ("user", "assistant"):
            continue
        message = entry.get("message") or {}
        role = message.get("role", entry["type"])
        content = message.get("content", "")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = "\n".join(
                block.get("text", "") for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        else:
            continue
        text = text.strip()
        # Écarte les tours purement outillés et les rappels système injectés.
        if not text or text.startswith("<system-reminder>") or text.startswith("<local-command-"):
            continue
        turns.append((role, text))

if not turns:
    sys.exit(0)

today = datetime.date.today().isoformat()
slug = f"session-{today}-{session_id}"
inbox = os.path.realpath(os.path.join(os.environ["VAULT"], "inbox"))
path = os.path.realpath(os.path.join(inbox, f"{slug}.md"))
if os.path.dirname(path) != inbox:
    sys.exit(0)
with open(path, "w", encoding="utf-8") as f:
    f.write(
        "---\n"
        "type: session\n"
        f"date: {today}\n"
        f"projet: {project_name}\n"
        f"declencheur: compactage {trigger}\n"
        "description: transcript de session Claude Code déposé avant compactage — à ingérer via /doc-ingest (n'en extraire que les décisions et faits durables)\n"
        "---\n\n"
    )
    for role, text in turns:
        heading = "Utilisateur" if role == "user" else "Claude"
        f.write(f"## {heading}\n\n{text}\n\n")
print(f"Transcript déposé : inbox/{slug}.md ({len(turns)} tours)")
PY
)"
