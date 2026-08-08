# services/markdown_corpus.py
"""CE qu'un dossier indexé contient : la définition unique du corpus markdown.

Partagé par les deux bras de recherche (`semantic_index/` vectoriel,
`lexical_index/` BM25). Ce n'est pas une factorisation de confort : si les deux
bras énuméraient ou lisaient les fichiers chacun de leur côté, ils pourraient un
jour classer des corpus différents — et leurs scores, comparés ou fusionnés,
mentiraient.

Agnostique du contenu : ce module sait ce qu'est un fichier `.md` et ce qu'est un
front matter YAML, pas ce qu'est une « note » ou un « vault ». L'unité, ici comme
partout, est le FICHIER, identifié par son chemin relatif à la racine indexée."""

from pathlib import Path

from pydantic import BaseModel

# Le délimiteur du front matter YAML en tête de fichier — convention markdown
# universelle (Jekyll, Hugo, Pandoc, Obsidian…), au même titre qu'un titre ATX
_FRONT_MATTER_FENCE = "---"


class MarkdownDocument(BaseModel):
    """Un fichier du corpus : sa clé de citation et son texte cherchable."""

    relative_path: str  # chemin relatif à la racine indexée, en POSIX (clé de citation)
    text: str           # le corps du fichier, front matter retiré (voir _strip_front_matter)


def read_markdown_corpus(root_directory: Path) -> list[MarkdownDocument]:
    """Tous les `.md` sous la racine (récursif), lus, dans un ordre stable.

    L'ordre est trié pour que deux constructions d'index à contenu identique
    produisent le même fichier — un diff de synchro cloud ne doit pas bouger sans
    raison."""
    return [
        MarkdownDocument(
            relative_path=markdown_path.relative_to(root_directory).as_posix(),
            text=_strip_front_matter(markdown_path.read_text(encoding="utf-8")),
        )
        for markdown_path in sorted(root_directory.rglob("*.md"))
    ]


def _strip_front_matter(markdown_text: str) -> str:
    """Retire le bloc de front matter YAML en tête de fichier — lui seul.

    Pourquoi il ne doit pas être indexé : ses clés se répètent à l'identique dans
    tous les fichiers d'un dossier. Elles ne discriminent donc RIEN (leur IDF tombe
    à zéro côté BM25, elles diluent le vecteur côté sémantique) et elles mangent
    les premiers mots de chaque aperçu, dont la longueur utile est limitée.

    Conséquence assumée : les VALEURS du front matter cessent d'être cherchables.
    Un fichier dont le résumé vit dans une clé `description` ne sera plus trouvé
    par ce résumé — le corps du fichier reste indexé et dit la même chose. Indexer
    les valeurs sans les clés serait plus fin, mais demanderait au moteur de
    décider ce qui, dans un front matter, est du contenu : ce sont les conventions
    de l'appelant, et le moteur ne les connaît pas. Le retrait complet est le seul
    comportement prévisible.

    Deux garde-fous, parce qu'un `---` n'est pas toujours un front matter :
    seule une ligne `---` en PREMIÈRE ligne ouvre un bloc (ailleurs, c'est une
    règle horizontale), et un bloc jamais refermé n'en est pas un — le texte
    ressort alors intact plutôt qu'amputé."""
    document_lines = markdown_text.splitlines()
    if not document_lines or document_lines[0].strip() != _FRONT_MATTER_FENCE:
        return markdown_text
    for line_index, line in enumerate(document_lines[1:], start=1):
        if line.strip() == _FRONT_MATTER_FENCE:
            return "\n".join(document_lines[line_index + 1:])
    return markdown_text
