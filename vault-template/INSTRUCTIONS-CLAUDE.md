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
├── references/              ← compilations d'entrées (/doc-query --all-references) — créé à la demande, hors index sémantique
├── wiki/
│   ├── sources/             ← couche IMMUABLE : le texte intégral standardisé d'une pièce
│   ├── enseignements/       ← couche IMMUABLE : ce qu'on retient d'une pièce, un ### par enseignement
│   ├── concepts/            ← couche vivante : pages de concepts
│   ├── entites/             ← couche vivante : personnes, outils, projets
│   └── syntheses/           ← réponses de /doc-query sauvegardées
```

**`references/` est un produit de travail, pas une couche de savoir.** Une
compilation d'entrées répondant à une question précise, **régénérable** :
relancer la commande la refait, plus complète si le vault a grandi. Rien ne s'y
maintient, rien ne s'y corrige : on la refait.

`/vault-init` ne le crée pas — c'est la première compilation acceptée qui le
crée, comme `BENCH.md` n'apparaît qu'au premier `/doc-bench`. Les dossiers
posés d'emblée servent tous à chaque ingestion ; celui-ci n'appartient qu'à un
mode facultatif, et la plupart des vaults n'en auront jamais.

Elle vit hors de `wiki/` pour une raison mécanique : son contenu est déjà dans
`sources/`, et l'indexer vectoriserait deux fois le même texte, ferait remonter
le même passage en double à chaque recherche et gonflerait le vault de copies.
C'est automatique — l'indexation sémantique ne parcourt que les cinq dossiers
de `wiki/`.

**En revanche elle reste dans le graphe Obsidian**, contrairement à `archives/`
et `inbox/`. Ce n'est pas un oubli : une compilation est un document construit,
qui cite les notes dont elle tire ses entrées et renvoie à la synthèse qu'on en
a tirée. Elle porte donc **deux liens** — `[[syntheses/<slug>]]` en tête si la
synthèse existe, et un renvoi par note citée en fin de fichier. Jamais un lien
par entrée : deux cents liens vers la même note ne feraient qu'un nœud
illisible.

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

Deux invariants d'une série, qu'aucun compteur ne rattrape :

- **du plus ancien au plus récent.** Certaines sources rendent l'inverse — une
  API qui pagine à rebours, un export qui commence par le dernier message : on
  remet d'aplomb, on ne reporte pas l'ordre de la source. Une note écrite à
  l'envers porte pourtant toutes ses entrées : le total est juste, et l'échange
  se lit à rebours ;
- **le fuseau se déclare en `fuseau:`, il ne se convertit pas.** Une API
  horodate volontiers en UTC, un export d'application rend l'heure locale de
  l'appareil. Mêlées sans le dire, deux séries produisent une chronologie
  fausse du décalage, et rien ne la signale — les heures ont l'air normales.
  Convertir depuis un décalage que la pièce ne donne pas serait une supposition
  écrite dans une couche immuable, indiscernable d'un fait par la suite.
  Fuseau indéterminable → l'écrire tel quel (`heure locale, fuseau non porté
  par la pièce`) et poser un `> [!warning]` dans la note d'enseignements.

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

**Ce slug partagé impose la forme du wikilink** : `[[sources/<slug>]]` et
`[[enseignements/<slug>]]`, **préfixés du dossier**. Un `[[<slug>]]` nu
désignerait deux fichiers à la fois et Obsidian choisirait pour vous, sans
rien signaler — le lien résout, il n'apparaît donc jamais comme cassé.

La règle ne se limite pas aux deux notes de la paire : **tout lien vers une
pièce se préfixe, d'où qu'il parte**, et c'est depuis `concepts/` et
`entites/` qu'on l'oublie, en citant une pièce par son nom sans penser à sa
couche. Le préfixe se choisit sur ce que la phrase fait dire au lien : un
renvoi à ce que la pièce **affirme** vise `[[enseignements/<slug>]]`, un
renvoi à son **texte intégral** vise `[[sources/<slug>]]`.

Le nom nu ne reste la règle que là où le nom est effectivement unique :
`concepts/`, `entites/`, `syntheses/`.

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
  s'accompagne d'un `> [!warning]` — dans **`wiki/enseignements/`**, sous son
  propre titre `###`, jamais dans `wiki/sources/` : c'est un constat sur la
  pièce, pas ce qu'elle dit (voir la convention des callouts plus bas).
- **Modèle de note — frontmatter obligatoire** (une note sans ces propriétés
  n'est pas conforme ; `/doc-lint` les vérifie) :
  - toutes les notes : `type` (source | enseignements | concept | entite |
    synthese),
    `date` (`YYYY-MM-DD`, jamais modifiée ensuite) — pour `type: source` et
    `type: enseignements`, **la date de la pièce, celle-là même qui préfixe le
    slug**, jamais la date d'ingestion ; pour les couches vivantes (`concept`,
    `entite`, `synthese`), la date de création de la page, qui n'est la pièce de
    personne. Pièce non datée → pas de `date` du tout, comme il n'y a pas de
    préfixe : une date d'ingestion mise là daterait la lecture en faisant croire
    qu'elle date la pièce,
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
    titres `###`, un par enseignement, chacun suivi de sa citation verbatim,
    de sa ligne d'attribution et des wikilinks vers les concepts/entités
    concernés. Le `###` n'est pas
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
- **Toute citation porte son bloc d'attribution, juste en dessous** :

  ```
  > « <citation> »

  > [!source]- <auteur>, <date de l'entrée>
  > `wiki/sources/<slug>.md` Ligne <n>
  > original `archives/<pièce brute>` Ligne <n>
  ```

  Trois questions distinctes, dont aucune ne se déduit des autres : **qui** l'a
  dit, **dans quelle pièce**, **où exactement**. Sans elles, contrôler la
  citation suppose de relire la pièce entière — donc personne ne la contrôle.
  Deux pointeurs, deux rôles : la note de `wiki/sources/` est toujours
  adressable ligne à ligne et donne le repère précis ; l'**original** est la
  pièce brute, qui fait foi. Sans lui, la citation ne remonte qu'à une lecture
  de la pièce, et c'est la lecture qui est faillible.
  Le repère de l'original suit ce que son format porte : ligne pour un fichier
  lisible ligne à ligne, **rien pour un PDF** — il n'a pas de lignes, la page
  n'est qu'un bonus. La ligne s'obtient par `grep -n`, jamais à l'estime : un
  numéro plausible donne à une citation approximative l'apparence d'une
  citation vérifiée.
  **Ce bloc est tenu hors du texte vectorisé.** D'où deux règles : l'auteur
  d'une citation **figure aussi parmi les wikilinks de sa section** — sans quoi
  son nom disparaît de la recherche —, et rien de ce qui doit être cherchable
  n'entre dans ce bloc.

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
  `lint`, `synthese`, `bench`, `references`), suivies d'une ligne de détail. Ne
  jamais modifier une entrée existante. Un `LOG.md` racine hérité d'une version
  antérieure est **gelé** : il se consulte, on n'y écrit plus.
  **Aucun wikilink dans le journal** — les notes s'y nomment en clair. Une
  entrée relie les pages touchées le même jour, ce qui est une coïncidence de
  calendrier et non un rapport de sens : en faire des `[[...]]` fabrique des
  arêtes qui n'énoncent rien, et rend le journal d'autant plus central dans le
  graphe qu'on s'en sert. Pire, une page pointée depuis le seul journal
  paraîtrait reliée alors qu'aucune connaissance ne la cite.
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
