# claude-vault-drive

[![plugin Claude Code](https://img.shields.io/badge/plugin-Claude%20Code-d97757)](https://code.claude.com/docs/en/plugins)
[![version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FZairth%2Fclaude-vault-drive%2Fmain%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version&color=blue)](CHANGELOG.md)
[![licence MIT](https://img.shields.io/github/license/Zairth/claude-vault-drive?color=green)](LICENSE)
[![sans service ni clone](https://img.shields.io/badge/install-sans%20clone%2C%20sans%20service-lightgrey)](#démarrer)

**Donnez à Claude Code une mémoire qui survit à vos sessions.**

Vous lui déposez des documents — un PDF, une capture d'écran, un export, un
compte rendu. Le plugin en fait des notes markdown rangées et reliées entre
elles, dans un dossier bien à vous. À la session suivante, Claude les relit et
répond en citant ses sources. Ouvrez ce dossier dans Obsidian si vous voulez le
voir en graphe — rien ne vous y oblige, ce ne sont que des fichiers.

## Démarrer

Une fois, valable pour tous vos projets :

```
/plugin marketplace add https://github.com/Zairth/marketplace
/plugin install claude-vault-drive@zairth_store
/plugin install agentic-toolbox@zairth_store
```

**Prenez le second.** Techniquement facultatif, il change tout ce qui compte :
sans lui, la recherche se fait par mots-clés — elle trouve ce que vous avez su
nommer, et rate la reformulation. Avec lui, elle cherche **par le sens** :
« qui a validé le budget ? » remonte une note qui parle d'accord donné sur une
enveloppe, sans partager un seul mot avec la question. Il apporte aussi la
lecture des documents scannés, sans quoi un PDF photographié n'est qu'une
image.
Il demande en retour `uv` et une clé d'API Mistral, gratuite —
[PREREQUIS.md](PREREQUIS.md) détaille les deux, y compris comment couper
l'utilisation de vos données pour l'entraînement. Si vous ne l'installez pas,
rien ne casse : les commandes annoncent leur repli au lieu de faire semblant.

Puis dans le projet qui doit avoir sa mémoire :

```
/vault-init "/chemin/vers/mon-vault"
```

Relancez la session : le vault existe, il est vide.

Reste à lui donner de quoi lire. **Deux façons**, au choix :

```
/doc-ingest inbox/                    ← tout ce que vous avez déposé dans le sas
/doc-ingest /chemin/vers/mes-docs     ← un dossier, un fichier, ou un lien
```

- **Le sas.** `/vault-init` crée un dossier `inbox/` à la racine du vault :
  déposez-y vos fichiers, puis lancez `/doc-ingest inbox/` pour ingérer le lot,
  ou `/doc-ingest <nom-du-fichier>` pour n'en prendre qu'un. Sans argument, la
  commande liste ce qui s'y trouve et vous demande — elle n'avale jamais un lot
  entier sans qu'on le lui dise.
- **Un chemin quelconque**, sans rien déplacer. Une seule condition : il doit
  être **autorisé**. Un dossier situé hors du vault et hors du projet sera
  refusé tant qu'il ne figure pas dans `additionalDirectories`
  (`.claude/settings.local.json`) — c'est le cas le plus courant quand les
  sources sont rangées à côté du vault plutôt que dedans.

Puis interrogez : `/doc-query <votre question>`. Aucun clone, aucun service à
faire tourner. Le vault peut être n'importe où — Google Drive, Dropbox, ou un
disque local. Options, montage Drive et cas particuliers :
[installation détaillée](#installation-détaillée).

## Les cinq commandes

| commande | ce qu'elle fait |
|---|---|
| `/vault-init` | crée le vault et branche le projet dessus |
| `/doc-ingest` | range une source dans le vault — un fichier, un dossier, un lien |
| `/doc-query` | pose une question, obtient une réponse qui cite ses notes — `--all-references` rend toutes les entrées d'un sujet |
| `/doc-lint` | vérifie la cohérence de l'ensemble |
| `/doc-repair` | corrige une information et la répercute partout où elle apparaît |

Au quotidien, deux suffisent : **`/doc-ingest` pour nourrir, `/doc-query` pour
consulter.** Le reste s'enchaîne tout seul — une ingestion lance sa
vérification sans qu'on le lui demande.

## Pour aller plus loin

- Le moteur de recherche par le sens et d'OCR :
  [agentic-toolbox](https://github.com/Zairth/agentic-toolbox) — dépôt séparé,
  installé plus haut.
- Prérequis pas à pas, montage Drive, clés API : [PREREQUIS.md](PREREQUIS.md)
- Ce que change chaque version : [CHANGELOG.md](CHANGELOG.md)
- Comment c'est construit : [Principes](#principes) et
  [Usage](#usage) plus bas.

## Ce que contient ce repo

Le repo est un plugin Claude Code, distribué via le marketplace
[Zairth/marketplace](https://github.com/Zairth/marketplace) :

```
claude-vault-drive/
├── .claude-plugin/
│   └── plugin.json          # manifeste du plugin
├── PREREQUIS.md             # de la machine nue au vault : WSL, Claude Code, Drive, toolbox
├── CHANGELOG.md             # pourquoi mettre à jour — une entrée par version
├── commands/
│   ├── vault-init.md        # /vault-init — initialiser le vault du projet courant
│   ├── doc-ingest.md        # /doc-ingest — ingérer une source (lecture, standardisation, contrôle, lint enchaîné)
│   ├── doc-query.md         # /doc-query — interroger le vault (fork isolé, réponse citée ; --all-references pour l'exhaustif)
│   ├── doc-lint.md          # /doc-lint — maintenance (fork isolé : treize vérifications, dont les identifiants en clair)
│   ├── doc-repair.md        # /doc-repair — corriger une information et rebrancher sa chaîne, vérification contre la pièce
│   └── doc-bench.md         # /doc-bench — banc de questions de référence (mesure mécanique, ou réelle via /doc-query)
├── hooks/
│   └── hooks.json           # déclaration des trois hooks (SessionStart, UserPromptSubmit, PreCompact)
├── docs/                    # captures illustrant les prérequis (opt-out d'entraînement : Mistral, Anthropic)
├── scripts/
│   ├── vault-check.sh       # portier : vérifie l'accès au vault, imprime son chemin
│   ├── vault-init.sh        # initialisation du vault en une commande, idempotente
│   ├── toolbox-env.sh       # résolution du moteur : dossier (cache des plugins) + invocation uv
│   ├── vault-index-targets.sh   # les dossiers de wiki/ à indexer séparément (un index par dossier)
│   ├── vault-index.sh       # indexation sémantique incrémentale (porte CLI du moteur)
│   ├── vault-search.sh      # recherche sémantique, un appel pour tous les dossiers (porte CLI)
│   ├── vault-lexical.sh     # recherche par mots-clés BM25 — zéro appel API, aucun index requis
│   ├── vault-ocr.sh         # conversion OCR — scan, photo : le seul cas où l'OCR est le bon outil
│   ├── pdf-text.py          # couche de texte d'un PDF, sans dépendance ni réseau (essayée avant l'OCR)
│   ├── verify-entries.py    # recompte les entrées datées d'une source dans la note produite
│   ├── hook-session-start.sh    # hook : INDEX.md injecté à l'ouverture de session
│   ├── hook-prompt-context.sh   # hook : pistes par mots-clés sous chaque prompt (gratuit)
│   └── hook-precompact-inbox.sh # hook : transcript déposé dans inbox/ avant compactage, identifiants masqués
└── vault-template/          # fichiers copiés à la racine d'un nouveau vault
    ├── INSTRUCTIONS-CLAUDE.md   # le schéma du vault — toute commande le lit d'abord
    └── INDEX.md                 # carte du vault, point d'entrée des recherches (dérivé, régénérable)
```

Le code (commandes, scripts, template) vit dans le plugin, partagé entre tous
les projets ; la config vit dans chaque projet (`.claude/vault-path.local`,
`settings.local.json`, `toolbox-path.local` — gitignorés) : **un plugin, un
vault par projet**.

## Principes

- **Source de vérité = les `.md` du vault.** Tout le reste (`INDEX.md` —
  régénéré depuis le frontmatter des notes —, index de recherche, caches) est
  un dérivé jetable et reconstructible.
- **Recherche isolée du contexte principal** : `/doc-query` et `/doc-lint`
  s'exécutent entièrement dans un sub-agent (`context: fork` dans le
  frontmatter de la commande) — le contexte principal de Claude ne voit jamais
  les notes brutes ni même les instructions de la commande (anti-saturation,
  anti-distracteurs) ; seuls la réponse citée ou le rapport remontent.
- **Trois degrés de fidélité pour une même pièce**, du plus travaillé au plus
  brut : `wiki/enseignements/<slug>.md` (ce qu'on en retient, un `###` par
  enseignement — ce qu'on lit), `wiki/sources/<slug>.md` (le texte intégral
  standardisé, fidèle et sans tri — ce qu'on fouille), `archives/<pièce>` (la
  pièce elle-même, jamais indexée ni modifiée — ce qui fait foi). Un doute se
  remonte toujours dans ce sens. Par-dessus, les couches vivantes :
  `wiki/concepts/` + `wiki/entites/` (reliées par wikilinks) et
  `wiki/syntheses/` (réponses transversales persistées).
  Rien de ce qui est ingéré n'est perdu : ce qu'aucun enseignement n'a retenu
  reste cherchable dans le texte intégral.
  À côté de ces couches, `references/` — hors de `wiki/`, créé à la demande —
  garde les compilations d'entrées produites par `--all-references`. Ce n'est
  pas du savoir mais un **produit de travail**, jamais vectorisé (son contenu
  est déjà dans `sources/`) et régénérable en relançant la commande.
- **Un index sémantique par dossier de `wiki/`**, dans le dossier lui-même
  (un `.index/` dans chacun des cinq dossiers). Chaque dossier est un espace
  vectoriel séparé, donc les notes ne concourent qu'entre semblables : une
  entité de dix lignes ne peut plus être écrasée par un extrait d'un texte
  intégral de trois cents, et surtout **on peut chercher dans une couche sans
  l'autre** — interroger les enseignements, puis descendre au texte si le
  doute persiste. Le nombre d'index ne dépend pas du nombre de sources : cinq,
  quelle que soit la taille du vault. Et la séparation ne coûte rien à la
  requête : un seul appel porte les cinq dossiers, la question n'étant
  vectorisée qu'une fois.
- **Le grep ne disparaît jamais derrière le vectoriel** : `/doc-query` lance
  toujours les deux. Le sub-agent **ouvre toutes les touches, puis trie** et ne
  remonte que ce qui répond : son contexte est jetable, lire large et rendre
  étroit est son métier. Une note qui contient littéralement les mots de la
  question est souvent le meilleur résultat possible, et aucun score de
  similarité ne le dira.
- **Modèle de note** : frontmatter obligatoire sur chaque note — `type`,
  `date` (création), `auteur`, `description` (alimente l'INDEX), plus
  `origine`/`original` (sources et enseignements) et `question` (synthèses) ; défini dans l'`INSTRUCTIONS-CLAUDE.md` du vault,
  appliqué par `/doc-ingest`, vérifié par `/doc-lint`.
- **Vault auto-porteur** : `inbox/` est un sas, pas un stockage — un fichier
  ingéré est déplacé vers `archives/`, jamais supprimé. Le savoir vit dans
  `wiki/`, la pièce d'origine reste vérifiable dans le vault, qui voyage d'un
  bloc. `archives/` est immuable et **hors index sémantique**
  (seuls les dossiers de `wiki/` sont indexés : zéro coût, zéro bruit — les
  fichiers archivés gardent leur nom et leur extension) ; attention
  avant de partager le vault, les archives peuvent contenir des données
  sensibles que les notes condensées ont volontairement écartées.
- **Échecs explicites** : Drive non monté, vault non initialisé → message clair,
  jamais de vault vide silencieux.

## Installation détaillée

Pour l'installation courante, trois commandes suffisent : voir
[Démarrer](#démarrer) plus haut. Cette section couvre les prérequis, les
options et ce que `/vault-init` écrit exactement.

**Prérequis** : [Claude Code](https://claude.com/claude-code) ; Google Drive
pour Desktop si le vault doit être partagé (sinon n'importe quel dossier local
convient) ; le plugin [agentic-toolbox](https://github.com/Zairth/agentic-toolbox)
pour la recherche sémantique et l'OCR (facultatif — repli grep sinon) ; Obsidian est
**facultatif** — c'est la vitrine humaine, le système fonctionne sans.
**Guide pas à pas** (commandes d'installation, WSL, montage Drive, clés API) :
[PREREQUIS.md](PREREQUIS.md).

Dans Claude Code (une fois, valable pour tous les projets) :

```
/plugin marketplace add https://github.com/Zairth/marketplace
/plugin install claude-vault-drive@zairth_store
/plugin install agentic-toolbox@zairth_store   # facultatif : la toolbox en plugin autonome (outils MCP + skill)
```

**Aucun clone nulle part** : Claude Code récupère et met en cache les deux
plugins lui-même depuis GitHub. Le plugin agentic-toolbox embarque son serveur
MCP (lancé à la demande via `uv`, clés API saisies à l'installation) — les
commandes `/doc-*` utilisent ses outils en priorité.

Puis dans chaque projet qui doit avoir son vault :

1. `/vault-init "/mnt/g/Mon Drive/<Section>/<MonVault>"` — idempotent (ne
   remplace jamais un fichier existant) et complet : config locale gitignorée
   dans le `.claude/` du projet (`vault-path.local` + `settings.local.json`
   avec la permission d'écriture), `.gitignore` complété, arborescence du
   vault, copie du template, entrée `init` du journal (`LOG/`, un fichier par
   jour), vérification finale par `vault-check.sh`.
2. Relancer la session Claude Code (pour charger la permission
   `additionalDirectories`) — les commandes `/doc-ingest`, `/doc-query` et
   `/doc-lint` sont prêtes.
3. (Facultatif, humain) Ouvrir le dossier du vault comme coffre dans Obsidian.
   **Rien à régler** : `/vault-init` a déjà écrit les deux réglages qui
   comptent, et il ne touche à aucun autre.
   - **Le graphe est coloré par dossier** (`.obsidian/graph.json`) : bleu pour
     `sources/`, vert pour `enseignements/`, ambre pour `concepts/`, violet
     pour `entites/`, rouge pour `syntheses/`. Sans ça, tous les nœuds se
     ressemblent et le graphe ne dit rien. Vos propres groupes de couleurs, si
     vous en avez, sont conservés — le fichier porte aussi vos réglages de
     zoom et de forces, il n'est jamais écrasé.
   - **`archives/` et `inbox/` sont exclus de l'index Obsidian**
     (`.obsidian/app.json`) : ni les pièces d'origine ni la matière brute en
     attente ne sont des notes. Sans ce filtre, les markdown OCR archivés
     référencent des images non extraites qui apparaissent en nœuds fantômes —
     cliquer sur l'un d'eux crée une note vide à la racine.

   Bon à savoir pour lire le graphe : ses arêtes ne viennent **que** des
   wikilinks `[[...]]`. Les chemins bruts et les propriétés
   `origine`/`original` n'en créent aucune.

Installer une mise à jour : automatique en arrière-plan, ou manuelle —
`/plugin marketplace update zairth_store` puis `/reload-plugins` (récupère le
dernier commit directement depuis GitHub, aucun `git pull` local ; le cache
n'est invalidé que si la version du plugin a changé). Ce qui a changé et
pourquoi mettre à jour : [CHANGELOG.md](CHANGELOG.md).

Développement du plugin uniquement (tester des modifs avant de pousser) :
`/plugin marketplace add /chemin/du/clone` ou `claude --plugin-dir /chemin/du/clone`.

Le chemin du vault ne vit que dans les fichiers locaux gitignorés du projet —
jamais dans un fichier versionné. `vault-path.local` peut être édité depuis
Windows : BOM/CRLF/espaces finaux sont nettoyés automatiquement.

## Usage

Première commande à taper dans un projet, une fois le plugin installé :
`/vault-init "/chemin/du/vault"` (le chemin en argument, sinon la commande le
demande et s'arrête), puis **relancer la session Claude Code** — c'est ce
redémarrage qui charge la permission `additionalDirectories` et rend les
commandes ci-dessous opérationnelles (détail : [installation détaillée](#installation-détaillée)).

- `/doc-ingest <texte | fichier | URL | élément de inbox/>` — un sub-agent
  lecteur lit la source (le contexte principal ne la voit jamais) et en tire
  ses enseignements — autant qu'elle en porte, sans plafond. **La commande ne
  demande son avis à personne** : ce qui arrive dans `inbox/` y est déposé pour
  que le vault s'en serve, souvent sans que l'utilisateur ait ouvert la pièce,
  et lui faire valider des enseignements tirés d'un texte qu'il n'a pas lu ne
  vérifie rien. Ce qui est douteux devient un `> [!question]` dans le vault au
  lieu de bloquer l'ingestion.
  La source est routée selon sa nature : **PDF → sa couche de texte si elle
  existe** (exact, gratuit, instantané — un OCR sur un PDF produit par un
  logiciel confond des mots voisins et le fait *systématiquement*, ce qui rend
  un résultat plausible et faux) ; **scan ou photo de document → OCR**, seul
  cas où il est le bon outil ; **capture d'écran → lecture visuelle directe par le
  lecteur, jamais d'OCR** (un OCR documentaire est réglé pour une mise en page
  de document : sur une capture d'interface il rend un flux linéaire où la
  disposition a disparu, et une partie du sens avec elle) ; des captures
  formant un même ensemble
  comptent pour **une** source, et ce sont les images qui sont archivées ;
  un doute sur un enseignement se lève auprès de ce même sub-agent (relais
  SendMessage, contexte conservé) ; puis l'agent principal
  écrit : note source immuable, pages concepts/entités, INDEX, LOG, et
  **enchaîne un `/doc-lint`** dont les corrections mécaniques s'appliquent
  dans la foulée.
  Contradiction détectée → tranchée sur les pièces (la plus récente, la plus
  directe, celle qui fait foi) : la note porte la
  valeur courante, l'ancienne descend en `## Historique` (une seule vérité en
  tête, l'historique conservé) ; non tranchable → callout `> [!question]` sur
  la page concept/entité — à ne pas confondre avec `> [!warning]`, qui porte
  une réserve documentaire permanente sur la pièce (OCR partiel, capture non
  datée) et n'appelle aucun arbitrage.
  Le brut venu d'`inbox/` est **archivé dans `archives/`**, jamais supprimé —
  le vault reste auto-porteur (condensé + pièces d'origine).
- `/doc-query <question>` — le tout en fork isolé : réindexation incrémentale
  + recherche sémantique, puis INDEX → notes → wikilinks → grep ; réponse
  citée ; option « sauvegarder en synthèse » (appliquée en contexte principal
  après accord).
  Ajouter `dans:<dossier>` pour cibler un dossier voisin du vault (ex. une
  section alimentée par des tiers) : lecture seule, la synthèse reste dans le
  vault. Ajouter `--no-index` pour interroger sans réindexer. Moteur
  sémantique indisponible → repli grep **explicite** (⚠ affiché), jamais
  d'échec silencieux.
- `/doc-query <question> --all-references` — le mode **exhaustif**. Le mode
  normal cherche *ce qui répond* et rédige une réponse ; celui-ci cherche
  *tout ce qui concerne* et rend **les entrées elles-mêmes**, datées,
  attribuées, citables une par une. Pour qui doit pouvoir produire chaque
  pièce, pas une synthèse.
  Un classement rend les K meilleurs résultats, jamais l'ensemble : le grep
  passe donc **d'abord** (seule couche qui rende toutes les occurrences), puis
  des vagues sémantiques — la première avec la question **non reformulée**,
  les suivantes sous un angle différent chacune —, jusqu'à ce qu'une vague
  n'apporte plus aucun fichier neuf. Jamais un nombre fixe de vagues : un
  compteur gaspille ou tronque.
  Résultat écrit dans **`references/`**, hors de `wiki/` donc jamais
  vectorisé — son contenu est déjà dans `sources/`, l'indexer ferait remonter
  le même passage en double. Le dossier est **créé à la demande** et la
  compilation est **régénérable** : relancer la commande la refait, plus
  complète si le vault a grandi. Compilation et synthèse sont proposées
  ensemble et se pointent mutuellement — l'une porte les pièces, l'autre la
  thèse qu'on en tire.
  Ce que le mode **ne** garantit **pas** est écrit dans son rapport : le grep
  garantit le littéral, les vagues élargissent, le lecteur juge — un jugement
  n'est pas une preuve, et rien ne rattrape ce qui n'a jamais été ingéré.
- `/doc-lint` — rapport produit en fork isolé, ouvert par une ligne de
  compteurs (l'état de santé du vault d'un coup d'œil, comparable d'un lint à
  l'autre) : **identifiants en clair** — un vault vit sur un dossier
  synchronisé, donc un jeton oublié dans `inbox/` part avec lui ; la valeur
  n'est jamais affichée et le remède est la révocation, pas l'effacement —,
  wikilinks pendants **et ambigus** (un nom nu que deux dossiers portent
  résout quand même, vers l'un des deux au hasard), **renvois à sens unique**
  (une note qui se déclare le complément d'une autre sans être pointée en
  retour est introuvable depuis sa page-parent), doublons suspectés de pages
  vivantes (noms
  normalisés + similarité sémantique ; fusion assistée après validation —
  wikilinks entrants réécrits, ancien nom conservé en alias),
  contradictions en souffrance (les callouts `> [!question]` seuls — les
  `> [!warning]`, réserves documentaires permanentes, sont comptés mais
  jamais réclamés),
  pages orphelines, trous d'INDEX, fichiers de conflit Drive, inbox en
  attente, frontmatters obligatoires manquants, parasites hors `wiki/`
  (`.md` inattendu à la racine, notes vides, nœuds fantômes venus des
  archives OCR), cohérence de l'index vectoriel
  (`.index/`, granularité de découpage comprise). **Deux régimes** : ce qui est
  mécanique et réversible s'applique d'office ; ce qui détruit ou ne se défait
  pas — fusionner, supprimer, écrire dans une couche immuable — est soumis une
  fois, verdict à l'appui, et la question porte sur l'autorisation d'agir,
  jamais sur la réponse.
- `/doc-repair <note> "<passage>" "<nouvelle valeur>"` — corriger une
  information repérée et **rebrancher toute sa chaîne**. En fork isolé : la
  correction est d'abord **vérifiée contre la pièce d'origine** (`archives/`),
  puis qualifiée — erreur de restitution (on remplace) ou information
  périmée (valeur courante mise à jour, ancienne en `## Historique`). Le
  rapport liste toutes les notes portant la même affirmation, les wikilinks à
  refaire et les dossiers à réindexer ; l'agent principal n'applique que ce
  que l'utilisateur valide. `archives/` n'est jamais modifié : on corrige ce
  que le vault a dit de la pièce, jamais la pièce.
- `/doc-bench` — **instrument facultatif**, le mètre étalon de la recherche.
  Rien ne l'exige : le vault fonctionne sans, et aucun réglage n'attend d'être
  calibré sur votre corpus. Il sert à qui veut vérifier une régression après
  une mise à jour du moteur, ou décider si un changement vaut d'être gardé.
  Trois modes. `creer`
  (ou premier lancement) : propose ~20 questions de référence tirées du
  contenu du vault, chacune avec ses notes attendues — validées puis figées
  dans `BENCH.md` (racine du vault, hors index). Sans argument : run
  **mécanique** — réindexation, puis top 3 sémantique par dossier, wikilinks des notes remontées
  et grep par question, aucun jugement dans le score →
  `sémantique@3 · +1 saut · grep · couverture`, détail des échecs avec ce que
  la recherche a renvoyé à la place. L'écart entre `sémantique@3` et
  `+1 saut` chiffre ce que le graphe de wikilinks rattrape déjà tout seul.
  Avec `reel` : la même question posée à `/doc-query` lui-même — un sub-agent
  lecteur par question exécute la cascade complète (il lit la procédure dans
  `doc-query.md`, la mesure ne peut donc pas se désynchroniser) et ne remonte
  que les notes qu'il citerait → `réel · citations complètes · à vide`.
  Le mécanique est gratuit et reproductible : il détecte un gain de +1 entre
  deux versions du moteur. Le réel dit si le vault répond vraiment, mais il
  est coûteux et non déterministe — **un score réel ne se compare qu'à un
  autre score réel**. Entrée `bench` ou `bench-reel` au journal. C'est le juge
  des évolutions du moteur : une fusion scorée ou une décroissance n'entrera
  que si le banc prouve qu'elle fait mieux.

## Hooks — le vault dans la session, sans commande

Trois hooks accompagnent les commandes. Tous partagent la même garde : dans un
projet sans `.claude/vault-path.local`, ils sortent immédiatement, silencieux —
le plugin est invisible tant que `/vault-init` n'a pas été lancé. Aucune donnée
du hook ne transite par argv ni par l'environnement ; tout champ servant à
nommer un fichier est filtré et confiné au vault.

- **SessionStart** — injecte la carte du vault (`INDEX.md`) dans le contexte à
  l'ouverture de session : Claude sait d'emblée ce que le vault contient. Une
  sortie de hook n'étant injectée telle quelle qu'en deçà d'environ 2 Ko, un
  INDEX volumineux est **condensé** — les slugs seuls, sans les descriptions,
  répartis équitablement entre sections (`(+n autres)` là où ça déborde) et
  suivis du chemin de l'INDEX complet : une carte entière vaut mieux qu'un
  début de carte. Vault configuré mais inaccessible → une seule ligne
  d'avertissement (Drive pas monté ?).
- **UserPromptSubmit** — recherche **par mots-clés (BM25)** sur chaque prompt
  (`vault-lexical.sh`) : quelques pistes injectées — des extraits, pas une
  réponse, `/doc-query` reste la vraie recherche.
  **Gratuit et sans prérequis** : aucun appel API, aucune clé, aucun index à
  construire au préalable, et rien du prompt ne quitte la machine. C'est ce
  qui permet à un hook déclenché à chaque prompt d'exister sans devenir un
  poste de dépense — une recherche sémantique y coûterait un embedding à
  chaque fois. Contrepartie : il trouve le terme exact, pas la reformulation.
  Filtres : commandes slash/`!`/`#` et prompts de moins de 12 caractères
  ignorés ; silence si rien ne ressort. Un hook est un process shell, il ne
  peut pas appeler les outils MCP : il passe donc par la porte en ligne de
  commande du moteur (agentic-toolbox 4.1.0 ou plus, résolu automatiquement
  dans le cache des plugins).
- **PreCompact** — avant qu'un compactage n'écrase la conversation, dépose sa
  partie textuelle (tours utilisateur/assistant, jamais les sorties d'outils
  ni les rappels système) dans `inbox/session-YYYY-MM-DD-<id>.md`
  (`type: session`) : le savoir de la session attend dans le sas, et
  `/doc-ingest` en extraira à froid les décisions et faits durables — jamais
  le déroulé — avant d'archiver le brut. Même session recompactée plusieurs
  fois → même fichier, réécrit plus complet.

## Notes d'environnement

- **Le vault vit côté Windows, pas dans WSL** : un vault créé dans le disque
  WSL (`~/...`) fait planter l'Obsidian Windows à l'ouverture (`EISDIR ...
  watch '\\wsl.localhost\...'` — Obsidian ne sait pas surveiller un chemin
  réseau UNC). Toujours donner à `/vault-init` un chemin `/mnt/<lettre>/...`
  (Drive ou dossier Windows) et ouvrir le coffre Obsidian via son chemin
  Windows natif (`G:\...`, `C:\...`).
- **WSL + Google Drive** : si le lecteur apparaît après le démarrage de WSL,
  `/mnt/<lettre>` peut être vide → `sudo mount -t drvfs <lettre>: /mnt/<lettre>`.
- **Vue Obsidian en retard** : les écritures faites hors d'Obsidian (par Claude)
  peuvent mettre un moment à apparaître — Ctrl+R recharge ; `/doc-lint` fait foi.
- **Édition simultanée** : les fichiers de conflit créés par Drive (`* (1).md`)
  sont détectés par `/doc-lint` ; règle sociale simple — un écrivain à la fois.
  Les deux points chauds structurels sont neutralisés : le journal est un
  fichier par jour (`LOG/`), et un conflit sur `INDEX.md` — un dérivé — se
  résout en le régénérant.

## Recherche sémantique (facultative, repli grep sinon)

Il y a **un index par dossier de savoir**, dans le dossier lui-même :
`<vault>/wiki/<dossier>/.index/embeddings.jsonl` pour `concepts/`, `entites/`,
`syntheses/` et `sources/`. Ni `archives/`, ni `inbox/`, ni les fichiers
racine. Chaque index est un mapping
`hash(chunk) → vecteur` partagé via Drive, fournisseur/modèle épinglés en
ligne 1, réindexation incrémentale par hash (jamais de fallback d'embeddings
entre modèles : espaces vectoriels incompatibles). Tous sont **dérivés et
reconstructibles** : les supprimer ne perd rien.

Le moteur n'est pas inclus dans ce repo : c'est
**[agentic-toolbox](https://github.com/Zairth/agentic-toolbox)** (projet de
l'auteur — routeur LLM multi-fournisseurs + module `semantic_index` : chunking
par section, embeddings `mistral-embed` épinglés, index JSONL dans le vault).
Les commandes `/doc-*` l'atteignent par deux portes, dans cet ordre :

1. **Outils MCP du plugin agentic-toolbox** (voie nominale, zéro clone) —
   `semantic_index_build`, `semantic_search`, `semantic_info`, `ocr_convert`…
   Serveur lancé à la demande par Claude Code via `uv`, clés API gérées par le
   plugin. Les commandes passent toujours le dossier du vault **explicitement**
   (celui du projet, via `vault-check.sh`) — jamais de dossier implicite :
   un vault par projet, garanti.
2. **Wrappers `scripts/vault-index.sh`, `vault-search.sh`,
   `vault-lexical.sh`** — la porte en **ligne de commande** du même moteur
   (`python -m cli`, agentic-toolbox 4.1.0+), pour les appelants qui ne peuvent
   pas être clients MCP : les **hooks sont des scripts shell**, sans session ni
   client MCP. Aucun service qui tourne, aucun venv à maintenir — `uv` résout
   les dépendances et met en cache.
   Résolution du moteur, dans cet ordre : `.claude/toolbox-path.local` du
   projet (une ligne, gitignoré), puis le plugin agentic-toolbox **dans le
   cache des plugins** (déduit de `CLAUDE_PLUGIN_ROOT`, version la plus haute),
   puis un clone en `~/projects/agentic-toolbox`. Tout moteur respectant le
   même contrat (JSON sur stdout, message sur stderr et code non nul en cas
   d'échec) s'y substitue en éditant les wrappers, sans toucher aux commandes.

Sans moteur, tout fonctionne : `/doc-query` dégrade vers grep avec un
avertissement explicite, `/doc-ingest` note l'indexation « à rattraper », et le
hook de contexte se tait. Installation du moteur :
[PREREQUIS.md](PREREQUIS.md).

**Ce qui sort du vault** : indexer envoie le texte de `wiki/` au fournisseur
d'embeddings, chaque `/doc-query` y envoie la question, et l'OCR y envoie les
pièces converties. Un vault n'est donc jamais purement local dès qu'un moteur
est branché.

> **Règle à s'appliquer pour chaque clé API utilisée avec ce plugin** : avant
> de la coller, ouvrir la console du fournisseur et **décider explicitement du
> sort de vos données** — servent-elles à entraîner ses modèles, combien de
> temps sont-elles conservées, l'opt-out est-il actif ? Ce n'est pas une
> formalité : plusieurs paliers gratuits (Mistral compris) autorisent
> l'entraînement **par défaut**, et le réglage ne vaut en général que pour les
> appels **futurs** — le faire après une première indexation, c'est le faire
> trop tard. La même question vaut pour la session Claude Code elle-même, qui
> transmet à Anthropic tout ce que Claude lit, écrit, ou que vous collez à la
> main. Procédures, régimes par fournisseur et captures des deux pages de
> réglage :
> [PREREQUIS.md](PREREQUIS.md#5-agentic-toolbox-recherche-sémantique--ocr--facultatif).
