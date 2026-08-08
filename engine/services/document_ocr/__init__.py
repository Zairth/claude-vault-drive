# services/document_ocr/__init__.py
"""Façade publique de la conversion OCR — l'appelant n'importe que d'ici.

    from pathlib import Path
    from services.document_ocr import convert_to_markdown, DocumentOcrError

    report = await convert_to_markdown(Path("facture.pdf"))   # écrit facture.md à côté

Contrat central : le fournisseur OCR est ÉPINGLÉ (mistral — seul à proposer
l'OCR, tier Experiment gratuit) — jamais de fallback. Toute indisponibilité
lève DocumentOcrError explicite. Via le plugin : outil MCP `ocr_convert`.
"""

from services.document_ocr.errors import DocumentOcrError
from services.document_ocr.service import OcrConversionReport, convert_to_markdown

__all__ = [
    "DocumentOcrError",
    "OcrConversionReport",
    "convert_to_markdown",
]
