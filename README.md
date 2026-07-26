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
`context: fork` — le contexte principal n'est jamais saturé) et par des
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
│   └── doc-lint.md          # /doc-lint — maintenance (fork isolé : orphelins, INDEX, conflits Drive, vecteurs)
├── scripts/
│   ├── vault-check.sh       # portier : vérifie l'accès au vault, imprime son chemin
│   ├── vault-init.sh        # initialisation du vault en une commande, idempotente
│   ├── toolbox-env.sh       # résolution du moteur sémantique (dossier + venv)
│   ├── vault-index.sh       # indexation sémantique incrémentale (repli CLI, sans plugin toolbox)
│   └── vault-search.sh      # recherche sémantique dans un dossier indexé (repli CLI)
└── vault-template/          # fichiers copiés à la racine d'un nouveau vault
    ├── INSTRUCTIONS-CLAUDE.md   # le schéma du vault — toute commande le lit d'abord
    ├── INDEX.md                 # carte du vault, point d'entrée des recherches
    └── LOG.md                   # journal append-only
```

Le code (commandes, scripts, template) vit dans le plugin, partagé entre tous
les projets ; la config vit dans chaque projet (`.claude/vault-path.local`,
`settings.local.json`, `toolbox-path.local` — gitignorés) : **un plugin, un
vault par projet**.

## Principes

- **Source de vérité = les `.md` du vault.** Tout le reste (index de recherche,
  caches) est un dérivé jetable et reconstructible.
- **Recherche isolée du contexte principal** : `/doc-query` et `/doc-lint`
  s'exécutent entièrement dans un sub-agent (`context: fork` dans le
  frontmatter de la commande) — le contexte principal de Claude ne voit jamais
  les notes brutes ni même les instructions de la commande (anti-saturation,
  anti-distracteurs) ; seuls la réponse citée ou le rapport remontent.
- **Trois couches de savoir** : `wiki/sources/` (immuable, une note par source),
  `wiki/concepts/` + `wiki/entites/` (vivantes, reliées par wikilinks),
  `wiki/syntheses/` (réponses transversales persistées).
- **Modèle de note** : frontmatter obligatoire sur chaque note — `type`,
  `date` (création), `auteur`, plus `origine`/`original` (sources) et
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
   vault, copie du template, date de l'entrée `init` du LOG, vérification
   finale par `vault-check.sh`.
2. Relancer la session Claude Code (pour charger la permission
   `additionalDirectories`) — les commandes `/doc-ingest`, `/doc-query` et
   `/doc-lint` sont prêtes.
3. (Facultatif, humain) Ouvrir le dossier du vault comme coffre dans Obsidian.
   Astuce vue graphique : les arêtes du graphe ne viennent que des wikilinks
   `[[...]]` (les chemins bruts et propriétés `origine`/`original` n'en créent
   pas) ; pour colorer les nœuds par type, créer un groupe par dossier dans
   les paramètres du graphe — `path:wiki/concepts`, `path:wiki/entites`,
   `path:wiki/sources`, `path:wiki/syntheses`.

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

- `/doc-ingest <texte | fichier | URL | élément de inbox/>` — propose 2-5
  enseignements clés, discute, puis écrit : note source immuable, pages
  concepts/entités, INDEX, LOG. Contradiction détectée → callout `> [!warning]`.
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
- `/doc-lint` — rapport produit en fork isolé : contradictions en souffrance,
  pages orphelines, trous d'INDEX, fichiers de conflit Drive, inbox en
  attente, frontmatters obligatoires manquants, cohérence de l'index vectoriel
  (`.index/`) ; corrections validées avec l'utilisateur puis appliquées en
  contexte principal.

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
   (celui du projet, via `vault-check.sh`) — jamais le `VAULT_PATH` global du
   plugin : un vault par projet, garanti.
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
