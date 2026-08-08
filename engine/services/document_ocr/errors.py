# services/document_ocr/errors.py
"""Exception du module document_ocr.

Une seule classe : ce module échoue toujours EXPLICITEMENT (fichier introuvable,
format non supporté, Mistral indisponible...) — jamais de fallback, l'OCR n'existe
que chez UN fournisseur de la chaîne. L'appelant attrape DocumentOcrError et
décide lui-même de la suite (réessayer plus tard, saisir le texte à la main...)."""


class DocumentOcrError(Exception):
    """Échec explicite de la conversion OCR — le message porte la raison humaine."""
