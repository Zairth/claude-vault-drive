---
description: Ingérer une source dans le vault Obsidian — lecture, standardisation, wiki, INDEX, LOG, vérification
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
  pas de sub-agent, passer directement au contrôle avant écriture.
- Fichier local, élément d'`inbox/`, URL, PDF, capture d'écran → **NE JAMAIS
  lire la source en contexte principal** (anti-saturation : sur un gros
  volume, l'ingestion ferait déborder la session).

  **Router d'abord selon la nature de la source** — l'OCR n'est pas un passage
  obligé, c'est un outil à documents :

  - **PDF** → **tester d'abord s'il porte une couche de texte**, avant toute
    idée d'OCR. Un PDF produit par un logiciel (export tableur, traitement de
    texte, facture générée) contient le texte tel que le logiciel l'a écrit :
    l'extraire est **exact, gratuit et instantané**. Le passer à l'OCR revient
    à le photographier pour deviner ce qu'on pouvait lire — et un OCR se
    trompe : il confond des mots voisins, et il le fait **systématiquement**,
    remplaçant partout la même valeur par la même autre. L'erreur est alors
    invisible, parce que le résultat reste plausible et cohérent avec
    lui-même.
    Le plugin embarque l'extracteur, précisément pour que ce test ne dépende
    d'aucune installation :
    `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pdf-text.py" <fichier> [<sortie>]`
    — bibliothèque standard seule, aucun réseau, aucune clé. Il rend le texte
    et sort en **0** ; il sort en **1** avec un message explicite quand le PDF
    ne porte pas de couche de texte exploitable, et c'est ce code de sortie
    qui décide : 0 → **c'est lui la transcription**, dépôt dans
    `$VAULT/inbox/`, pas d'OCR, pas d'appel API ; 1 → passer à la ligne
    suivante.
    Il ne reconstruit pas la mise en page : la sortie est le texte dans
    l'ordre où le PDF le dessine, cellule après cellule pour un tableau. C'est
    la standardisation qui lui rend sa structure, comme pour toute autre
    source.
  - **Scan, photo de document, PDF sans couche de texte** → là seulement,
    conversion markdown par OCR (outil MCP
    `mcp__plugin_agentic-toolbox_toolbox__ocr_convert` si disponible, sinon la
    porte en ligne de commande du moteur :
    `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-ocr.sh" <fichier> [<sortie>]`),
    dépôt dans `$VAULT/inbox/`, puis mesure du markdown obtenu. C'est son
    terrain : une page dont il n'existe aucune autre lecture que l'image.
    Le noter dans la note d'enseignements par un `> [!warning]` : une pièce
    lue par OCR est une pièce lue par une machine faillible, et c'est une
    réserve documentaire comme une autre.
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
      `> [!warning]` dans la note d'enseignements ;
    - **une série d'entrées datées** (relevé, journal, suite d'échanges) se
      standardise avec **un titre `###` par entrée**, portant son auteur et
      son horodatage quand ils sont lisibles. C'est ce qui fait de chaque
      entrée un extrait indexé à elle seule, donc retrouvable
      individuellement ; sans ces titres, tout l'écran part en un seul
      extrait. **Chaque titre porte le fichier dont l'entrée vient** : une
      série reste UNE note — la découper en une note par fichier donnerait des
      notes de trois lignes qui ne veulent rien dire seules —, et cette
      mention y rétablit la traçabilité, plus finement qu'un découpage ne le
      ferait. Les dates ne portant souvent ni l'année ni le jour, chercher
      l'ancrage dans le vault (une note existante qui date le même événement)
      ou dans la pièce voisine du même lot. Introuvable → **demander l'ancrage
      à l'utilisateur**, la date de la première entrée : c'est un fait qu'il
      détient et que la pièce ne porte pas — l'une des deux seules questions
      que cette commande a le droit de poser, avec `auteur`. Sans réponse,
      **ne pas bloquer** : ingérer sans date, avec un `> [!warning]` qui dit
      l'ancrage manquant. Ne jamais la déduire : une année devinée dans une
      couche immuable ne se verra plus jamais ;
    - ce sont les **images elles-mêmes** qui sont archivées, avec la
      transcription fidèle qu'en a faite le lecteur — même règle que pour un
      document et sa sortie d'OCR. Aucune référence d'image n'est écrite dans
      la note : la pièce se rejoint par `origine:`, jamais par un lien qui
      deviendrait un nœud fantôme du graphe.
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
  2. **obtenir la version standardisée** dans
     `$VAULT/inbox/<slug>.standardise.md`. Elle est **écrite sur disque**,
     jamais retournée — c'est ce qui permet de garder le texte intégral sans
     qu'il traverse aucun contexte. Le fichier reste dans le sas tant que
     l'ingestion n'est pas validée.
     **Ce que « standardiser » veut dire, précisément.** Le découpage
     sémantique se fait **par titre markdown**, et retombe sur un découpage
     par paragraphes au-delà d'environ 2 000 caractères. Une source bien
     standardisée est donc celle où **aucun bloc dépassant cette taille ne
     reste sans titre** : la structure réelle de la pièce — ses articles, ses
     chapitres, ses sections, ses entrées datées — devient la hiérarchie de
     titres, et chaque unité de sens devient un extrait indexé. Sans ça, le
     moteur coupe où il peut, au milieu d'un article, et l'extrait remonté ne
     veut plus rien dire.
     C'est le seul objectif de cette étape. On ne réécrit pas le texte, on ne
     le résume pas, on ne le corrige pas : on lui donne les titres qui
     permettront de le retrouver par morceaux.

     **La chaîne est la même pour toute source, sans exception :**
     `pièce → transcription fidèle → standardisation → wiki/sources/`.
     Seule la première flèche change de nature — la transcription est
     **donnée** pour un markdown déposé, produite par l'**OCR** pour un
     document paginé, écrite par le **lecteur** pour une image. Les deux
     suivantes sont identiques pour tout le monde : copie, titres, dépôt.
     **Ce qui décide du coût de l'ingestion, c'est de ne jamais confondre la
     deuxième flèche avec la première.**
     - **Le texte existe déjà** (markdown déposé, sortie d'OCR, export
       converti) → le **copier**, puis le retoucher par éditions ciblées :
       hiérarchie de titres, références mortes neutralisées, frontmatter.
       **Ne jamais le réécrire intégralement.** Régénérer un document de
       soixante-dix kilo-octets, c'est le retaper mot pour mot en jetons
       produits — pour un fichier qui est déjà sur le disque. C'est le poste
       de dépense principal d'une ingestion, et il est évitable.
     - **Le texte n'existe pas** (image, capture) → le lecteur écrit d'abord
       la **transcription fidèle** dans `$VAULT/inbox/<slug>.transcription.md`,
       à plat, telle qu'il lit l'écran. Elle sera archivée avec les images.
       Puis il la **copie** et y pose les titres, comme pour n'importe quelle
       autre source : la standardisation ne régénère rien, même ici.
       Deux passes, mais une seule génération — c'est ce qui donne à une
       capture les mêmes trois degrés de fidélité qu'à un PDF. Sans cette
       transcription, vérifier la version structurée exigerait de **relire
       toutes les images**, bien plus cher que de relancer un OCR.
     Un fichier déjà propre ne demande alors qu'un frontmatter. Le lecteur ne
     doit pas confondre « standardiser » et « reproduire » : son travail est
     de rendre la structure exploitable, pas de recopier ce qui l'est déjà.
     **Une seule chose n'est jamais transcrite telle quelle : une référence de
     fichier qui ne pointe nulle part.** Un markdown déjà converti par un outil
     tiers contient souvent des `![img-0.jpeg](…)` vers des images jamais
     extraites. Recopiées, elles deviennent des **nœuds fantômes du graphe
     Obsidian** — et un clic dessus crée une note vide. Remplacer chacune par un
     marqueur textuel inerte (`[figure 1 — non extraite]`, numéroté dans
     l'ordre) : l'information « il y avait une figure ici » est conservée, le
     lien mort disparaît. Cette couche est fidèle au **texte**, pas aux liens
     brisés de son convertisseur ;
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
  en sources** — décision qui t'appartient, elle se prend en ouvrant les
  fichiers :
  - plusieurs fichiers qui forment **un même ensemble** comptent pour UNE
    source, qu'un seul lecteur ouvre dans l'ordre. Le nom de fichier est un
    indice **faible** — un préfixe commun ou une numérotation continue ne
    prouvent rien, et deux pièces sans rapport peuvent se ressembler. Ce qui
    tranche, c'est le **contenu** : ouvrir le premier fichier de chaque groupe
    pressenti et vérifier qu'ils se poursuivent réellement l'un l'autre. Un
    sous-dossier dédié reste le seul indice de nom qui vaille. Dans le doute,
    **séparer** plutôt que regrouper : deux notes qu'il faudra fusionner sont
    plus faciles à rattraper qu'une note qui mélange deux pièces. Ne pas
    bloquer sur ce choix — `/doc-repair` corrige après coup sans tout
    refaire ;
  - un document, un export, un article = une source chacun.

  Annoncer le regroupement retenu (« <n> fichiers → <m> sources : … ») — pour
  information, pas pour accord —, puis un lecteur par **source** (parallèle,
  4 au plus) et écriture par source.
  Une source du lot dépasse le seuil → lui appliquer le montage gros volume.

  Cas particulier — `inbox/session-*.md` (`type: session` : transcript de
  session Claude Code déposé automatiquement avant compactage) : densité utile
  faible — la mission du lecteur devient « extraire les décisions prises et
  les faits durables, jamais le déroulé de la session ». Aucun enseignement
  durable → archivage direct (déplacement vers `archives/`), sans note source
  ni question posée : un transcript sans enseignement n'a rien à faire valider.

  Dans tous les montages, le lecteur (ou le synthétiseur en gros volume) garde
  son contexte : le conserver pour tout le contrôle ci-dessous.

## Contrôle avant écriture (le tien, pas celui de l'utilisateur)

**L'ingestion ne demande son avis à personne.** Ce qui arrive dans `inbox/` y
est déposé pour que le vault s'en serve, le plus souvent **sans que
l'utilisateur ait lu la pièce** : lui faire valider des enseignements tirés
d'un texte qu'il n'a pas ouvert ne vérifie rien, ça déplace seulement la charge
sur celui qui a le moins de contexte. Le contexte est dans la pièce, et la
pièce, c'est toi qui viens de la lire. Tu décides.

Relis donc toi-même le dossier d'ingestion avant d'écrire :

1. **Chaque enseignement est-il porté par la source ?** Un enseignement qui ne
   se rattache à aucun passage est une invention — le retirer. Dans le doute,
   relancer le lecteur (SendMessage : son contexte, source comprise, est
   conservé ; en gros volume, le synthétiseur, qui relancera un lecteur de
   tranche si la source est requise). Interlocuteur perdu ou SendMessage
   indisponible → relancer le montage concerné sur la tranche en cause.
2. **Ce qui est douteux se consigne, il ne se demande pas.** Une pièce qui se
   contredit, une date qu'aucun passage n'établit, deux lectures possibles d'un
   même passage : écrire la lecture la mieux étayée et poser un
   `> [!question]` sur la page de concept concernée, en disant ce qui manque
   pour trancher. C'est ce qui remonte au `/doc-lint` suivant. Bloquer
   l'ingestion sur une ambiguïté serait le pire des deux mondes : rien n'est
   ingéré, et la question reste posée.
3. **Ne rien inventer pour combler.** Une date absente reste absente
   (`> [!warning]`), un auteur inconnu se demande — c'est l'une des rares
   choses que l'utilisateur sait et que la pièce ne dit pas.

Puis écrire, en contexte principal, à partir du seul dossier d'ingestion —
sans jamais rouvrir la source.

Ce filet-là n'est pas le seul : l'auto-vérification de l'étape 8 contrôle ce
que l'écriture pouvait casser, `/doc-lint` balaie l'ensemble ensuite, et
`/doc-repair` corrige après coup sans tout refaire. Une erreur d'ingestion se
rattrape ; une ingestion qui n'a pas eu lieu parce qu'elle attendait une
réponse, non.

## Écriture (dans cet ordre — à partir du dossier d'ingestion validé, sans
jamais rouvrir la source en contexte principal)

Une même pièce produit **deux notes**, qui partagent le même slug et se
pointent mutuellement en wikilink — **préfixé du dossier**
(`[[sources/<slug>]]`, `[[enseignements/<slug>]]`) : le slug étant partagé, un
lien nu désignerait les deux à la fois.
**La règle vaut pour TOUT lien vers une pièce, d'où qu'il parte** — et c'est
depuis `concepts/` et `entites/` qu'on l'oublie, en citant une pièce par son
nom sans penser à sa couche. Un `[[<slug>]]` nu n'est pas signalé comme
pendant, puisqu'il résout : Obsidian choisit silencieusement l'une des deux
notes. Un renvoi à ce que la pièce **dit** vise `[[enseignements/<slug>]]` ;
seul un renvoi à son **texte intégral** vise `[[sources/<slug>]]`.
Le slug préfixe la **date de la pièce** (`YYYY-MM-DD-`), jamais celle de
l'ingestion. Pièce non datée → pas de préfixe, et surtout aucune date inventée
ni déduite : l'absence est une information, à doubler d'un `> [!warning]` dans
la note d'**enseignements**, jamais dans celle de `sources/`. Elles ne font pas
double emploi : l'une est fidèle, l'autre est utile.

1. `$VAULT/wiki/sources/YYYY-MM-DD-<slug>.md` — **le texte intégral
   standardisé** de la pièce. Frontmatter conforme au modèle de note
   d'`INSTRUCTIONS-CLAUDE.md` (`type: source`, `date`, `auteur` — repérable
   dans les notes existantes du vault, sinon le demander —, `description`,
   `origine` = ce dont la note a été faite (chemin archivé, URL, mention
   libre) ; `original` seulement si la pièce qui fait foi en diffère — le PDF
   dont la transcription est tirée — **jamais un chemin absolu de la
   machine**).
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
   **Aucun commentaire éditorial dans cette note** : elle porte le texte de la
   pièce, et rien d'autre. Les réserves constatées vont dans la note
   d'enseignements (voir 2) — sans quoi une recherche sur les sources
   remonterait du commentaire au lieu du contenu des pièces. Jamais de
   `> [!question]` non plus : la couche est immuable.
   Note trop volumineuse → la découper par la structure réelle de la pièce
   (`YYYY-MM-DD-<slug>-1.md`, `-2.md`…), chacune renvoyant à la suivante en
   wikilink ; jamais par une coupe arbitraire au milieu d'une section.
   **Ingestion interrompue** (échec de lecture, source illisible) → supprimer
   les fichiers `*.standardise*.md` du sas : rien ne reste en attente.
2. `$VAULT/wiki/enseignements/YYYY-MM-DD-<slug>.md` — **ce qu'on en retient**.
   Frontmatter `type: enseignements`, même `origine`, wikilink vers la note de
   source. Corps : **un titre `###` par enseignement**, chacun suivi de sa
   citation verbatim ≤ 125 caractères et des wikilinks vers les
   concepts/entités concernés.
   Le `###` n'est pas cosmétique : le découpage sémantique se fait par titre,
   donc un enseignement devient exactement un extrait indexé — ni dilué dans
   ses voisins, ni coupé en deux.
   **Les réserves sur la pièce vont ici**, sous leur propre `###` (un callout
   `> [!warning]` par réserve, ou un seul les regroupant). Une réserve n'est
   pas ce que la pièce dit, c'est ce qu'on en constate : c'est un enseignement.
   Critère : **ce qui change ce que la pièce vaut** — tronquée, non datée, non
   signée, signataire manquant, OCR partiel, en-tête d'une autre société,
   propos rapporté. Pas les coquilles ni les fautes d'accord, qui n'enlèvent
   rien à ce qu'elle prouve.
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
   d'`INSTRUCTIONS-CLAUDE.md`. La trancher **toi-même** quand les pièces le
   permettent : la plus récente, la plus directe, ou celle qui fait foi
   l'emporte → valeur courante mise à jour dans le corps + entrée
   `## Historique` en fin de note, disant ce qui a départagé. Aucune pièce ne
   départage → callout
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
   n'est jamais déplacé ni supprimé).
   **Archiver la pièce ET sa transcription fidèle** — le PDF et sa sortie
   d'OCR, les images et la transcription qu'en a faite le lecteur. Ce ne sont pas deux exemplaires du même objet : la transcription est
   ce que la machine a lu, `wiki/sources/` en est la version structurée. Garder
   la première permet de vérifier la seconde sans relancer un OCR, qui coûterait
   un appel et rendrait un texte peut-être différent.
   Captures d'écran : archiver **les images elles-mêmes**, toutes celles de
   l'ensemble, dans leur ordre — elles sont la pièce, il n'y a rien d'autre à
   conserver. Les fichiers archivés gardent leur
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

8. **Auto-vérification, bornée aux fichiers que tu viens d'écrire.** Pas un
   `/doc-lint` : celui-là balaie tout le vault et coûte un fork entier, ce qui
   est disproportionné après une ingestion — et il rapporte sans corriger.
   Ici on contrôle uniquement ce que CETTE ingestion pouvait casser, sur les
   seules notes touchées, et on corrige immédiatement :
   - **wikilinks pendants** — chaque `[[cible]]` des nouvelles notes désigne-t-il
     un fichier existant ou un alias déclaré ? La cible peut être un nom nu ou
     préfixée du dossier (`sources/<slug>`). Une cible morte → créer la page
     manquante, corriger le lien, ou le délier ; jamais une page coquille pour
     éteindre le compteur ;
   - **wikilinks ambigus** — un `[[cible]]` **nu** dont le slug existe dans
     plusieurs dossiers de `wiki/` résout quand même, mais vers l'une des deux
     notes au hasard : le contrôle précédent ne le verra jamais. Le préfixer
     (`enseignements/` pour ce que la pièce dit, `sources/` pour son texte
     intégral) en laissant le texte affiché intact ;
   - **appariement** — chaque nouvelle note de `sources/` a-t-elle son
     `enseignements/` de même slug, et se pointent-elles mutuellement ?
   - **entrées d'INDEX** — chaque note écrite y figure-t-elle, dans sa section ?
   - **références de fichier mortes** — un `![...](...)` dont la cible n'existe
     pas s'est-il glissé dans une note ? Le remplacer par `[figure N — non
     extraite]` ;
   - **titres `###`** — la note d'enseignements en porte-t-elle au moins un ?
     Sans eux ses enseignements sont indexés en un seul bloc.
   Tout écart est corrigé **avant** le compte rendu, et mentionné dedans. C'est
   le moment le moins cher : le contexte de l'ingestion est encore là, et le
   défaut n'a pas eu le temps de se propager aux ingestions suivantes.

9. **Contrôle complet du vault, enchaîné automatiquement.** L'étape 8 ne voit
   que les notes écrites ; certains défauts ne se voient qu'à l'échelle du
   vault (une orpheline créée par un renommage, une page vivante devenue
   doublon d'une autre, un `INDEX.md` qui a dérivé). Lancer un **sub-agent**
   (outil Agent, type `Explore`, avant-plan) avec cette mission :

   > Lis `${CLAUDE_PLUGIN_ROOT}/commands/doc-lint.md` et exécute-le
   > intégralement sur le vault `<$VAULT>`. Tu n'écris RIEN. Retourne ton
   > rapport final tel que la commande le définit.

   Une seule fois par ingestion, quel que soit le nombre de sources — jamais
   par source. Puis **appliquer sans rien demander** tout ce qui est mécanique
   et réversible : trous d'`INDEX.md`, liens pendants ou ambigus, frontmatters
   incomplets, parasites, réindexation des dossiers touchés, et les
   suppressions **sans perte possible** (note vide, conflit Drive sur un
   dérivé jetable, reliquat d'index). Ce qui reste — fusion de pages vivantes,
   édition d'une couche immuable, suppression d'un fichier qui porte du
   contenu — n'est PAS appliqué et n'est PAS soumis : ces trois-là ne se
   défont pas, le vault n'étant pas versionné, et une ingestion n'est pas le
   moment de les décider. Les compter, et **dire leur nombre au compte
   rendu** : reportés, pas oubliés.
   Exception : un **identifiant en clair** trouvé dans le vault (contrôle 13)
   se dit immédiatement, quel que soit le reste. Ce n'est pas une dette de
   maintenance qui peut attendre le prochain lint, c'est une fuite en cours.
   Échec du sub-agent (moteur absent, fork indisponible) → non bloquant :
   l'ingestion reste valide, le noter en une ligne.

## Compte rendu

**Court.** L'ingestion est finie, tout est écrit, vérifié et indexé : ce compte
rendu confirme, il ne fait pas travailler. Aucune liste de fichiers, aucun
tableau, aucune question posée — l'utilisateur n'a rien à faire après l'avoir
lu.

Quatre lignes au plus :

1. **Ce qui est entré** : `<n> source(s) → <n> enseignements · <n> concepts et
   entités touchés`. Des nombres, pas des chemins.
2. **Ce qui attendra**, seulement s'il y en a : `<n> contradiction(s) à
   trancher · <n> point(s) reportés à /doc-lint` — sans les détailler. Elles ne sont pas urgentes, elles vivent
   dans le vault, et `/doc-lint` les listera quand l'utilisateur voudra s'en
   occuper. Les réserves documentaires ne se mentionnent pas : elles sont
   définitives, il n'y a rien à en faire.
3. **Ce que les vérifications ont corrigé** — l'auto-vérification et le lint
   enchaîné confondus, en un seul nombre. Rien trouvé → ne pas le dire.
4. **L'indexation** : `<n> extraits vectorisés`. Détail par dossier seulement
   si l'utilisateur le demande. Échec → là, le dire franchement :
   « ⚠ indexation sémantique échouée (<raison>) — sera rattrapée au prochain
   `/doc-query` ».

Tout le reste — chemins, callouts posés, ce que les pièces apportent — se donne
**sur demande**, jamais spontanément. Une ingestion qui s'est bien passée est un
non-événement.
