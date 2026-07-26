---
description: Ingérer une source dans le vault Obsidian (validation conversationnelle, wiki, INDEX, LOG)
argument-hint: <texte | chemin de fichier | URL | nom d'un fichier de inbox/>
---

# /doc-ingest — ingérer une source dans le vault

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas d'échec : transmettre
   le message d'erreur tel quel à l'utilisateur et S'ARRÊTER. Sinon, la sortie
   est le chemin du vault — appelé `$VAULT` ci-dessous.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (conventions de notes, règles de maintenance).

## Récupérer la source ($ARGUMENTS)

- Texte brut fourni directement → l'utiliser tel quel.
- Nom d'un fichier présent dans `$VAULT/inbox/` ou chemin de fichier → le lire.
- URL → récupérer le contenu (WebFetch).
- PDF → ne pas l'ingérer tel quel : proposer de le convertir d'abord en
  markdown propre par OCR (moteur : agentic-toolbox — outil MCP
  `mcp__plugin_agentic-toolbox_toolbox__ocr_convert` si disponible dans la
  session, sinon son CLI `services.document_ocr.cli_parser convert` depuis le
  clone local), déposer le markdown obtenu dans `$VAULT/inbox/`, puis
  reprendre ce circuit normalement.
- Argument vide ou ambigu → demander à l'utilisateur ce qu'il veut ingérer
  (lister le contenu de `$VAULT/inbox/` s'il n'est pas vide).

## Validation conversationnelle (OBLIGATOIRE avant toute écriture)

1. Proposer 2 à 5 enseignements clés extraits de la source (une ligne chacun).
2. En discuter : l'utilisateur peut en retirer, corriger, reformuler, ajouter.
3. N'écrire dans le vault QU'APRÈS son accord explicite.

## Écriture (dans cet ordre)

1. `$VAULT/wiki/sources/YYYY-MM-DD-<slug>.md` (date du jour, slug kebab-case) :
   frontmatter conforme au modèle de note d'`INSTRUCTIONS-CLAUDE.md`
   (`type: source`, `date`, `auteur` — repérable dans les notes existantes du
   vault, sinon le demander —, `origine` = chemin archivé/URL/« conversation »,
   `original` seulement si la pièce d'origine diffère de la copie pointée par
   `origine` — ex. le PDF dont la note vient par OCR : chemin de sa copie dans
   `archives/`, ou emplacement durable hors vault (URL, dossier partagé) —
   **jamais un chemin absolu de la machine**),
   les enseignements validés, citations verbatim ≤ 125 caractères, wikilinks
   vers les concepts/entités concernés. Immuable une fois écrit.
2. Pour chaque concept ou entité touché : créer ou mettre à jour la page dans
   `$VAULT/wiki/concepts/` ou `$VAULT/wiki/entites/` (frontmatter `type: concept`
   ou `type: entite` + `date` + `auteur` à la création, paraphrase, wikilink
   retour vers la note source).
   Contradiction avec le contenu existant → callout `> [!warning]` décrivant les
   deux versions, signalée à l'utilisateur pour résolution.
3. Mettre à jour `$VAULT/INDEX.md` : ajouter chaque nouvelle note dans sa
   section, sous forme `- [[<slug>]] — <description en quelques mots>`.
4. Ajouter en fin de `$VAULT/LOG.md` : `## [YYYY-MM-DD] ingest | <titre de la source>`
   suivi d'une ligne listant les fichiers créés/modifiés.
5. Archiver la pièce d'origine — pour TOUTE source qui est un fichier local :
   venue de `$VAULT/inbox/` → la **déplacer** vers `$VAULT/archives/` ; venue
   d'ailleurs sur la machine → l'y **copier** (le fichier de l'utilisateur
   n'est jamais déplacé ni supprimé). PDF passé par OCR : archiver les deux —
   le markdown OCR et le PDF d'origine. Les fichiers archivés gardent leur
   nom et leur extension — `archives/` est hors index par construction, seul
   `$VAULT/wiki` est indexé. Renseigner `origine:`
   (et `original:` le cas échéant) avec ces chemins archivés, relatifs au
   vault — **jamais un chemin absolu de la machine** (`/home/...`,
   `/mnt/...`, `C:\...`) : il meurt avec la machine, le vault doit rester
   auto-porteur.
6. Indexation sémantique — outil MCP
   `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
   `directory: $VAULT/wiki` **explicite** (jamais son défaut `VAULT_PATH`,
   global ; `wiki` seul : `archives/` et `inbox/` restent hors index)
   si le plugin agentic-toolbox est installé, sinon
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"` (clone + venv).
   Incrémental — seuls les chunks des notes créées/modifiées coûtent un appel
   API. **Échec = non bloquant** : l'ingestion reste valide ; noter que
   l'indexation se rattrapera au prochain `/doc-query`.

## Compte rendu

Lister les fichiers créés/modifiés (chemins relatifs au vault) et les
`> [!warning]` posés, le cas échéant. Terminer par l'état de l'indexation :
`embedded_chunks`/`reused_chunks` du rapport JSON, ou « ⚠ indexation sémantique
échouée (<raison>) — à rattraper » si l'étape 6 a échoué.
