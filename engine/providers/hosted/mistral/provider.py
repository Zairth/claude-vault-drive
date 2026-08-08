# providers/hosted/mistral/provider.py
"""Mistral La Plateforme (tier Experiment gratuit) — l'unique fournisseur du registre.

Toute la mécanique (auth, requête, parsing, erreurs) est héritée
d'OpenAICompatibleProvider (providers/base.py) : ce fichier est la source
unique de vérité de CE fournisseur (identité, endpoint, modèles, clé) — y compris
sa capacité OCR (/ocr), propriétaire Mistral, hors protocole OpenAI."""

from operator import itemgetter

from pydantic import BaseModel

from core.settings import settings
from providers.base import OpenAICompatibleProvider


class OcrResponse(BaseModel):
    """Réponse OCR normalisée : le markdown de chaque page, dans l'ordre du document.

    Vit ici et pas dans providers/schema.py : ce schéma-là est le contrat
    AGNOSTIQUE des fournisseurs interchangeables — l'OCR n'existe que chez Mistral."""

    page_markdowns: list[str]          # une entrée par page, ordre du document
    model: str                         # modèle OCR réellement utilisé
    pages_processed: int | None = None  # usage_info.pages_processed si remonté (coût : facturation à la page)


class MistralProvider(OpenAICompatibleProvider):
    """Changer de modèle = éditer default_embedding_model ou ocr_model ici."""

    name = "mistral"
    base_url = "https://api.mistral.ai/v1"
    default_embedding_model = "mistral-embed"  # 1024 dimensions
    api_key = settings.mistral_api_key
    # Capacité OCR — endpoint propriétaire Mistral (PAS le protocole OpenAI), inclus
    # dans le tier Experiment gratuit. Hors du contrat LLMProvider : jamais de
    # fallback sur l'OCR, l'appelant (services/document_ocr) épingle CE fournisseur.
    ocr_model = "mistral-ocr-latest"
    ocr_path = "/ocr"
    ocr_timeout_seconds = 300.0  # très large : un PDF de centaines de pages est long à traiter

    async def ocr(self, document_payload: dict) -> OcrResponse:
        """OCR d'un document, markdown par page.

        `document_payload` : le bloc `document` du protocole OCR Mistral, construit
        par l'appelant — {"type": "document_url", "document_url": "data:application/pdf;base64,…"}
        pour un PDF, {"type": "image_url", "image_url": "data:image/png;base64,…"} pour
        une image. Lève ProviderRequestError en cas d'échec (mécanique _post_json)."""
        request_payload = {"model": self.ocr_model, "document": document_payload}
        response_body = await self._post_json(self.ocr_path, request_payload, self.ocr_timeout_seconds)

        # L'ordre de sortie suit `index`, pas la position dans `pages` (même prudence que embed())
        ordered_pages = sorted(response_body["pages"], key=itemgetter("index"))
        usage_info = response_body.get("usage_info") or {}
        return OcrResponse(
            page_markdowns=[page["markdown"] for page in ordered_pages],
            model=response_body.get("model", self.ocr_model),
            pages_processed=usage_info.get("pages_processed"),
        )
