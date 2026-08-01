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
    disponible, sinon la porte en ligne de commande du moteur :
    `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-ocr.sh" <fichier> [<sortie>]`), dépôt dans `$VAULT/inbox/`, puis mesure du markdown
    obtenu. C'est son terrain : mise en page structurée, texte au fil des
    pages.
  - **Capture d'écran** (`.png`, `.jpg`, `.jpeg`, `.webp`, `.heic`…) →
    **jamais d'OCR**. Un OCR documentaire est réglé pour une mise en page de
    document ; sur une capture d'interface, il rend un flux linéaire où la
    disposition — colonnes, encadrés, alignements — a disparu, et avec elle
    une partie du sens. Le sub-agent lecteur **ouvre l'image directement**
    (outil Read, qui affiche les images) et en produit lui-même la version
    standardisée. Trois
    conséquences :
    - pas de mesure par `wc -c` — une image ne se compte pas en octets de
      texte. Des captures qui forment **un même ensemble** comptent pour UNE
      source, qu'un seul lecteur ouvre dans l'ordre (une dizaine au plus par
      lecteur ; au-delà, découper en tranches et appliquer le montage gros
      volume) ;
    - mission de lecture explicite : restituer la structure lisible à
      l'écran, l'ordre, les dates visibles ; et **signaler tout passage
      illisible, coupé ou ambigu plutôt que de le deviner** — ce sera un
      `> [!warning]` sur la note source ;
    - c'est l'**image elle-même** qui est archivée et que pointe `origine:`.
      Aucun markdown intermédiaire n'est produit, donc aucune référence
      d'image pendante à traîner ensuite dans le graphe.
  - **Texte lisible tel quel** — `.md`, `.txt`, `.csv`, `.tsv`, `.json`,
    `.xml`, `.html`, `.eml`, code source, export brut → transmis au lecteur
    sans conversion, mesure par `wc -c`.
  - **Bureautique binaire** — `.xlsx`, `.ods`, `.docx`, `.odt`, `.pptx`… →
    **illisibles tels quels**, et il est hors de question d'en deviner le
    contenu. Convertir d'abord avec ce qui est présent sur la machine
    (`libreoffice --headless --convert-to csv|txt|pdf`, `pandoc`…), dépôt du
    résultat dans `$VAULT/inbox/`, puis router le résultat comme une source
    texte ou paginée. **Aucun convertisseur disponible → le dire et demander à
    l'utilisateur une version texte, CSV ou PDF.** Ne jamais présenter un
    binaire à un lecteur.
    La conversion perd formules, mise en forme et onglets masqués : c'est le
    fichier d'origine qui est archivé et que pointe `origine:`, jamais sa
    conversion seule.
  - **Archive** — `.zip`, `.tar.gz`… → décompresser dans un sous-dossier
    d'`inbox/`, puis appliquer le montage « lot de fichiers » à son contenu.
  - **Audio, vidéo** → hors périmètre du plugin. Le dire, et proposer
    d'ingérer une version texte si l'utilisateur en a une.
  - **URL** → taille inconnue : partir du montage nominal, le lecteur signale
    s'il déborde.
  - **Format non identifié** → ne **jamais** deviner : `file <chemin>` pour
    l'identifier, puis rattacher à l'une des natures ci-dessus. Toujours
    indéterminé → demander à l'utilisateur ce qu'est ce fichier et comment il
    veut qu'on le traite. Une ingestion ratée pollue une couche immuable.

  Puis choisir le montage :

  **Montage nominal — source unique ≤ ~150 Ko de texte** : un **sub-agent
  lecteur** (outil Agent, en avant-plan — `run_in_background: false`) avec
  pour mission :
  1. lire la source — fichier local (chemin transmis), URL (WebFetch) ;
  2. **écrire lui-même la version standardisée** dans
     `$VAULT/inbox/<slug>.standardise.md` : tout le texte de la pièce en
     markdown structuré, fidèle et sans tri. Il l'**écrit sur disque**, il ne
     la retourne pas — c'est ce qui permet de garder le texte intégral sans
     qu'il traverse aucun contexte. Le fichier reste dans le sas tant que
     l'ingestion n'est pas validée ;
  3. rédiger le **dossier d'ingestion** : les enseignements clés (une ligne
     chacun), **autant qu'en porte la source** — pas de plafond : un article
     en donne deux, un document de cent pages en donne trente, et les brider
     reviendrait à jeter ce qu'on vient d'ingérer. Le critère est la qualité,
     pas le nombre : une idée par enseignement, aucun qui n'apporte un fait
     durable, aucun remplissage. Pour chacun une citation verbatim ≤ 125
     caractères, les concepts/entités candidats (wikilinks), et une
     description en quelques mots pour l'INDEX ;
  4. ne retourner QUE ce dossier et le chemin du fichier standardisé — jamais
     la source brute, jamais ce fichier lui-même, jamais de longs
     extraits. S'il constate en lisant que la source dépasse ce qu'il peut
     traiter proprement, il retourne un **plan de découpe** (structure et
     bornes) au lieu d'un dossier — basculer alors sur le montage suivant.

  **Gros volume — source unique > ~150 Ko** : découper en tranches ≤ ~150 Ko
  par la structure (sections markdown, chapitres, plages de pages, plages de
  lignes pour un tabulaire — repérée par grep/offsets, sans lire le contenu en
  contexte principal). **Un lecteur
  par tranche**, lancés en parallèle (4 au plus à la fois) ; chacun écrit la
  version standardisée de SA tranche
  (`$VAULT/inbox/<slug>.standardise-<n>.md`, numérotée dans l'ordre) et rend
  un dossier partiel. Puis un **sub-agent synthétiseur** reçoit les dossiers
  partiels (jamais les sources ni les fichiers standardisés) et les
  **assemble** en
  un dossier d'ingestion
  global — il dédoublonne et organise, il ne **comprime pas** : ramener cent
  pages à cinq lignes perdrait l'essentiel de ce qui vient d'être lu. Le
  dossier garde une section par partie de la source. C'est lui l'interlocuteur
  de la validation.
  Retouche exigeant un retour à la source → relancer un lecteur sur la
  tranche concernée et transmettre sa réponse au synthétiseur.

  **Lot de fichiers (plusieurs chemins, un dossier, inbox/ entier)** : le
  modèle reste « une note par source » — mais **une source n'est pas
  forcément un fichier**. Avant de répartir les lecteurs, **regrouper le lot
  en sources**, et le faire valider :
  - plusieurs fichiers qui forment **un même ensemble** comptent pour UNE
    source, qu'un seul lecteur ouvre dans l'ordre. Le nom de fichier est un
    indice **faible** — un préfixe commun ou une numérotation continue ne
    prouvent rien, et deux pièces sans rapport peuvent se ressembler. Ce qui
    tranche, c'est le **contenu** : ouvrir le premier fichier de chaque groupe
    pressenti et vérifier qu'ils se poursuivent réellement l'un l'autre. Un
    sous-dossier dédié reste le seul indice de nom qui vaille. Dans le doute,
    **demander** plutôt que découper — mais un mauvais découpage n'est plus
    fatal : `/doc-repair` corrige après coup sans tout refaire ;
  - un document, un export, un article = une source chacun.

  Annoncer le regroupement retenu avant de lancer quoi que ce soit
  (« <n> fichiers → <m> sources : … »), puis un lecteur par **source**
  (parallèle, 4 au plus), validation présentée source par source (l'affichage
  peut être groupé, l'accord est explicite par source) et écriture par source.
  Une source du lot dépasse le seuil → lui appliquer le montage gros volume.

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

1. Proposer les enseignements extraits de la source, **écrits en clair dans le
   corps de la réponse** (liste numérotée, une ligne chacun). Au-delà d'une
   dizaine, **valider par tranches** — présenter les enseignements d'une partie
   de la source, recueillir l'accord, passer à la suivante : une liste de
   quarante lignes validée d'un bloc n'est plus une validation.
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

Une même pièce produit **deux notes**, qui partagent le slug
`YYYY-MM-DD-<slug>` et se pointent mutuellement en wikilink. Elles ne font pas
double emploi : l'une est fidèle, l'autre est utile.

1. `$VAULT/wiki/sources/YYYY-MM-DD-<slug>.md` — **le texte intégral
   standardisé** de la pièce. Frontmatter conforme au modèle de note
   d'`INSTRUCTIONS-CLAUDE.md` (`type: source`, `date`, `auteur` — repérable
   dans les notes existantes du vault, sinon le demander —, `description`,
   `origine` = chemin archivé/URL/« conversation », `original` seulement si la
   pièce d'origine diffère de la copie pointée par `origine` — **jamais un
   chemin absolu de la machine**).
   Corps : le fichier standardisé que le lecteur a déposé dans `inbox/` —
   **déplacée telle quelle**, jamais relue ni réécrite en contexte principal
   (le seul frontmatter est ajouté en tête). Elle contient tout le texte de la
   pièce en markdown structuré : titres pour ses sections réelles, listes,
   tableaux. Fidèle et sans tri — on ne résume pas, on ne choisit pas, on
   reporte. C'est cette couche qui garantit qu'aucune information ingérée
   n'est perdue, et c'est elle qu'on fouille quand l'enseignement ne suffit
   plus.
   Plusieurs tranches (gros volume) → les concaténer dans l'ordre, ou en faire
   autant de notes numérotées si l'ensemble reste trop gros pour une seule.
   Réserve constatée sur la pièce — OCR partiel, capture non datée, propos
   rapporté, document non signé, date déduite → callout `> [!warning]` ici,
   permanent : il décrit la pièce, il n'y a rien à trancher. **Jamais de
   `> [!question]`** dans cette couche ni dans la suivante, toutes deux
   immuables.
   Note trop volumineuse → la découper par la structure réelle de la pièce
   (`YYYY-MM-DD-<slug>-1.md`, `-2.md`…), chacune renvoyant à la suivante en
   wikilink ; jamais par une coupe arbitraire au milieu d'une section.
   **Ingestion abandonnée** (l'utilisateur refuse) → supprimer les fichiers
   `*.standardise*.md` du sas : rien ne reste en attente.
2. `$VAULT/wiki/enseignements/YYYY-MM-DD-<slug>.md` — **ce qu'on en retient**.
   Frontmatter `type: enseignements`, même `origine`, wikilink vers la note de
   source. Corps : **un titre `###` par enseignement**, chacun suivi de sa
   citation verbatim ≤ 125 caractères et des wikilinks vers les
   concepts/entités concernés.
   Le `###` n'est pas cosmétique : le découpage sémantique se fait par titre,
   donc un enseignement devient exactement un extrait indexé — ni dilué dans
   ses voisins, ni coupé en deux.
3. Pour chaque concept ou entité touché : créer ou mettre à jour la page dans
   `$VAULT/wiki/concepts/` ou `$VAULT/wiki/entites/` (frontmatter `type: concept`
   ou `type: entite` + `date` + `auteur` + `description` à la création,
   paraphrase, **wikilink retour vers la note d'enseignements** — c'est elle
   qui porte l'affirmation et sa citation ; le texte intégral se rejoint
   ensuite d'un saut, depuis cette note).
   Ces pages sont la **seule couche organisée par sujet** : `sources/` et
   `enseignements/` sont organisées par pièce, et aucune ne peut répondre à
   une question qui traverse plusieurs pièces. Ce sont aussi les seules
   **vivantes** — elles se réécrivent au fil des ingestions, alors que les
   deux couches d'origine sont figées —, et donc le seul endroit où une
   contradiction s'arbitre.
   **Avant de créer** : vérifier qu'aucune page
   vivante existante ne couvre déjà le sujet — nom normalisé (casse, accents,
   tirets), alias `aliases:`, libellé proche — et en cas de doute enrichir
   l'existante plutôt que créer un doublon.
   Contradiction avec le contenu existant → convention
   d'`INSTRUCTIONS-CLAUDE.md` : la trancher avec l'utilisateur (la validation
   est le bon moment) → valeur courante mise à jour dans le corps + entrée
   `## Historique` en fin de note ; impossible à trancher → callout
   `> [!question]` **sur cette page** (jamais dans `sources/` ni
   `enseignements/`, immuables : on ne pourrait plus l'en retirer une fois
   tranché), décrivant les deux
   versions et pointant chacune vers sa source en wikilink, signalé à
   l'utilisateur.
4. Mettre à jour `$VAULT/INDEX.md` : ajouter chaque nouvelle note dans sa
   section, sous forme `- [[<slug>]] — <description>` — la même `description`
   que le frontmatter (INDEX est un dérivé du frontmatter, mêmes mots aux
   deux endroits). Les deux notes d'une même pièce y figurent, chacune dans sa
   section.
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
7. Indexation sémantique — **seulement les dossiers touchés par cette
   ingestion** : `sources` et `enseignements`, plus `concepts`/`entites` si
   des pages y ont été touchées. Chacun a son propre index (la liste des dossiers indexables est
   donnée par
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index-targets.sh"`).
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
attente d'arbitrage). Terminer par l'état de l'indexation, **par dossier** :
`<dossier> : <embedded_chunks>/<reused_chunks>`, ou « ⚠ indexation sémantique
échouée (<raison>) — à rattraper » si l'étape 7 a échoué.
