# tests — le filet de non-régression du moteur

## Pourquoi ce dossier existe

Le moteur a deux endroits où une erreur est **invisible** : elle ne lève rien,
elle dégrade silencieusement la pertinence — et la corriger coûte une
réindexation, donc des appels API. Ces deux endroits sont la **découpe** des
fichiers et le **classement** des résultats. Ce sont eux que couvrent ces tests,
et à peu près rien d'autre : ni le réseau, ni les fournisseurs, ni la qualité du
classement (ça, c'est le banc, pas un test).

**Zéro infrastructure, zéro dépendance** : `unittest` de la bibliothèque
standard, aucun runner à installer, aucune configuration. Les seules dépendances
sont celles du moteur lui-même (`requirements.txt`), d'où le lancement via `uv` —
le même que celui qui exécute le plugin :

```
uv run --with-requirements requirements.txt python -m unittest discover -s tests -t .
```

Deux principes de rédaction :

- **aucun seuil recopié** — les tests lisent les constantes depuis les modules
  (`MAX_CHUNK_CHARS`…). Changer la granularité de chunk doit rester une
  décision qu'on mesure au banc, pas une liste de tests à réécrire ;
- **aucun appel réseau** — le fournisseur d'embedding est remplacé, les index de
  test sont des objets en mémoire, les corpus des dossiers temporaires.

Contenu, brièvement :

- `test_markdown_corpus.py` — quel texte est cherchable : énumération, retrait du front matter
- `test_chunker.py` — l'escalier de découpe : sections, seuils, chevauchement
- `test_store.py` — le fichier d'index : ce qu'un index dit de lui-même survit au disque
- `test_semantic_search.py` — recherche multi-répertoires : un seul embedding, classements séparés
- `test_lexical_index.py` — BM25 : IDF, saturation, normalisation par la longueur
- `test_cli.py` — la porte shell : contrat de sortie (JSON/stderr/codes) et aiguillage
- `__init__.py` — marqueur de package (découverte `python -m unittest`)

## Documentation détaillée par fichier

### `test_markdown_corpus.py`

Couvre `services/markdown_corpus.py`, le seul point où le moteur décide QUEL
texte est cherchable — une erreur là se propage identiquement aux deux bras, donc
invisiblement : ils resteraient d'accord entre eux tout en indexant la mauvaise
chose. Vérifie l'énumération (récursive, `.md` seulement, ordre stable) et le
retrait du **front matter** : bloc de tête retiré, fichier sans front matter
intact, `---` au milieu du document conservé (c'est une règle horizontale), bloc
de tête jamais refermé conservé (le texte ressort intact plutôt qu'amputé), seul
le premier bloc retiré, fichier réduit à son front matter sans texte cherchable.

### `test_chunker.py`

Couvre `services/semantic_index/chunker.py`. Deux familles :
`SectionSplittingTests` (une section par titre ATX, préambule, sections vides
ignorées, `#tag` et `#!/bin/bash` qui ne sont pas des titres, titre inclus dans
le texte vectorisé) et `OversizedSectionTests` (l'escalier). Les trois tests qui
comptent : **aucun chunk ne dépasse jamais le seuil** quel que soit le document
(paragraphes, mur de lignes, mur de mots, « mot » plus long que le seuil dans un
même fichier), **rien n'est perdu** (les chunks recollés rendent le texte
d'origine, chevauchement retiré) et le chevauchement du cran des mots **tombe sur
une frontière de mot**. Le chevauchement est mesuré de l'extérieur — le plus long
début d'un chunk qui termine le précédent — pour que le test ne rejoue pas la
logique qu'il vérifie. `DirectoryChunkingTests` vérifie ce qui est réellement
indexé, en passant par la définition du corpus : aucun front matter ne parvient
jusqu'à un chunk.

### `test_store.py`

Couvre `services/semantic_index/store.py` sur un seul point, mais celui qui coûte
de l'argent : un index que le store juge **illisible** est traité comme jamais
construit, donc revectorisé en entier. Tout champ ajouté à `IndexMetadata` ouvre
ce risque pour les index déjà sur disque — d'où ce filet, posé avec l'arrivée de
`chunk_chars`. Vérifie que la granularité survit à l'aller-retour disque, et
qu'une ligne 1 **sans** le champ reste lue (granularité inconnue, pas index
invalide).

### `test_semantic_search.py`

Couvre `search_indexes` (`services/semantic_index/service.py`), sans réseau :
`_embed_texts` et `_resolve_embedding_provider` sont remplacés, `read_index` rend
des index fabriqués. Vérifie que **cinq répertoires ne coûtent qu'une seule
vectorisation de la question** (le gain du multi-répertoires), que les
classements restent **groupés par répertoire dans l'ordre demandé**, qu'un
répertoire non indexé fait échouer la recherche **avant** de dépenser un appel
d'embedding, et que des contrats épinglés divergents sont refusés explicitement.
`OneResultPerFileTests` teste le cran interne `_ONE_RESULT_PER_FILE` dans ses
DEUX états — activé (l'état livré depuis la 4.3.0 : top-k de fichiers distincts,
chacun représenté par son meilleur extrait, regroupement AVANT troncature) et
désactivé (retour au classement par chunk), parce qu'un cran qu'on peut remettre
à `False` au banc doit rester couvert dans les deux positions.

### `test_lexical_index.py`

Couvre `services/lexical_index/`. Prouve les trois propriétés qui justifient le
bras lexical : **IDF** (un terme présent partout ne discrimine plus, c'est le
terme rare qui décide), **saturation de fréquence** (à longueur de document
égale, passer de 10 à 100 occurrences rapporte moins que de 1 à 10) et
**normalisation par la longueur** (un fichier court n'est pas écrasé par un
long). Vérifie aussi ce que le tokeniseur couvre nativement (casse, accents,
formes fléchies par requête en préfixe), que la ponctuation d'une question en
langage naturel n'est jamais relue comme de la syntaxe FTS5, que le **nom** des
fichiers n'est jamais cherché (aucune supposition de nomenclature), que le **front
matter** ne pollue ni l'aperçu ni l'index, que le dossier cherché ressort
**intact** (index éphémère) et que chaque échec est explicite. La frontière qui compte : un dossier **sans `.md`** rend zéro résultat
sans interrompre les autres dossiers de l'appel (un corpus jeune a des couches
vides), un dossier **introuvable** échoue (c'est un appel fautif).

### `test_cli.py`

Couvre `cli/__main__.py`. Vérifie ce sur quoi un script appelant s'appuie sans
pouvoir le deviner : **stdout ne porte que du JSON** (et reste vide en cas
d'échec), un échec métier part sur **stderr avec le code 1** et son message est
relayé **verbatim** (la porte ne reformule ni ne préfixe), un usage invalide sort
en **code 2**. `CommandDispatchTests` vérifie l'aiguillage — chaque sous-commande
pointe bien sur sa brique, `--dir` est répétable et garde son ordre. Seule
`lexical` est exécutée pour de vrai : c'est la seule des quatre commandes qui ne
demande ni réseau ni clé.
