# tests/test_store.py
"""Non-régression du fichier d'index (`services/semantic_index/store.py`).

Un seul comportement est couvert ici, mais il coûte cher quand il casse : un index
que le store juge ILLISIBLE est traité comme jamais construit, donc revectorisé en
entier — des appels API dépensés pour une métadonnée. C'est le risque qu'ouvre tout
champ ajouté à `IndexMetadata`, d'où ce filet au moment où `chunk_chars` arrive."""

import json
import tempfile
import unittest
from pathlib import Path

from services.semantic_index.store import (
    IndexMetadata,
    StoredChunk,
    index_file_path,
    read_index,
    write_index,
)

_A_CHUNK = StoredChunk(
    path="note.md",
    section="Titre",
    hash="abc",
    created_at="2026-08-02T10:00:00+00:00",
    excerpt="un aperçu",
    vector=[0.5, -0.25],
)


class MetadataRoundTripTests(unittest.TestCase):
    """Ce que l'index dit de lui-même survit à l'aller-retour disque."""

    def setUp(self):
        self.index_path = index_file_path(Path(self.enterContext(tempfile.TemporaryDirectory())))

    def test_the_chunking_granularity_survives_the_round_trip(self):
        metadata = IndexMetadata(
            provider="mistral", model="mistral-embed", dimension=2, version=1, chunk_chars=800
        )
        write_index(self.index_path, metadata, [_A_CHUNK])
        self.assertEqual(read_index(self.index_path).metadata.chunk_chars, 800)

    def test_an_index_without_the_field_stays_readable(self):
        """Un index d'avant le champ ne doit PAS passer pour « jamais construit » :
        le refuser revectoriserait tout un corpus pour une métadonnée manquante."""
        legacy_metadata = {"provider": "mistral", "model": "mistral-embed", "dimension": 2, "version": 1}
        write_index(self.index_path, IndexMetadata(**legacy_metadata, chunk_chars=800), [_A_CHUNK])
        index_lines = self.index_path.read_text(encoding="utf-8").splitlines()
        index_lines[0] = json.dumps(legacy_metadata)  # la ligne 1 telle qu'écrite avant le champ
        self.index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

        loaded_index = read_index(self.index_path)
        self.assertIsNotNone(loaded_index)
        self.assertIsNone(loaded_index.metadata.chunk_chars)  # granularité inconnue, pas index invalide
        self.assertEqual(len(loaded_index.chunks), 1)


if __name__ == "__main__":
    unittest.main()
