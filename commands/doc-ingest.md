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

## Récupérer et lire la source ($ARGUMENTS) — en sub-agent lecteur

- Argument vide ou ambigu → demander à l'utilisateur ce qu'il veut ingérer
  (lister le contenu de `$VAULT/inbox/` s'il n'est pas vide).
- Texte bref fourni directement dans `$ARGUMENTS` → il est déjà en contexte :
  pas de sub-agent, passer directement à la validation.
- Fichier local, élément d'`inbox/`, URL, PDF → **NE JAMAIS lire la source en
  contexte principal** (anti-saturation : sur un gros volume, l'ingestion
  ferait déborder la session). **Mesurer d'abord le volume** sans lire le
  contenu : `wc -c` par fichier ; PDF → conversion markdown par OCR d'abord
  (outil MCP `mcp__plugin_agentic-toolbox_toolbox__ocr_convert` si
  disponible, sinon le CLI `services.document_ocr.cli_parser convert` depuis
  le clone local), dépôt dans `$VAULT/inbox/`, et mesure du markdown obtenu ;
  URL → taille inconnue : partir du montage nominal, le lecteur signale s'il
  déborde. Puis choisir le montage :

  **Montage nominal — source unique ≤ ~150 Ko de texte** : un **sub-agent
  lecteur** (outil Agent, en avant-plan — `run_in_background: false`) avec
  pour mission :
  1. lire la source — fichier local (chemin transmis), URL (WebFetch) ;
  2. rédiger le **dossier d'ingestion** : 2 à 5 enseignements clés (une ligne
     chacun), pour chacun une citation verbatim ≤ 125 caractères, les
     concepts/entités candidats (wikilinks), et une description en quelques
     mots pour l'INDEX ;
  3. ne retourner QUE ce dossier — jamais la source brute ni de longs
     extraits. S'il constate en lisant que la source dépasse ce qu'il peut
     traiter proprement, il retourne un **plan de découpe** (structure et
     bornes) au lieu d'un dossier — basculer alors sur le montage suivant.

  **Gros volume — source unique > ~150 Ko** : découper en tranches ≤ ~150 Ko
  par la structure (sections markdown, chapitres, plages de pages — repérée
  par grep/offsets, sans lire le contenu en contexte principal). **Un lecteur
  par tranche**, lancés en parallèle (4 au plus à la fois), chacun rend un
  dossier partiel. Puis un **sub-agent synthétiseur** reçoit les dossiers
  partiels (jamais les sources) et les fusionne en un dossier d'ingestion
  global de 2 à 5 enseignements. C'est lui l'interlocuteur de la validation.
  Retouche exigeant un retour à la source → relancer un lecteur sur la
  tranche concernée et transmettre sa réponse au synthétiseur.

  **Lot de fichiers (plusieurs chemins, un dossier, inbox/ entier)** : le
  modèle reste « une note par source » — un lecteur par fichier (parallèle,
  4 au plus), puis validation présentée source par source (l'affichage peut
  être groupé, l'accord est explicite par source) et écriture par source.
  Un fichier du lot dépasse le seuil → lui appliquer le montage gros volume.

  Dans tous les montages, l'interlocuteur de validation (lecteur, ou
  synthétiseur en gros volume) garde son contexte : le conserver pour toute
  la phase de validation ci-dessous.

## Validation conversationnelle (OBLIGATOIRE avant toute écriture)

1. Proposer 2 à 5 enseignements clés extraits de la source, **écrits en clair
   dans le corps de la réponse** (liste numérotée, une ligne chacun).
   INTERDIT de les reléguer dans les options ou descriptions d'un outil de
   question (AskUserQuestion ou équivalent) : l'utilisateur doit avoir lu
   chaque enseignement intégralement AVANT qu'on lui demande de se prononcer.
   Un outil de question ne peut servir qu'à recueillir l'accord (valider /
   modifier / abandonner) — jamais à porter le contenu.
2. En discuter : l'utilisateur peut en retirer, corriger, reformuler, ajouter.
   Retrait ou retouche de forme → se fait en contexte principal. Toute
   demande qui exige de **retourner à la source** (reformuler sur le fond,
   vérifier, ajouter un enseignement manqué) → la relayer via SendMessage à
   l'interlocuteur de validation du montage (le lecteur — contexte, source
   comprise, conservé ; en gros volume le synthétiseur, qui passe par un
   lecteur de tranche relancé si la source est requise) — puis présenter sa
   nouvelle version en clair. Autant d'allers-retours que nécessaire.
   Interlocuteur perdu ou SendMessage indisponible → relancer le montage
   concerné avec la source ET le cumul des retours utilisateur déjà exprimés.
3. N'écrire dans le vault QU'APRÈS son accord explicite — l'écriture se fait
   en contexte principal, à partir du seul dossier d'ingestion validé.

## Écriture (dans cet ordre — à partir du dossier d'ingestion validé, sans
jamais rouvrir la source en contexte principal)

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
   `directory: $VAULT/wiki` **explicite** (`wiki` seul : `archives/` et
   `inbox/` restent hors index)
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
