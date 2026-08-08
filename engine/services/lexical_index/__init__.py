# services/lexical_index/__init__.py
"""Façade publique de la recherche lexicale BM25 — l'appelant n'importe que d'ici.

    from services.lexical_index import search_lexical, LexicalIndexError

    grouped = search_lexical([Path("notes/"), Path("refs/")], "ma question", top_k=5)

Zéro appel API, zéro fichier écrit : l'index FTS5 est construit en mémoire à la
requête et jeté après (on persiste ce qui coûte de l'argent — les embeddings —,
on reconstruit ce qui est gratuit). Aucune dépendance ajoutée : FTS5 et `bm25()`
sont dans le `sqlite3` de la bibliothèque standard.

Statut : **non câblé** dans la recherche par défaut, et ce n'est pas une attente
mais un verdict de banc — le lexical n'atteint aucune cible que le vectoriel
rate, une fusion n'ajouterait rien. C'est un outil à part : terme rare (un
identifiant, une référence) → bonne cible en premier rang ; périphrase sans mot
commun avec sa cible → rien, et c'est au vectoriel de répondre. Via le plugin :
outil MCP `lexical_search`.
"""

from services.lexical_index.errors import LexicalIndexError
from services.lexical_index.service import (
    DirectoryLexicalResults,
    LexicalResult,
    search_lexical,
)

__all__ = [
    "DirectoryLexicalResults",
    "LexicalIndexError",
    "LexicalResult",
    "search_lexical",
]
