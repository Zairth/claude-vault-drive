# claude-obsidian-drive

Un vault Obsidian partagé (Google Drive ou tout dossier synchronisé), consultable
et maintenu par Claude Code — **sans MCP, sans plugin, sans service qui tourne**.
Le vault n'est que des fichiers markdown dans un dossier : Obsidian est la
vitrine humaine (graphe, wikilinks), Claude Code y accède directement.

## Ce que contient ce repo

```
claude-obsidian-drive/
├── .claude/
│   ├── commands/
│   │   ├── doc-ingest.md    # /doc-ingest — ingérer une source (validation conversationnelle)
│   │   ├── doc-query.md     # /doc-query — interroger le vault (sub-agent, réponse citée)
│   │   └── doc-lint.md      # /doc-lint — maintenance (orphelins, INDEX, conflits Drive)
│   └── scripts/
│       └── vault-check.sh   # portier : vérifie l'accès au vault, imprime son chemin
└── vault-template/          # fichiers à copier à la racine d'un nouveau vault
    ├── INSTRUCTIONS-CLAUDE.md   # le schéma du vault — toute commande le lit d'abord
    ├── INDEX.md                 # carte du vault, point d'entrée des recherches
    └── LOG.md                   # journal append-only
```

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
convient) ; Obsidian est **facultatif** — c'est la vitrine humaine, le système
fonctionne sans.

1. Cloner ce repo (nouveau projet) ou copier `.claude/` + `vault-template/`
   dans un projet existant.
2. Ouvrir Claude Code dans le dossier et lancer l'initialisation — directement,
   ou en demandant à Claude de le faire :
   ```bash
   bash .claude/scripts/vault-init.sh "/mnt/g/Mon Drive/<Section>/<MonVault>"
   ```
   Le script est **idempotent** (il ne remplace jamais un fichier existant) et
   fait tout : config locale gitignorée (`vault-path.local` +
   `settings.local.json` avec la permission d'écriture), arborescence du vault,
   copie des fichiers du template, date de l'entrée `init` du LOG, puis
   vérification finale par `vault-check.sh`.
3. Relancer la session Claude Code (pour charger la permission
   `additionalDirectories`) — les commandes `/doc-ingest`, `/doc-query` et
   `/doc-lint` sont prêtes.
4. (Facultatif, humain) Ouvrir le dossier du vault comme coffre dans Obsidian.

Le chemin du vault ne vit que dans les deux fichiers locaux gitignorés — jamais
dans un fichier versionné. `vault-path.local` peut être édité depuis Windows :
BOM/CRLF/espaces finaux sont nettoyés automatiquement.

## Usage

- `/doc-ingest <texte | fichier | URL | élément de inbox/>` — propose 2-5
  enseignements clés, discute, puis écrit : note source immuable, pages
  concepts/entités, INDEX, LOG. Contradiction détectée → callout `> [!warning]`.
- `/doc-query <question>` — sub-agent : INDEX → notes → wikilinks → grep ;
  réponse citée ; option « sauvegarder en synthèse ».
- `/doc-lint` — rapport : contradictions en souffrance, pages orphelines, trous
  d'INDEX, fichiers de conflit Drive, inbox en attente ; corrections validées
  avec l'utilisateur.

## Notes d'environnement

- **WSL + Google Drive** : si le lecteur apparaît après le démarrage de WSL,
  `/mnt/<lettre>` peut être vide → `sudo mount -t drvfs <lettre>: /mnt/<lettre>`.
- **Vue Obsidian en retard** : les écritures faites hors d'Obsidian (par Claude)
  peuvent mettre un moment à apparaître — Ctrl+R recharge ; `/doc-lint` fait foi.
- **Édition simultanée** : les fichiers de conflit créés par Drive (`* (1).md`)
  sont détectés par `/doc-lint` ; règle sociale simple — un écrivain à la fois.

## Extension possible : recherche sémantique

La structure réserve `<vault>/.index/` pour un index d'embeddings partagé
(mapping `hash(chunk) → vecteur` en JSONL, modèle épinglé, réindexation
incrémentale — jamais de fallback d'embeddings entre modèles : espaces
vectoriels incompatibles). Le moteur n'est pas inclus dans ce repo : n'importe
quelle CLI capable d'`index`/`search` sur un dossier markdown convient, appelée
par le sub-agent de `/doc-query`, avec repli grep explicite si indisponible.
