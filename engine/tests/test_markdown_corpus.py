# tests/test_markdown_corpus.py
"""La définition du corpus (`services/markdown_corpus.py`) — énumération et
retrait du front matter.

C'est le seul point où le moteur décide QUEL texte est cherchable. Une erreur ici
se propage identiquement aux deux bras, donc invisiblement : ils resteraient
d'accord entre eux tout en indexant la mauvaise chose."""

import tempfile
import unittest
from pathlib import Path

from services.markdown_corpus import read_markdown_corpus


class MarkdownCorpusTestCase(unittest.TestCase):
    """Écrit un corpus jetable et le relit."""

    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.corpus_directory = Path(self._temporary_directory.name)
        self.addCleanup(self._temporary_directory.cleanup)

    def write_document(self, relative_path: str, text: str) -> None:
        document_path = self.corpus_directory / relative_path
        document_path.parent.mkdir(parents=True, exist_ok=True)
        document_path.write_text(text, encoding="utf-8")

    def read_text_of(self, relative_path: str) -> str:
        documents = {document.relative_path: document.text for document in read_markdown_corpus(self.corpus_directory)}
        return documents[relative_path]


class EnumerationTests(MarkdownCorpusTestCase):
    """Quels fichiers composent le corpus, et dans quel ordre."""

    def test_markdown_files_are_found_recursively_with_posix_paths(self):
        self.write_document("sous/dossier/note.md", "corps")
        documents = read_markdown_corpus(self.corpus_directory)
        self.assertEqual([document.relative_path for document in documents], ["sous/dossier/note.md"])

    def test_non_markdown_files_are_ignored(self):
        self.write_document("note.md", "corps")
        (self.corpus_directory / "note.txt").write_text("corps", encoding="utf-8")
        documents = read_markdown_corpus(self.corpus_directory)
        self.assertEqual([document.relative_path for document in documents], ["note.md"])

    def test_the_order_is_stable(self):
        """Deux constructions à contenu identique doivent produire le même index —
        un diff de synchro cloud ne doit pas bouger sans raison."""
        for relative_path in ("c.md", "a.md", "b.md"):
            self.write_document(relative_path, "corps")
        documents = read_markdown_corpus(self.corpus_directory)
        self.assertEqual([document.relative_path for document in documents], ["a.md", "b.md", "c.md"])


class FrontMatterTests(MarkdownCorpusTestCase):
    """Le front matter YAML n'est pas du contenu cherchable."""

    def test_a_leading_front_matter_block_is_removed(self):
        self.write_document("note.md", "---\ntype: entite\ntags: [a, b]\n---\n# Titre\nle corps")
        self.assertEqual(self.read_text_of("note.md"), "# Titre\nle corps")

    def test_a_file_without_front_matter_is_untouched(self):
        self.write_document("note.md", "# Titre\nle corps")
        self.assertEqual(self.read_text_of("note.md"), "# Titre\nle corps")

    def test_a_horizontal_rule_inside_the_document_is_kept(self):
        """`---` au milieu d'un document est une règle horizontale, pas un délimiteur."""
        self.write_document("note.md", "# Titre\navant\n\n---\n\naprès")
        self.assertEqual(self.read_text_of("note.md"), "# Titre\navant\n\n---\n\naprès")

    def test_a_leading_fence_never_closed_is_kept(self):
        """Un bloc jamais refermé n'est pas un front matter — le texte ressort
        intact plutôt qu'amputé de tout ce qui suit."""
        self.write_document("note.md", "---\n# Titre\nle corps")
        self.assertEqual(self.read_text_of("note.md"), "---\n# Titre\nle corps")

    def test_only_the_first_block_is_removed(self):
        """Le `---` suivant appartient au corps : le retrait s'arrête au premier bloc."""
        self.write_document("note.md", "---\ntype: entite\n---\nle corps\n\n---\n\nla suite")
        self.assertEqual(self.read_text_of("note.md"), "le corps\n\n---\n\nla suite")

    def test_a_file_made_only_of_front_matter_has_no_searchable_text(self):
        self.write_document("note.md", "---\ntype: entite\n---\n")
        self.assertEqual(self.read_text_of("note.md"), "")


if __name__ == "__main__":
    unittest.main()
