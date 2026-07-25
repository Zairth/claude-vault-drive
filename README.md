# claude-vault-drive

Un vault Obsidian partagé (Google Drive ou tout dossier synchronisé), consultable
et maintenu par Claude Code — distribué comme **plugin Claude Code** : s'installe
en deux commandes dans n'importe quel projet, **sans MCP, sans service qui
tourne**. Le vault n'est que des fichiers markdown dans un dossier : Obsidian est
la vitrine humaine (graphe, wikilinks), Claude Code y accède directement.

## Objectif

Combiné à [agentic-toolbox](https://github.com/Zairth/agentic-toolbox), ce
plugin fait naître le fameux **deuxième cerveau de Claude** : une mémoire
externe durable et partagée, optimisée par **orchestration agentique**
(sub-agents qui explorent le vault sans jamais saturer le contexte principal)
et par des **skills** pour la recherche sémantique et l'OCR.

Le cas d'usage type : brancher un projet sur son dossier Drive — Claude le
**consomme** (`/doc-query` répond en citant les notes) et l'**alimente en
retour** (`/doc-ingest`, synthèses persistées) au fur et à mesure des
itérations de sessions sur ce projet. Le savoir s'accumule d'une session à
l'autre au lieu de disparaître avec le contexte, et reste lisible par les
humains dans Obsidian.

## Ce que contient ce repo

Le repo est à la fois le plugin et son propre marketplace :

```
claude-vault-drive/
├── .claude-plugin/
│   ├── plugin.json          # manifeste du plugin
│   └── marketplace.json     # le repo est son propre marketplace (source "./")
├── PREREQUIS.md             # de la machine nue au vault : WSL, Claude Code, Drive, toolbox
├── commands/
│   ├── vault-init.md        # /vault-init — initialiser le vault du projet courant
│   ├── doc-ingest.md        # /doc-ingest — ingérer une source (validation conversationnelle)
│   ├── doc-query.md         # /doc-query — interroger le vault (sub-agent, réponse citée)
│   └── doc-lint.md          # /doc-lint — maintenance (orphelins, INDEX, conflits Drive, vecteurs)
├── skills/
│   └── agentic-toolbox/
│       └── SKILL.md         # mode d'emploi du moteur sémantique/OCR/LLM (commandes exactes, pièges)
├── scripts/
│   ├── vault-check.sh       # portier : vérifie l'accès au vault, imprime son chemin
│   ├── vault-init.sh        # initialisation du vault en une commande, idempotente
│   ├── toolbox-env.sh       # résolution du moteur sémantique (dossier + venv)
│   ├── vault-index.sh       # indexation sémantique incrémentale du vault
│   └── vault-search.sh      # recherche sémantique dans un dossier indexé
└── vault-template/          # fichiers copiés à la racine d'un nouveau vault
    ├── INSTRUCTIONS-CLAUDE.md   # le schéma du vault — toute commande le lit d'abord
    ├── INDEX.md                 # carte du vault, point d'entrée des recherches
    └── LOG.md                   # journal append-only
```

Le code (commandes, scripts, template) vit dans le plugin, partagé entre tous
les projets ; la config vit dans chaque projet (`.claude/vault-path.local`,
`settings.local.json`, `toolbox-path.local` — gitignorés) : **un plugin, un
vault par projet**.

## Principes

- **Source de vérité = les `.md` du vault.** Tout le reste (index de recherche,
  caches) est un dérivé jetable et reconstructible.
- **Recherche via sub-agents uniquement** : le contexte principal de Claude ne
  voit jamais les notes brutes (anti-saturation, anti-distracteurs) — seule la
  réponse citée remonte.
- **Trois couches de savoir** : `wiki/sources/` (immuable, une note par source),
  `wiki/concepts/` + `wiki/entites/` (vivantes, reliées par wikilinks),
  `wiki/syntheses/` (réponses transversales persistées).
- **Échecs explicites** : Drive non monté, vault non initialisé → message clair,
  jamais de vault vide silencieux.

## Installation

**Prérequis** : [Claude Code](https://claude.com/claude-code) ; Google Drive
pour Desktop si le vault doit être partagé (sinon n'importe quel dossier local
convient) ; [agentic-toolbox](https://github.com/Zairth/agentic-toolbox) pour
la recherche sémantique (facultatif — repli grep sinon) ; Obsidian est
**facultatif** — c'est la vitrine humaine, le système fonctionne sans.
**Guide pas à pas** (commandes d'installation, WSL, montage Drive, clés API) :
[PREREQUIS.md](PREREQUIS.md).

Dans Claude Code (une fois, valable pour tous les projets) :

```
/plugin marketplace add Zairth/claude-vault-drive
/plugin install claude-vault-drive@zairth
```

**Pas besoin de cloner ce repo** : Claude Code le récupère et le met en cache
lui-même depuis GitHub.

Puis dans chaque projet qui doit avoir son vault :

1. `/vault-init "/mnt/g/Mon Drive/<Section>/<MonVault>"` — idempotent (ne
   remplace jamais un fichier existant) et complet : config locale gitignorée
   dans le `.claude/` du projet (`vault-path.local` + `settings.local.json`
   avec la permission d'écriture), `.gitignore` complété, arborescence du
   vault, copie du template, date de l'entrée `init` du LOG, vérification
   finale par `vault-check.sh`.
2. Relancer la session Claude Code (pour charger la permission
   `additionalDirectories`) — les commandes `/doc-ingest`, `/doc-query` et
   `/doc-lint` sont prêtes.
3. (Facultatif, humain) Ouvrir le dossier du vault comme coffre dans Obsidian.

Mise à jour : automatique en arrière-plan, ou manuelle en une seule étape —
`/plugin marketplace update zairth` (récupère le dernier commit
directement depuis GitHub, aucun `git pull` local).

Développement du plugin uniquement (tester des modifs avant de pousser) :
`/plugin marketplace add /chemin/du/clone` ou `claude --plugin-dir /chemin/du/clone`.

Le chemin du vault ne vit que dans les fichiers locaux gitignorés du projet —
jamais dans un fichier versionné. `vault-path.local` peut être édité depuis
Windows : BOM/CRLF/espaces finaux sont nettoyés automatiquement.

## Usage

- `/doc-ingest <texte | fichier | URL | élément de inbox/>` — propose 2-5
  enseignements clés, discute, puis écrit : note source immuable, pages
  concepts/entités, INDEX, LOG. Contradiction détectée → callout `> [!warning]`.
- `/doc-query <question>` — réindexation incrémentale + recherche sémantique
  (pistes injectées dans le sub-agent), puis sub-agent : INDEX → notes →
  wikilinks → grep ; réponse citée ; option « sauvegarder en synthèse ».
  Ajouter `dans:<dossier>` pour cibler un dossier voisin du vault (ex. une
  section alimentée par des tiers) : lecture seule, la synthèse reste dans le
  vault. Ajouter `--no-index` pour interroger sans réindexer. Moteur
  sémantique indisponible → repli grep **explicite** (⚠ affiché), jamais
  d'échec silencieux.
- `/doc-lint` — rapport : contradictions en souffrance, pages orphelines, trous
  d'INDEX, fichiers de conflit Drive, inbox en attente, cohérence de l'index
  vectoriel (`.index/`) ; corrections validées avec l'utilisateur.

## Notes d'environnement

- **WSL + Google Drive** : si le lecteur apparaît après le démarrage de WSL,
  `/mnt/<lettre>` peut être vide → `sudo mount -t drvfs <lettre>: /mnt/<lettre>`.
- **Vue Obsidian en retard** : les écritures faites hors d'Obsidian (par Claude)
  peuvent mettre un moment à apparaître — Ctrl+R recharge ; `/doc-lint` fait foi.
- **Édition simultanée** : les fichiers de conflit créés par Drive (`* (1).md`)
  sont détectés par `/doc-lint` ; règle sociale simple — un écrivain à la fois.

## Recherche sémantique (facultative, repli grep sinon)

L'index d'embeddings vit dans `<vault>/.index/embeddings.jsonl` — un mapping
`hash(chunk) → vecteur` partagé via Drive, fournisseur/modèle épinglés en
ligne 1, réindexation incrémentale par hash (jamais de fallback d'embeddings
entre modèles : espaces vectoriels incompatibles). Il est **dérivé et
reconstructible** : le supprimer ne perd rien.

Le moteur n'est pas inclus dans ce repo — les wrappers `scripts/vault-index.sh`
et `vault-search.sh` du plugin appellent l'implémentation de référence :
**[agentic-toolbox](https://github.com/Zairth/agentic-toolbox)** (projet de l'auteur —
routeur LLM multi-fournisseurs + module `semantic_index` : chunking par
section, embeddings `mistral-embed` épinglés, index JSONL dans le vault).
Exécuté depuis son venv, aucun service qui tourne. Résolution du chemin :
`.claude/toolbox-path.local` du projet (une ligne, gitignoré), à défaut
`~/projects/agentic-toolbox`. Tout moteur respectant le même contrat CLI
(`index <dossier>` / `search "question" --dir <dossier>`, JSON sur stdout)
s'y substitue en éditant les deux wrappers, sans toucher aux commandes.

Sans moteur, tout fonctionne : `/doc-query` dégrade vers grep avec un
avertissement explicite, `/doc-ingest` note l'indexation « à rattraper ».
Installation du moteur (clone, venv, clé Mistral) : [PREREQUIS.md](PREREQUIS.md).
