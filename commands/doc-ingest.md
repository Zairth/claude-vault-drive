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
- Fichier local, élément d'`inbox/`, URL, PDF, capture d'écran → **NE JAMAIS
  lire la source en contexte principal** (anti-saturation : sur un gros
  volume, l'ingestion ferait déborder la session).

  **Router d'abord selon la nature de la source** — l'OCR n'est pas un passage
  obligé, c'est un outil à documents :

  - **PDF, scan, document multi-pages** → conversion markdown par OCR
    (outil MCP `mcp__plugin_agentic-toolbox_toolbox__ocr_convert` si
    disponible, sinon le CLI `services.document_ocr.cli_parser convert` depuis
    le clone local), dépôt dans `$VAULT/inbox/`, puis mesure du markdown
    obtenu. C'est son terrain : mise en page structurée, texte au fil des
    pages.
  - **Capture d'écran** (`.png`, `.jpg`, `.jpeg`, `.webp`, `.heic`…) →
    **jamais d'OCR**. Un OCR documentaire aplatit en flux linéaire ce qui,
    dans une conversation, porte le sens par la **position** — bulle à gauche
    ou à droite, en-tête de fil, alignement : l'attribution du locuteur n'est
    pas mal transcrite, elle est détruite à la lecture, et aucun réglage n'y
    remédie. Le sub-agent lecteur **ouvre l'image directement** (outil Read,
    qui affiche les images) et la transcrit lui-même. Trois conséquences :
    - pas de mesure par `wc -c` — une image ne se compte pas en octets de
      texte. L'unité de source est la **conversation, pas le fichier** : une
      série de captures d'un même fil est UNE source, qu'un seul lecteur
      ouvre dans l'ordre (une dizaine au plus par lecteur ; au-delà, découper
      la série en tranches et appliquer le montage gros volume) ;
    - mission de lecture explicite : restituer **qui parle** (déduit de
      l'alignement et des en-têtes), les horodatages visibles, l'ordre
      chronologique ; et **signaler tout passage illisible, coupé ou ambigu
      plutôt que de le deviner** — ce sera un `> [!warning]` sur la note
      source ;
    - c'est l'**image elle-même** qui est archivée et que pointe `origine:`.
      Aucun markdown intermédiaire n'est produit, donc aucune référence
      d'image pendante à traîner ensuite dans le graphe.
  - **Texte, markdown, export brut** → tel quel, mesure par `wc -c`.
  - **URL** → taille inconnue : partir du montage nominal, le lecteur signale
    s'il déborde.

  Puis choisir le montage :

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

  Cas particulier — `inbox/session-*.md` (`type: session` : transcript de
  session Claude Code déposé automatiquement avant compactage) : densité utile
  faible — la mission du lecteur devient « extraire les décisions prises et
  les faits durables, jamais le déroulé de la session ». Aucun enseignement
  durable → proposer l'archivage direct (déplacement vers `archives/`), sans
  note source.

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
   vault, sinon le demander —, `description` — celle du dossier d'ingestion —,
   `origine` = chemin archivé/URL/« conversation »,
   `original` seulement si la pièce d'origine diffère de la copie pointée par
   `origine` — ex. le PDF dont la note vient par OCR : chemin de sa copie dans
   `archives/`, ou emplacement durable hors vault (URL, dossier partagé) —
   **jamais un chemin absolu de la machine**),
   les enseignements validés, citations verbatim ≤ 125 caractères, wikilinks
   vers les concepts/entités concernés. Immuable une fois écrit.
   Réserve constatée sur la pièce elle-même — OCR partiel, capture non datée,
   propos rapporté, document non signé, date déduite → callout
   `> [!warning]` dans cette note, permanent : il décrit la pièce, il n'y a
   rien à trancher. **Jamais de `> [!question]` ici** (voir 3).
2. **Source conversationnelle uniquement** (captures d'un fil, export d'un outil de messagerie — pas un document,
   pas un article) : écrire en plus la
   **transcription intégrale** dans
   `$VAULT/wiki/transcriptions/<conversation>/<slug>.md`, où `<conversation>`
   est un dossier en kebab-case nommant le fil (`<fil-a>`,
   `<fil-b>`, `<fil-c>`…) — créé s'il n'existe pas,
   réutilisé s'il existe déjà. Frontmatter `type: transcription` + `date` +
   `auteur` + `description` + `origine` (les pièces d'`archives/`, captures
   dans leur ordre) + `conversation` + `participants` + `periode`.
   Corps : **un message par bloc**, auteur et horodatage en tête quand ils sont
   lisibles, ordre chronologique, texte intégral — pas un résumé. Wikilinks
   vers les entités citées, et vers la note source du 1 (qui pointe en retour).
   Immuable une fois écrite.
   Un passage illisible ou ambigu se **signale** (`[illisible]`, et un
   `> [!warning]` en tête si la conversation en compte plusieurs) ; il ne se
   devine jamais.
   Fil très long → plusieurs notes **dans le même dossier**, découpées par
   période (`2026-03.md`, `2026-04.md`…) : le dossier reste l'unité de
   conversation.
   **`transcriptions/` n'est pas vectorisé** (voir 7) : cette note se retrouve
   par le wikilink de son condensé, par grep, et par lecture.
   **Pourquoi cette note en plus du condensé** : sans elle, seuls les 2 à 5
   enseignements retenus sont interrogeables, et une question du type « tous
   les messages où X reconnaît le travail de Y » n'a aucune matière. Le
   condensé est ce qu'on lit ; la transcription est ce qu'on fouille.
3. Pour chaque concept ou entité touché : créer ou mettre à jour la page dans
   `$VAULT/wiki/concepts/` ou `$VAULT/wiki/entites/` (frontmatter `type: concept`
   ou `type: entite` + `date` + `auteur` + `description` à la création,
   paraphrase, wikilink retour vers la note source). **Avant de créer** : vérifier qu'aucune page
   vivante existante ne couvre déjà le sujet — nom normalisé (casse, accents,
   tirets), alias `aliases:`, libellé proche — et en cas de doute enrichir
   l'existante plutôt que créer un doublon.
   Contradiction avec le contenu existant → convention
   d'`INSTRUCTIONS-CLAUDE.md` : la trancher avec l'utilisateur (la validation
   est le bon moment) → valeur courante mise à jour dans le corps + entrée
   `## Historique` en fin de note ; impossible à trancher → callout
   `> [!question]` **sur cette page** (jamais sur la note source, immuable :
   on ne pourrait plus l'en retirer une fois tranché), décrivant les deux
   versions et pointant chacune vers sa source en wikilink, signalé à
   l'utilisateur.
4. Mettre à jour `$VAULT/INDEX.md` : ajouter chaque nouvelle note dans sa
   section, sous forme `- [[<slug>]] — <description>` — la même `description`
   que le frontmatter (INDEX est un dérivé du frontmatter, mêmes mots aux
   deux endroits). Une transcription va en section Transcriptions, son dossier
   de conversation entre parenthèses.
5. Ajouter en fin de `$VAULT/LOG/YYYY-MM-DD.md` (le fichier du jour — le créer
   au besoin ; jamais dans un `LOG.md` racine hérité, gelé) :
   `## [YYYY-MM-DD] ingest | <titre de la source>`
   suivi d'une ligne listant les fichiers créés/modifiés.
6. Archiver la pièce d'origine — pour TOUTE source qui est un fichier local :
   venue de `$VAULT/inbox/` → la **déplacer** vers `$VAULT/archives/` ; venue
   d'ailleurs sur la machine → l'y **copier** (le fichier de l'utilisateur
   n'est jamais déplacé ni supprimé). PDF passé par OCR : archiver les deux —
   le markdown OCR et le PDF d'origine. Captures d'écran : archiver **les
   images elles-mêmes**, toutes celles de la série, dans leur ordre — elles
   sont la pièce d'origine, il n'y a rien d'autre à conserver. Les fichiers archivés gardent leur
   nom et leur extension — `archives/` est hors index par construction, seul
   `$VAULT/wiki` est indexé. Renseigner `origine:`
   (et `original:` le cas échéant) avec ces chemins archivés, relatifs au
   vault — **jamais un chemin absolu de la machine** (`/home/...`,
   `/mnt/...`, `C:\...`) : il meurt avec la machine, le vault doit rester
   auto-porteur.
7. Indexation sémantique — **seulement les dossiers de savoir touchés par
   cette ingestion** : `sources`, et `concepts`/`entites` si des pages y ont
   été touchées. Chacun a son propre index (la liste des dossiers indexables
   est donnée par
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index-targets.sh"`).
   **Ne jamais indexer `transcriptions/`** : c'est un choix de conception, pas
   un oubli — un corpus de messages se lit en entier, et un classement ne
   garantirait pas l'exhaustivité qu'on lui demanderait.
   Outil MCP `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
   `directory: $VAULT/wiki/<dossier>` **explicite**, un appel par dossier —
   jamais `$VAULT/wiki` seul, que le moteur indexerait récursivement et qui
   vectoriserait deux fois les sous-dossiers.
   Sans le plugin agentic-toolbox :
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh" "$VAULT/wiki/<dossier>"`
   par dossier, ou sans argument pour tout réindexer.
   Incrémental — seuls les chunks des notes créées/modifiées coûtent un appel
   API. **Échec = non bloquant** : l'ingestion reste valide ; noter que
   l'indexation se rattrapera au prochain `/doc-query`.

## Compte rendu

Lister les fichiers créés/modifiés (chemins relatifs au vault) et les callouts
posés, le cas échéant, **en séparant les deux natures** : `> [!warning]`
(réserves documentaires, définitives) et `> [!question]` (contradictions en
attente d'arbitrage). Pour une source conversationnelle, dire explicitement
combien de messages la transcription contient et sur quelle période — c'est ce
qui permet de repérer une transcription tronquée.
Terminer par l'état de l'indexation, **par dossier** :
`<dossier> : <embedded_chunks>/<reused_chunks>`, ou « ⚠ indexation sémantique
échouée (<raison>) — à rattraper » si l'étape 7 a échoué.
