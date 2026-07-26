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
├── inbox/                   ← sas : dépôts bruts en attente d'ingestion
├── archives/                ← pièces d'origine conservées après ingestion (hors index)
├── wiki/
│   ├── sources/             ← couche IMMUABLE : une note par source, jamais réécrite
│   ├── concepts/            ← couche vivante : pages de concepts
│   ├── entites/             ← couche vivante : personnes, outils, projets
│   ├── syntheses/           ← réponses de /doc-query sauvegardées
│   └── .index/              ← index de recherche sémantique optionnel (ne pas toucher)
```

## Conventions de notes

- **Français.** Notes courtes et denses : une idée par note, aucun remplissage,
  aucun distracteur.
- Nommage : `kebab-case.md` ; sources préfixées `YYYY-MM-DD-`.
- **Modèle de note — frontmatter obligatoire** (une note sans ces propriétés
  n'est pas conforme ; `/doc-lint` les vérifie) :
  - toutes les notes : `type` (source | concept | entite | synthese),
    `date` (date de création `YYYY-MM-DD`, jamais modifiée ensuite) et
    `auteur` (qui a créé la note : la personne pilotant la session — la
    demander une fois si inconnue, puis réutiliser — ou le nom de l'équipe
    tierce pour une note importée) ;
  - `type: source` : `origine` — provenance de la note : chemin archivé
    relatif au vault (pièce dans `archives/`), URL, ou mention libre
    (« conversation », …) ; `original` en plus, seulement si la pièce
    d'origine diffère de la copie pointée par `origine` (ex. le PDF dont la
    note vient par OCR) : chemin de sa copie dans `archives/`, ou emplacement
    durable hors vault (URL, dossier partagé). **Jamais de chemin absolu de
    la machine** (`/home/...`, `/mnt/...`, `C:\...`) dans `origine`/`original` :
    un fichier local ingéré est copié dans `archives/` et référencé
    relativement au vault ;
  - `type: synthese` : `question` — la question posée ; `perimetre` si la
    recherche visait un dossier voisin du vault.

  Optionnel partout : `tags`, et toute propriété utile au cas particulier
  (ex. `image`, `capture_precedente`/`capture_suivante` pour des captures OCR
  en série) — enrichir librement, ne jamais retirer une propriété obligatoire.
- Wikilinks `[[...]]` libéraux vers les concepts et entités. Toute référence
  à une autre note du vault s'écrit en wikilink, **jamais en chemin brut** :
  seuls les wikilinks créent des liens (graphe Obsidian, backlinks, détection
  d'orphelines par `/doc-lint`). Exceptions : les propriétés `origine`/
  `original` (pointent vers `archives/` ou hors vault — hors graphe, voulu).
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
- `inbox/` est un **sas**, pas un stockage : un fichier ingéré avec succès est
  **déplacé vers `archives/`** (jamais supprimé) ; un fichier local ingéré
  depuis l'extérieur du vault y est **copié** (l'original de l'utilisateur
  n'est pas touché) — le condensé vit dans `wiki/sources/`, la pièce
  d'origine reste vérifiable dans le vault, qui voyage ainsi d'un bloc
  (auto-porteur).
- `archives/` est immuable comme `wiki/sources/`. Les fichiers archivés
  gardent leur nom et leur extension ; l'index sémantique ne couvre que
  `wiki/`, les archives restent donc hors index (zéro coût, zéro bruit).
  Attention avant de partager le vault : les archives peuvent
  contenir des données sensibles que les notes condensées ont volontairement
  écartées.

## Règles de recherche (pour les sub-agents)

- Point d'entrée : `INDEX.md`, puis suivre les wikilinks des notes pertinentes.
- Compléter par grep sur les mots-clés de la question **et leurs synonymes /
  variantes françaises**.
- Ne remonter au contexte principal **que** la réponse citée (avec les chemins
  des notes sources, relatifs au vault) — jamais le contenu brut des notes.
- Rien de pertinent trouvé : le dire explicitement et lister ce qui s'en rapproche.
