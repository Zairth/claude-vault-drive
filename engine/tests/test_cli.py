# tests/test_cli.py
"""La porte d'entrée shell (`cli/__main__.py`) — contrat de sortie et aiguillage.

Ce qui est vérifié ici est ce sur quoi un script appelant s'appuie et qu'il ne
peut pas deviner : **stdout est du JSON et rien d'autre**, un échec métier part
sur **stderr avec le code 1**, et chaque sous-commande appelle bien SA brique.

Seule `lexical` est exécutée pour de vrai — c'est la seule des quatre qui ne
demande ni réseau ni clé. Les trois autres sont vérifiées au niveau de
l'aiguillage, là où une erreur de câblage se produirait."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from cli.__main__ import _build_parser, _run_convert, _run_index, _run_lexical, _run_search, main


class CommandDispatchTests(unittest.TestCase):
    """Chaque sous-commande porte sa fonction — la table d'aiguillage EST le parser."""

    def _parsed(self, argv: list[str]):
        return _build_parser().parse_args(argv)

    def test_each_subcommand_is_wired_to_its_brick(self):
        wirings = {
            ("search", "q", "--dir", "A"): _run_search,
            ("lexical", "q", "--dir", "A"): _run_lexical,
            ("index", "--dir", "A"): _run_index,
            ("convert", "doc.pdf"): _run_convert,
        }
        for argv, expected_run in wirings.items():
            with self.subTest(command=argv[0]):
                self.assertIs(self._parsed(list(argv)).run, expected_run)

    def test_the_dir_option_is_repeatable_and_keeps_its_order(self):
        arguments = self._parsed(["lexical", "q", "--dir", "B", "--dir", "A"])
        self.assertEqual(arguments.directories, ["B", "A"])

    def test_the_exclude_callout_option_is_repeatable_and_empty_by_default(self):
        """Le défaut vide est le contrat : sans déclaration, l'indexation ne change pas
        (mêmes hashs, mêmes vecteurs)."""
        self.assertEqual(self._parsed(["index", "--dir", "A"]).excluded_callouts, [])
        arguments = self._parsed(["index", "--dir", "A", "--exclude-callout", "x", "--exclude-callout", "y"])
        self.assertEqual(arguments.excluded_callouts, ["x", "y"])

    def test_top_k_has_a_default_on_both_searches(self):
        for command in ("search", "lexical"):
            with self.subTest(command=command):
                self.assertEqual(self._parsed([command, "q", "--dir", "A"]).top_k, 5)

    def test_an_unknown_command_is_a_usage_error(self):
        with self.assertRaises(SystemExit) as raised, redirect_stderr(io.StringIO()):
            self._parsed(["inconnue"])
        self.assertEqual(raised.exception.code, 2)

    def test_a_search_without_any_directory_is_a_usage_error(self):
        """Le moteur n'a aucun dossier par défaut — l'oubli doit se voir tout de suite."""
        with self.assertRaises(SystemExit) as raised, redirect_stderr(io.StringIO()):
            self._parsed(["lexical", "q"])
        self.assertEqual(raised.exception.code, 2)


class ShellContractTests(unittest.TestCase):
    """Ce qu'un script appelant lit : du JSON sur stdout, l'échec sur stderr."""

    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.corpus_directory = Path(self._temporary_directory.name)
        self.addCleanup(self._temporary_directory.cleanup)
        (self.corpus_directory / "note.md").write_text("la kryptonite", encoding="utf-8")

    def test_stdout_carries_the_json_and_nothing_else(self):
        captured_stdout = io.StringIO()
        with redirect_stdout(captured_stdout):
            main(["lexical", "kryptonite", "--dir", str(self.corpus_directory)])
        grouped_results = json.loads(captured_stdout.getvalue())
        self.assertEqual(grouped_results[0]["directory"], str(self.corpus_directory))
        self.assertEqual(grouped_results[0]["results"][0]["relative_path"], "note.md")

    def test_several_directories_come_back_grouped_in_the_order_asked(self):
        other_directory = self.corpus_directory / "autre"
        other_directory.mkdir()
        (other_directory / "b.md").write_text("kryptonite", encoding="utf-8")
        captured_stdout = io.StringIO()
        with redirect_stdout(captured_stdout):
            main(["lexical", "kryptonite", "--dir", str(other_directory), "--dir", str(self.corpus_directory)])
        grouped_results = json.loads(captured_stdout.getvalue())
        self.assertEqual(
            [group["directory"] for group in grouped_results],
            [str(other_directory), str(self.corpus_directory)],
        )

    def test_a_business_failure_goes_to_stderr_with_exit_code_1(self):
        captured_stdout, captured_stderr = io.StringIO(), io.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
                main(["lexical", "kryptonite", "--dir", str(self.corpus_directory / "absent")])
        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(captured_stdout.getvalue(), "", "stdout doit rester du JSON pur")
        self.assertIn("dossier introuvable", captured_stderr.getvalue())

    def test_the_engine_message_is_relayed_verbatim(self):
        """La porte ne reformule ni ne préfixe : le message porte déjà la raison et
        la marche à suivre, et c'est lui que le script appelant relaiera."""
        captured_stderr = io.StringIO()
        missing_directory = self.corpus_directory / "absent"
        with self.assertRaises(SystemExit), redirect_stderr(captured_stderr):
            main(["lexical", "kryptonite", "--dir", str(missing_directory)])
        self.assertEqual(captured_stderr.getvalue().strip(), f"dossier introuvable : {missing_directory}")


if __name__ == "__main__":
    unittest.main()
