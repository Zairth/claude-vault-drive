# services/semantic_index/store.py
"""Persistance JSONL d'un index sémantique, adressé par contenu.

L'index vit DANS le dossier indexé (<dossier>/.index/embeddings.jsonl) : il voyage
avec lui (synchro cloud comprise), aucun fichier ailleurs sur la machine. Ligne 1 =
les métadonnées épinglées (fournisseur, modèle, dimension, version de format,
granularité de découpe, blocs exclus de la vectorisation) ;
puis une ligne JSON par chunk. Le store parle vecteurs (list[float]) — l'encodage
`vector_b64` (float32 little-endian → base64, endianness fixée car l'index voyage
entre machines) est un détail interne à ce module."""

import base64
import json
import struct
from pathlib import Path

from pydantic import BaseModel, ValidationError


# Version du format de fichier — à incrémenter si la structure des lignes change
INDEX_VERSION = 1
# Emplacement de l'index, relatif au dossier indexé — source unique de la convention
_INDEX_RELATIVE_PATH = Path(".index") / "embeddings.jsonl"


class IndexMetadata(BaseModel):
    """Le contrat épinglé (ligne 1 du fichier) : QUI a vectorisé, avec QUOI, en quelle
    dimension — à quelle granularité de découpe, et en excluant quels blocs."""

    provider: str
    model: str
    dimension: int
    version: int
    # Seuil de découpe (MAX_CHUNK_CHARS) en vigueur lors de la construction. Deux index
    # bâtis à des granularités différentes restent cherchables ensemble — leurs vecteurs
    # viennent du même modèle, donc leurs scores sont comparables ; mais ils ne décrivent
    # pas le même grain, ce qui fausse toute comparaison de pertinence entre les deux.
    # Inscrit ici pour que ce soit CONSTATABLE (semantic_info) plutôt que tenu de tête.
    # Optionnel : un index bâti avant la 4.5.0 ne le porte pas — None = granularité
    # inconnue, et il DOIT rester lisible (le refuser le ferait passer pour « jamais
    # construit », donc revectoriser tout un corpus pour un champ manquant).
    chunk_chars: int | None = None
    # Types de bloc de callout que l'appelant a exclus de la vectorisation (normalisés,
    # triés). Inscrit ici pour la même raison que `chunk_chars` : deux index d'un même
    # corpus bâtis avec des exclusions différentes n'ont pas vectorisé le même texte, et
    # ça doit être CONSTATABLE (semantic_info) plutôt que tenu de tête. Liste vide plutôt
    # qu'optionnel, contrairement à `chunk_chars` : un index bâti avant que le champ
    # existe n'avait aucune exclusion — « vide » n'est pas une inconnue ici, c'est un fait.
    excluded_callouts: list[str] = []


class StoredChunk(BaseModel):
    """Une ligne chunk du fichier, vecteur désérialisé (l'encodage reste interne au store)."""

    path: str        # chemin du fichier relatif au dossier indexé
    section: str     # titre de la section d'origine
    hash: str        # SHA-256 du texte vectorisé — l'identité du chunk (jamais les mtime)
    created_at: str  # ISO 8601 UTC de la vectorisation d'origine (conservé à la réutilisation)
    excerpt: str     # aperçu monoligne, renvoyé tel quel par la recherche
    vector: list[float]


class LoadedIndex(BaseModel):
    """Un index entier relu en mémoire — la recherche travaille directement dessus."""

    metadata: IndexMetadata
    chunks: list[StoredChunk]

    def chunks_by_hash(self) -> dict[str, StoredChunk]:
        """hash → chunk : la base de la réindexation incrémentale (un texte inchangé
        garde son vecteur et son created_at — zéro appel API, zéro quota)."""
        return {chunk.hash: chunk for chunk in self.chunks}


def index_file_path(indexed_directory: Path) -> Path:
    """LE chemin de l'index d'un dossier — les appelants ne connaissent que le dossier."""
    return indexed_directory / _INDEX_RELATIVE_PATH


def read_index(index_path: Path) -> LoadedIndex | None:
    """Relit l'index entier — None si absent ou illisible (= jamais construit :
    le build suivant revectorise tout, visible dans son rapport)."""
    if not index_path.is_file():
        return None
    try:
        first_line, *chunk_lines = index_path.read_text(encoding="utf-8").splitlines()
        metadata = IndexMetadata(**json.loads(first_line))
        chunks = [_line_to_chunk(line) for line in chunk_lines if line.strip()]
    except (json.JSONDecodeError, ValidationError, KeyError, ValueError, TypeError):
        return None
    return LoadedIndex(metadata=metadata, chunks=chunks)


def write_index(index_path: Path, metadata: IndexMetadata, chunks: list[StoredChunk]) -> None:
    """Réécrit l'index entier, atomiquement (fichier temporaire puis rename) : une
    interruption ne laisse jamais un index tronqué. Remplacement total plutôt que
    diff : l'incrémental se joue en AMONT (chunks_by_hash) sur les appels API —
    réécrire quelques milliers de lignes JSONL est instantané et sans chunk orphelin."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_lines = [json.dumps(metadata.model_dump(), ensure_ascii=False)]
    index_lines.extend(_chunk_to_line(chunk) for chunk in chunks)
    temporary_path = index_path.with_suffix(".jsonl.tmp")
    temporary_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    temporary_path.replace(index_path)


def _chunk_to_line(chunk: StoredChunk) -> str:
    """StoredChunk → ligne JSONL : le vecteur part en vector_b64, le reste tel quel
    (le modèle pydantic EST le schéma de la ligne — pas de liste de clés parallèle)."""
    payload = chunk.model_dump(exclude={"vector"}) | {"vector_b64": _vector_to_b64(chunk.vector)}
    return json.dumps(payload, ensure_ascii=False)


def _line_to_chunk(line: str) -> StoredChunk:
    """Ligne JSONL → StoredChunk (opération inverse de _chunk_to_line)."""
    record = json.loads(line)
    vector = _b64_to_vector(record.pop("vector_b64"))
    return StoredChunk(**record, vector=vector)


def _vector_to_b64(vector: list[float]) -> str:
    """list[float] → float32 little-endian (4 octets par dimension) encodés base64."""
    return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode("ascii")


def _b64_to_vector(vector_b64: str) -> list[float]:
    """Opération inverse de _vector_to_b64."""
    raw_bytes = base64.b64decode(vector_b64)
    return list(struct.unpack(f"<{len(raw_bytes) // 4}f", raw_bytes))
