# Instructions pour Claude — vault

Ce fichier est le **schéma du vault** : structure, conventions, règles de
maintenance et de recherche. Toute commande (`/doc-ingest`, `/doc-query`,
`/doc-lint`) commence par le lire intégralement et s'y conforme.

## Rôle du vault

- Documentation du projet et connaissances externes.
- La source de vérité est constituée des fichiers `.md` de ce dossier. Obsidian
  n'est que la vitrine humaine (graphe, wikilinks) — rien ne dépend de ses plugins.
- Si le dossier est partagé (Google Drive ou autre), d'autres personnes peuvent
  alimenter des sections voisines : elles se consultent, mais on n'écrit que
  dans ce vault.

## Structure

```
<vault>/
├── INSTRUCTIONS-CLAUDE.md   ← ce fichier
├── INDEX.md                 ← carte du vault, point d'entrée de toute recherche
├── LOG.md                   ← journal append-only des opérations
├── inbox/                   ← dépôts bruts en attente d'ingestion
├── wiki/
│   ├── sources/             ← couche IMMUABLE : une note par source, jamais réécrite
│   ├── concepts/            ← couche vivante : pages de concepts
│   ├── entites/             ← couche vivante : personnes, outils, projets
│   └── syntheses/           ← réponses de /doc-query sauvegardées
└── .index/                  ← index de recherche sémantique optionnel (ne pas toucher)
```

## Conventions de notes

- **Français.** Notes courtes et denses : une idée par note, aucun remplissage,
  aucun distracteur.
- Nommage : `kebab-case.md` ; sources préfixées `YYYY-MM-DD-`.
- Frontmatter minimal : `type` (source | concept | entite | synthese), `date`,
  `tags` seulement si utile.
- Wikilinks `[[...]]` libéraux vers les concepts et entités.
- Citations verbatim ≤ 125 caractères ; au-delà, paraphraser — le verbatim long
  reste dans `wiki/sources/`.
- Contradiction entre une nouvelle information et l'existant : poser un callout
  `> [!warning]` dans la page concernée décrivant les deux versions, et la
  résoudre en conversation avec l'utilisateur — jamais silencieusement.

## Règles de maintenance

- `wiki/sources/` est **immuable** : une note de source n'est jamais modifiée
  après son ingestion.
- Toute écriture dans `wiki/` met à jour `INDEX.md` **dans la foulée**.
- `LOG.md` est **append-only** : `## [YYYY-MM-DD] <action> | <titre>` (actions :
  `init`, `ingest`, `lint`, `synthese`), suivi d'une ligne de détail. Ne jamais
  modifier une entrée existante.
- `inbox/` : un fichier ingéré avec succès est **supprimé** de l'inbox — son
  contenu condensé vit désormais dans `wiki/sources/`.

## Règles de recherche (pour les sub-agents)

- Point d'entrée : `INDEX.md`, puis suivre les wikilinks des notes pertinentes.
- Compléter par grep sur les mots-clés de la question **et leurs synonymes /
  variantes françaises**.
- Ne remonter au contexte principal **que** la réponse citée (avec les chemins
  des notes sources, relatifs au vault) — jamais le contenu brut des notes.
- Rien de pertinent trouvé : le dire explicitement et lister ce qui s'en rapproche.
