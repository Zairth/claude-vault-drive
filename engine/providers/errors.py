# providers/errors.py
"""Exceptions du module llm — hiérarchie unique : l'appelant attrape large (LLMError)
ou fin (ProviderRequestError) selon son besoin."""


class LLMError(Exception):
    """Base commune de toutes les erreurs du module llm."""


class ProviderRequestError(LLMError):
    """Échec d'un appel à UN fournisseur (HTTP >= 400, timeout, erreur réseau).

    `status_code` vaut None pour les erreurs réseau/timeout (pas de réponse HTTP).
    `retry_after_seconds` reprend l'en-tête Retry-After si le fournisseur l'a fourni —
    l'appelant peut s'en servir pour dimensionner une nouvelle tentative."""

    def __init__(
        self,
        provider_name: str,
        detail: str,
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ):
        self.provider_name = provider_name
        self.detail = detail
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds
        status_label = status_code if status_code is not None else "réseau"
        super().__init__(f"[{provider_name}] ({status_label}) {detail}")
