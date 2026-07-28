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
├── INDEX.md                 ← carte du vault, point d'entrée de toute recherche — dérivé, régénérable
├── BENCH.md                 ← banc de questions de référence (/doc-bench) — optionnel, hors index
├── LOG/                     ← journal append-only : un fichier par jour (YYYY-MM-DD.md)
├── inbox/                   ← sas : dépôts bruts en attente d'ingestion
├── archives/                ← pièces d'origine conservées après ingestion (hors index)
├── wiki/
│   ├── sources/             ← couche IMMUABLE : une note par source, jamais réécrite
│   ├── transcriptions/      ← couche IMMUABLE : un dossier par conversation, texte intégral (NON vectorisé)
│   │   └── <conversation>/  ← les notes du fil
│   ├── concepts/            ← couche vivante : pages de concepts
│   ├── entites/             ← couche vivante : personnes, outils, projets
│   └── syntheses/           ← réponses de /doc-query sauvegardées
```

**Un index sémantique par dossier de savoir**, dans le dossier lui-même
(`concepts/.index/`, `entites/.index/`, `syntheses/.index/`,
`sources/.index/` — dérivés jetables, ne pas y toucher). Ce n'est pas un
détail d'implémentation : chaque dossier est un **espace vectoriel séparé**,
donc les notes ne concourent qu'entre semblables. Une entité de dix lignes ne
peut plus être écrasée par un gros extrait d'une source de trois cents. C'est
ce qui rend la recherche utilisable sans réglage de score.

**`transcriptions/` n'est pas vectorisé**, délibérément. Ce qu'on demande à un
corpus de messages est presque toujours exhaustif (« tous les messages qui… »),
or un index rend les K meilleurs résultats, jamais l'ensemble des résultats
qualifiants : il faut lire les conversations en entier — et dès lors qu'on lit
tout, l'ordre de lecture ne change plus rien. On y accède donc par le condensé
de `sources/` (vectorisé, il désigne quelle conversation ouvrir et pointe
dessus en wikilink), par grep, et par lecture intégrale.

Conséquence : **une note posée directement à la racine de `wiki/` n'est
indexée par rien** — toute note de savoir vit dans un de ces dossiers. Et
`transcriptions/` ne contient que des dossiers, jamais de note en direct : le
dossier est l'unité de conversation.

## Conventions de notes

- **Français.** Notes courtes et denses : une idée par note, aucun remplissage,
  aucun distracteur.
- Nommage : `kebab-case.md` ; sources préfixées `YYYY-MM-DD-`.
- **Modèle de note — frontmatter obligatoire** (une note sans ces propriétés
  n'est pas conforme ; `/doc-lint` les vérifie) :
  - toutes les notes : `type` (source | transcription | concept | entite |
    synthese),
    `date` (date de création `YYYY-MM-DD`, jamais modifiée ensuite),
    `auteur` (qui a créé la note : la personne pilotant la session — la
    demander une fois si inconnue, puis réutiliser — ou le nom de l'équipe
    tierce pour une note importée) et `description` (la note en quelques
    mots — c'est elle qui alimente l'entrée `INDEX.md` de la note) ;
  - `type: source` : `origine` — provenance de la note : chemin archivé
    relatif au vault (pièce dans `archives/`), URL, ou mention libre
    (« conversation », …) ; `original` en plus, seulement si la pièce
    d'origine diffère de la copie pointée par `origine` (ex. le PDF dont la
    note vient par OCR) : chemin de sa copie dans `archives/`, ou emplacement
    durable hors vault (URL, dossier partagé). **Jamais de chemin absolu de
    la machine** (`/home/...`, `/mnt/...`, `C:\...`) dans `origine`/`original` :
    un fichier local ingéré est copié dans `archives/` et référencé
    relativement au vault ;
  - `type: transcription` : `origine` (même règle que pour une source : les
    pièces d'`archives/` dont vient le texte — captures dans leur ordre,
    export brut), `conversation` (le nom du fil, identique au dossier qui la
    porte), `participants` (liste), et `periode` (`YYYY-MM-DD → YYYY-MM-DD`)
    quand elle est connue ;
  - `type: synthese` : `question` — la question posée ; `perimetre` si la
    recherche visait un dossier voisin du vault.

  Optionnel partout : `tags`, `aliases` (liste de noms alternatifs de la
  page — après une fusion de doublons, le nom de la page absorbée vit ici :
  les wikilinks `[[ancien-nom]]` continuent de résoudre dans Obsidian et
  `/doc-lint` ne les compte pas comme pendants), et toute propriété utile au cas particulier
  (ex. `image`, `capture_precedente`/`capture_suivante` pour une série de
  captures d'écran — lues visuellement, jamais passées à l'OCR : un OCR
  documentaire détruit l'attribution du locuteur, qui tient à la position des
  bulles) — enrichir librement, ne jamais retirer une propriété obligatoire.
- Avant de créer une page dans `concepts/` ou `entites/` : vérifier qu'aucune
  page existante ne couvre déjà le sujet — nom normalisé (casse, accents,
  tirets), alias `aliases:`, libellé proche. En cas de doute, **enrichir
  l'existante** plutôt que créer un doublon : un savoir éclaté entre
  `Docker.md` et `conteneurisation-docker.md` fragmente le graphe et fausse
  les recherches (`/doc-lint` détecte les doublons suspectés, mais la
  prévention se joue ici).
- Wikilinks `[[...]]` libéraux vers les concepts et entités. Toute référence
  à une autre note du vault s'écrit en wikilink, **jamais en chemin brut** :
  seuls les wikilinks créent des liens (graphe Obsidian, backlinks, détection
  d'orphelines par `/doc-lint`). Exceptions : les propriétés `origine`/
  `original` (pointent vers `archives/` ou hors vault — hors graphe, voulu).
- Citations verbatim ≤ 125 caractères ; au-delà, paraphraser — le verbatim long
  reste dans `wiki/sources/`.
- **Deux callouts, et deux seulement**, ont un sens dans le vault. Ils ne se
  distinguent pas par leur gravité mais par leur **durée de vie** — l'un est
  définitif, l'autre est une tâche en attente. Ne jamais les confondre :
  `/doc-lint` les compte séparément et ne réclame que le second.
  - `> [!warning]` — **mise en garde documentaire** : une réserve sur la pièce
    elle-même (OCR partiel ou illisible, capture non datée, propos rapporté,
    document non signé, expéditeur non identifié, date déduite). Rien à
    trancher : c'est un fait constaté sur la source. **Permanente** — elle vit
    surtout dans `wiki/sources/`, immuable, et n'est jamais retirée.
  - `> [!question]` — **contradiction non tranchée** : deux affirmations
    incompatibles sans savoir laquelle fait foi. Appelle un arbitrage de
    l'utilisateur et **disparaît** une fois tranchée. Elle ne se pose donc
    **jamais dans `wiki/sources/`** : la couche est immuable, un callout posé
    là ne pourrait plus jamais être retiré. Sa place est sur la page
    `concepts/`, `entites/` ou `syntheses/` qui porte l'affirmation.
- Contradiction entre une nouvelle information et l'existant — jamais résolue
  silencieusement, deux issues :
  - **tranchée** (l'utilisateur confirme que la nouvelle version fait foi) →
    mettre à jour la valeur courante dans le corps de la note, et pousser
    l'ancienne dans une section `## Historique` en fin de note (append-only) :
    `- [YYYY-MM-DD] <ancienne affirmation> — remplacée par : <la nouvelle,
    wikilink vers sa source>`. Une seule vérité lisible en tête de note,
    l'historique conservé dessous ;
  - **non tranchée** (impossible de savoir laquelle fait foi) → callout
    `> [!question]` sur la page concept/entité concernée, décrivant les deux
    versions et pointant chacune vers sa source en wikilink, à résoudre en
    conversation — `/doc-lint` rappelle ceux en souffrance.

## Règles de maintenance

- `wiki/sources/` et `wiki/transcriptions/` sont **immuables** : ni une note de
  source ni une transcription n'est modifiée après son ingestion.
- Une **source conversationnelle** (captures d'écran d'un fil, export d'un outil de messagerie) produit **deux notes**, et elles ne font pas double emploi :
  - le **condensé** dans `wiki/sources/` — 2 à 5 enseignements, citations
    courtes, wikilinks : c'est ce qu'on lit ;
  - la **transcription intégrale** dans
    `wiki/transcriptions/<conversation>/` — **un message par bloc**, avec
    auteur et horodatage quand ils sont lisibles : c'est ce qu'on fouille.
    Sans elle, une question comme « tous les messages où X reconnaît Y » n'a
    aucune matière à interroger — seuls les quelques enseignements retenus
    seraient cherchables.
  Les deux se pointent mutuellement en wikilink, et `origine` renvoie dans les
  deux cas aux pièces d'`archives/`.
  Un fil très long se découpe en plusieurs notes **dans le même dossier**
  (`2026-03.md`, `2026-04.md`…) : le dossier reste l'unité de conversation.
- Toute écriture dans `wiki/` met à jour `INDEX.md` **dans la foulée**.
  `INDEX.md` est un **dérivé** : chaque entrée vient du frontmatter de la note
  (`- [[<slug>]] — <description>`) et `/doc-lint` sait le régénérer
  entièrement — en cas de conflit de synchro ou de doute, régénérer plutôt
  que réparer.
- Le journal `LOG/` est **append-only, un fichier par jour**
  (`LOG/YYYY-MM-DD.md`, créé au besoin — jamais de fichier unique partagé) :
  entrées `## [YYYY-MM-DD] <action> | <titre>` (actions : `init`, `ingest`,
  `lint`, `synthese`, `bench`), suivies d'une ligne de détail. Ne jamais modifier une
  entrée existante. Un `LOG.md` racine hérité d'une version antérieure est
  **gelé** : il se consulte, on n'y écrit plus.
- `inbox/` est un **sas**, pas un stockage : un fichier ingéré avec succès est
  **déplacé vers `archives/`** (jamais supprimé) ; un fichier local ingéré
  depuis l'extérieur du vault y est **copié** (l'original de l'utilisateur
  n'est pas touché) — le condensé vit dans `wiki/sources/`, la pièce
  d'origine reste vérifiable dans le vault, qui voyage ainsi d'un bloc
  (auto-porteur).
- Dépôts automatiques `inbox/session-*.md` (`type: session` : transcript de
  session Claude Code déposé par le plugin avant compactage) : s'ingèrent
  comme le reste du sas, avec une règle de densité — un transcript est verbeux
  et peu dense, n'en extraire que les **décisions prises et les faits
  durables**, jamais le déroulé ; le brut part en `archives/` comme toute
  pièce ingérée. Un dépôt sans enseignement durable s'archive directement,
  sans note source.
- `archives/` est immuable comme `wiki/sources/`. Les fichiers archivés
  gardent leur nom et leur extension ; l'index sémantique ne couvre que
  `wiki/`, les archives restent donc hors index (zéro coût, zéro bruit).
  **Obsidian, lui, indexe tout le vault** : exclure `archives/` dans
  Paramètres → Fichiers et liens → Filtres d'exclusion, sinon les markdown
  OCR y référencent des images non extraites, qui apparaissent en nœuds
  fantômes dans le graphe — et un clic sur l'un d'eux crée une note vide à la
  racine du vault.
  Attention avant de partager le vault : les archives peuvent
  contenir des données sensibles que les notes condensées ont volontairement
  écartées.

## Règles de recherche (pour les sub-agents)

- Point d'entrée : `INDEX.md`, puis suivre les wikilinks des notes pertinentes.
- Compléter par grep sur les mots-clés de la question **et leurs synonymes /
  variantes françaises**.
- **Les transcriptions ne sont pas vectorisées** : on les atteint par le
  condensé de `sources/` qui pointe dessus en wikilink, par grep, et par
  lecture.
- **Question exhaustive** — « tous les messages qui… », « combien de fois… »,
  « liste tous les… » : aucun classement ne peut y répondre. Un index rend les
  K meilleurs résultats, jamais l'ensemble des résultats qualifiants —
  demander 5 en rend 5, même si quarante messages conviennent. L'exhaustivité
  vient de la **lecture intégrale** des dossiers
  `transcriptions/<conversation>/` retenus. Ne jamais conclure « tous les X »
  sur la foi d'extraits remontés, et dire quelles conversations ont été
  balayées quand la couverture est partielle.
- Ne remonter au contexte principal **que** la réponse citée (avec les chemins
  des notes sources, relatifs au vault) — jamais le contenu brut des notes.
- Un passage trouvé sous une section `## Historique` est une version périmée :
  ne jamais le citer comme état courant — la vérité est en tête de note.
- Rien de pertinent trouvé : le dire explicitement et lister ce qui s'en rapproche.
