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
│   ├── sources/             ← couche IMMUABLE : le texte intégral standardisé d'une pièce
│   ├── enseignements/       ← couche IMMUABLE : ce qu'on retient d'une pièce, un ### par enseignement
│   ├── concepts/            ← couche vivante : pages de concepts
│   ├── entites/             ← couche vivante : personnes, outils, projets
│   └── syntheses/           ← réponses de /doc-query sauvegardées
```

**Trois degrés de fidélité, du plus travaillé au plus brut.** Une même pièce
existe à trois endroits, et on descend d'un cran à chaque fois qu'un doute
persiste :

1. `wiki/enseignements/<slug>.md` — ce qu'on en a retenu, un enseignement par
   titre `###`, avec sa citation courte. C'est ce qu'on lit ;
2. `wiki/sources/<slug>.md` — le **texte intégral** de la pièce, converti en
   markdown structuré, fidèle et sans tri. C'est ce qu'on fouille quand
   l'enseignement ne suffit pas.
   « Structuré » a un sens précis : le découpage sémantique se fait **par
   titre**, et retombe sur les paragraphes au-delà d'environ 2 000 caractères.
   Une source bien standardisée est donc celle où **aucun bloc de cette taille
   ne reste sans titre** — la structure réelle de la pièce devient la
   hiérarchie de titres, et chaque unité de sens devient un extrait
   retrouvable. Sans ça, le moteur coupe où il peut, au milieu d'un article ;
**Une série d'entrées datées** — un relevé, un journal, une suite de captures
d'un même écran — se standardise avec **un titre `###` par entrée**, comme les
enseignements : chacune devient alors un extrait indexé à elle seule, et se
retrouve individuellement. Sans ces titres, tout le fichier part en un ou deux
extraits et l'entrée précise devient introuvable.
Quand les entrées ne portent qu'une date partielle — une heure sans jour, un
jour sans année —, **demander l'ancrage à l'utilisateur** avant de
standardiser, et le noter en frontmatter. Ne jamais le déduire : une année
devinée dans une couche immuable est une erreur qu'on ne verra plus jamais.

3. `archives/<nom d'origine>` — la **pièce elle-même**, telle qu'elle est
   arrivée. Jamais indexée, jamais modifiée. C'est ce qui fait foi quand le
   texte standardisé est mis en doute.
   La **transcription fidèle** y est archivée avec la pièce : ce ne sont pas
   deux exemplaires du même objet — l'une est ce qui a été lu, le degré 2 en
   est la version structurée. La garder permet de vérifier le degré 2 sans
   relire la pièce. Vrai pour un document, dont l'OCR fournit la
   transcription ; vrai aussi pour une image, dont le lecteur l'écrit — et là
   c'est encore plus décisif, relire une série de captures coûtant bien plus
   qu'un OCR.

Les deux notes portent le même `<slug>` et se pointent mutuellement en
wikilink ; leur `origine` désigne la pièce d'`archives/`. Un doute se remonte
donc toujours dans le même sens : enseignement → texte → pièce.

**Ce slug partagé impose la forme du wikilink entre elles** : `[[sources/<slug>]]`
et `[[enseignements/<slug>]]`, **préfixés du dossier**. Un `[[<slug>]]` nu
désignerait deux fichiers à la fois et Obsidian choisirait pour vous. Cette
forme vaut pour ces deux couches et pour l'`INDEX.md` ; partout ailleurs, les
noms étant uniques, le nom nu reste la règle.

**Un index sémantique par dossier**, dans le dossier lui-même
(un `.index/` dans chacun des cinq dossiers — dérivés jetables, ne pas y
toucher). Ce n'est pas un détail d'implémentation : chaque dossier est un
**espace vectoriel séparé**, donc les notes ne concourent qu'entre semblables.
Une entité de dix lignes ne peut plus être écrasée par un extrait d'un texte
intégral de trois cents, et surtout **on peut chercher dans une couche sans
l'autre** — interroger les enseignements sans que les textes intégraux
saturent les résultats, puis descendre d'un cran si le doute persiste. Le
nombre d'index ne dépend pas du nombre de sources : cinq, quelle que soit la
taille du vault.

Conséquence : **une note posée directement à la racine de `wiki/` n'est
indexée par rien** — toute note vit dans un de ces dossiers.

## Conventions de notes

- **Français.** Notes courtes et denses : une idée par note, aucun remplissage,
  aucun distracteur.
- Nommage : `kebab-case.md`. Une pièce datée préfixe ses deux notes de la
  **date de la pièce**, `YYYY-MM-DD-` — jamais la date d'ingestion, qui ne dit
  rien d'elle. Une pièce **non datée** (lettre sans date, capture sans
  horodatage) n'est pas préfixée : ne jamais inventer ni déduire une date pour
  satisfaire la forme. L'absence de préfixe est alors une information, et elle
  s'accompagne d'un `> [!warning]` sur la note de source.
- **Modèle de note — frontmatter obligatoire** (une note sans ces propriétés
  n'est pas conforme ; `/doc-lint` les vérifie) :
  - toutes les notes : `type` (source | enseignements | concept | entite |
    synthese),
    `date` (date de création `YYYY-MM-DD`, jamais modifiée ensuite),
    `auteur` (qui a créé la note : la personne pilotant la session — la
    demander une fois si inconnue, puis réutiliser — ou le nom de l'équipe
    tierce pour une note importée) et `description` (la note en quelques
    mots — c'est elle qui alimente l'entrée `INDEX.md` de la note) ;
  - `type: source` : `origine` — ce dont la note a été faite : chemin archivé
    relatif au vault, URL, ou mention libre. `original` en plus, seulement si
    la pièce qui fait foi en diffère — le PDF dont la transcription est tirée,
    ou un emplacement durable hors vault. **Jamais de chemin absolu de la
    machine** — un fichier local ingéré est copié dans `archives/` et
    référencé relativement au vault ;
  - `type: enseignements` : `origine` (même pièce que la note de source
    correspondante) et un wikilink vers cette note ; le corps est une suite de
    titres `###`, un par enseignement, chacun suivi de sa citation verbatim et
    des wikilinks vers les concepts/entités concernés. Le `###` n'est pas
    cosmétique : le découpage sémantique se fait par titre, donc un
    enseignement = un extrait indexé, ni dilué dans ses voisins ni coupé en
    deux.
  - `type: synthese` : `question` — la question posée ; `perimetre` si la
    recherche visait un dossier voisin du vault.

  Optionnel partout : `tags`, `aliases` (liste de noms alternatifs de la
  page — après une fusion de doublons, le nom de la page absorbée vit ici :
  les wikilinks `[[ancien-nom]]` continuent de résoudre dans Obsidian et
  `/doc-lint` ne les compte pas comme pendants), et toute propriété utile au cas particulier
  (ex. `image`, `capture_precedente`/`capture_suivante` pour une série de
  captures d'écran) — enrichir librement, ne jamais retirer une propriété
  obligatoire.
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
    elle-même. Rien à trancher : c'est un fait constaté. **Permanente**, elle
    n'est jamais retirée.
    Sa place est dans **`wiki/enseignements/`**, sous son propre titre `###`,
    jamais dans `wiki/sources/`. Une réserve n'est pas ce que la pièce *dit*,
    c'est ce qu'on en *constate* — donc un enseignement comme un autre, et
    c'est bien la couche du constat. La conséquence est double : `sources/`
    reste du texte de pièce pur, cherchable comme tel sans qu'un commentaire
    éditorial s'y mêle ; et la réserve devient un extrait indexé à elle seule,
    donc retrouvable — « quelles pièces ne sont pas signées ? » a une réponse.
    Le critère : **ce qui change ce que la pièce vaut**. Document tronqué, non
    daté, non signé, signataire manquant, expéditeur non identifié, OCR partiel
    ou illisible, en-tête d'une autre société, propos rapporté, date déduite.
    Pas les coquilles ni les fautes d'accord : ce sont des défauts du texte,
    pas de la pièce, et ils n'enlèvent rien à ce qu'elle prouve.
  - `> [!question]` — **contradiction non tranchée** : deux affirmations
    incompatibles sans savoir laquelle fait foi. Appelle un arbitrage de
    l'utilisateur et **disparaît** une fois tranchée. Elle ne se pose donc
    **jamais dans `wiki/sources/` ni `wiki/enseignements/`** : ces couches sont
    immuables, un callout posé là ne pourrait plus jamais être retiré. Sa place
    est sur la page `concepts/`, `entites/` ou `syntheses/` qui porte
    l'affirmation.
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

- `wiki/sources/` et `wiki/enseignements/` sont **immuables** : ni le texte
  d'une pièce ni ce qu'on en a retenu ne sont réécrits au fil de l'eau. La
  seule modification autorisée passe par `/doc-repair`, qui corrige une erreur
  constatée et la journalise — jamais une édition silencieuse.
- `archives/` ne se corrige **jamais**, par `/doc-repair` ni autrement : la
  pièce d'origine est la preuve. Si elle est fausse, c'est un fait sur la
  pièce, à consigner ; ce qu'on corrige, c'est ce que le vault en a dit.
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
  **Obsidian, lui, indexe tout le vault** : exclure `archives/` **et
  `inbox/`** dans Paramètres → Fichiers et liens → Filtres d'exclusion
  (`/vault-init` le fait), sinon les markdown
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
- **Question exhaustive** — « tous les… », « combien de fois… », « liste tous
  les… » : aucun classement ne peut y répondre. Un index rend les K meilleurs
  résultats, jamais l'ensemble des résultats qualifiants : en demander 5 en
  rend 5, même si quarante notes conviennent. L'exhaustivité vient de la
  **lecture** des notes retenues. Ne jamais conclure « tous les X » sur la foi
  d'extraits remontés, et dire ce qui n'a pas été couvert quand la couverture
  est partielle.
- Ne remonter au contexte principal **que** la réponse citée (avec les chemins
  des notes sources, relatifs au vault) — jamais le contenu brut des notes.
- Un passage trouvé sous une section `## Historique` est une version périmée :
  ne jamais le citer comme état courant — la vérité est en tête de note.
- Rien de pertinent trouvé : le dire explicitement et lister ce qui s'en rapproche.
