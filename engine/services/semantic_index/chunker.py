# services/semantic_index/chunker.py
"""Découpe de fichiers markdown en chunks indexables (un chunk = une section).

Agnostique du contenu : ce module sait ce qu'est un TITRE markdown et ce qu'est la
FORME d'un bloc de callout, pas ce qu'est une « note », un « vault » ou un callout
de tel ou tel type — ces conventions appartiennent aux projets appelants, qui
déclarent eux-mêmes les types à ne pas vectoriser."""

import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from services.markdown_corpus import read_markdown_corpus

# Contenu apparaissant avant le premier titre d'un fichier (ou fichier sans titre)
PREAMBLE_SECTION = "(préambule)"
# Granularité de recherche : au-delà, une section est re-découpée
# (limite de pertinence du chunk, pas limite d'API — les modèles acceptent bien plus).
# Un vecteur est une moyenne : un chunk long dilue chaque idée qu'il contient, un chunk
# court perd le contexte qui la rend interprétable. Aucune théorie ne tranche entre les
# deux — 800 a donc été ESSAYÉ, puis MESURÉ au banc face à ces 2 000, et abandonné :
# un échange, pas un progrès (une question gagnée, une perdue, rang moyen inchangé) ;
# et la question gagnée l'était par contournement, son vrai défaut étant ailleurs.
# Cette valeur est donc mesurée, pas supposée : ne pas la rouvrir sans banc.
# Changer ce seuil coûte des appels API, mais PAS une revectorisation complète : une
# section déjà sous le nouveau seuil n'est pas re-découpée, son texte ne bouge pas, donc
# son hash non plus et son vecteur est réutilisé (mesuré : 621 chunks sur 1 564 réutilisés
# en passant de 2 000 à 800). Seules les sections que le nouveau seuil coupe autrement
# sont revectorisées — d'autant plus nombreuses que le corpus a de longues sections.
# Publique parce qu'elle est INSCRITE dans les métadonnées de chaque index (store.py) :
# un index dit à quelle granularité il a été produit. Une seule définition, lue par le
# build — jamais une valeur recopiée dans le fichier d'index.
MAX_CHUNK_CHARS = 2000
# L'escalier de découpe, du plus structurel au plus fin : on ne descend d'un cran que
# pour les morceaux qui dépassent ENCORE le seuil. Le cran « lignes » récupère tout ce
# qui n'a pas de ligne vide (exports de messagerie, listes, transcripts) ; le cran
# « mots » est le filet qui ne peut pas échouer, et il tombe sur une frontière de mot.
_PARAGRAPH_SEPARATOR = "\n\n"
_LINE_SEPARATOR = "\n"
_WORD_SEPARATOR = " "
_CHUNK_SEPARATORS = (_PARAGRAPH_SEPARATOR, _LINE_SEPARATOR, _WORD_SEPARATOR)
# Chevauchement au cran des mots UNIQUEMENT : c'est le seul qui tranche au milieu d'une
# idée. Paragraphes et lignes coupent à des articulations réelles du texte, où il n'y a
# rien à réparer — y ajouter du chevauchement ne ferait que gonfler le volume vectorisé.
# Le budget des chunks de ce cran est réduit d'autant : chevauchement compris, aucun
# chunk ne dépasse MAX_CHUNK_CHARS.
_WORD_LEVEL_OVERLAP_CHARS = MAX_CHUNK_CHARS // 10
_WORD_LEVEL_CHUNK_CHARS = MAX_CHUNK_CHARS - _WORD_LEVEL_OVERLAP_CHARS
# La FORME d'un bloc de callout — construction markdown répandue (Obsidian, alertes
# GitHub) : une citation dont la PREMIÈRE ligne porte un type entre crochets
# (`> [!note]`, `> [!warning]-` replié, `> [!tip]+` déplié), puis qui se poursuit tant
# que les lignes restent des lignes de citation. Le moteur ne connaît QUE cette forme :
# aucun nom de type n'est écrit ici, ils viennent tous de l'appelant.
_CALLOUT_OPENING_PATTERN = re.compile(r"^>\s*\[!(?P<type>[^\]]+)\][-+]?")
_QUOTE_CONTINUATION_PREFIX = ">"


class MarkdownChunk(BaseModel):
    """Un extrait indexable : sa provenance (fichier + section) et son contenu."""

    relative_path: str   # chemin du fichier relatif à la racine indexée (clé de citation)
    section: str         # titre de la section d'origine (PREAMBLE_SECTION si aucun)
    content: str         # texte ENTIER du chunk, sans la ligne de titre — c'est lui que rend la recherche
    # Types de callout déclarés par l'appelant comme non vectorisables (déjà normalisés
    # par `normalized_callout_types`). Vide par défaut : sans déclaration, rien ne change.
    excluded_callouts: frozenset[str] = frozenset()

    @property
    def embedding_content(self) -> str:
        """`content` privé des blocs de callout exclus — et rien d'autre.

        Deux textes pour un chunk, délibérément : celui qu'on VECTORISE et celui qu'on
        MONTRE. Amputer `content` ferait disparaître le bloc du résultat de recherche,
        c'est-à-dire priver l'utilisateur de l'information qu'il vient de trouver."""
        return _strip_excluded_callouts(self.content, self.excluded_callouts)

    @property
    def embedding_text(self) -> str:
        """LE texte vectorisé (et haché) pour ce chunk — le titre de section en fait
        partie : il porte souvent l'intention de la note mieux que son corps.

        Le hash en dérivant, exclure un type de callout change TOUS les hashs (donc
        revectorise le corpus au premier passage) — mais rend ensuite gratuite toute
        modification du contenu d'un bloc exclu : elle ne touche plus ce texte."""
        return f"{self.section}\n{self.embedding_content}"


def normalized_callout_types(excluded_callouts: Iterable[str]) -> frozenset[str]:
    """Les types déclarés ramenés à LA forme de comparaison : minuscules, sans marges,
    vides écartés. Normalisés une fois pour toutes en entrée plutôt qu'à chaque ligne
    examinée — et c'est aussi cette forme que l'index inscrit dans ses métadonnées, pour
    que `[!Ref]` et `[!ref]` ne produisent pas deux index qui se disent différents."""
    return frozenset(
        callout_type.strip().lower() for callout_type in excluded_callouts if callout_type.strip()
    )


def chunk_markdown_directory(
    root_directory: Path, excluded_callouts: Iterable[str] = ()
) -> list[MarkdownChunk]:
    """Tous les chunks des fichiers .md sous la racine (récursif), ordre stable.

    L'énumération des fichiers vient de `markdown_corpus` — la même que le bras
    lexical : les deux bras indexent le même corpus par construction."""
    markdown_chunks: list[MarkdownChunk] = []
    for document in read_markdown_corpus(root_directory):
        markdown_chunks.extend(
            chunk_markdown_text(document.text, document.relative_path, excluded_callouts)
        )
    return markdown_chunks


def chunk_markdown_text(
    markdown_text: str, relative_path: str, excluded_callouts: Iterable[str] = ()
) -> list[MarkdownChunk]:
    """Découpe un document : une section par titre ATX (#, ##, ...), sections trop
    longues re-découpées par l'escalier de séparateurs. Les sections vides sont
    ignorées. Aucun titre dans le fichier = une seule section `(préambule)`, que
    l'escalier découpe seul : le découpage ne dépend jamais de la présence de titres.

    `excluded_callouts` : les types de bloc que l'appelant ne veut pas vectoriser
    (comparaison insensible à la casse). L'exclusion ne touche QUE le texte vectorisé —
    le découpage, lui, reste celui du texte entier, pour que `content` et son extrait
    restent ceux du fichier."""
    callout_types = normalized_callout_types(excluded_callouts)
    markdown_chunks: list[MarkdownChunk] = []
    section_title = PREAMBLE_SECTION
    section_lines: list[str] = []

    def close_current_section() -> None:
        section_content = "\n".join(section_lines).strip()
        if section_content:
            for piece in _split_oversized_content(section_content):
                chunk = MarkdownChunk(
                    relative_path=relative_path,
                    section=section_title,
                    content=piece,
                    excluded_callouts=callout_types,
                )
                # Plus rien à vectoriser une fois les blocs exclus retirés : pas de chunk.
                # On ne vectorise pas du vide — et l'appel API serait payé pour rien.
                if chunk.embedding_content:
                    markdown_chunks.append(chunk)
        section_lines.clear()

    for line in markdown_text.splitlines():
        heading_title = _parse_heading_title(line)
        if heading_title is not None:
            close_current_section()
            section_title = heading_title
        else:
            section_lines.append(line)
    close_current_section()
    return markdown_chunks


def _strip_excluded_callouts(text: str, excluded_callouts: frozenset[str]) -> str:
    """Retire les blocs de callout dont le type est déclaré exclu — eux seuls.

    Aucune déclaration : le texte ressort tel quel, à l'octet près. C'est ce qui garantit
    qu'un appelant qui ne passe pas l'option garde exactement ses hashs, donc ses vecteurs.

    Un bloc s'ouvre sur une ligne de type (`> [!x]`) et court tant que les lignes sont des
    lignes de citation ; il se ferme sur la première ligne qui ne l'est pas — d'où : deux
    blocs collés se traitent chacun pour son propre type, et la prose qui suit un bloc sans
    ligne vide est conservée. Une citation ordinaire, sans type entre crochets, n'ouvre
    jamais de bloc : elle n'est donc jamais exclue."""
    if not excluded_callouts:
        return text
    kept_lines: list[str] = []
    inside_excluded_block = False
    for line in text.splitlines():
        callout_opening = _CALLOUT_OPENING_PATTERN.match(line)
        if callout_opening is not None:
            inside_excluded_block = callout_opening.group("type").strip().lower() in excluded_callouts
        elif inside_excluded_block and not line.startswith(_QUOTE_CONTINUATION_PREFIX):
            inside_excluded_block = False
        if not inside_excluded_block:
            kept_lines.append(line)
    return "\n".join(kept_lines).strip()


def _parse_heading_title(line: str) -> str | None:
    """Le titre d'une ligne de heading ATX (`## Titre` → "Titre") — None sinon."""
    stripped_line = line.lstrip()
    if not stripped_line.startswith("#"):
        return None
    hashes, _separator, title = stripped_line.partition(" ")
    if hashes != "#" * len(hashes):  # exclut les faux positifs type "#tag" ou "#!/bin/bash"
        return None
    return title.strip() or "(titre vide)"


def _split_oversized_content(section_content: str, separators: tuple[str, ...] = _CHUNK_SEPARATORS) -> list[str]:
    """Re-découpe un contenu > MAX_CHUNK_CHARS en descendant l'escalier de séparateurs.

    Récursif : le contenu est coupé au séparateur courant, seuls les morceaux qui
    dépassent encore le seuil redescendent d'un cran, puis les morceaux consécutifs
    sont recollés tant qu'ils tiennent (sans quoi un cran fin produirait une nuée de
    micro-chunks sans contexte). Escalier épuisé — un « mot » plus long que le seuil,
    URL géante ou blob base64 — : coupe sèche à la longueur, le filet ne peut pas
    échouer. Aucune détection de frontière de phrase : trop d'erreurs sur du texte
    réel (`M. Dupont`, `art. 12`, une URL) et inopérante dans les langues sans casse."""
    if not separators:
        return [
            section_content[start:start + _WORD_LEVEL_CHUNK_CHARS]
            for start in range(0, len(section_content), _WORD_LEVEL_CHUNK_CHARS)
        ]
    separator = separators[0]
    at_word_level = separator == _WORD_SEPARATOR
    chunk_limit = _WORD_LEVEL_CHUNK_CHARS if at_word_level else MAX_CHUNK_CHARS
    if len(section_content) <= chunk_limit:
        return [section_content]

    content_pieces: list[str] = []
    for piece in section_content.split(separator):
        if len(piece) <= chunk_limit:
            content_pieces.append(piece)
        else:
            content_pieces.extend(_split_oversized_content(piece, separators[1:]))
    merged_chunks = _merge_pieces(content_pieces, separator, chunk_limit)
    return _prepend_overlap(merged_chunks) if at_word_level else merged_chunks


def _merge_pieces(content_pieces: list[str], separator: str, chunk_limit: int) -> list[str]:
    """Recolle les morceaux consécutifs (avec leur séparateur d'origine) tant que le
    cumul tient sous le seuil — un morceau seul déjà au-delà part tel quel."""
    merged_chunks: list[str] = []
    accumulated_pieces: list[str] = []
    accumulated_length = 0
    for piece in content_pieces:
        piece_length = len(piece) + len(separator)  # + le séparateur de re-jonction
        if accumulated_pieces and accumulated_length + piece_length > chunk_limit:
            merged_chunks.append(separator.join(accumulated_pieces))
            accumulated_pieces = []
            accumulated_length = 0
        accumulated_pieces.append(piece)
        accumulated_length += piece_length
    if accumulated_pieces:
        merged_chunks.append(separator.join(accumulated_pieces))
    return merged_chunks


def _prepend_overlap(word_level_chunks: list[str]) -> list[str]:
    """Fait reprendre à chaque chunk la fin du précédent (~10 % du seuil, tronquée au
    premier mot entier) : la coupe au cran des mots tombe au milieu d'une idée, ce
    rappel rend le début du chunk lisible hors de son contexte.

    Aucun espace dans cette fin = la coupe précédente était une coupe sèche au milieu
    d'un « mot » (URL géante, blob base64) : pas de rappel — il n'y a pas de mots à
    rappeler, et insérer un espace altérerait le contenu."""
    overlapped_chunks = word_level_chunks[:1]
    for previous_chunk, chunk in zip(word_level_chunks, word_level_chunks[1:]):
        overlap_tail = previous_chunk[-_WORD_LEVEL_OVERLAP_CHARS:]
        _partial_word, _found_separator, whole_words = overlap_tail.partition(_WORD_SEPARATOR)
        overlapped_chunks.append(f"{whole_words}{_WORD_SEPARATOR}{chunk}" if whole_words else chunk)
    return overlapped_chunks
