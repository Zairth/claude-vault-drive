# providers/base.py
"""Contrat abstrait des fournisseurs LLM + implémentation générique OpenAI-compatible.

Deux niveaux d'héritage :
- LLMProvider : le contrat minimal qu'un consommateur agnostique connaît ;
- OpenAICompatibleProvider : TOUTE la mécanique HTTP du protocole OpenAI vit ici (DRY).
  Une sous-classe concrète ne déclare que son identité : `name`, `base_url` et
  `api_key = settings.<x>_api_key` (lien EXPLICITE vers le champ settings — aucune
  convention de nommage, aucun getattr) — voir hosted/<name>/provider.py.
"""

from abc import ABC, abstractmethod
from operator import itemgetter
from typing import ClassVar

import httpx
from pydantic import SecretStr

from providers.errors import ProviderRequestError
from providers.schema import EmbeddingResponse

# Raison unique « pas de modèle d'embedding » — partagée entre embedding_configuration_issue()
# (diagnostic sans réseau) et embed() (garde-fou à l'appel) : les deux doivent dire pareil.
_NO_EMBEDDING_MODEL_REASON = "aucun modèle d'embedding déclaré (default_embedding_model)"


class LLMProvider(ABC):
    """Contrat minimal d'un fournisseur : un consommateur ne connaît que cette interface."""

    name: ClassVar[str]

    @abstractmethod
    def configuration_issue(self) -> str | None:
        """None si le fournisseur est appelable ; sinon la raison humaine du blocage
        (clé API absente...). Une seule méthode porte le booléen ET son explication —
        l'appelant échoue explicitement sans appel réseau condamné."""


class OpenAICompatibleProvider(LLMProvider):
    """Fournisseur générique parlant le protocole OpenAI (/embeddings notamment).

    Les points de variation entre fournisseurs sont isolés dans des méthodes
    `resolve_*` surchargeables — c'est là que joue le polymorphisme."""

    base_url: ClassVar[str]
    # Modèle d'embedding du fournisseur — None (défaut) = fournisseur inutilisable pour
    # l'embedding (embedding_configuration_issue le dit).
    default_embedding_model: ClassVar[str | None] = None
    # Clé API déclarée EXPLICITEMENT par chaque fournisseur : `api_key = settings.<x>_api_key`
    # (évaluée à l'import — settings est un singleton chargé une fois).
    api_key: ClassVar[SecretStr | None] = None
    requires_api_key: ClassVar[bool] = True
    # Propriétés du protocole OpenAI — elles appartiennent à CETTE classe (pas à un
    # fichier de constantes) et restent surchargeables par un fournisseur atypique.
    embeddings_path: ClassVar[str] = "/embeddings"
    embeddings_timeout_seconds: ClassVar[float] = 60.0

    def resolve_api_key(self) -> str | None:
        """La clé déclarée par la classe, normalisée.

        Une variable laissée vide (`MISTRAL_API_KEY=`) produit un SecretStr("") :
        on la traite comme une clé absente pour que le fournisseur soit ignoré."""
        if self.api_key is None:
            return None
        api_key_value = self.api_key.get_secret_value().strip()
        return api_key_value or None

    def resolve_embedding_model(self) -> str | None:
        """Le modèle d'embedding déclaré par la classe — None = pas de support
        embedding chez ce fournisseur."""
        return self.default_embedding_model

    def resolve_base_url(self) -> str:
        """URL de base statique par défaut — surchargeable si elle devient dynamique."""
        return self.base_url

    def configuration_issue(self) -> str | None:
        if self.requires_api_key and self.resolve_api_key() is None:
            return "clé API absente"
        return None

    def embedding_configuration_issue(self) -> str | None:
        """None si embed() est appelable ; sinon la raison humaine du blocage — même
        philosophie que configuration_issue (le booléen ET son explication ensemble)."""
        base_issue = self.configuration_issue()
        if base_issue is not None:
            return base_issue
        if self.resolve_embedding_model() is None:
            return _NO_EMBEDDING_MODEL_REASON
        return None

    def describe(self) -> dict:
        # Diagnostic pour l'outil MCP `llm_check` UNIQUEMENT — volontairement hors du
        # contrat LLMProvider : les consommateurs métier n'en ont pas besoin.
        return {
            "name": self.name,
            "configured": self.configuration_issue() is None,
            "embedding_model": self.resolve_embedding_model(),
            "base_url": self.resolve_base_url(),
        }

    async def _post_json(self, endpoint_path: str, request_payload: dict, timeout_seconds: float) -> dict:
        """POST authentifié vers un endpoint du protocole OpenAI, corps JSON décodé.

        LA mécanique HTTP partagée par tous les appels (embed, ocr) : auth Bearer,
        erreurs réseau et HTTP normalisées en ProviderRequestError (Retry-After
        compris)."""
        request_headers = {}
        api_key = self.resolve_api_key()
        if api_key is not None:
            request_headers["Authorization"] = f"Bearer {api_key}"

        endpoint_url = f"{self.resolve_base_url()}{endpoint_path}"
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as http_client:
                response = await http_client.post(endpoint_url, json=request_payload, headers=request_headers)
        except httpx.HTTPError as network_error:
            raise ProviderRequestError(self.name, detail=str(network_error)) from network_error

        if response.status_code >= 400:
            raise ProviderRequestError(
                self.name,
                detail=response.text[:300],
                status_code=response.status_code,
                retry_after_seconds=_parse_retry_after(response.headers.get("retry-after")),
            )
        return response.json()

    async def embed(self, texts: list[str], model: str | None = None) -> EmbeddingResponse:
        """Vectorise une liste de textes (endpoint /embeddings, appel par lots).

        `model` : modèle épinglé par l'appelant (cas d'un index existant — le modèle
        de l'index fait foi, PAS le défaut courant de la classe) ; None = le modèle
        résolu par le fournisseur. Jamais de fallback sur les embeddings :
        l'appelant choisit SA classe concrète."""
        embedding_model = model or self.resolve_embedding_model()
        if embedding_model is None:
            raise ProviderRequestError(self.name, detail=_NO_EMBEDDING_MODEL_REASON)

        request_payload = {"model": embedding_model, "input": texts}
        response_body = await self._post_json(self.embeddings_path, request_payload, self.embeddings_timeout_seconds)

        # L'ordre de sortie suit `index`, pas la position dans `data` (le protocole ne garantit que l'index)
        embedding_items = sorted(response_body["data"], key=itemgetter("index"))
        token_usage = response_body.get("usage") or {}
        return EmbeddingResponse(
            vectors=[item["embedding"] for item in embedding_items],
            provider_name=self.name,
            model=response_body.get("model", embedding_model),
            input_tokens=token_usage.get("prompt_tokens"),
        )


def _parse_retry_after(header_value: str | None) -> float | None:
    """Retry-After numérique (secondes) → float ; format date HTTP ou absent → None."""
    if header_value is None:
        return None
    try:
        return float(header_value)
    except ValueError:
        return None
