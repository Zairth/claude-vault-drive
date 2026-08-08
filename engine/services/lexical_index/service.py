# services/lexical_index/service.py
"""Recherche lexicale BM25 sur un dossier markdown — index ÉPHÉMÈRE, zéro API.

Le bras lexical, à côté du bras vectoriel de `semantic_index/`. Il apporte trois
correctifs qu'aucun réglage manuel ne remplace :

- **IDF** — un terme présent dans la plupart des fichiers ne pèse presque rien.
  C'est le correctif du motif « un mot courant touche la moitié du corpus et ne
  discrimine plus rien » ;
- **saturation de fréquence** — répéter dix fois un terme ne rend pas le fichier
  dix fois plus pertinent ;
- **normalisation par la longueur du document** — les fichiers courts ne sont
  plus écrasés par les longs.

**Rien n'est persisté** : l'index FTS5 est construit en mémoire à la requête et
jeté après. Le principe : on persiste ce qui coûte de l'argent à recalculer (les
embeddings), on reconstruit ce qui est gratuit (mesuré : ~10 ms pour 500
fichiers, ~210 ms pour 10 000). Effets de bord, tous acquis : aucune péremption
possible, aucun conflit de synchronisation (un fichier SQLite dans un dossier
synchronisé se corrompt, il ne se fusionne pas), rien à ignorer côté lint, et ça
fonctionne sur un répertoire en LECTURE SEULE.

Aucune dépendance ajoutée : le `sqlite3` de la bibliothèque standard embarque
FTS5 et sa fonction `bm25()`."""

import re
import sqlite3
from pathlib import Path

from pydantic import BaseModel

from services.lexical_index.errors import LexicalIndexError
from services.markdown_corpus import MarkdownDocument, read_markdown_corpus

# Le tokeniseur gère nativement la casse et les accents (« Élégant » trouve « elegant ») ;
# les requêtes en préfixe (`mot*`) couvrent les formes fléchies (pluriels, conjugaisons)
_FTS5_TOKENIZER = "unicode61 remove_diacritics 2"
# Les mots de la question, dans n'importe quelle langue (\w est unicode par défaut en py3) :
# tout ce qui n'est pas un mot est écarté, ce qui neutralise aussi la syntaxe FTS5
# (guillemets, parenthèses, NOT…) qu'une question en langage naturel contiendrait
_QUESTION_WORD_PATTERN = re.compile(r"\w+")
# Longueur de l'aperçu rendu, en tokens — FTS5 le centre sur les termes trouvés
_SNIPPET_TOKENS = 30


class LexicalResult(BaseModel):
    """Un résultat lexical : le FICHIER trouvé, son score et l'aperçu centré sur les termes.

    LE score BM25 n'a de sens QUE relativement aux autres scores du même
    répertoire, dans le même appel. Il n'est comparable ni d'un corpus à l'autre
    (l'IDF se calcule sur un corpus donné) ni dans l'absolu (BM25 n'a pas
    d'échelle bornée, contrairement à une similarité cosinus). Sur un petit
    corpus, tous les scores s'écrasent d'ailleurs près du plancher d'IDF de FTS5
    (~1e-6) : le CLASSEMENT reste juste — la normalisation par la longueur
    départage — mais les VALEURS ne veulent rien dire. Ne jamais construire de
    seuil dessus : calibré sur un corpus, il serait faux sur le suivant."""

    relative_path: str
    score: float      # BM25 renversé (SQLite le rend négatif) : plus haut = plus pertinent
    excerpt: str


class DirectoryLexicalResults(BaseModel):
    """Le classement d'UN répertoire, jamais fusionné avec celui d'un autre.

    Même règle que le bras vectoriel : deux répertoires sont deux corpus disjoints.
    Ici c'est encore plus littéral — l'IDF d'un terme se calcule SUR un corpus, les
    scores de deux corpus n'ont donc même pas la même échelle."""

    directory: str
    results: list[LexicalResult]


def search_lexical(directories: list[Path], question: str, top_k: int) -> list[DirectoryLexicalResults]:
    """Cherche les mots de la question dans un ou plusieurs répertoires markdown.

    Un index éphémère PAR répertoire, jamais un index commun : l'IDF doit se
    calculer sur le corpus qu'on interroge, sinon un terme banal ici et rare
    là-bas recevrait un poids moyen qui ne décrit ni l'un ni l'autre.

    L'unité rendue est le FICHIER (`relative_path`), pas la section : c'est
    l'unité de citation du moteur, et c'est sur la longueur du fichier que porte
    la normalisation BM25."""
    if not directories:
        raise LexicalIndexError("aucun répertoire à chercher — en fournir au moins un")
    match_expression = _build_match_expression(question)
    return [
        DirectoryLexicalResults(
            directory=str(directory),
            results=_search_one_directory(directory, match_expression, top_k),
        )
        for directory in directories
    ]


def _build_match_expression(question: str) -> str:
    """La question en langage naturel → une expression MATCH FTS5.

    Chaque mot devient une recherche en préfixe (`"mot"*`, guillemets compris pour
    qu'aucun mot ne soit relu comme un opérateur), et tous sont joints par OR : un
    fichier n'a pas à contenir TOUS les mots de la question — c'est BM25 qui
    décide combien chacun pèse, et l'IDF qui neutralise ceux qui ne discriminent
    rien. Un AND rendrait le plus souvent zéro résultat."""
    question_words = _QUESTION_WORD_PATTERN.findall(question)
    if not question_words:
        raise LexicalIndexError(f"aucun mot cherchable dans la question : {question!r}")
    return " OR ".join(f'"{question_word}"*' for question_word in question_words)


def _search_one_directory(directory: Path, match_expression: str, top_k: int) -> list[LexicalResult]:
    """Construit l'index éphémère du répertoire, l'interroge, le jette.

    Un répertoire SANS aucun `.md` est un état normal, pas une faute : il rend
    zéro résultat et la recherche continue sur les autres. Il n'y a rien à
    construire ici — juste rien à trouver. (Le cas est différent d'un index
    sémantique absent, qui signifie « la construction a été oubliée ».) Un
    répertoire INTROUVABLE, lui, reste une erreur : c'est un appel fautif."""
    if not directory.is_dir():
        raise LexicalIndexError(f"dossier introuvable : {directory}")
    documents = read_markdown_corpus(directory)
    if not documents:
        return []

    connection = _build_ephemeral_index(documents)
    try:
        matched_rows = connection.execute(
            "SELECT relative_path, -bm25(documents), snippet(documents, 1, '', '', '…', ?) "
            "FROM documents WHERE documents MATCH ? ORDER BY bm25(documents) LIMIT ?",
            (_SNIPPET_TOKENS, match_expression, top_k),
        ).fetchall()
    except sqlite3.OperationalError as query_error:
        raise LexicalIndexError(
            f"requête lexicale refusée par SQLite ({query_error}) — expression : {match_expression}"
        ) from query_error
    finally:
        connection.close()

    # Score non arrondi, contrairement à la similarité cosinus du bras vectoriel : BM25
    # n'a pas d'échelle bornée, et FTS5 plancher l'IDF à 1e-6 pour un terme présent dans
    # TOUS les documents — un arrondi décimal écraserait ces scores-là à zéro
    return [
        LexicalResult(relative_path=relative_path, score=score, excerpt=_flatten(snippet))
        for relative_path, score, snippet in matched_rows
    ]


def _build_ephemeral_index(documents: list[MarkdownDocument]) -> sqlite3.Connection:
    """L'index FTS5 en mémoire d'un corpus — vivant le temps d'une requête.

    `relative_path` est UNINDEXED : c'est une clé de citation, pas du texte à
    chercher — l'indexer ferait remonter des fichiers sur la seule ressemblance de
    leur nom, exactement la supposition de nomenclature que le moteur s'interdit."""
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(
            "CREATE VIRTUAL TABLE documents USING "
            f"fts5(relative_path UNINDEXED, body, tokenize='{_FTS5_TOKENIZER}')"
        )
    except sqlite3.OperationalError as creation_error:
        connection.close()
        raise LexicalIndexError(
            f"ce SQLite ({sqlite3.sqlite_version}) ne fournit pas FTS5 : {creation_error} — "
            "recherche lexicale indisponible, s'en tenir à la recherche sémantique"
        ) from creation_error
    connection.executemany(
        "INSERT INTO documents (relative_path, body) VALUES (?, ?)",
        [(document.relative_path, document.text) for document in documents],
    )
    return connection


def _flatten(snippet: str) -> str:
    """Aperçu monoligne — même forme que celui du bras vectoriel, comparable à l'œil."""
    return " ".join(snippet.split())
