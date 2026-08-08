# tests/test_lexical_index.py
"""Le bras lexical BM25 (`services/lexical_index/`) — ce qu'il apporte, prouvé.

Les trois tests qui comptent portent sur les propriétés qu'aucun réglage manuel
ne remplace : IDF, saturation de fréquence, normalisation par la longueur. Le
reste vérifie le contrat d'échec explicite et la forme de la réponse."""

import tempfile
import unittest
from pathlib import Path

from services.lexical_index import LexicalIndexError, search_lexical

_TOP_K = 5


class LexicalCorpusTestCase(unittest.TestCase):
    """Écrit un corpus markdown jetable et le cherche — aucun réseau, aucun index persisté."""

    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.corpus_directory = Path(self._temporary_directory.name)
        self.addCleanup(self._temporary_directory.cleanup)

    def write_document(self, relative_path: str, text: str) -> None:
        document_path = self.corpus_directory / relative_path
        document_path.parent.mkdir(parents=True, exist_ok=True)
        document_path.write_text(text, encoding="utf-8")

    def ranked_paths(self, question: str) -> list[str]:
        grouped_results = search_lexical([self.corpus_directory], question, _TOP_K)
        return [result.relative_path for result in grouped_results[0].results]

    def scores_by_path(self, question: str) -> dict[str, float]:
        grouped_results = search_lexical([self.corpus_directory], question, _TOP_K)
        return {result.relative_path: result.score for result in grouped_results[0].results}


class RankingPropertyTests(LexicalCorpusTestCase):
    """Ce que BM25 apporte et qu'un comptage de mots ne donne pas."""

    def test_a_term_present_almost_everywhere_stops_discriminating(self):
        """L'IDF : « projet » est partout, c'est « kryptonite » qui décide."""
        for document_index in range(5):
            self.write_document(f"banal{document_index}.md", "projet projet projet")
        self.write_document("rare.md", "projet kryptonite")
        self.assertEqual(self.ranked_paths("projet kryptonite")[0], "rare.md")

    def test_repeating_a_term_saturates(self):
        """Répéter dix fois un terme ne rend pas le fichier dix fois plus pertinent.

        Les trois documents ont la MÊME longueur — seule la fréquence du terme
        change — pour que la normalisation par la longueur ne fasse pas le
        travail à la place de la saturation. Le gain doit décroître : passer de
        10 à 100 occurrences rapporte moins que passer de 1 à 10."""
        document_length = 200
        for filler_index in range(5):  # sans eux, le terme serait dans TOUS les documents…
            self.write_document(f"sans-terme{filler_index}.md", "remplissage")  # …et son IDF nul
        for occurrences in (1, 10, 100):
            padded_document = ["kryptonite"] * occurrences + ["remplissage"] * (document_length - occurrences)
            self.write_document(f"tf{occurrences}.md", " ".join(padded_document))
        scores = self.scores_by_path("kryptonite")
        self.assertLess(scores["tf1.md"], scores["tf10.md"])
        self.assertLess(scores["tf10.md"], scores["tf100.md"])
        self.assertLess(
            scores["tf100.md"] - scores["tf10.md"],
            scores["tf10.md"] - scores["tf1.md"],
            "la fréquence de terme ne sature pas",
        )

    def test_a_short_document_is_not_crushed_by_a_long_one(self):
        """La normalisation par la longueur — le défaut poursuivi depuis le premier banc."""
        self.write_document("court.md", "kryptonite")
        self.write_document("long.md", "kryptonite " + "remplissage " * 500)
        self.assertEqual(self.ranked_paths("kryptonite")[0], "court.md")


class TokenizerTests(LexicalCorpusTestCase):
    """Ce que le tokeniseur `unicode61 remove_diacritics 2` couvre nativement."""

    def test_accents_and_case_are_ignored(self):
        self.write_document("accents.md", "Un dossier Élégant")
        self.assertEqual(self.ranked_paths("elegant"), ["accents.md"])

    def test_a_query_word_matches_its_inflected_forms(self):
        """Les requêtes en préfixe couvrent pluriels et conjugaisons."""
        self.write_document("flechi.md", "des chatons partout")
        self.assertEqual(self.ranked_paths("chaton"), ["flechi.md"])

    def test_natural_language_punctuation_is_not_read_as_fts5_syntax(self):
        """Une question est du texte, pas une expression de recherche : guillemets,
        parenthèses et opérateurs n'y ont aucun pouvoir."""
        self.write_document("cible.md", "kryptonite")
        self.assertEqual(self.ranked_paths('"kryptonite" (NOT ceci) - où ?'), ["cible.md"])


class ResponseShapeTests(LexicalCorpusTestCase):
    """La forme rendue : groupée par répertoire, unité fichier, aperçu monoligne."""

    def test_results_stay_grouped_per_directory_in_the_order_asked(self):
        first_directory = self.corpus_directory / "premier"
        second_directory = self.corpus_directory / "second"
        for directory in (first_directory, second_directory):
            directory.mkdir()
            (directory / "note.md").write_text("kryptonite", encoding="utf-8")
        grouped_results = search_lexical([second_directory, first_directory], "kryptonite", _TOP_K)
        self.assertEqual(
            [group.directory for group in grouped_results],
            [str(second_directory), str(first_directory)],
        )
        self.assertEqual([len(group.results) for group in grouped_results], [1, 1])

    def test_the_cited_unit_is_the_file_path_relative_to_the_directory(self):
        self.write_document("sous/dossier/note.md", "kryptonite")
        self.assertEqual(self.ranked_paths("kryptonite"), ["sous/dossier/note.md"])

    def test_the_file_name_itself_is_never_searched(self):
        """Aucune supposition de nomenclature : c'est le contenu qui est cherché."""
        self.write_document("kryptonite.md", "un contenu sans rapport")
        self.write_document("autre.md", "kryptonite")
        self.assertEqual(self.ranked_paths("kryptonite"), ["autre.md"])

    def test_top_k_bounds_the_results(self):
        for document_index in range(10):
            self.write_document(f"note{document_index}.md", "kryptonite")
        grouped_results = search_lexical([self.corpus_directory], "kryptonite", 3)
        self.assertEqual(len(grouped_results[0].results), 3)

    def test_the_front_matter_pollutes_neither_the_excerpt_nor_the_index(self):
        """Les clés du front matter se répètent à l'identique dans tout un dossier :
        elles ne discriminent rien et mangent les premiers mots de l'aperçu."""
        self.write_document(
            "note.md", "---\ntype: entite\n---\n# Bordeaux\nIncubateur qui héberge des startups."
        )
        excerpt = search_lexical([self.corpus_directory], "incubateur", _TOP_K)[0].results[0].excerpt
        self.assertTrue(excerpt.startswith("# Bordeaux"), excerpt)
        self.assertEqual(self.ranked_paths("entite"), [], "le front matter reste cherchable")

    def test_the_excerpt_is_a_single_line_of_the_matched_text(self):
        self.write_document("note.md", "avant\nla kryptonite\naprès")
        excerpt = search_lexical([self.corpus_directory], "kryptonite", _TOP_K)[0].results[0].excerpt
        self.assertIn("kryptonite", excerpt)
        self.assertNotIn("\n", excerpt)

    def test_a_directory_without_any_markdown_yields_no_result_and_stops_nothing(self):
        """Un répertoire vide est un état normal — un corpus jeune en a. Il rend
        zéro résultat, et les autres répertoires de l'appel sont cherchés quand
        même : une couche vide ne doit pas faire échouer toute la recherche."""
        empty_directory = self.corpus_directory / "vide"
        empty_directory.mkdir()
        self.write_document("rempli/note.md", "kryptonite")
        grouped_results = search_lexical(
            [empty_directory, self.corpus_directory / "rempli"], "kryptonite", _TOP_K
        )
        self.assertEqual([len(group.results) for group in grouped_results], [0, 1])

    def test_a_file_without_any_query_word_is_absent(self):
        self.write_document("hors-sujet.md", "rien de commun")
        self.write_document("cible.md", "kryptonite")
        self.assertEqual(self.ranked_paths("kryptonite"), ["cible.md"])

    def test_nothing_is_written_to_the_searched_directory(self):
        """L'index est éphémère : le dossier cherché ressort intact — c'est ce qui
        permet de chercher un répertoire en lecture seule."""
        self.write_document("note.md", "kryptonite")
        self.ranked_paths("kryptonite")
        self.assertEqual([path.name for path in self.corpus_directory.iterdir()], ["note.md"])


class ExplicitFailureTests(LexicalCorpusTestCase):
    """Jamais de résultat vide qui laisserait croire à une recherche aboutie."""

    def test_a_missing_directory_fails_explicitly(self):
        """Un dossier qui n'existe pas est un appel fautif, pas un corpus vide."""
        with self.assertRaises(LexicalIndexError):
            search_lexical([self.corpus_directory / "absent"], "kryptonite", _TOP_K)

    def test_a_question_without_any_searchable_word_fails_explicitly(self):
        self.write_document("note.md", "kryptonite")
        with self.assertRaises(LexicalIndexError):
            search_lexical([self.corpus_directory], "??? !!!", _TOP_K)

    def test_an_empty_directory_list_fails_explicitly(self):
        with self.assertRaises(LexicalIndexError):
            search_lexical([], "kryptonite", _TOP_K)


if __name__ == "__main__":
    unittest.main()
