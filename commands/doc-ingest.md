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
  markdown propre par OCR externe (implémentation de référence : l'OCR
  Mistral Document AI d'agentic-toolbox, clé API dans son `.env`), déposer le
  markdown obtenu dans `$VAULT/inbox/`, puis reprendre ce circuit normalement.
- Argument vide ou ambigu → demander à l'utilisateur ce qu'il veut ingérer
  (lister le contenu de `$VAULT/inbox/` s'il n'est pas vide).

## Validation conversationnelle (OBLIGATOIRE avant toute écriture)

1. Proposer 2 à 5 enseignements clés extraits de la source (une ligne chacun).
2. En discuter : l'utilisateur peut en retirer, corriger, reformuler, ajouter.
3. N'écrire dans le vault QU'APRÈS son accord explicite.

## Écriture (dans cet ordre)

1. `$VAULT/wiki/sources/YYYY-MM-DD-<slug>.md` (date du jour, slug kebab-case) :
   frontmatter (`type: source`, `date`, `origine` = URL/fichier/« conversation »),
   les enseignements validés, citations verbatim ≤ 125 caractères, wikilinks
   vers les concepts/entités concernés. Immuable une fois écrit.
2. Pour chaque concept ou entité touché : créer ou mettre à jour la page dans
   `$VAULT/wiki/concepts/` ou `$VAULT/wiki/entites/` (frontmatter `type: concept`
   ou `type: entite`, paraphrase, wikilink retour vers la note source).
   Contradiction avec le contenu existant → callout `> [!warning]` décrivant les
   deux versions, signalée à l'utilisateur pour résolution.
3. Mettre à jour `$VAULT/INDEX.md` : ajouter chaque nouvelle note dans sa
   section, sous forme `- [[<slug>]] — <description en quelques mots>`.
4. Ajouter en fin de `$VAULT/LOG.md` : `## [YYYY-MM-DD] ingest | <titre de la source>`
   suivi d'une ligne listant les fichiers créés/modifiés.
5. Si la source venait de `$VAULT/inbox/` : supprimer le fichier ingéré.
6. Indexation sémantique : exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"`.
   Incrémental — seuls les chunks des notes créées/modifiées coûtent un appel
   API. **Échec = non bloquant** : l'ingestion reste valide ; noter que
   l'indexation se rattrapera au prochain `/doc-query`.

## Compte rendu

Lister les fichiers créés/modifiés (chemins relatifs au vault) et les
`> [!warning]` posés, le cas échéant. Terminer par l'état de l'indexation :
`embedded_chunks`/`reused_chunks` du rapport JSON, ou « ⚠ indexation sémantique
échouée (<raison>) — à rattraper » si l'étape 6 a échoué.
