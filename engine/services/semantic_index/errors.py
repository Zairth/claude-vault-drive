# services/semantic_index/errors.py
"""Exception du module semantic_index.

Une seule classe : ce module échoue toujours EXPLICITEMENT (fournisseur épinglé
indisponible, index absent, dimension incompatible...) — jamais de fallback
silencieux, c'est le contrat. L'appelant (l'agent qui consomme les outils MCP)
attrape SemanticIndexError et dégrade lui-même vers sa recherche par mots-clés."""


class SemanticIndexError(Exception):
    """Échec explicite de l'index sémantique — le message porte la raison humaine."""
