# services/semantic_index/__init__.py
"""Façade publique de l'index sémantique — l'appelant n'importe que d'ici.

    from services.semantic_index import build_index, search_indexes, SemanticIndexError

    report = await build_index(Path("notes/"), "mistral")   # écrit notes/.index/embeddings.jsonl
    grouped = await search_indexes([Path("notes/"), Path("refs/")], "ma question", top_k=5)

Un index par dossier, mais UNE seule vectorisation de la question pour toute la
recherche : c'est le seul coût API, le reste est du calcul local. Les résultats
restent groupés par dossier — deux dossiers indexés séparément sont deux corpus
disjoints, leurs scores ne se comparent pas.

Contrat central : le fournisseur et le modèle d'embedding sont ÉPINGLÉS dans les
métadonnées de l'index — jamais de fallback (des vecteurs de deux modèles ne sont
pas comparables). Toute indisponibilité lève SemanticIndexError : c'est l'appelant
qui dégrade vers sa recherche par mots-clés. Via le plugin : outils MCP
`semantic_index_build`, `semantic_search`, `semantic_info`.
"""

from services.semantic_index.errors import SemanticIndexError
from services.semantic_index.service import (
    DirectorySearchResults,
    IndexBuildReport,
    SearchResult,
    build_index,
    read_index_metadata,
    search_indexes,
)

__all__ = [
    "DirectorySearchResults",
    "IndexBuildReport",
    "SearchResult",
    "SemanticIndexError",
    "build_index",
    "read_index_metadata",
    "search_indexes",
]
