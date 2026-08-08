# services/lexical_index — Recherche lexicale BM25 (index éphémère, zéro API)

## Pourquoi ce dossier existe

Le **bras lexical**, à côté du bras vectoriel de `semantic_index/`. Le vectoriel
trouve les synonymes (« voiture » retrouve « automobile ») mais dilue les termes
exacts ; le lexical fait l'inverse — noms propres, références, identifiants,
formulations littérales — avec trois propriétés qu'aucun réglage manuel ne
remplace :

- **IDF** — un terme présent dans la plupart des fichiers ne pèse presque rien.
  C'est le correctif du motif « un mot courant touche la moitié du corpus et ne
  discrimine plus rien » ;
- **saturation de fréquence** — répéter dix fois un terme ne rend pas le fichier
  dix fois plus pertinent ;
- **normalisation par la longueur du document** — les fichiers courts ne sont
  plus écrasés par les longs.

**Rien n'est persisté, rien n'est appelé** : l'index FTS5 est construit en
mémoire à la requête et jeté après (~10 ms pour 500 fichiers, ~210 ms pour
10 000 — 30 Mo de texte). Le principe : on persiste ce qui coûte de l'argent à
recalculer (les embeddings de `semantic_index/`), on reconstruit ce qui est
gratuit. Tout le reste en découle : aucune péremption possible, aucun conflit de
synchronisation (un fichier SQLite dans un dossier synchronisé se corrompt, il ne
se fusionne pas), rien à ignorer côté lint, et ça fonctionne sur un répertoire en
**lecture seule** — sans `semantic_index_build` préalable.

**Aucune dépendance ajoutée** : le `sqlite3` de la bibliothèque standard embarque
FTS5 et sa fonction `bm25()`. Un build SQLite sans FTS5 lève `LexicalIndexError`
— échec explicite, comme partout ici.

## Statut : non câblé — mesuré, pas supposé

`semantic_search` reste purement vectoriel, et ce n'est plus une attente : le
banc a tranché. Sur 22 questions, **zéro** où le lexical touche une cible que le
sémantique rate — une fusion n'ajouterait donc aucune couverture. Deux questions
sortaient mieux classées côté BM25, soit un dixième de rang moyen gagné, sur des
cibles déjà dans la fenêtre des trois premiers résultats et déjà rattrapées par
l'expansion de liens de l'appelant. Fusionner reviendrait à importer l'écrasement
par la longueur de BM25 dans un classement que la séparation des index en
protège, pour un gain redondant.

Le partage des rôles, lui, est net et chiffré :

- **terme rare → BM25 en premier rang, immédiatement** : un identifiant, une
  référence, une empreinte de commit ancrent la question, et la bonne cible sort
  en r1 ;
- **périphrase → BM25 ne rend rien** : sept questions du banc ne partageaient
  aucun token avec leur cible (« parapheur numérique » face à des fichiers qui
  disent « yousign »). Aucun mot commun, aucun résultat — c'est exactement le
  terrain du bras vectoriel.

Ce n'est donc pas un demi-moteur en attente de branchement, mais un outil à part
entière qu'on choisit quand la question est ancrée sur un terme exact. Portée du
verdict : mesuré sur UN corpus (148 notes) et avec un appelant qui fait déjà de
l'expansion de liens — c'est le contexte dans lequel le gain de la fusion
disparaît.

Comme le bras vectoriel : l'unité rendue est le **fichier** (`relative_path`),
les résultats sont **groupés par répertoire** (l'IDF se calcule SUR un corpus —
les scores de deux corpus n'ont même pas la même échelle), et le texte cherché
vient de `services/markdown_corpus.py`, le même que celui du chunker — front
matter YAML retiré compris, sinon les clés répétées dans tout un dossier
mangeraient les premiers mots de chaque aperçu sans rien discriminer.

## Ce que le score ne dit PAS

**Le score BM25 n'a de sens que relativement aux autres scores du même répertoire,
dans le même appel.** Il n'est comparable :

- **ni d'un corpus à l'autre** — l'IDF d'un terme se calcule sur le corpus
  interrogé, donc le même mot ne pèse pas la même chose dans deux dossiers ;
- **ni dans l'absolu** — BM25 n'a pas d'échelle bornée, contrairement à une
  similarité cosinus qui vit dans [-1, 1].

Sur un petit corpus, les scores s'écrasent en plus près du **plancher d'IDF de
FTS5** : mesuré sur deux documents, tout tombe autour de `1e-06`, l'IDF valant
zéro pour à peu près tout terme (SQLite le plancher à `1e-6` dès qu'il serait
négatif, c'est-à-dire dès qu'un terme est présent dans plus de la moitié des
documents). Le **classement reste juste** — la normalisation par la longueur
départage — mais les **valeurs ne veulent rien dire**.

Il n'y a rien à corriger là-dedans : c'est la nature de la mesure. Mais **ne
jamais construire de seuil dessus** (« ignorer les résultats sous X ») : calibré
sur un corpus, il serait faux sur le suivant. Pour filtrer, se servir du rang
(`top_k`), pas de la valeur.

Contenu, brièvement :

- `__init__.py` — la façade publique (`search_lexical`, `LexicalIndexError`, ...)
- `service.py` — index FTS5 éphémère, traduction de la question, classement BM25
- `errors.py` — `LexicalIndexError`, l'échec explicite du module

## Documentation détaillée par fichier

### `__init__.py`

La façade : ré-exporte `search_lexical`, les types de résultats
(`LexicalResult`, `DirectoryLexicalResults`) et `LexicalIndexError`. Les
appelants importent d'ici et de nulle part ailleurs.

### `service.py`

`search_lexical(directories, question, top_k)` → un `DirectoryLexicalResults` par
répertoire (`directory`, `results`), dans l'ordre demandé ; chaque
`LexicalResult` porte `relative_path`, `score` et `excerpt`.

Un index éphémère **par répertoire**, jamais un index commun : l'IDF d'un terme
se calcule sur le corpus qu'on interroge, sinon un terme banal ici et rare
là-bas recevrait un poids moyen qui ne décrit ni l'un ni l'autre.

La table est `fts5(relative_path UNINDEXED, body, tokenize='unicode61
remove_diacritics 2')`. `relative_path` est **UNINDEXED** : c'est une clé de
citation, pas du texte à chercher — l'indexer ferait remonter des fichiers sur la
seule ressemblance de leur nom, exactement la supposition de nomenclature que le
moteur s'interdit. Le tokeniseur gère nativement la casse et les accents
(« Élégant » trouve « elegant »).

`_build_match_expression` traduit une question en langage naturel en expression
MATCH : chaque mot (`\w+`, unicode) devient une recherche en **préfixe**
(`"mot"*` — couvre pluriels et conjugaisons), guillemets compris pour qu'aucun
mot ne soit relu comme un opérateur FTS5 ; tous sont joints par **OR**. Un
fichier n'a pas à contenir tous les mots de la question — c'est BM25 qui décide
combien chacun pèse, un AND rendrait le plus souvent zéro résultat. Une question
sans aucun mot cherchable est une erreur explicite.

Le `score` rendu est `-bm25()` (SQLite rend un score négatif, plus bas = plus
pertinent) : **plus haut = plus pertinent**, comme la similarité cosinus du bras
vectoriel — mais lisible seulement en relatif (voir « Ce que le score ne dit
PAS »). Il n'est pas arrondi, contrairement à elle : BM25 n'a pas d'échelle
bornée et FTS5 plancher l'IDF à `1e-6` pour un terme présent dans TOUS les
documents — un arrondi décimal écraserait ces scores-là à zéro. L'`excerpt` vient
de `snippet()`, centré sur les termes trouvés et aplati sur une ligne (même forme
que l'aperçu du bras vectoriel, comparable à l'œil).

### `errors.py`

`LexicalIndexError`, unique exception du module : dossier introuvable, corpus
vide, question sans mot cherchable, SQLite sans FTS5. Jamais de résultat vide qui
laisserait croire à une recherche aboutie.
