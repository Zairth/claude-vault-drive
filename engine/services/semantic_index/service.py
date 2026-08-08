# services/semantic_index/service.py
"""Orchestration de l'index sémantique : construction (chunks → vecteurs → JSONL
dans le dossier indexé) et recherche (question → top-k par répertoire, un seul
embedding de la question quel que soit le nombre de répertoires), avec LE contrat
anti-fallback des embeddings.

Pourquoi jamais de fallback : des vecteurs produits par deux modèles différents ne
sont pas comparables — un fallback silencieux renverrait des résultats FAUX. Ici,
le fournisseur et le modèle sont épinglés dans les métadonnées de l'index ; toute
indisponibilité ou incompatibilité lève SemanticIndexError, et c'est l'appelant
qui dégrade vers sa recherche par mots-clés. Même logique côté coût : un contrat
épinglé incompatible ne déclenche JAMAIS une revectorisation silencieuse — erreur
explicite proposant le rebuild complet (supprimer l'index)."""

import hashlib
from collections.abc import Iterable
from datetime import datetime, timezone
from math import sqrt
from operator import attrgetter
from pathlib import Path

from pydantic import BaseModel

from providers.base import OpenAICompatibleProvider
from providers.errors import LLMError, ProviderRequestError
from providers.registry import resolve_embedding_provider
from services.semantic_index.chunker import (
    MAX_CHUNK_CHARS,
    MarkdownChunk,
    chunk_markdown_directory,
    normalized_callout_types,
)
from services.semantic_index.errors import SemanticIndexError
from services.semantic_index.store import (
    INDEX_VERSION,
    IndexMetadata,
    LoadedIndex,
    StoredChunk,
    index_file_path,
    read_index,
    write_index,
)

# Textes par appel /embeddings : réduit le nombre de requêtes (quotas des tiers
# gratuits) tout en restant loin des limites de lot des fournisseurs
_EMBED_BATCH_SIZE = 32
# Longueur de l'extrait stocké et renvoyé par la recherche (aperçu, pas le chunk entier)
_EXCERPT_CHARS = 200
# La marche à suivre ajoutée à CHAQUE échec d'embedding — source unique du message
_NO_FALLBACK_HINT = "pas de fallback (vecteurs incomparables), dégrader vers la recherche par mots-clés (grep)"
# Cran interne « un extrait par fichier » : les chunks d'un même fichier sont regroupés,
# seul le meilleur représente le fichier — le top-k devient un top-k de fichiers DISTINCTS.
# ACTIVÉ depuis la baseline du 2026-08-02 (148 notes, 1 219 chunks, 4 index disjoints), qui
# donne enfin un point de comparaison à l'écart qu'il introduit. Ce cran ne vise PAS le défaut
# relevé au banc — l'attracteur y vient de fichiers distincts au gabarit identique, pas des
# chunks d'un même fichier : il dépense k places sur des fichiers différents, rien de plus.
# Reste un cran, et pas un paramètre : de retour au banc, il se remet à False d'un caractère.
# Interne dans les deux états : jamais exposé à l'appelant.
_ONE_RESULT_PER_FILE = True


class IndexBuildReport(BaseModel):
    """Bilan d'une (re)construction : ce qui a été vectorisé vs réutilisé (coût API)."""

    files: int
    chunks: int
    embedded_chunks: int   # chunks réellement envoyés au fournisseur (nouveaux/modifiés)
    reused_chunks: int     # chunks inchangés — vecteur repris de l'index précédent
    provider_name: str
    model: str
    dimension: int


class SearchResult(BaseModel):
    """Un résultat de recherche : provenance, similarité et aperçu."""

    relative_path: str
    section: str
    score: float           # similarité cosinus ∈ [-1, 1], 1 = identique
    excerpt: str


class DirectorySearchResults(BaseModel):
    """Le classement d'UN répertoire, jamais fusionné avec celui d'un autre.

    Deux répertoires indexés séparément sont deux corpus DISJOINTS : leurs scores
    ne se comparent pas, et un classement unique les mélangeant serait faux. La
    réponse reste donc groupée, dans l'ordre des répertoires demandés."""

    directory: str
    results: list[SearchResult]


async def build_index(
    notes_directory: Path, provider_name: str, excluded_callouts: Iterable[str] = ()
) -> IndexBuildReport:
    """(Re)construit l'index d'un dossier markdown avec le fournisseur épinglé.

    L'index vit DANS le dossier (.index/embeddings.jsonl — il voyage avec lui).
    Incrémental sur le COÛT, par hash de contenu (jamais les mtime) : un chunk au
    texte inchangé garde son vecteur et son created_at sans appel API — une note
    renommée mais inchangée ne coûte rien.

    `excluded_callouts` : les types de bloc de callout que l'appelant ne veut pas
    vectoriser (voir `chunker`). Le hash dérivant du texte vectorisé, ADOPTER ou
    CHANGER cette liste revectorise tout le corpus au passage suivant — en échange
    de quoi modifier ensuite le contenu d'un bloc exclu ne coûte plus aucun appel.
    La liste est inscrite dans les métadonnées : un index dit avec quelle exclusion
    il a été bâti."""
    if not notes_directory.is_dir():
        raise SemanticIndexError(f"dossier introuvable : {notes_directory}")
    markdown_chunks = chunk_markdown_directory(notes_directory, excluded_callouts)
    if not markdown_chunks:
        raise SemanticIndexError(f"aucun fichier .md avec du contenu sous {notes_directory}")

    provider = _resolve_embedding_provider(provider_name)
    embedding_model = provider.resolve_embedding_model()

    index_path = index_file_path(notes_directory)
    previous_index = read_index(index_path)
    reusable_chunks = _read_reusable_chunks(previous_index, provider_name, embedding_model, index_path)

    chunk_hashes = [_content_hash(chunk) for chunk in markdown_chunks]
    pending_indexes = [
        chunk_index for chunk_index, chunk_hash in enumerate(chunk_hashes)
        if chunk_hash not in reusable_chunks
    ]
    embedded_vectors = await _embed_chunks(provider, [markdown_chunks[i] for i in pending_indexes])
    fresh_vectors_by_hash = {
        chunk_hashes[chunk_index]: vector for chunk_index, vector in zip(pending_indexes, embedded_vectors)
    }

    dimension = len(embedded_vectors[0]) if embedded_vectors else previous_index.metadata.dimension
    if previous_index is not None and embedded_vectors and dimension != previous_index.metadata.dimension:
        raise _rebuild_required_error(
            f"dimension renvoyée par {provider_name} ({dimension}) ≠ dimension épinglée "
            f"({previous_index.metadata.dimension})",
            index_path,
        )

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stored_chunks = []
    for chunk, chunk_hash in zip(markdown_chunks, chunk_hashes):
        previous_chunk = reusable_chunks.get(chunk_hash)
        stored_chunks.append(
            StoredChunk(
                path=chunk.relative_path,
                section=chunk.section,
                hash=chunk_hash,
                created_at=previous_chunk.created_at if previous_chunk else created_at,
                excerpt=_build_excerpt(chunk.content),
                vector=previous_chunk.vector if previous_chunk else fresh_vectors_by_hash[chunk_hash],
            )
        )
    metadata = IndexMetadata(
        provider=provider_name,
        model=embedding_model,
        dimension=dimension,
        version=INDEX_VERSION,
        chunk_chars=MAX_CHUNK_CHARS,  # l'index dit à quelle granularité il a été produit
        # ... et avec quelle exclusion — sous la forme normalisée qui a réellement servi
        excluded_callouts=sorted(normalized_callout_types(excluded_callouts)),
    )
    write_index(index_path, metadata, stored_chunks)

    return IndexBuildReport(
        files=len({chunk.relative_path for chunk in markdown_chunks}),
        chunks=len(markdown_chunks),
        embedded_chunks=len(pending_indexes),
        reused_chunks=len(markdown_chunks) - len(pending_indexes),
        provider_name=provider_name,
        model=embedding_model,
        dimension=dimension,
    )


async def search_indexes(
    notes_directories: list[Path], question: str, top_k: int
) -> list[DirectorySearchResults]:
    """Recherche sémantique sur UN OU PLUSIEURS répertoires, en vectorisant la
    question UNE SEULE FOIS.

    L'embedding de la question est le seul coût API d'une recherche : le reste
    n'est que du calcul local sur des vecteurs déjà stockés. Chercher dans cinq
    répertoires coûte donc exactement le même appel réseau que dans un seul —
    c'est toute la raison d'être de cette forme. Les classements restent groupés
    par répertoire (corpus disjoints), et l'appelant se sert de la liste pour
    CIBLER un périmètre : un dossier, ou trois, selon la question."""
    if not notes_directories:
        raise SemanticIndexError("aucun répertoire à chercher — en fournir au moins un")
    loaded_indexes = [(directory, _load_index(directory)) for directory in notes_directories]
    pinned_contract = _require_shared_pinned_contract(loaded_indexes)

    provider = _resolve_embedding_provider(pinned_contract.provider)
    query_response = await _embed_texts(provider, [question], model=pinned_contract.model)
    query_vector = query_response.vectors[0]
    if len(query_vector) != pinned_contract.dimension:
        raise _rebuild_required_error(
            f"dimension de la question ({len(query_vector)}) ≠ dimension des index "
            f"({pinned_contract.dimension})",
            index_file_path(notes_directories[0]),
        )

    query_norm = sqrt(sum(value * value for value in query_vector))
    return [
        DirectorySearchResults(
            directory=str(directory),
            results=_rank_chunks(loaded_index, query_vector, query_norm, top_k),
        )
        for directory, loaded_index in loaded_indexes
    ]


def read_index_metadata(notes_directory: Path) -> IndexMetadata | None:
    """Le contrat épinglé de l'index d'un dossier (commande info) — zéro réseau.

    `chunk_chars` et `excluded_callouts` y compris : c'est ce qui rend comparable-ou-non
    deux index d'un même banc — même grain de découpe, même texte soustrait à la
    vectorisation —, et un appelant peut le vérifier sur tous ses dossiers sans dépenser
    un appel. `chunk_chars` à `None` = index construit avant que le champ existe
    (< 4.5.0) ; `excluded_callouts` vide = aucune exclusion."""
    loaded_index = read_index(index_file_path(notes_directory))
    return None if loaded_index is None else loaded_index.metadata


def _load_index(notes_directory: Path) -> LoadedIndex:
    """L'index d'un répertoire, ou l'échec explicite qui nomme le répertoire fautif.

    Un répertoire jamais indexé fait échouer la recherche ENTIÈRE, y compris quand
    les autres sont prêts : rendre un résultat partiel silencieux laisserait
    croire à l'appelant qu'il a cherché partout."""
    index_path = index_file_path(notes_directory)
    loaded_index = read_index(index_path)
    if loaded_index is None:
        raise SemanticIndexError(
            f"index absent ou illisible ({index_path}) — construire d'abord "
            f"(outil MCP semantic_index_build, ou `python -m cli index --dir`)"
        )
    _require_current_version(loaded_index.metadata, index_path)
    return loaded_index


def _require_shared_pinned_contract(
    loaded_indexes: list[tuple[Path, LoadedIndex]]
) -> IndexMetadata:
    """LE contrat épinglé commun à tous les répertoires cherchés — sinon, échec.

    Une seule vectorisation de la question ne peut servir qu'un seul modèle. Des
    index épinglés sur des modèles différents ne sont donc pas cherchables
    ensemble : les interroger avec le même vecteur rendrait des scores FAUX sur
    tous sauf un. Plutôt que de vectoriser la question une fois par modèle (le
    coût qu'on cherche justement à supprimer), on refuse explicitement — c'est
    l'appelant qui regroupe ses répertoires ou reconstruit l'intrus.

    `chunk_chars` et `excluded_callouts` n'entrent PAS dans ce refus, délibérément :
    un grain de découpe ou une exclusion de blocs différents rendent des scores justes
    (même modèle, même espace vectoriel), seulement établis sur un texte inégal.
    Refuser bloquerait la recherche pendant toute reconstruction partielle d'un corpus,
    pour un défaut d'hygiène qui se constate (`semantic_info`) et se corrige par un
    build. Une erreur se lève quand le résultat serait FAUX, pas quand il est imparfait."""
    reference_directory, reference_index = loaded_indexes[0]
    reference_contract = reference_index.metadata
    for directory, loaded_index in loaded_indexes[1:]:
        contract = loaded_index.metadata
        if (contract.provider, contract.model, contract.dimension) != (
            reference_contract.provider, reference_contract.model, reference_contract.dimension
        ):
            raise SemanticIndexError(
                f"contrats épinglés différents entre les répertoires cherchés : {reference_directory} "
                f"utilise {reference_contract.provider}/{reference_contract.model} "
                f"({reference_contract.dimension}d) et {directory} utilise "
                f"{contract.provider}/{contract.model} ({contract.dimension}d) — les chercher ensemble "
                f"exigerait une vectorisation de la question par modèle ; les chercher séparément, "
                f"ou reconstruire l'index divergent"
            )
    return reference_contract


def _rank_chunks(
    loaded_index: LoadedIndex, query_vector: list[float], query_norm: float, top_k: int
) -> list[SearchResult]:
    """Le classement d'UN index : similarité cosinus de tous ses chunks, top-k."""
    search_results = [
        SearchResult(
            relative_path=chunk.path,
            section=chunk.section,
            score=round(_cosine_similarity(query_vector, query_norm, chunk.vector), 4),
            excerpt=chunk.excerpt,
        )
        for chunk in loaded_index.chunks
    ]
    search_results.sort(key=attrgetter("score"), reverse=True)
    if _ONE_RESULT_PER_FILE:
        search_results = _keep_best_chunk_per_file(search_results)
    return search_results[:top_k]


def _keep_best_chunk_per_file(sorted_results: list[SearchResult]) -> list[SearchResult]:
    """Un seul extrait par fichier : le mieux classé, l'ordre des scores conservé.

    L'ORDRE DES OPÉRATIONS fait tout : regrouper d'abord, tronquer à k ENSUITE.
    Dédoublonner un top-k déjà tronqué rendrait moins de k résultats. Le
    regroupement porte ici sur la liste ENTIÈRE plutôt que sur un « top-n large »
    intermédiaire : l'index est déjà chargé et trié en mémoire, donc élargir ne
    coûte rien et garantit k fichiers distincts dès que le corpus en contient k —
    aucun seuil arbitraire à régler."""
    best_result_per_path: dict[str, SearchResult] = {}
    for result in sorted_results:
        best_result_per_path.setdefault(result.relative_path, result)  # 1er vu = mieux classé
    return list(best_result_per_path.values())


def _read_reusable_chunks(
    previous_index: LoadedIndex | None, provider_name: str, embedding_model: str, index_path: Path
) -> dict[str, StoredChunk]:
    """Les chunks de l'index précédent, réutilisables SEULEMENT si le contrat épinglé
    est identique. Contrat différent → JAMAIS de revectorisation silencieuse (coût
    API) : erreur explicite, c'est l'humain qui décide du rebuild complet."""
    if previous_index is None:
        return {}
    metadata = previous_index.metadata
    _require_current_version(metadata, index_path)
    if (metadata.provider, metadata.model) != (provider_name, embedding_model):
        raise _rebuild_required_error(
            f"modèle épinglé {metadata.provider}/{metadata.model} ≠ configuration courante "
            f"{provider_name}/{embedding_model}",
            index_path,
        )
    return previous_index.chunks_by_hash()


def _require_current_version(metadata: IndexMetadata, index_path: Path) -> None:
    """Refuse un index écrit dans un autre format de fichier que le format courant."""
    if metadata.version != INDEX_VERSION:
        raise _rebuild_required_error(
            f"version d'index {metadata.version} ≠ version courante {INDEX_VERSION}", index_path
        )


def _rebuild_required_error(reason: str, index_path: Path) -> SemanticIndexError:
    """L'erreur « contrat épinglé incompatible » : la marche à suivre est LE rebuild
    complet, décidé explicitement par l'humain (coût API) — jamais automatique."""
    return SemanticIndexError(f"{reason} — rebuild complet requis : supprimer {index_path} puis relancer index")


def _resolve_embedding_provider(provider_name: str) -> OpenAICompatibleProvider:
    """LE fournisseur épinglé (résolution partagée : providers/registry.py),
    avec l'échec traduit dans le vocabulaire du module — le non-fallback se joue là-bas."""
    try:
        return resolve_embedding_provider(provider_name)
    except LLMError as resolution_error:
        raise SemanticIndexError(f"{resolution_error} — {_NO_FALLBACK_HINT}") from resolution_error


async def _embed_texts(provider: OpenAICompatibleProvider, texts: list[str], model: str | None = None):
    """provider.embed avec l'échec réseau/API traduit dans le vocabulaire du module."""
    try:
        return await provider.embed(texts, model=model)
    except ProviderRequestError as request_error:
        raise SemanticIndexError(
            f"échec du fournisseur d'embedding épinglé : {request_error} — {_NO_FALLBACK_HINT}"
        ) from request_error


async def _embed_chunks(provider: OpenAICompatibleProvider, chunks: list[MarkdownChunk]) -> list[list[float]]:
    """Vectorise les chunks par lots, dans l'ordre — un vecteur par chunk."""
    chunk_vectors: list[list[float]] = []
    for batch_start in range(0, len(chunks), _EMBED_BATCH_SIZE):
        batch = chunks[batch_start:batch_start + _EMBED_BATCH_SIZE]
        batch_response = await _embed_texts(provider, [chunk.embedding_text for chunk in batch])
        chunk_vectors.extend(batch_response.vectors)
    return chunk_vectors


def _content_hash(chunk: MarkdownChunk) -> str:
    """Empreinte du texte vectorisé — l'identité d'un chunk pour la réindexation."""
    return hashlib.sha256(chunk.embedding_text.encode("utf-8")).hexdigest()


def _cosine_similarity(query_vector: list[float], query_norm: float, candidate_vector: list[float]) -> float:
    """Similarité cosinus, norme de la question précalculée (une fois pour tout l'index)."""
    dot_product = sum(query_value * candidate_value
                      for query_value, candidate_value in zip(query_vector, candidate_vector))
    candidate_norm = sqrt(sum(value * value for value in candidate_vector))
    if query_norm == 0.0 or candidate_norm == 0.0:
        return 0.0
    return dot_product / (query_norm * candidate_norm)


def _build_excerpt(chunk_content: str) -> str:
    """Aperçu monoligne du chunk, stocké à l'indexation (les sub-agents relisent le
    fichier pour le contexte complet)."""
    flattened_content = " ".join(chunk_content.split())
    if len(flattened_content) <= _EXCERPT_CHARS:
        return flattened_content
    return flattened_content[:_EXCERPT_CHARS].rsplit(" ", 1)[0] + "…"
