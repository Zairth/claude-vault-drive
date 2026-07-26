# Changelog — claude-vault-drive

Ce que contient chaque mise à jour du plugin : la raison en une ligne, puis le
détail des changements — de quoi savoir si elle vaut le coup avant de
l'installer. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/), versions en
[semver](https://semver.org/lang/fr/) (patch = fix/docs, minor = feature).

Installer une mise à jour : `/plugin marketplace update zairth_store` puis
`/reload-plugins` (le cache n'est invalidé que si la version change).

## [1.6.0] — 2026-07-26

**Raison de l'update** : sur un gros volume, l'ingestion saturait le contexte principal (source brute lue en session). `/doc-ingest` lit désormais la source dans un sub-agent lecteur — le contexte principal ne voit que les enseignements.

### Modifié
- `/doc-ingest` : la lecture de la source (fichier, URL, OCR de PDF) se fait
  dans un **sub-agent lecteur** qui ne retourne qu'un « dossier d'ingestion »
  (enseignements, citations ≤ 125 car., concepts/entités candidats,
  description INDEX) — jamais la source brute. Un texte bref passé en
  argument reste ingéré sans sub-agent (déjà en contexte).
- Validation conversationnelle : les retouches de fond sont relayées au même
  sub-agent via SendMessage (contexte, source comprise, conservé sur tous les
  allers-retours) ; sub-agent perdu → relance avec la source et le cumul des
  retours. L'écriture (wiki, INDEX, LOG, archivage, indexation) reste en
  contexte principal, à partir du seul dossier validé.

## [1.5.5] — 2026-07-26

**Raison de l'update** : la validation de `/doc-ingest` pouvait être présentée via un outil de question dont les options contenaient les enseignements — l'utilisateur validait sans avoir pu les lire.

### Corrigé
- `/doc-ingest` (validation conversationnelle) : les 2-5 enseignements clés
  doivent être écrits en clair dans le corps de la réponse avant toute demande
  d'accord ; un outil de question (AskUserQuestion ou équivalent) ne peut que
  recueillir l'accord, jamais porter le contenu.

## [1.5.4] — 2026-07-26

**Raison de l'update** : fin du renommage `.md` → `.md.txt` à l'archivage — les archives gardent leurs extensions d'origine. L'exclusion de l'index se fait proprement : seul `wiki/` est indexé, et l'index vit dans `wiki/.index/`.

### Modifié
- Périmètre d'indexation : `$VAULT/wiki` au lieu de `$VAULT` — `archives/`,
  `inbox/` et les fichiers racine (LOG, INDEX, INSTRUCTIONS) sortent de
  l'index par construction ; le filtre « bruit d'indexation » de `/doc-query`
  devient inutile (gardé en tolérance pour un index ≤ 1.5.3 pas encore
  reconstruit). L'index vit dans `wiki/.index/` (voyage toujours avec le
  vault) ; `vault-init.sh`, les wrappers CLI et les trois commandes `/doc-*`
  sont alignés.
- `/doc-ingest` : plus aucun renommage à l'archivage — un fichier archivé
  garde son nom et son extension.
- `/doc-lint` : un `.index/` à la racine du vault est signalé comme reliquat
  ≤ 1.5.3 (suppression proposée — dérivé jetable).

## [1.5.3] — 2026-07-26

**Raison de l'update** : `origine`/`original` pouvaient contenir un chemin absolu de la machine (`/home/...`) — mort avec la machine, vault plus auto-porteur. Toute pièce locale ingérée est désormais copiée dans `archives/` et référencée relativement au vault.

### Corrigé
- `/doc-ingest` (étape 5) : l'archivage vaut pour TOUT fichier local — venu
  d'`inbox/` → déplacé, venu d'ailleurs sur la machine → **copié** (l'original
  de l'utilisateur n'est jamais touché) ; PDF passé par OCR → le markdown OCR
  ET le PDF d'origine sont archivés. `origine:`/`original:` reçoivent ces
  chemins archivés relatifs au vault — jamais un chemin absolu de la machine.
- `vault-template/INSTRUCTIONS-CLAUDE.md` : modèle de note — `original`
  seulement si la pièce diffère de la copie pointée par `origine` (copie dans
  `archives/` ou emplacement durable : URL, dossier partagé) ; interdiction
  explicite des chemins absolus machine dans `origine`/`original`.

## [1.5.2] — 2026-07-25

**Raison de l'update** : le README ne disait pas par où commencer une fois le plugin installé — la section « Usage » ouvre maintenant sur `/vault-init` et le redémarrage de session obligatoire.

### Ajouté
- `README.md` : rappel en tête de « Usage » — première commande
  `/vault-init "/chemin/du/vault"`, puis relance de la session Claude Code
  (chargement de la permission `additionalDirectories`) avant les `/doc-*`.

## [1.5.1] — 2026-07-25

**Raison de l'update** : les synthèses apparaissaient déconnectées dans le graphe Obsidian — leurs références étaient des chemins bruts, qui ne créent pas de liens.

### Corrigé
- `/doc-query` : la section `## Références` des synthèses utilise des
  wikilinks `[[<slug>]]`, plus des chemins bruts.
- `vault-template/INSTRUCTIONS-CLAUDE.md` : règle explicite — toute référence
  inter-notes en wikilink, jamais en chemin brut (exceptions : `origine`/
  `original`, hors graphe voulu).

### Ajouté
- `README.md` : astuce vue graphique — colorer les nœuds par type via un
  groupe par dossier (`path:wiki/concepts`, etc.).

## [1.5.0] — 2026-07-25

**Raison de l'update** : modèle de note à frontmatter obligatoire — `type`, `date`, `auteur`, `origine` (sources), `question` (synthèses) — appliqué par `/doc-ingest`, vérifié par `/doc-lint`.

### Ajouté
- `vault-template/INSTRUCTIONS-CLAUDE.md` : section « Modèle de note » —
  propriétés obligatoires communes (`type`, `date` de création, `auteur`) et
  par type (`origine` + `original` optionnel pour les sources, `question` +
  `perimetre` optionnel pour les synthèses) ; propriétés libres autorisées en
  plus (ex. `image`, `capture_precedente`/`capture_suivante`), jamais en moins.
- `/doc-lint` : 7e vérification — notes de `wiki/` non conformes au modèle,
  avec proposition de valeurs déduites du contenu ou du LOG (jamais inventées
  sans le signaler).

### Modifié
- `/doc-ingest` et `/doc-query` (synthèses) : frontmatter aligné sur le modèle,
  `auteur` repéré dans les notes existantes ou demandé une fois.
- **Vaults existants** : le template ne s'applique qu'aux nouveaux vaults —
  reporter la section « Modèle de note » dans l'`INSTRUCTIONS-CLAUDE.md` de
  votre vault, puis `/doc-lint` mettra les notes en conformité.

## [1.4.3] — 2026-07-25

**Raison de l'update** : le rôle d'`archives/` documenté dans le README — principe « vault auto-porteur ».

### Ajouté
- `README.md`, section Principes : `inbox/` = sas, fichier ingéré déplacé vers
  `archives/` (immuable, hors index sémantique via renommage `.md.txt`, jamais
  supprimé), avertissement données sensibles avant partage.

## [1.4.2] — 2026-07-25

**Raison de l'update** : README aligné sur l'en-tête du changelog — installer une mise à jour = update **puis** `/reload-plugins`, cache invalidé seulement si la version change.

### Corrigé
- `README.md` : « manuelle en une seule étape » → la séquence complète
  (`/plugin marketplace update zairth_store` puis `/reload-plugins`), avec la
  condition d'invalidation du cache.

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
