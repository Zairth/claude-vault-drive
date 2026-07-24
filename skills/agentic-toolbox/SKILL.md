---
name: agentic-toolbox
description: À utiliser dès qu'une tâche touche à agentic-toolbox (le moteur sémantique/OCR/LLM appelé par les commandes /doc-*) — recherche sémantique/embeddings, OCR de PDF ou d'images, routeur LLM multi-fournisseurs (mistral/gemini/openrouter/ollama) — pour obtenir les commandes exactes sans réexplorer le dépôt.
---

# agentic-toolbox — mode d'emploi

## Vue d'ensemble

Boîte à outils agentique (https://github.com/Zairth/agentic-toolbox) : trois
briques CLI (sorties JSON pour index/search/info, check et convert ; texte
lisible pour chat/embed ; échecs explicites `❌` + exit 1), zéro service qui
tourne. Dossier : `.claude/toolbox-path.local` du projet courant s'il existe,
sinon `~/projects/agentic-toolbox`.
**Invariant d'appel** : toujours depuis la racine de la toolbox, via son venv —

```bash
cd ~/projects/agentic-toolbox && .venv/bin/python -m <module> <commande> ...
```

Jamais le python système, jamais `pip install` local, jamais Docker (le
conteneur est une seconde porte d'entrée pour d'autres usages). Les clés API
vivent dans son `.env` (`MISTRAL_API_KEY`, etc. — jamais les lire ni les copier).

## Référence rapide

| Besoin | Module | Commandes |
|---|---|---|
| Recherche sémantique d'un dossier markdown | `services.semantic_index.cli_parser` | `index <dossier>` · `search "question" --dir <dossier> [--top-k 5]` · `info --dir <dossier>` (zéro réseau) |
| PDF/image → markdown (OCR) | `services.document_ocr.cli_parser` | `convert <fichier> [--output x.md]` — formats .pdf .png .jpg .jpeg .avif ; sortie écrasée si existante |
| État de la chaîne LLM (zéro réseau, zéro quota) | `providers.cli_parser` | `check` |
| Prompt via le routeur (fallback réel) | `providers.cli_parser` | `chat "prompt"` · `chat --provider gemini "prompt"` (un seul fournisseur, diagnostic) |
| Vectoriser un texte | `providers.cli_parser` | `embed --provider mistral "texte"` (`--provider` obligatoire) |

**Pour le vault du projet** : ne pas appeler `semantic_index` directement —
passer par les wrappers du plugin
`bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"` et
`bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-search.sh" "question"` (ils gèrent
venv, cd et chemin du vault).

## Pièges connus

- **Embeddings : jamais de fallback entre fournisseurs** (espaces vectoriels
  incomparables). Seul **mistral** a un modèle d'embedding dans la chaîne ;
  `embed --provider gemini` échoue. Fournisseur indisponible = échec explicite
  → dégrader vers grep, jamais vers un autre fournisseur.
- **OCR : mistral épinglé**, seul fournisseur OCR — indisponible = `❌` + exit 1,
  pas de plan B.
- **L'index sémantique vit DANS le dossier indexé** (`<dossier>/.index/embeddings.jsonl`)
  et son fournisseur/modèle est épinglé en ligne 1. Contrat incompatible →
  le moteur exige un rebuild complet (supprimer l'index), jamais de
  revectorisation silencieuse.
- **Chat a un fallback** (mistral → gemini → openrouter → ollama), c'est voulu ;
  seuls les embeddings et l'OCR n'en ont pas.
- `check` et `info` sont purement locaux : à utiliser librement pour
  diagnostiquer sans consommer de quota.
- Les logs (`INFO 🧮 ...`) sortent sur **stderr** : stdout est du JSON pur,
  parsable strictement (depuis le commit `97b2dac` — aucune parade `sed`
  nécessaire).
