# cli/__main__.py
"""La porte d'entrée SHELL du moteur — pour les appelants qui ne peuvent pas être
clients MCP.

    python -m cli search "ma question" --dir A --dir B [--top-k 5]
    python -m cli lexical "ma question" --dir A --dir B [--top-k 5]
    python -m cli index --dir A [--exclude-callout TYPE ...]
    python -m cli convert document.pdf [--out sortie.md]

Pourquoi elle existe à côté de `mcp_server/` : un hook Claude Code est un script
shell. Il n'a pas de session, pas de client MCP, pas de boucle d'agent — juste un
processus qui lit stdin et écrit stdout. Cette catégorie d'appelants ne peut
structurellement pas passer par MCP.

Le contrat shell, identique pour les quatre commandes :

- **stdout = JSON**, et rien d'autre (mêmes structures que les outils MCP — une
  seule forme de réponse pour les deux portes) ;
- **échec métier = message sur stderr + code de sortie 1** ; usage invalide = 2
  (argparse). Le message porte déjà la raison humaine et la marche à suivre :
  la porte ne les reformule pas.

`lexical` est la commande pensée pour un hook déclenché à chaque prompt : elle ne
coûte aucun appel API, ne demande aucune clé, aucun index préalable, et rend la
main en quelques dizaines de millisecondes.

**Chaque commande importe SA brique dans son corps, pas en tête de module** —
c'est délibéré et mesuré : tout importer coûte 280 ms au démarrage (pydantic,
httpx, les fournisseurs), n'importer que le bras lexical en coûte 170. Sur une
porte MCP lancée une fois par session ce serait du zèle ; sur un hook qui se
déclenche à chaque prompt, ces 110 ms sont un poste de dépense permanent."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import NoReturn

_DEFAULT_TOP_K = 5


def main(argv: list[str] | None = None) -> None:
    """Analyse la ligne de commande, exécute LA commande, écrit son JSON."""
    arguments = _build_parser().parse_args(argv)
    print(json.dumps(arguments.run(arguments), indent=2, ensure_ascii=False))


def _run_search(arguments: argparse.Namespace) -> list[dict]:
    """Recherche sémantique : une seule vectorisation de la question, N index."""
    from services.semantic_index import SemanticIndexError, search_indexes

    try:
        grouped_results = asyncio.run(
            search_indexes(_directory_paths(arguments), arguments.question, arguments.top_k)
        )
    except SemanticIndexError as search_failure:
        _fail(search_failure)
    return [group.model_dump() for group in grouped_results]


def _run_lexical(arguments: argparse.Namespace) -> list[dict]:
    """Recherche lexicale BM25 : zéro réseau, zéro clé, zéro index préalable."""
    from services.lexical_index import LexicalIndexError, search_lexical

    try:
        grouped_results = search_lexical(_directory_paths(arguments), arguments.question, arguments.top_k)
    except LexicalIndexError as search_failure:
        _fail(search_failure)
    return [group.model_dump() for group in grouped_results]


def _run_index(arguments: argparse.Namespace) -> dict:
    """(Re)construction de l'index sémantique d'UN dossier — un index par dossier."""
    from providers import PINNED_PROVIDER
    from services.semantic_index import SemanticIndexError, build_index

    try:
        report = asyncio.run(
            build_index(Path(arguments.directory), PINNED_PROVIDER, arguments.excluded_callouts)
        )
    except SemanticIndexError as build_failure:
        _fail(build_failure)
    return report.model_dump()


def _run_convert(arguments: argparse.Namespace) -> dict:
    """Conversion OCR d'un document en markdown."""
    from services.document_ocr import DocumentOcrError, convert_to_markdown

    output_path = Path(arguments.out) if arguments.out else None
    try:
        report = asyncio.run(convert_to_markdown(Path(arguments.document), output_path))
    except DocumentOcrError as conversion_failure:
        _fail(conversion_failure)
    return report.model_dump()


def _build_parser() -> argparse.ArgumentParser:
    """Les quatre commandes. Chacune porte SA fonction (`run`) : pas de chaîne de
    `if` à tenir en parallèle de la liste des sous-commandes."""
    parser = argparse.ArgumentParser(
        prog="python -m cli",
        description="Moteur sémantique/lexical/OCR en ligne de commande — sortie JSON sur stdout.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    search_command = subcommands.add_parser(
        "search", help="Recherche sémantique (embeddings) — coûte UN appel API, quel que soit le nombre de dossiers"
    )
    _add_question_arguments(search_command)
    search_command.set_defaults(run=_run_search)

    lexical_command = subcommands.add_parser(
        "lexical", help="Recherche lexicale BM25 — zéro réseau, zéro clé, aucun index préalable"
    )
    _add_question_arguments(lexical_command)
    lexical_command.set_defaults(run=_run_lexical)

    index_command = subcommands.add_parser("index", help="(Re)construit l'index sémantique d'un dossier")
    index_command.add_argument(
        "--dir", dest="directory", required=True, metavar="CHEMIN",
        help="Dossier à indexer — un seul : l'index vit DANS le dossier qu'il décrit",
    )
    index_command.add_argument(
        "--exclude-callout", action="append", dest="excluded_callouts", default=[], metavar="TYPE",
        help="Type de bloc de callout (`> [!TYPE]`) à ne PAS vectoriser — RÉPÉTABLE, "
             "insensible à la casse. Le bloc reste entier dans les résultats de recherche ; "
             "seul le vecteur (donc le hash) l'ignore",
    )
    index_command.set_defaults(run=_run_index)

    convert_command = subcommands.add_parser("convert", help="Document (.pdf, .png, .jpg, .jpeg, .avif) → markdown par OCR")
    convert_command.add_argument("document", help="Fichier à convertir")
    convert_command.add_argument(
        "--out", default=None, metavar="CHEMIN",
        help="Destination du markdown (défaut : <document>.md à côté de la source, écrasé s'il existe)",
    )
    convert_command.set_defaults(run=_run_convert)
    return parser


def _add_question_arguments(command_parser: argparse.ArgumentParser) -> None:
    """Les arguments communs aux deux recherches — une seule forme d'appel à retenir."""
    command_parser.add_argument("question")
    command_parser.add_argument(
        "--dir", action="append", dest="directories", required=True, metavar="CHEMIN",
        help="Dossier à chercher — RÉPÉTABLE : les résultats reviennent groupés par dossier",
    )
    command_parser.add_argument(
        "--top-k", type=int, default=_DEFAULT_TOP_K, dest="top_k",
        help=f"Nombre de résultats par dossier (défaut : {_DEFAULT_TOP_K})",
    )


def _directory_paths(arguments: argparse.Namespace) -> list[Path]:
    """Les `--dir` répétés, dans l'ordre donné — c'est celui des groupes de résultats."""
    return [Path(directory) for directory in arguments.directories]


def _fail(engine_failure: Exception) -> NoReturn:
    """Échec métier : le message du moteur sur stderr, code de sortie 1.

    Le message n'est jamais reformulé ni préfixé — il porte déjà la raison et la
    marche à suivre, et c'est ce que le script appelant relaiera."""
    print(str(engine_failure), file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
