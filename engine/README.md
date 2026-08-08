# engine — le moteur sémantique/OCR du plugin

Moteur sémantique/OCR/LLM exposé aux agents IA **via MCP**, pensé pour être
piloté par des agents (sorties structurées, échecs explicites) et tourner à
coût quasi nul (tiers gratuits). Il est embarqué dans `claude-vault` : le
manifeste du plugin (à la racine du dépôt, pas ici) déclare son serveur MCP et
lui passe la clé API.

Rien dans ce dossier ne connaît le vault : le moteur reçoit ses dossiers en
argument, toujours, et n'en suppose aucun. Ce sont les commandes `/doc-*` et
les wrappers `scripts/vault-*.sh` qui savent où est le vault.

Trois briques aujourd'hui, dont deux servies par un seul fournisseur (Mistral,
tier gratuit) et une qui ne consomme rien du tout :

- **`services/semantic_index`** — recherche sémantique sur un ou plusieurs
  dossiers markdown : embeddings épinglés (jamais de fallback), index JSONL qui
  vit DANS le dossier indexé, **une seule vectorisation de la question** quel que
  soit le nombre de dossiers cherchés ;
- **`services/lexical_index`** — recherche lexicale BM25 sur les mêmes dossiers :
  index SQLite FTS5 **éphémère** (construit en mémoire à la requête, jamais
  persisté), zéro appel API, zéro dépendance ajoutée. **Non câblé** dans la
  recherche par défaut — le banc a tranché : il n'atteint aucune cible que le
  vectoriel rate, mais il ancre les termes rares que celui-ci dilue ;
- **`services/document_ocr`** — PDF et scans → markdown via l'OCR Mistral
  (`mistral-ocr-latest`, inclus dans le tier gratuit) : la sortie est directement
  indexable par `semantic_index`.

Sous ces briques, **`providers`** porte le protocole OpenAI-compatible et le
registre des fournisseurs (un seul inscrit aujourd'hui, la structure d'ajout
reste).

Côté clé API (gratuite) : demandée par le formulaire d'activation du plugin — à
créer ici : https://console.mistral.ai/?profile_dialog=api-keys (tier
Experiment — vérification téléphone).

## Structure

```
engine/
├── mcp_server/              # serveur MCP du plugin : les briques métier en outils structurés
│   ├── server.py            # les 6 outils (semantic_*, lexical_search, ocr_convert, llm_check)
│   └── __main__.py          # entrée stdio `python -m mcp_server` (lancée par le plugin via uv)
├── cli/                     # porte d'entrée shell — pour les appelants qui ne peuvent pas être
│   └── __main__.py          # clients MCP (les hooks sont des scripts) : search, lexical, index,
│                            # convert — JSON sur stdout, échec sur stderr + exit 1
├── core/
│   └── settings.py          # Settings pydantic — source unique des clés/credentials (env du plugin)
├── providers/               # Le « cerveau » LLM : protocole OpenAI-compatible (base.py), registre
│   │                        # des fournisseurs (registry.py) + un dossier par fournisseur
│   └── hosted/              # Inférence chez un tiers, au token : mistral/ (embeddings, OCR)
├── tests/                   # Le filet de non-régression : découpe, classement, portes d'entrée
│                            # (unittest, zéro dépendance, zéro réseau)
└── services/                # Les briques métier — chacune CONSOMME providers/, jamais l'inverse
    ├── markdown_corpus.py   # QUEL texte est cherchable (front matter retiré) — partagé, 2 bras
    ├── semantic_index/      # Bras vectoriel : chunker.py, store.py (JSONL dans le dossier indexé),
    │                        # service.py — modèle ÉPINGLÉ, un seul embedding par recherche
    ├── lexical_index/       # Bras lexical BM25 : service.py — index FTS5 éphémère, zéro API
    │                        # (NON câblé dans la recherche par défaut : verdict de banc)
    └── document_ocr/        # PDF/scans → markdown via l'OCR Mistral : service.py
                             # — fournisseur ÉPINGLÉ (seul à proposer l'OCR)
```

## Installation

Le moteur vit dans le plugin — aucun clone, aucun venv à gérer. Le plugin
fournit :

- un **serveur MCP** (`mcp_server/`), lancé automatiquement via `uv` depuis la
  copie du plugin : six outils structurés (`semantic_index_build`,
  `semantic_search`, `semantic_info`, `lexical_search`, `ocr_convert`,
  `llm_check`) ;
- une **porte d'entrée shell** (`cli/`) pour les appelants qui ne peuvent pas
  être clients MCP — un hook Claude Code est un script : `python -m cli
  {search,lexical,index,convert}`, JSON sur stdout, échec sur stderr + exit 1 ;
- le **skill** `skills/vault-engine/` (mode d'emploi pour agents : outils,
  pièges connus), à la racine du plugin car c'est là que Claude Code les lit.

La clé API est demandée à l'activation (champ `userConfig` du manifeste
racine) et stockée par Claude Code hors du dépôt (keychain ou credentials
chiffrés utilisateur) ; `/plugin uninstall` retire tout. Un seul champ : la clé
Mistral. Seul prérequis : [uv](https://docs.astral.sh/uv/)
(`curl -LsSf https://astral.sh/uv/install.sh | sh`) — il télécharge les
dépendances Python à la volée, en cache partagé.

Chaque version et sa raison d'être : le [CHANGELOG](../CHANGELOG.md) du plugin.

## Recherche sémantique : embeddings + index local (`services/semantic_index`)

Indexe n'importe quel dossier de fichiers markdown (chunks par section → vecteurs →
JSONL) et le cherche par similarité — pensé pour être appelé par les sub-agents
d'un projet tiers (ex : un vault de notes). **L'index vit DANS le dossier indexé**
(`<dossier>/.index/embeddings.jsonl`) : il voyage avec lui (synchro cloud comprise).
Les embeddings ne fallbackent JAMAIS : des vecteurs de deux
modèles ne sont pas comparables, donc le fournisseur/modèle est épinglé dans les
métadonnées de l'index (défaut : `mistral`/`mistral-embed`) ; indisponibilité →
échec explicite (l'appelant dégrade vers grep), contrat incompatible → erreur
proposant le rebuild complet. La réindexation est incrémentale par hash de
contenu : seuls les chunks nouveaux/modifiés coûtent un appel API (renommer une
note inchangée ne coûte rien).

**L'appelant peut soustraire ses blocs de service au vecteur** : `excluded_callouts`
(outil MCP) / `--exclude-callout` (CLI) déclare des types de blocs de callout
(`> [!TYPE]`, insensible à la casse) qui ne partiront ni au vecteur ni au hash —
pour les lignes qu'un projet écrit dans ses fichiers (chemins, numéros de ligne,
identifiants, horodatages) et qui diluent le vecteur sans répondre à aucune
question. Le moteur reste agnostique : il connaît la FORME d'un callout, jamais un
type — ils viennent tous de l'appelant. Le bloc reste **entier** dans les résultats
de recherche, seul le texte vectorisé l'ignore ; en échange d'une revectorisation
au premier passage, modifier ensuite le contenu d'un bloc exclu ne coûte plus rien.

**Une recherche = un seul appel API**, quel que soit le nombre de dossiers :
`semantic_search` prend une LISTE de dossiers, vectorise la question une fois et
parcourt chaque index localement. Les résultats reviennent groupés par dossier —
deux dossiers indexés séparément sont deux corpus disjoints, leurs scores ne se
comparent pas. La liste sert aussi à cibler : un dossier, ou trois, selon la
question. Le `top_k` compte des **fichiers distincts** : les chunks d'un même
fichier sont regroupés avant la troncature, et chaque fichier remonte une fois,
par son meilleur extrait — un fichier bien découpé ne peut plus occuper tout le
classement. Outils MCP : `semantic_index_build`, `semantic_search`, `semantic_info`
— dossiers cibles toujours en argument : le moteur n'a aucun dossier par défaut,
c'est l'appelant qui connaît ses chemins.

## Recherche lexicale : BM25 sans rien persister (`services/lexical_index`)

Le bras lexical à côté du bras vectoriel : là où les embeddings trouvent les
synonymes, BM25 trouve les termes exacts (noms propres, références,
identifiants), pondère par **IDF** (un mot présent dans la moitié du corpus n'y
pèse presque rien), **sature** la répétition d'un terme et **normalise par la
longueur** du fichier. L'index SQLite FTS5 est construit **en mémoire à la
requête et jeté** : on persiste ce qui coûte de l'argent à recalculer (les
embeddings), on reconstruit ce qui est gratuit (~10 ms pour 500 fichiers,
~210 ms pour 10 000). D'où : aucune péremption, aucun conflit de synchronisation,
aucune dépendance ajoutée (FTS5 et `bm25()` sont dans le `sqlite3` standard), et
ça marche sur un dossier en lecture seule, sans indexation préalable. Outil MCP :
`lexical_search`.

**Il n'est pas câblé dans `semantic_search`, et c'est une conclusion mesurée.**
Sur 22 questions de banc, aucune où le lexical touche une cible que le sémantique
rate : une fusion n'ajouterait pas un résultat, seulement l'écrasement par la
longueur de BM25 dans un classement que la séparation des index en protège. Le
partage des rôles, en revanche, est net : un **terme rare** (identifiant,
référence, empreinte de commit) ancre la question et sort la bonne cible en
premier rang ; une **périphrase** qui ne partage aucun mot avec sa cible
(« parapheur numérique » face à des fichiers qui disent « yousign ») ne lui rend
rien — c'est là que le bras vectoriel travaille. Deux outils, deux usages.

Un point à connaître avant de s'en servir : le **score BM25 ne se lit qu'en
relatif**, entre les résultats d'un même dossier et dans un même appel. Il n'est
comparable ni d'un corpus à l'autre (l'IDF se calcule sur le corpus interrogé) ni
dans l'absolu (BM25 n'a pas d'échelle bornée, contrairement au cosinus). Sur un
petit corpus, tous les scores s'écrasent près du plancher d'IDF de FTS5 (~1e-06) :
le classement reste juste, les valeurs ne veulent rien dire — filtrer sur le rang
(`top_k`), jamais sur un seuil de score.

## Deux portes d'entrée : MCP et shell (`mcp_server/`, `cli/`)

Les agents passent par les outils MCP. Mais **un hook Claude Code est un script
shell** : pas de session, pas de client MCP, juste un processus qui lit stdin et
écrit stdout. Pour cette catégorie d'appelants, `cli/` sert les mêmes briques et
rend les mêmes structures — stdout = JSON et rien d'autre, échec métier = message
sur stderr + code 1, usage invalide = code 2.

```
uv run --directory "$CLAUDE_PLUGIN_ROOT" \
       --with-requirements "$CLAUDE_PLUGIN_ROOT/requirements.txt" \
       python -m cli lexical "ma question" --dir "$corpus" --top-k 5
```

`lexical` est la commande pensée pour un hook déclenché à chaque prompt : aucun
appel API, aucune clé, aucun index préalable, ~220 ms de bout en bout. Un hook
qui se déclenche à chaque prompt ne peut pas coûter un embedding à chaque fois.

## OCR : PDF et scans → markdown (`services/document_ocr`)

Convertit un PDF (ou une image scannée : png, jpg, avif) en fichier markdown via
le modèle OCR de Mistral (`mistral-ocr-latest`, inclus dans le tier Experiment
gratuit — limite API : 50 Mo par document). Comme les embeddings, l'OCR ne
fallback JAMAIS : un seul fournisseur le propose (endpoint `/ocr`
propriétaire Mistral, hors protocole OpenAI) — mistral indisponible → échec
explicite. Le `.md` produit est directement indexable par `semantic_index`.
Outil MCP : `ocr_convert` (document, output — défaut `<document>.md` à côté de
la source, écrasé si existant). Diagnostic de la configuration (clé, modèles) :
`llm_check`, zéro réseau, zéro quota.
