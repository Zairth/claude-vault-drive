# Changelog — claude-vault-drive

Ce que contient chaque mise à jour du plugin : la raison en une ligne, puis le
détail des changements — de quoi savoir si elle vaut le coup avant de
l'installer. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/), versions en
[semver](https://semver.org/lang/fr/) (patch = fix/docs, minor = feature).

Installer une mise à jour : `/plugin marketplace update zairth_store` puis
`/reload-plugins` (le cache n'est invalidé que si la version change).

## [1.4.1] — 2026-07-25

**Raison de l'update** : description du plugin réécrite — l'optimisation agentique (`context: fork`) mise en avant, alignée avec l'About du repo GitHub.

### Modifié
- `plugin.json` : la description mentionne l'exécution de `/doc-query` et
  `/doc-lint` en sub-agent isolé (zéro pollution du contexte principal).

## [1.4.0] — 2026-07-25

**Raison de l'update** : `/doc-query` et `/doc-lint` s'exécutent désormais entièrement dans un sub-agent (`context: fork`) — zéro pollution du contexte principal, préambule et notes compris.

### Modifié
- `/doc-query`, `/doc-lint` : frontmatter `context: fork` + `agent: Explore` +
  `background: false` — toute la commande (vault-check, lecture
  d'`INSTRUCTIONS-CLAUDE.md`, indexation, recherche, vérifications) tourne
  dans un sub-agent isolé ; seul le rapport final remonte. L'instruction
  « lancer un sub-agent » dans le corps des commandes devient inutile et
  disparaît.
- Les étapes interactives (proposer la sauvegarde en synthèse, valider les
  corrections de lint) restent en contexte principal : le rapport du fork se
  termine par un bloc « Pour l'agent principal » avec le chemin du vault
  résolu et les recettes exactes à appliquer après accord de l'utilisateur —
  un fork ne peut pas dialoguer.
- `/doc-ingest` inchangé : sa validation conversationnelle exige le contexte
  principal, un fork ne peut pas dialoguer avec l'utilisateur.
- `README.md` : principes et usage mis à jour (fork isolé).

## [1.3.2] — 2026-07-25

**Raison de l'update** : en-tête du changelog clarifié — il aide à décider d'*installer* une mise à jour, il n'invite pas à modifier le repo.

### Corrigé
- « Mise à jour côté consommateur » → « Installer une mise à jour » (même
  clarification dans le changelog d'agentic-toolbox).

## [1.3.1] — 2026-07-25

**Raison de l'update** : ce CHANGELOG — savoir pourquoi mettre à jour sans lire l'historique git.

### Ajouté
- `CHANGELOG.md` : une entrée par version, avec la raison de l'update.

## [1.3.0] — 2026-07-25

**Raison de l'update** : la stack fonctionne désormais **sans aucun clone** — les `/doc-*` utilisent les outils MCP du plugin agentic-toolbox en priorité.

### Modifié
- `/doc-query`, `/doc-ingest`, `/doc-lint` : cascade moteur — outils MCP
  (`mcp__plugin_agentic-toolbox_toolbox__semantic_index_build`,
  `…semantic_search`, `…semantic_info`, `…ocr_convert`) → wrappers CLI si
  clone local présent → repli grep explicite. Le dossier du vault est
  toujours passé **explicitement** aux outils MCP (celui du projet, via
  `vault-check.sh`) — jamais le `VAULT_PATH` global du plugin toolbox : un
  vault par projet, garanti.
- `PREREQUIS.md` section 5 : voie nominale = plugin agentic-toolbox + `uv`
  (clés saisies à l'installation), clone + venv relégué en alternative.
- `README.md` : « sans clone, sans service qui tourne » ; section recherche
  sémantique réécrite en deux portes d'entrée.

## [1.2.1] — 2026-07-25

**Raison de l'update** : docs d'installation alignées sur le marketplace dédié ; aucune config personnelle versionnée.

### Modifié
- Installation documentée via [Zairth/marketplace](https://github.com/Zairth/marketplace)
  (`/plugin marketplace add` en URL HTTPS — clonable anonymement, sans clé SSH).
- `.claude/settings.json` sorti du versioning (config par machine) ;
  `.claude/` et `CLAUDE.md` locaux gitignorés.

## [1.2.0] — 2026-07-25

**Raison de l'update** : le repo redevient un simple plugin — skill et catalogue vivent chez eux.

### Modifié
- Skill agentic-toolbox déplacé dans le repo
  [agentic-toolbox](https://github.com/Zairth/agentic-toolbox) (il vit avec le
  code qu'il documente) ; distribué via une entrée marketplace externe.
- Catalogue marketplace déménagé dans son propre dépôt Zairth/marketplace —
  plus de `marketplace.json` ici.

## [1.1.0] — 2026-07-25

**Raison de l'update** : le vault devient auto-porteur (`archives/`) et les wrappers acceptent les chemins relatifs.

### Ajouté
- `archives/` : `/doc-ingest` **déplace** le brut d'`inbox/` au lieu de le
  supprimer (`.md` renommé `.md.txt`, hors index sémantique) ; `vault-init.sh`
  crée le dossier.
- `PREREQUIS.md` (de la machine nue au vault), section Objectif du README,
  licence MIT.

### Corrigé
- Chemins relatifs : `vault-check.sh` imprime un chemin absolu, les wrappers
  résolvent leur cible avant le `cd` vers la toolbox.
- Piège WSL documenté : le vault vit côté Windows (`/mnt/...`), jamais dans le
  disque WSL (Obsidian plante en `EISDIR` sur `\\wsl.localhost\...`).

## [1.0.0] — 2026-07-25

**Raison de l'update** : première version distribuée en plugin Claude Code.

### Ajouté
- Conversion en plugin : manifeste `.claude-plugin/plugin.json`, commandes
  `/vault-init`, `/doc-ingest`, `/doc-query`, `/doc-lint`, scripts
  (`vault-check`, `vault-init`, `toolbox-env`, wrappers sémantiques),
  template de vault. Code dans le plugin, config dans chaque projet
  (`.claude/*.local` gitignorés) : un plugin, un vault par projet.
