# providers/__init__.py
"""Façade publique du « cerveau » LLM — l'appelant n'importe que d'ici.

Embeddings : l'appelant épingle UN fournisseur via `resolve_embedding_provider(name)`
puis appelle `provider.embed(texts)` directement — jamais de fallback, des
vecteurs de deux modèles ne sont pas comparables (voir services/semantic_index/
pour l'usage type).

LA liste des fournisseurs est PROVIDER_REGISTRY dans registry.py — imports
statiques, une seule liste, dans le code.

Ajouter un fournisseur hébergé :
1. créer le dossier `hosted/<name>/` avec sa classe dans `provider.py`
   (name + base_url — le reste est hérité) ;
2. sa clé API dans core/settings.py (`<name>_api_key`) et dans le userConfig
   du plugin (.claude-plugin/plugin.json) ;
3. l'importer et l'inscrire dans PROVIDER_REGISTRY (registry.py) — c'est tout.
"""

from providers.errors import LLMError, ProviderRequestError
from providers.registry import (
    PINNED_PROVIDER,
    PROVIDER_REGISTRY,
    describe_providers,
    resolve_embedding_provider,
)
from providers.schema import EmbeddingResponse

__all__ = [
    "EmbeddingResponse",
    "LLMError",
    "PINNED_PROVIDER",
    "PROVIDER_REGISTRY",
    "ProviderRequestError",
    "describe_providers",
    "resolve_embedding_provider",
]
