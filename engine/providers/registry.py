# providers/registry.py
"""Le registre des fournisseurs — LA source unique des noms et des classes.

C'est LE point d'entrée du module (ré-exporté par __init__.py) : l'appelant
résout un fournisseur par son nom (`resolve_embedding_provider`) ou diagnostique
l'état de la configuration (`describe_providers`) sans jamais instancier une
classe concrète lui-même."""

from providers.base import LLMProvider, OpenAICompatibleProvider
from providers.errors import LLMError
from providers.hosted.mistral.provider import MistralProvider

# LA liste des fournisseurs — imports statiques, une seule liste, dans le code.
# Ajouter un fournisseur = son dossier + son import + une entrée ici.
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    provider_class.name: provider_class
    for provider_class in (MistralProvider,)
}

# LE fournisseur qu'épinglent les portes d'entrée (MCP et CLI) quand elles construisent
# un index ou convertissent un document. Ici et pas dans chaque porte : deux portes
# portant chacune leur constante finiraient un jour par épingler deux fournisseurs
# différents — et un index construit par l'une serait illisible pour l'autre.
PINNED_PROVIDER = "mistral"


def resolve_embedding_provider(provider_name: str) -> OpenAICompatibleProvider:
    """LE fournisseur épinglé pour l'embedding, appelable — sinon LLMError explicite.

    Jamais de fallback par conception : des vecteurs de deux modèles ne sont pas
    comparables, l'appelant épingle UN fournisseur et assume son indisponibilité
    (dégradation chez lui). Point unique du contrat — consommé par
    services/semantic_index (service)."""
    provider_class = PROVIDER_REGISTRY.get(provider_name)
    if provider_class is None:
        raise LLMError(f"fournisseur inconnu : {provider_name!r} — noms connus : {list(PROVIDER_REGISTRY)}")
    provider = provider_class()
    if not isinstance(provider, OpenAICompatibleProvider):
        raise LLMError(f"{provider_name} ne supporte pas l'endpoint /embeddings")
    provider_issue = provider.embedding_configuration_issue()
    if provider_issue is not None:
        raise LLMError(f"{provider_name} inutilisable pour l'embedding : {provider_issue}")
    return provider


def describe_providers() -> list[dict]:
    """État de chaque fournisseur du registre (pour l'outil MCP `llm_check`) —
    purement local : zéro réseau, zéro quota."""
    return [provider_class().describe() for provider_class in PROVIDER_REGISTRY.values()]
