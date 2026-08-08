# services/document_ocr/service.py
"""Conversion de documents (PDF, images scannées) en markdown via l'OCR Mistral.

Pourquoi jamais de fallback : l'OCR n'existe pas dans le protocole OpenAI et un
seul fournisseur le propose (Mistral, endpoint /ocr propriétaire,
inclus dans le tier Experiment gratuit). Le fournisseur est donc ÉPINGLÉ — même
philosophie que les embeddings : indisponibilité → DocumentOcrError explicite,
jamais de fallback silencieux. Le document part en data URI base64 (aucun upload
préalable, aucun fichier stocké chez Mistral) ; le markdown est écrit à côté de
la source par défaut — prêt à être indexé par services/semantic_index."""

import base64
import re
from pathlib import Path

from pydantic import BaseModel

from services.document_ocr.errors import DocumentOcrError
from providers.errors import ProviderRequestError
from providers.hosted.mistral.provider import MistralProvider

# Extensions acceptées → type MIME du data URI. Deux familles car le protocole OCR
# Mistral les distingue : les documents partent en bloc document_url, les images en image_url.
_DOCUMENT_MIME_TYPES = {".pdf": "application/pdf"}
_IMAGE_MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".avif": "image/avif"}
# Limite documentée de l'API OCR Mistral — vérifiée localement AVANT tout appel réseau
_MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
# La marche à suivre ajoutée à CHAQUE échec — source unique du message
_NO_FALLBACK_HINT = "pas de fallback (mistral est le seul fournisseur OCR de la chaîne)"
# L'OCR référence les figures du document (`![img-0.jpeg](img-0.jpeg)`) alors qu'aucune
# sous-image n'est écrite sur disque : ces cibles n'existent nulle part. Le markdown
# finissant dans un vault Obsidian, qui indexe tout, chaque référence morte y devient un
# nœud fantôme du graphe — et un clic dessus CRÉE une note vide. On ne laisse donc jamais
# sortir de syntaxe d'image : marqueur textuel inerte, qui garde l'information « il y
# avait une figure ici » sans lien pendant.
_IMAGE_REFERENCE_PATTERN = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_FIGURE_MARKER = "[figure {number} — non extraite]"


class OcrConversionReport(BaseModel):
    """Bilan d'une conversion : provenance, destination et volume traité."""

    source_path: str
    output_path: str
    pages: int                 # pages de markdown écrites (= coût API : l'OCR se facture à la page)
    model: str                 # modèle OCR réellement utilisé


async def convert_to_markdown(document_path: Path, output_path: Path | None = None) -> OcrConversionReport:
    """Convertit un document en UN fichier markdown (pages concaténées, ordre du document).

    `output_path` : destination explicite ; None = `<document>.md` à côté de la
    source. La sortie est ÉCRASÉE si elle existe — relancer = régénérer (la source
    fait foi, le markdown n'est qu'une projection)."""
    if not document_path.is_file():
        raise DocumentOcrError(f"fichier introuvable : {document_path}")
    document_bytes = document_path.read_bytes()
    if len(document_bytes) > _MAX_DOCUMENT_BYTES:
        raise DocumentOcrError(
            f"fichier trop volumineux ({len(document_bytes) / 1024 / 1024:.1f} Mo) — "
            f"limite de l'API OCR Mistral : {_MAX_DOCUMENT_BYTES // (1024 * 1024)} Mo"
        )
    document_payload = _build_document_payload(document_path, document_bytes)

    provider = MistralProvider()
    configuration_issue = provider.configuration_issue()
    if configuration_issue is not None:
        raise DocumentOcrError(
            f"fournisseur {provider.name} indisponible : {configuration_issue} — {_NO_FALLBACK_HINT}"
        )

    try:
        ocr_response = await provider.ocr(document_payload)
    except ProviderRequestError as request_error:
        raise DocumentOcrError(f"échec de l'appel OCR : {request_error} — {_NO_FALLBACK_HINT}") from request_error

    markdown_output = _replace_image_references("\n\n".join(ocr_response.page_markdowns).strip()) + "\n"
    resolved_output_path = output_path if output_path is not None else document_path.with_suffix(".md")
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(markdown_output, encoding="utf-8")

    return OcrConversionReport(
        source_path=str(document_path),
        output_path=str(resolved_output_path),
        pages=len(ocr_response.page_markdowns),
        model=ocr_response.model,
    )


def _replace_image_references(markdown_text: str) -> str:
    """Remplace chaque `![...](...)` par un marqueur numéroté (1, 2, … dans l'ordre du
    document) — le motif n'ayant aucun groupe capturant, `split` ne renvoie que le texte
    entre les références."""
    text_segments = _IMAGE_REFERENCE_PATTERN.split(markdown_text)
    cleaned_text = text_segments[0]
    for figure_number, following_segment in enumerate(text_segments[1:], start=1):
        cleaned_text += _FIGURE_MARKER.format(number=figure_number) + following_segment
    return cleaned_text


def _build_document_payload(document_path: Path, document_bytes: bytes) -> dict:
    """Le bloc `document` du protocole OCR Mistral : data URI base64, typé selon
    l'extension (document_url pour un PDF, image_url pour une image)."""
    file_suffix = document_path.suffix.lower()
    encoded_content = base64.b64encode(document_bytes).decode("ascii")
    if file_suffix in _DOCUMENT_MIME_TYPES:
        return {
            "type": "document_url",
            "document_url": f"data:{_DOCUMENT_MIME_TYPES[file_suffix]};base64,{encoded_content}",
        }
    if file_suffix in _IMAGE_MIME_TYPES:
        return {
            "type": "image_url",
            "image_url": f"data:{_IMAGE_MIME_TYPES[file_suffix]};base64,{encoded_content}",
        }
    supported_extensions = ", ".join(sorted(_DOCUMENT_MIME_TYPES | _IMAGE_MIME_TYPES))
    raise DocumentOcrError(
        f"extension non supportée : {file_suffix or '(aucune)'} — formats acceptés : {supported_extensions}"
    )
