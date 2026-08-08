# tests/test_chunker.py
"""Non-régression de l'escalier de découpe (`services/semantic_index/chunker.py`).

Le découpage est le seul endroit du moteur où une erreur est INVISIBLE : elle ne
lève rien, elle dégrade silencieusement la pertinence de tout l'index — et un
rebuild coûte des appels API. D'où ce filet.

Les tests lisent les seuils depuis le module (`MAX_CHUNK_CHARS` &co) au lieu de
les recopier : changer la granularité de chunk doit rester une décision qu'on
mesure au banc, pas un test à réécrire."""

import tempfile
import unittest
from pathlib import Path

from services.semantic_index.chunker import (
    MAX_CHUNK_CHARS,
    PREAMBLE_SECTION,
    _WORD_LEVEL_CHUNK_CHARS,
    _WORD_LEVEL_OVERLAP_CHARS,
    chunk_markdown_directory,
    chunk_markdown_text,
)
from services.semantic_index.service import _content_hash

_ANY_PATH = "dossier/fichier.md"
# Un type de callout inventé pour les tests : le moteur n'en connaît AUCUN par avance,
# ils viennent tous de l'appelant — un nom arbitraire le rend visible.
_EXCLUDED_TYPE = "bloc-de-service"


def _unique_words(word_count: int) -> str:
    """Un mur de texte d'un seul tenant, sans deux mots identiques.

    L'unicité rend la reconstruction de test fiable : le plus long recouvrement
    entre deux chunks est alors forcément le chevauchement réel, jamais une
    répétition fortuite du texte."""
    return " ".join(f"mot{word_index:05d}" for word_index in range(word_count))


def _longest_overlap(previous_chunk: str, chunk: str) -> str:
    """Le plus long début de `chunk` qui termine `previous_chunk` — le chevauchement,
    mesuré de l'extérieur (le test ne rejoue pas la logique du chunker)."""
    for overlap_length in range(min(len(previous_chunk), len(chunk)), 0, -1):
        if previous_chunk.endswith(chunk[:overlap_length]):
            return chunk[:overlap_length]
    return ""


class SectionSplittingTests(unittest.TestCase):
    """Le premier découpage : une section par titre ATX."""

    def test_one_chunk_per_heading_section(self):
        chunks = chunk_markdown_text("# Premier\ncorps un\n\n## Second\ncorps deux", _ANY_PATH)
        self.assertEqual([chunk.section for chunk in chunks], ["Premier", "Second"])
        self.assertEqual([chunk.content for chunk in chunks], ["corps un", "corps deux"])

    def test_content_before_the_first_heading_becomes_the_preamble(self):
        chunks = chunk_markdown_text("intro libre\n\n# Titre\ncorps", _ANY_PATH)
        self.assertEqual([chunk.section for chunk in chunks], [PREAMBLE_SECTION, "Titre"])

    def test_a_file_without_any_heading_is_a_single_preamble_section(self):
        chunks = chunk_markdown_text("juste du texte\nsur deux lignes", _ANY_PATH)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].section, PREAMBLE_SECTION)

    def test_empty_sections_are_dropped(self):
        chunks = chunk_markdown_text("# Vide\n\n# Pleine\ncorps", _ANY_PATH)
        self.assertEqual([chunk.section for chunk in chunks], ["Pleine"])

    def test_a_hash_that_is_not_a_heading_stays_content(self):
        """`#tag` et `#!/bin/bash` ne sont pas des titres — les prendre pour tels
        éclaterait un fichier en sections fantômes."""
        chunks = chunk_markdown_text("# Titre\n#tag et #!/bin/bash", _ANY_PATH)
        self.assertEqual([chunk.section for chunk in chunks], ["Titre"])
        self.assertEqual(chunks[0].content, "#tag et #!/bin/bash")

    def test_a_heading_without_title_still_opens_a_section(self):
        chunks = chunk_markdown_text("##\ncorps", _ANY_PATH)
        self.assertEqual([chunk.section for chunk in chunks], ["(titre vide)"])

    def test_the_section_title_is_part_of_the_embedded_text(self):
        """Le titre porte souvent l'intention mieux que le corps — il est vectorisé
        avec lui, et c'est ce texte-là qui est haché (identité du chunk)."""
        chunk = chunk_markdown_text("# Le titre\nle corps", _ANY_PATH)[0]
        self.assertEqual(chunk.embedding_text, "Le titre\nle corps")

    def test_the_relative_path_is_carried_on_every_chunk(self):
        chunks = chunk_markdown_text("# A\ncorps\n\n# B\ncorps", _ANY_PATH)
        self.assertEqual({chunk.relative_path for chunk in chunks}, {_ANY_PATH})


class OversizedSectionTests(unittest.TestCase):
    """L'escalier : paragraphes → lignes → mots → coupe sèche."""

    def test_no_chunk_ever_exceeds_the_limit(self):
        """L'invariant qui compte : quoi qu'on lui donne, aucun chunk géant.

        Le document mélange les quatre crans — paragraphes courts, paragraphe
        massif sans ligne vide, mur de texte sans retour à la ligne, et « mot »
        plus long que le seuil (URL géante, blob base64)."""
        nasty_document = "\n\n".join([
            "# Titre",
            "un paragraphe court",
            "\n".join(f"ligne {line_index} " + "x" * 100 for line_index in range(60)),
            _unique_words(600),
            "x" * (MAX_CHUNK_CHARS * 3),
        ])
        chunks = chunk_markdown_text(nasty_document, _ANY_PATH)
        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.content), MAX_CHUNK_CHARS)

    def test_small_consecutive_paragraphs_stay_in_one_chunk(self):
        """Un cran fin ne doit pas produire une nuée de micro-chunks sans contexte :
        les morceaux consécutifs sont recollés tant qu'ils tiennent."""
        short_paragraphs = "\n\n".join("un paragraphe court" for _ in range(10))
        chunks = chunk_markdown_text(f"# Titre\n{short_paragraphs}", _ANY_PATH)
        self.assertEqual(len(chunks), 1)

    def test_a_long_paragraph_falls_back_to_line_splitting(self):
        """Avant l'escalier, un paragraphe unique trop long restait entier : tout
        ce qui n'a pas de ligne vide produisait un chunk géant."""
        line_count = (MAX_CHUNK_CHARS // 100) * 3
        one_long_paragraph = "\n".join("y" * 99 for _ in range(line_count))
        chunks = chunk_markdown_text(one_long_paragraph, _ANY_PATH)
        self.assertGreater(len(chunks), 1)
        self.assertEqual("\n".join(chunk.content for chunk in chunks), one_long_paragraph)

    def test_a_wall_of_text_falls_back_to_word_splitting_with_overlap(self):
        """Le cran des mots tranche au milieu d'une idée : chaque chunk reprend la
        fin du précédent, sur une frontière de mot."""
        wall_of_text = _unique_words(600)
        chunks = chunk_markdown_text(wall_of_text, _ANY_PATH)
        self.assertGreater(len(chunks), 1)
        for previous_chunk, chunk in zip(chunks, chunks[1:]):
            overlap = _longest_overlap(previous_chunk.content, chunk.content)
            self.assertTrue(overlap, "aucun chevauchement au cran des mots")
            self.assertLessEqual(len(overlap), _WORD_LEVEL_OVERLAP_CHARS)
            self.assertEqual(chunk.content[len(overlap)], " ", "le chevauchement coupe un mot")

    def test_the_word_level_loses_no_content(self):
        """Chevauchement retiré, les chunks recollés rendent le texte d'origine."""
        wall_of_text = _unique_words(600)
        chunks = [chunk.content for chunk in chunk_markdown_text(wall_of_text, _ANY_PATH)]
        rebuilt_pieces = chunks[:1]
        for previous_chunk, chunk in zip(chunks, chunks[1:]):
            rebuilt_pieces.append(chunk[len(_longest_overlap(previous_chunk, chunk)):].lstrip(" "))
        self.assertEqual(" ".join(rebuilt_pieces), wall_of_text)

    def test_a_word_longer_than_the_limit_is_cut_flat_without_overlap(self):
        """Le filet qui ne peut pas échouer. Pas de chevauchement ici : il n'y a
        aucun mot à rappeler, et insérer un espace altérerait le contenu."""
        giant_word = "x" * (_WORD_LEVEL_CHUNK_CHARS * 2 + 300)
        chunks = [chunk.content for chunk in chunk_markdown_text(giant_word, _ANY_PATH)]
        self.assertEqual(
            [len(chunk) for chunk in chunks],
            [_WORD_LEVEL_CHUNK_CHARS, _WORD_LEVEL_CHUNK_CHARS, 300],
        )
        self.assertEqual("".join(chunks), giant_word)

    def test_the_splitting_never_depends_on_headings(self):
        """Un fichier sans aucun titre est une seule section `(préambule)` — que
        l'escalier découpe exactement comme les autres."""
        chunks = chunk_markdown_text(_unique_words(600), _ANY_PATH)
        self.assertGreater(len(chunks), 1)
        self.assertEqual({chunk.section for chunk in chunks}, {PREAMBLE_SECTION})


class ExcludedCalloutTests(unittest.TestCase):
    """Les blocs de callout qu'un appelant déclare non vectorisables.

    LA propriété à ne jamais casser : l'exclusion porte sur le texte VECTORISÉ (donc sur
    le hash, qui en dérive), jamais sur `content` — un résultat de recherche doit
    continuer à montrer le fichier tel qu'il est, sinon l'utilisateur perd l'information
    qu'il vient de trouver."""

    def _chunk(self, markdown_text: str, excluded_callouts=(_EXCLUDED_TYPE,)):
        chunks = chunk_markdown_text(markdown_text, _ANY_PATH, excluded_callouts)
        self.assertEqual(len(chunks), 1, "ce document tient en un seul chunk")
        return chunks[0]

    def test_an_excluded_block_leaves_the_embedded_text_but_stays_in_the_content(self):
        chunk = self._chunk(f"# Titre\nla prose\n\n> [!{_EXCLUDED_TYPE}]\n> ligne de service")
        self.assertNotIn("ligne de service", chunk.embedding_text)
        self.assertIn("la prose", chunk.embedding_text)
        self.assertIn("ligne de service", chunk.content)

    def test_a_block_of_another_type_is_untouched_on_both_sides(self):
        chunk = self._chunk("# Titre\nla prose\n\n> [!note]\n> une remarque utile")
        self.assertIn("une remarque utile", chunk.embedding_text)
        self.assertIn("une remarque utile", chunk.content)

    def test_the_type_comparison_ignores_case(self):
        chunk = self._chunk(
            f"# Titre\nla prose\n\n> [!{_EXCLUDED_TYPE.upper()}]\n> ligne de service",
            excluded_callouts=(_EXCLUDED_TYPE.capitalize(),),
        )
        self.assertNotIn("ligne de service", chunk.embedding_text)

    def test_a_block_at_the_very_end_without_a_trailing_newline_is_excluded(self):
        """Le dernier bloc d'un fichier n'est fermé par aucune ligne suivante — c'est le
        cas où une boucle mal écrite laisse passer le texte."""
        chunk = self._chunk(f"# Titre\nla prose\n\n> [!{_EXCLUDED_TYPE}]\n> dernière ligne")
        self.assertEqual(chunk.embedding_text, "Titre\nla prose")

    def test_two_consecutive_blocks_are_each_judged_on_their_own_type(self):
        """Un bloc collé au précédent doit rouvrir la décision : sans quoi le second
        hérite du sort du premier."""
        chunk = self._chunk(
            f"# Titre\n> [!{_EXCLUDED_TYPE}]\n> ligne de service\n> [!note]\n> une remarque utile"
        )
        self.assertNotIn("ligne de service", chunk.embedding_text)
        self.assertIn("une remarque utile", chunk.embedding_text)

    def test_prose_right_after_a_block_without_a_blank_line_is_kept(self):
        """Le bloc s'arrête à la première ligne qui n'est pas une citation — pas à la
        première ligne vide, qu'il peut ne jamais y avoir."""
        chunk = self._chunk(f"# Titre\n> [!{_EXCLUDED_TYPE}]\n> ligne de service\nla prose")
        self.assertEqual(chunk.embedding_text, "Titre\nla prose")

    def test_a_plain_quote_without_a_type_is_never_excluded(self):
        chunk = self._chunk("# Titre\n> une citation ordinaire\n> sur deux lignes")
        self.assertIn("une citation ordinaire", chunk.embedding_text)

    def test_a_section_reduced_to_an_excluded_block_produces_no_chunk(self):
        """On ne vectorise pas du vide : l'appel API serait payé pour rien."""
        chunks = chunk_markdown_text(
            f"# Titre\n> [!{_EXCLUDED_TYPE}]\n> ligne de service", _ANY_PATH, (_EXCLUDED_TYPE,)
        )
        self.assertEqual(chunks, [])

    def test_without_any_declaration_the_embedded_text_is_unchanged(self):
        """Le défaut est vide, et il ne doit RIEN changer : un appelant qui ne passe pas
        l'option garde ses hashs, donc ses vecteurs, donc son quota."""
        section_body = f"la prose\n\n> [!{_EXCLUDED_TYPE}]\n> ligne de service"
        self.assertEqual(
            [chunk.embedding_text for chunk in chunk_markdown_text(f"# Titre\n{section_body}", _ANY_PATH)],
            [f"Titre\n{section_body}"],
        )

    def test_chunking_the_same_document_twice_keeps_the_same_hashes(self):
        """Le hash EST l'identité d'un chunk : instable, il ferait revectoriser un corpus
        inchangé à chaque construction."""
        document = (
            f"# Titre\nla prose\n\n> [!{_EXCLUDED_TYPE}]\n> ligne de service\n\n"
            f"# Autre\n> [!note]\n> une remarque utile"
        )
        hashes = [
            [_content_hash(chunk) for chunk in chunk_markdown_text(document, _ANY_PATH, [_EXCLUDED_TYPE])]
            for _pass in range(2)
        ]
        self.assertEqual(hashes[0], hashes[1])
        self.assertEqual(len(hashes[0]), 2)


class DirectoryChunkingTests(unittest.TestCase):
    """Ce que le bras vectoriel indexe réellement — via la définition du corpus."""

    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.corpus_directory = Path(self._temporary_directory.name)
        self.addCleanup(self._temporary_directory.cleanup)

    def test_the_front_matter_never_reaches_a_chunk(self):
        """Sans ce retrait, le front matter atterrit dans le `(préambule)` de CHAQUE
        fichier : des clés identiques partout, qui ne discriminent rien et mangent
        les premiers mots de l'aperçu."""
        (self.corpus_directory / "note.md").write_text(
            "---\ntype: entite\ntags: [a, b]\n---\n# Bordeaux\nIncubateur qui héberge des startups.",
            encoding="utf-8",
        )
        chunks = chunk_markdown_directory(self.corpus_directory)
        self.assertEqual([chunk.section for chunk in chunks], ["Bordeaux"])
        self.assertNotIn("type", chunks[0].embedding_text)

    def test_a_file_reduced_to_its_front_matter_produces_no_chunk(self):
        (self.corpus_directory / "note.md").write_text("---\ntype: entite\n---\n", encoding="utf-8")
        self.assertEqual(chunk_markdown_directory(self.corpus_directory), [])


if __name__ == "__main__":
    unittest.main()
