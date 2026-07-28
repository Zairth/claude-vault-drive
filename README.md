# claude-vault-drive

Un vault Obsidian partagé (Google Drive ou tout dossier synchronisé), consultable
et maintenu par Claude Code — distribué comme **plugin Claude Code** : s'installe
en deux commandes dans n'importe quel projet, **sans clone, sans service qui
tourne**. Le vault n'est que des fichiers markdown dans un dossier : Obsidian est
la vitrine humaine (graphe, wikilinks), Claude Code y accède directement.

## Objectif

Combiné à [agentic-toolbox](https://github.com/Zairth/agentic-toolbox), ce
plugin fait naître le fameux **deuxième cerveau de Claude** : une mémoire
externe durable et partagée, optimisée par **orchestration agentique**
(`/doc-query` et `/doc-lint` s'exécutent entièrement dans un sub-agent via
`context: fork` ; `/doc-ingest` lit la source dans un sub-agent lecteur
conversationnel — le contexte principal n'est jamais saturé) et par des
**skills** pour la recherche sémantique et l'OCR.

Le cas d'usage type : brancher un projet sur son dossier Drive — Claude le
**consomme** (`/doc-query` répond en citant les notes) et l'**alimente en
retour** (`/doc-ingest`, synthèses persistées) au fur et à mesure des
itérations de sessions sur ce projet. Le savoir s'accumule d'une session à
l'autre au lieu de disparaître avec le contexte, et reste lisible par les
humains dans Obsidian.

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
│   ├── doc-ingest.md        # /doc-ingest — ingérer une source (validation conversationnelle)
│   ├── doc-query.md         # /doc-query — interroger le vault (fork isolé, réponse citée)
│   ├── doc-lint.md          # /doc-lint — maintenance (fork isolé : orphelins, INDEX, conflits Drive, vecteurs)
│   └── doc-bench.md         # /doc-bench — banc de questions de référence (mesure mécanique, ou réelle via /doc-query)
├── hooks/
│   └── hooks.json           # déclaration des trois hooks (SessionStart, UserPromptSubmit, PreCompact)
├── docs/                    # captures illustrant les prérequis (opt-out d'entraînement Mistral)
├── scripts/
│   ├── vault-check.sh       # portier : vérifie l'accès au vault, imprime son chemin
│   ├── vault-init.sh        # initialisation du vault en une commande, idempotente
│   ├── toolbox-env.sh       # résolution du moteur sémantique (dossier + venv)
│   ├── vault-index.sh       # indexation sémantique incrémentale (repli CLI, sans plugin toolbox)
│   ├── vault-search.sh      # recherche sémantique dans un dossier indexé (repli CLI)
│   ├── hook-session-start.sh    # hook : INDEX.md injecté à l'ouverture de session
│   ├── hook-prompt-context.sh   # hook : pistes sémantiques sous chaque prompt
│   └── hook-precompact-inbox.sh # hook : transcript déposé dans inbox/ avant compactage
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
- **Trois couches de savoir** : `wiki/sources/` (immuable, une note par source),
  `wiki/concepts/` + `wiki/entites/` (vivantes, reliées par wikilinks),
  `wiki/syntheses/` (réponses transversales persistées).
- **Modèle de note** : frontmatter obligatoire sur chaque note — `type`,
  `date` (création), `auteur`, `description` (alimente l'INDEX), plus
  `origine`/`original` (sources) et
  `question` (synthèses) ; défini dans l'`INSTRUCTIONS-CLAUDE.md` du vault,
  appliqué par `/doc-ingest`, vérifié par `/doc-lint`.
- **Vault auto-porteur** : `inbox/` est un sas, pas un stockage — un fichier
  ingéré est déplacé vers `archives/`, jamais supprimé. Le condensé vit dans
  `wiki/sources/`, la pièce d'origine reste vérifiable dans le vault, qui
  voyage d'un bloc. `archives/` est immuable et **hors index sémantique**
  (l'index ne couvre que `wiki/` : zéro coût, zéro bruit — les fichiers
  archivés gardent leur nom et leur extension) ; attention
  avant de partager le vault, les archives peuvent contenir des données
  sensibles que les notes condensées ont volontairement écartées.
- **Échecs explicites** : Drive non monté, vault non initialisé → message clair,
  jamais de vault vide silencieux.

## Installation

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
   Astuce vue graphique : les arêtes du graphe ne viennent que des wikilinks
   `[[...]]` (les chemins bruts et propriétés `origine`/`original` n'en créent
   pas) ; pour colorer les nœuds par type, créer un groupe par dossier dans
   les paramètres du graphe — `path:wiki/concepts`, `path:wiki/entites`,
   `path:wiki/sources`, `path:wiki/syntheses`. **Exclure `archives/`**
   (Paramètres → Fichiers et liens → Filtres d'exclusion) : Obsidian indexe
   tout le vault, et les markdown OCR archivés référencent des images non
   extraites qui apparaissent en nœuds fantômes — cliquer sur l'un d'eux crée
   une note vide à la racine.

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
commandes ci-dessous opérationnelles (détail : [Installation](#installation)).

- `/doc-ingest <texte | fichier | URL | élément de inbox/>` — un sub-agent
  lecteur lit la source (le contexte principal ne la voit jamais) et propose
  2-5 enseignements clés ; la discussion passe par ce même sub-agent (relais
  SendMessage, contexte conservé) ; après validation, l'agent principal
  écrit : note source immuable, pages concepts/entités, INDEX, LOG.
  Contradiction détectée → tranchée avec l'utilisateur : la note porte la
  valeur courante, l'ancienne descend en `## Historique` (une seule vérité en
  tête, l'historique conservé) ; non tranchable → callout `> [!warning]`.
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
- `/doc-lint` — rapport produit en fork isolé, ouvert par une ligne de
  compteurs (l'état de santé du vault d'un coup d'œil, comparable d'un lint à
  l'autre) : wikilinks pendants, doublons suspectés de pages vivantes (noms
  normalisés + similarité sémantique ; fusion assistée après validation —
  wikilinks entrants réécrits, ancien nom conservé en alias),
  contradictions en souffrance,
  pages orphelines, trous d'INDEX, fichiers de conflit Drive, inbox en
  attente, frontmatters obligatoires manquants, parasites hors `wiki/`
  (`.md` inattendu à la racine, notes vides, nœuds fantômes venus des
  archives OCR), cohérence de l'index vectoriel
  (`.index/`) ; corrections validées avec l'utilisateur puis appliquées en
  contexte principal.
- `/doc-bench` — le mètre étalon de la recherche, en trois modes. `creer`
  (ou premier lancement) : propose ~20 questions de référence tirées du
  contenu du vault, chacune avec ses notes attendues — validées puis figées
  dans `BENCH.md` (racine du vault, hors index). Sans argument : run
  **mécanique** — réindexation, puis top 5 sémantique, wikilinks de ce top 5
  et grep par question, aucun jugement dans le score →
  `sémantique@5 · +1 saut · grep · couverture`, détail des échecs avec ce que
  la recherche a renvoyé à la place. L'écart entre `sémantique@5` et
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
- **UserPromptSubmit** — recherche sémantique directe sur chaque prompt
  (`vault-search.sh`, appel du moteur sans fork) : le top 3 est injecté comme
  pistes — des extraits, pas une réponse, `/doc-query` reste la vraie
  recherche. Jamais d'indexation ici (index jamais construit → silence).
  Filtres : commandes slash/`!`/`#` et prompts de moins de 12 caractères
  ignorés. Requiert le **clone local** d'agentic-toolbox (un hook est un
  process shell : il ne peut pas appeler les outils MCP) — sans clone,
  silence. À savoir : chaque prompt éligible est envoyé à l'API Mistral pour
  être vectorisé, comme toute question `/doc-query`.
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

L'index d'embeddings vit dans `<vault>/wiki/.index/embeddings.jsonl` (seul
`wiki/` est indexé — ni `archives/`, ni `inbox/`, ni les fichiers racine) — un mapping
`hash(chunk) → vecteur` partagé via Drive, fournisseur/modèle épinglés en
ligne 1, réindexation incrémentale par hash (jamais de fallback d'embeddings
entre modèles : espaces vectoriels incompatibles). Il est **dérivé et
reconstructible** : le supprimer ne perd rien.

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
2. **Wrappers `scripts/vault-index.sh` / `vault-search.sh`** (repli : plugin
   agentic-toolbox absent, mais clone local présent) — exécutés depuis le venv
   du clone, aucun service qui tourne. Résolution du chemin :
   `.claude/toolbox-path.local` du projet (une ligne, gitignoré), à défaut
   `~/projects/agentic-toolbox`. Tout moteur respectant le même contrat CLI
   (`index <dossier>` / `search "question" --dir <dossier>`, JSON sur stdout)
   s'y substitue en éditant les deux wrappers, sans toucher aux commandes.

Sans moteur (ni plugin ni clone), tout fonctionne : `/doc-query` dégrade vers
grep avec un avertissement explicite, `/doc-ingest` note l'indexation « à
rattraper ». Installation du moteur (plugin, ou clone + venv + clé Mistral) :
[PREREQUIS.md](PREREQUIS.md).

**Ce qui sort du vault** : indexer envoie le texte de `wiki/` au fournisseur
d'embeddings, et chaque `/doc-query` y envoie la question. Sur le palier
gratuit de Mistral, ces appels alimentent l'entraînement des modèles **par
défaut** — l'opt-out est gratuit mais doit être coché avant la première
indexation (console → Administration → Confidentialité). Détail et procédure :
[PREREQUIS.md](PREREQUIS.md#5-agentic-toolbox-recherche-sémantique--ocr--facultatif).
