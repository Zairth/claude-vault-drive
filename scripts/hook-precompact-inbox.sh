#!/usr/bin/env bash
# claude-vault/scripts/hook-precompact-inbox.sh
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

# Masquage des secrets, AVANT écriture. Le hook dépose des tours de
# conversation dans un dossier synchronisé : un jeton collé dans un prompt y
# serait archivé tel quel, puis répliqué. Le détecter après coup (contrôle des
# identifiants en clair de /doc-lint) arrive trop tard — ici on l'empêche
# d'arriver.
#
# Le masquage est VOLONTAIREMENT trop large. L'asymétrie des erreurs est
# totale : un faux positif coûte un mot masqué dans un mémo de travail qu'on
# relira de toute façon à l'ingestion ; un faux négatif écrit un identifiant
# vivant dans un dossier répliqué. Dans le doute, masquer.
#
# Il ne garantit rien pour autant : un secret sans forme reconnaissable et sans
# nom de variable passe au travers. C'est une réduction de surface, pas une
# preuve — le contrôle de /doc-lint reste le filet derrière.
_MASK = "[secret masqué par le hook]"
_SECRET_NAME = (
    r"[A-Za-z0-9_.-]*"
    r"(?:TOKEN|SECRET|PASSWORD|PASSWD|PASSPHRASE|API[_-]?KEY|ACCESS[_-]?KEY|"
    r"PRIVATE[_-]?KEY|CREDENTIAL|CLIENT[_-]?SECRET|AUTH)"
    r"[A-Za-z0-9_.-]*"
)
# `(?!\[secret)` sur les motifs à préfixe conservé : sans lui, un motif
# masquerait la valeur déjà masquée par le précédent et empilerait les marques
# — les motifs se recouvrent volontairement, c'est le prix du « trop large ».
_SECRET_PATTERNS = [
    # NOM=valeur / NOM: valeur — la forme la plus fréquente (.env recopié).
    re.compile(rf"(?im)^(\s*(?:export\s+)?{_SECRET_NAME}\s*[:=]\s*).+$"),
    # En-tête d'autorisation, avant le motif générique qui capterait « AUTH ».
    re.compile(r"(?i)\b(authorization\s*:\s*(?:bearer|basic)\s+)(?!\[secret)\S+"),
    # La même forme NOM=valeur en ligne, entre guillemets ou non.
    re.compile(rf"(?i)\b({_SECRET_NAME}\s*[:=]\s*)(?!\[secret)(\"[^\"]*\"|'[^']*'|[^\s,;)}}\]]+)"),
    # Formes propres à un émetteur, reconnaissables sans nom de variable.
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bhf_[A-Za-z0-9]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    # Bloc de clé privée : tout le corps, pas seulement l'en-tête.
    re.compile(r"(?s)-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"),
]
masked_count = 0


def mask_secrets(text):
    """Remplace les valeurs sensibles, en gardant le NOM de la variable.

    Garder `DB_PASSWORD=` sans sa valeur préserve ce que le tour voulait dire —
    qu'il était question de cette configuration — sans en transporter le secret.
    """
    global masked_count
    for pattern in _SECRET_PATTERNS:
        replacement = (r"\1" + _MASK) if pattern.groups else _MASK
        text, count = pattern.subn(replacement, text)
        masked_count += count
    return text


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
        turns.append((role, mask_secrets(text)))

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
masked_note = f", {masked_count} secret(s) masqué(s)" if masked_count else ""
print(f"Transcript déposé : inbox/{slug}.md ({len(turns)} tours{masked_note})")
PY
)"
