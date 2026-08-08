# mcp_server — le plugin Claude Code parle au moteur sans shell

LA porte d'entrée du projet : le plugin Claude Code lance ce serveur MCP en
stdio via `uv`, depuis sa propre copie du dépôt, et les briques métier
deviennent des outils structurés. Les clés arrivent en variables d'environnement
(`userConfig` du plugin) ; les défauts du code s'appliquent pour tout le reste.

## Fichiers

- **`server.py`** — l'instance FastMCP et les six outils : `semantic_index_build`
  et `semantic_info` (un dossier : `directory`), `semantic_search` et
  `lexical_search` (une LISTE de dossiers : `directories` — un groupe de
  résultats par dossier, jamais fusionnés), `ocr_convert`, `llm_check`. Le
  dossier cible est toujours obligatoire : le moteur n'a aucun dossier par
  défaut. `lexical_search` n'est **pas câblé** dans `semantic_search` — verdict
  de banc, pas attente : il n'atteint aucune cible que le vectoriel rate, et sert
  les questions ancrées sur un terme rare. `semantic_index_build` prend en option
  `excluded_callouts` : les types de bloc (`> [!TYPE]`, insensible à la casse) que
  l'appelant soustrait à la vectorisation — le bloc reste entier dans les résultats,
  seul le vecteur (donc le hash) l'ignore. `semantic_info` rend aussi `chunk_chars`
  (la granularité de découpe) et `excluded_callouts` (l'exclusion en vigueur) : de quoi
  constater sur quel texte chaque index a été bâti. Les erreurs métier
  remontent telles quelles (messages déjà explicites — contrat du projet).
- **`__main__.py`** — entrée stdio `python -m mcp_server` : importe le serveur
  et le lance, rien d'autre. stdout est réservé au JSON-RPC du protocole MCP.
  (Les valeurs `userConfig` vides ou non substituées sont normalisées par
  `Settings` — `core/settings.py` —, pas ici.)
