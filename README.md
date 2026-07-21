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

## Installation dans un projet

1. Copier `.claude/commands/` et `.claude/scripts/` dans le `.claude/` du projet
   (ou cloner ce repo comme point de départ du projet).
2. Écrire le chemin du vault (une seule ligne) dans `.claude/vault-path.local` :
   ```bash
   echo "/mnt/g/Mon Drive/<Section>/<MonVault>" > .claude/vault-path.local
   ```
   Ce fichier est **gitignoré** (chemin = donnée locale/sensible). Il peut être
   édité depuis Windows : BOM/CRLF/espaces finaux sont nettoyés automatiquement.
3. Autoriser Claude Code à écrire dans le vault — `.claude/settings.local.json`
   (gitignoré lui aussi) :
   ```json
   {
     "permissions": {
       "additionalDirectories": ["/mnt/g/Mon Drive/<Section>/<MonVault>"]
     }
   }
   ```
4. Initialiser le vault : créer les dossiers et copier le template.
   ```bash
   vault="<chemin du vault>"
   mkdir -p "$vault/inbox" "$vault/wiki/sources" "$vault/wiki/concepts" \
            "$vault/wiki/entites" "$vault/wiki/syntheses" "$vault/.index"
   cp vault-template/*.md "$vault/"
   # puis remplacer la date [YYYY-MM-DD] de l'entrée init dans LOG.md
   ```
5. Vérifier : `bash .claude/scripts/vault-check.sh` doit imprimer le chemin du
   vault avec le code retour 0.
6. (Humain) Ouvrir le dossier comme coffre dans Obsidian.

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
