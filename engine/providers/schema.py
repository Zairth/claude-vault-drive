# providers/schema.py
"""Types agnostiques échangés entre l'appelant et les fournisseurs.

L'appelant ne manipule QUE ces types : c'est ce contrat qui rend les
fournisseurs interchangeables."""

from pydantic import BaseModel


class EmbeddingResponse(BaseModel):
    """Vecteurs d'embedding normalisés (endpoint /embeddings du protocole OpenAI).

    PAS de fallback possible : des vecteurs issus de deux modèles différents ne
    sont pas comparables — l'appelant choisit UN fournisseur et UN modèle, et
    échoue explicitement s'ils sont indisponibles.
    Pas de champ `raw` : les vecteurs (déjà extraits) constituent l'essentiel de la
    réponse brute — la conserver doublerait la mémoire pour rien."""

    vectors: list[list[float]]         # un vecteur par texte d'entrée, dans le même ordre
    provider_name: str                 # fournisseur ayant produit les vecteurs
    model: str                         # modèle d'embedding réellement utilisé
    input_tokens: int | None = None    # usage.prompt_tokens si le fournisseur le remonte

    @property
    def dimension(self) -> int:
        """Dimension des vecteurs — LA propriété à épingler avec le modèle dans les
        métadonnées d'un index : deux dimensions différentes = modèles incompatibles."""
        return len(self.vectors[0]) if self.vectors else 0
