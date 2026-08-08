# services — Les briques métier de la boîte à outils

## Pourquoi ce dossier existe

Regroupe ce que la boîte à outils **sait faire** : des briques indépendantes,
consommables via les outils MCP (`mcp_server/`) ou depuis le code (façade
`__init__.py` de chaque brique).
La frontière avec `providers/` : `providers/` sait *comment parler aux modèles*
(protocole, registre, clés) ; chaque service ici est une orchestration
métier qui **consomme** `providers/` — jamais l'inverse (`providers/` ne connaît
aucun service). Le futur harness (loops, sub-agents) s'appuiera sur ces briques.

Point commun des briques actuelles : quand la capacité n'a de sens que chez UN
fournisseur/modèle, il est ÉPINGLÉ — jamais de fallback silencieux, échec
explicite, c'est l'appelant qui décide de la dégradation.

Contenu, brièvement :

- `semantic_index/` — recherche sémantique sur un ou plusieurs dossiers markdown
  (embeddings épinglés, index JSONL qui vit DANS le dossier indexé)
- `lexical_index/` — recherche lexicale BM25 sur les mêmes dossiers (index FTS5
  éphémère, zéro API, zéro fichier écrit) — **non câblé** dans la recherche par
  défaut : mesuré au banc, il n'atteint aucune cible que le vectoriel rate. Outil
  à part, pour les questions ancrées sur un terme exact
- `document_ocr/` — PDF/scans → markdown via l'OCR Mistral (sortie directement
  indexable par `semantic_index`)
- `markdown_corpus.py` — CE qu'un dossier indexé contient et QUEL texte y est
  cherchable (front matter retiré) : partagé par les deux bras de recherche
- `__init__.py` — marqueur de package (en-tête de chemin uniquement)

## Documentation détaillée par fichier

### `markdown_corpus.py`

`read_markdown_corpus(racine)` → `list[MarkdownDocument]` (`relative_path` en
POSIX, `text`) : tous les `.md` sous la racine, récursif, ordre trié (deux
constructions à contenu identique produisent le même index — un diff de synchro
cloud ne bouge pas sans raison).

Ce n'est pas une factorisation de confort : si les bras vectoriel et lexical
énuméraient ou lisaient les fichiers chacun de leur côté, ils pourraient un jour
classer des corpus différents — et leurs scores, comparés ou fusionnés,
mentiraient. Agnostique du contenu, comme le reste : ce module sait ce qu'est un
fichier `.md` et ce qu'est un front matter, pas ce qu'est une « note » ou un
« vault ».

**Le front matter YAML en tête de fichier est retiré du texte cherchable.** Ses
clés se répètent à l'identique dans tous les fichiers d'un dossier : elles ne
discriminent rien (IDF nul côté BM25, dilution du vecteur côté sémantique) et
mangent les premiers mots de chaque aperçu, dont la longueur utile est limitée.
Le reconnaître n'est pas connaître les conventions de l'appelant — le bloc
délimité par `---` en tête de fichier est une convention markdown universelle
(Jekyll, Hugo, Pandoc, Obsidian), du même ordre qu'un titre ATX. Conséquence
assumée : les **valeurs** du front matter cessent d'être cherchables (le corps du
fichier dit la même chose) ; indexer les valeurs sans les clés demanderait au
moteur de décider ce qui, dans un front matter, est du contenu. Deux garde-fous :
seule une ligne `---` en **première** ligne ouvre un bloc (ailleurs c'est une
règle horizontale), et un bloc **jamais refermé** n'en est pas un — le texte
ressort intact plutôt qu'amputé.

### `__init__.py`

Marqueur de package (en-tête de chemin uniquement) — chaque brique expose sa
propre façade dans son `__init__.py`.
