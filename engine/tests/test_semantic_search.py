# tests/test_semantic_search.py
"""La recherche sémantique multi-répertoires (`services/semantic_index/service.py`).

Aucun réseau : le fournisseur d'embedding est remplacé, et les index sont des
objets en mémoire. Ce qui est vérifié ici n'est pas la qualité du classement (ça,
c'est le banc) mais les deux propriétés structurelles du module : **une seule
vectorisation de la question quel que soit le nombre de répertoires**, et des
classements qui restent **séparés par répertoire**."""

import unittest
from math import sqrt
from pathlib import Path
from unittest.mock import patch

from services.semantic_index import SemanticIndexError, search_indexes
from services.semantic_index.service import _rank_chunks, _require_shared_pinned_contract
from services.semantic_index.store import INDEX_VERSION, IndexMetadata, LoadedIndex, StoredChunk

# La question vectorisée dans tous les tests : le premier axe porte la similarité,
# un chunk de score s se fabrique donc en `[s, sqrt(1 - s²)]`
_QUERY_VECTOR = [1.0, 0.0]
_QUERY_NORM = 1.0


class _FakeEmbeddingResponse:
    """Ce que le fournisseur rendrait — juste assez pour la recherche."""

    def __init__(self, vectors: list[list[float]]):
        self.vectors = vectors


def _index_with(chunk_specifications: list[tuple[str, str, float]], model: str = "mistral-embed") -> LoadedIndex:
    """Un index en mémoire : (chemin du fichier, section, score visé) par chunk."""
    return LoadedIndex(
        metadata=IndexMetadata(provider="mistral", model=model, dimension=2, version=INDEX_VERSION),
        chunks=[
            StoredChunk(
                path=relative_path,
                section=section,
                hash=f"{relative_path}#{section}",
                created_at="2026-01-01T00:00:00+00:00",
                excerpt=f"extrait de {relative_path}",
                vector=[score, sqrt(1.0 - score * score)],
            )
            for relative_path, section, score in chunk_specifications
        ],
    )


class OneEmbeddingPerSearchTests(unittest.IsolatedAsyncioTestCase):
    """Le gain du point : chercher dans cinq répertoires coûte UN appel API."""

    async def asyncSetUp(self):
        self.embedding_calls: list[list[str]] = []

        async def record_embedding(provider, texts, model=None):
            self.embedding_calls.append(texts)
            return _FakeEmbeddingResponse([_QUERY_VECTOR])

        def fake_resolve_embedding_provider(provider_name):
            return None  # jamais appelé : _embed_texts est remplacé lui aussi

        self.enterContext(patch("services.semantic_index.service._embed_texts", record_embedding))
        self.enterContext(
            patch("services.semantic_index.service._resolve_embedding_provider", fake_resolve_embedding_provider)
        )

    def _patch_indexes(self, indexes_by_directory_name: dict[str, LoadedIndex]) -> None:
        def fake_read_index(index_path: Path):
            return indexes_by_directory_name.get(index_path.parent.parent.name)

        self.enterContext(patch("services.semantic_index.service.read_index", fake_read_index))

    async def test_five_directories_cost_a_single_query_embedding(self):
        directory_names = [f"corpus{index}" for index in range(5)]
        self._patch_indexes({name: _index_with([(f"{name}.md", "Titre", 0.9)]) for name in directory_names})
        await search_indexes([Path(name) for name in directory_names], "ma question", top_k=5)
        self.assertEqual(self.embedding_calls, [["ma question"]])

    async def test_results_stay_grouped_per_directory_in_the_order_asked(self):
        self._patch_indexes({
            "premier": _index_with([("a.md", "A", 0.9)]),
            "second": _index_with([("b.md", "B", 0.5)]),
        })
        grouped_results = await search_indexes([Path("second"), Path("premier")], "ma question", top_k=5)
        self.assertEqual([group.directory for group in grouped_results], ["second", "premier"])
        self.assertEqual(
            [result.relative_path for group in grouped_results for result in group.results],
            ["b.md", "a.md"],
        )

    async def test_a_directory_without_index_fails_before_any_api_call(self):
        """Un résultat partiel silencieux laisserait croire qu'on a cherché partout —
        et l'échec doit tomber AVANT de dépenser un appel d'embedding."""
        self._patch_indexes({"construit": _index_with([("a.md", "A", 0.9)])})
        with self.assertRaises(SemanticIndexError):
            await search_indexes([Path("construit"), Path("jamais-construit")], "ma question", top_k=5)
        self.assertEqual(self.embedding_calls, [])

    async def test_an_empty_directory_list_fails_explicitly(self):
        with self.assertRaises(SemanticIndexError):
            await search_indexes([], "ma question", top_k=5)


class SharedPinnedContractTests(unittest.TestCase):
    """Une seule vectorisation ne peut servir qu'un seul modèle épinglé."""

    def test_identical_contracts_give_the_one_to_embed_with(self):
        loaded_indexes = [
            (Path("premier"), _index_with([("a.md", "A", 0.9)])),
            (Path("second"), _index_with([("b.md", "B", 0.5)])),
        ]
        self.assertEqual(_require_shared_pinned_contract(loaded_indexes).model, "mistral-embed")

    def test_divergent_contracts_fail_explicitly(self):
        loaded_indexes = [
            (Path("premier"), _index_with([("a.md", "A", 0.9)])),
            (Path("second"), _index_with([("b.md", "B", 0.5)], model="autre-modele")),
        ]
        with self.assertRaises(SemanticIndexError) as raised:
            _require_shared_pinned_contract(loaded_indexes)
        self.assertIn("autre-modele", str(raised.exception))


class OneResultPerFileTests(unittest.TestCase):
    """Le cran interne du point 3 — ACTIVÉ depuis la baseline, testé dans les deux
    états : il reste réversible d'un caractère si le banc le condamne."""

    def setUp(self):
        # a.md tient les deux meilleurs extraits : sans regroupement il occupe tout le top-2
        self.loaded_index = _index_with([
            ("a.md", "Section 1", 0.90),
            ("a.md", "Section 2", 0.80),
            ("b.md", "Section 1", 0.70),
            ("c.md", "Section 1", 0.60),
        ])

    def _ranked_paths(self, top_k: int) -> list[str]:
        results = _rank_chunks(self.loaded_index, _QUERY_VECTOR, _QUERY_NORM, top_k)
        return [result.relative_path for result in results]

    def test_enabled_by_default_the_top_k_becomes_k_distinct_files(self):
        self.assertEqual(self._ranked_paths(top_k=2), ["a.md", "b.md"])

    def test_each_file_is_represented_by_its_best_excerpt(self):
        results = _rank_chunks(self.loaded_index, _QUERY_VECTOR, _QUERY_NORM, top_k=3)
        self.assertEqual([result.section for result in results], ["Section 1"] * 3)

    def test_the_grouping_happens_before_the_truncation(self):
        """L'ordre des opérations décide du résultat : dédoublonner un top-k déjà
        tronqué rendrait moins de k résultats."""
        self.assertEqual(len(self._ranked_paths(top_k=3)), 3)

    def test_disabled_the_ranking_falls_back_to_chunk_level(self):
        with patch("services.semantic_index.service._ONE_RESULT_PER_FILE", False):
            self.assertEqual(self._ranked_paths(top_k=2), ["a.md", "a.md"])


if __name__ == "__main__":
    unittest.main()
