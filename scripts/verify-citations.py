#!/usr/bin/env python3
"""Vérifie que chaque citation d'une note pointe là où elle dit pointer.

Usage : python3 verify-citations.py <vault> [<note.md> …]
Sans note nommée : `wiki/enseignements/` et `references/`.

Codes de sortie :
  0 — toutes les citations localisables ont été retrouvées à leur repère
  1 — au moins une citation est introuvable ou n'est pas où elle prétend
  2 — aucune citation porteuse d'un repère : rien n'a pu être contrôlé
  3 — vault introuvable ou illisible

Pourquoi ce script existe. Une citation sans point de retour n'est pas une
preuve, c'est une affirmation : pour la contrôler il faut relire la pièce en
entier, donc personne ne la contrôle. Lui adjoindre un repère résout ça — mais
crée un risque pire, parce qu'un repère est un chiffre et qu'un chiffre se
fabrique sans effort. Une ligne inventée donne à une citation approximative
l'apparence d'une citation vérifiée.

D'où ce contrôle : il rouvre les pièces, va au repère annoncé, et regarde si le
texte cité s'y trouve. Ce n'est pas un contrôle de forme — la forme, n'importe
quelle relecture l'attrape. C'est le seul contrôle qui distingue un repère
exact d'un repère plausible.

**Deux pointeurs, deux rôles.** La note de `wiki/sources/` est toujours
adressable ligne à ligne, quelle que soit la pièce : elle donne le repère
précis. L'**original** est la pièce brute, celle qui n'a subi aucun traitement :
elle fait foi. Sans lui, la citation ne remonterait qu'à une *lecture* de la
pièce — or c'est la lecture qui est faillible, et que la citation doit
permettre de contredire. Un original qui désigne une transcription, une sortie
d'OCR ou une note du vault est donc refusé.

De cette double vérification sort un contrôle qui n'existe nulle part ailleurs :
une citation **présente dans la version standardisée et absente de l'original**
n'a ni un mauvais repère ni un mauvais texte — c'est la **standardisation** qui
l'a altérée. Aucune relecture de note ne peut attraper ça.

L'exigence se gradue selon ce que le format porte, parce que réclamer d'un
format ce qu'il n'a pas ne produit que des repères inventés : la ligne est
obligatoire sur une pièce lisible ligne à ligne ; sur un PDF, le citer suffit —
il n'a pas de lignes, il a une mise en page, et `p. <n>` n'est qu'un bonus,
contrôlé s'il est donné.

Ce qu'il tolère, et pourquoi. Une citation élidée (`…`) est comparée fragment
par fragment, dans l'ordre : c'est l'élision qui est signalée dans la note, pas
une altération. Les blancs sont normalisés, parce qu'un export ne les place pas
comme un rendu. Tout le reste doit correspondre au caractère près.

Ce qu'il ne peut pas contrôler, il le dit plutôt que de le compter juste : une
ancre libre, ou un PDF sans couche de texte, sortent en « non vérifié » et
n'entrent dans aucun total.
"""
import re
import sys
import unicodedata
from pathlib import Path

# > « … »
#
# > [!source]- <auteur>, <date>
# > `sources/<slug>.md` Ligne <n>
# > original `archives/<pièce>` Ligne <n>
_QUOTE = re.compile(r"^>\s*[«\"](?P<texte>.+?)[»\"]\s*$", re.M)
# `[^\S\n]*` et non `\s*` : sur un bloc sans auteur, `\s*` franchirait le saut de
# ligne et absorberait le premier pointeur dans le champ auteur.
_BLOCK = re.compile(r"^>[^\S\n]*\[!source\][-+]?[^\S\n]*(?P<auteur>.*)$(?P<corps>(?:\n>.*)*)",
                    re.M | re.I)
_POINTER = re.compile(r"(?P<original>original\s*:?\s*)?`(?P<chemin>[^`]+)`"
                      r"\s*(?P<repere>(?:Ligne|l\.|L)\s*\d+|p\.\s*\d+|#\S+)?", re.I)
# Une ligne d'attribution en clair : au moins un chemin entre accents graves.
# La compilation de `references/` n'est pas vectorisée, donc la commande lui
# prescrit l'attribution en clair plutôt qu'un bloc `[!source]` — il n'y a rien
# à soustraire à un index qui n'existe pas.
_PLAIN = re.compile(r"^[^>\n]*`[^`]+`[^\n]*$", re.M)
# Tolérant à la LECTURE — « Ligne 292 », « l. 292 », « L292 » désignent la même
# chose et des fichiers existants portent chacune des formes. La commande, elle,
# n'en prescrit qu'une : être laxiste au contrôle et strict à l'écriture évite de
# casser l'existant sans laisser la forme dériver.
_LINES = re.compile(r"^(?:Ligne|l\.|L)\s*(\d+)", re.I)


def _flatten(text: str) -> str:
    """Forme comparable : échappements défaits, blancs réduits, signes unifiés.

    Les échappements comptent autant que les blancs. Un export au format JSON
    stocke ses guillemets en `\\"` et ses retours à la ligne en `\\n` littéraux :
    comparer sans les défaire fait échouer toute citation qui contient un
    guillemet ou qui vient d'un message multi-lignes. Mesuré sur un export réel :
    108 guillemets échappés et 248 retours à la ligne, soit la quasi-totalité des
    citations de la note concernée déclarées introuvables à tort.
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\\[nrt]", " ", text)
    for escaped, plain in ((r"\"", '"'), (r"\/", "/"), (r"\\", "\\")):
        text = text.replace(escaped, plain)
    for fancy, plain in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                         ("–", "-"), ("—", "-"), (" ", " ")):
        text = text.replace(fancy, plain)
    return re.sub(r"\s+", " ", text).strip()


def _fragments(quote: str) -> list[str]:
    """Les morceaux séparés par une élision, vides écartés."""
    parts = re.split(r"…|\.\.\.", quote)
    return [f for f in (_flatten(p) for p in parts) if len(f) >= 4]


def _recomposed(lines: list[str], quote: str) -> int | None:
    """Ligne où tous les éléments d'une citation recomposée se trouvent, sinon None.

    Une note condense parfois une entrée en n'en gardant que les valeurs, rejointes
    par des séparateurs qui ne sont pas ceux de la pièce — et en reformatant au
    passage une date ou un intitulé. Le texte n'est alors plus verbatim, mais
    l'entrée existe bel et bien : la déclarer introuvable serait un faux positif,
    l'accepter comme une citation en serait un autre. On la localise, et on la
    nomme pour ce qu'elle est.

    Un élément peut manquer — typiquement la date, réécrite dans un autre format.
    Au-delà, ce n'est plus une condensation, c'est un texte différent.
    """
    parts = [_flatten(p) for p in re.split(r"[|·;/]", quote)]
    parts = [p for p in parts if len(p) >= 4]
    if len(parts) < 2:
        return None
    for number, raw in enumerate(lines, 1):
        flat = _flatten(raw)
        cursor, found = 0, 0
        for part in parts:
            position = flat.find(part, cursor)
            if position >= 0:
                cursor, found = position + len(part), found + 1
        if found >= len(parts) - 1:
            return number
    return None


def _map_lines(lines: list[str]) -> tuple[str, list[int]]:
    """Le texte aplati de la pièce, et la ligne d'origine de chacun de ses caractères.

    Chercher la citation dans une fenêtre de quelques lignes autour du repère
    reviendrait à valider un repère faux dès qu'il tombe à côté de peu — ce qui
    est exactement l'erreur à attraper. On localise donc au caractère, puis on
    remonte à la ligne réelle.
    """
    flat, origin = [], []
    for number, raw in enumerate(lines, 1):
        text = _flatten(raw)
        if not text:
            continue
        if flat:
            flat.append(" ")
            origin.append(number)
        flat.extend(text)
        origin.extend([number] * len(text))
    return "".join(flat), origin


def _derived(target: str) -> str:
    """Nomme le traitement subi si la cible n'est pas la pièce brute, sinon ''.

    Un repère qui vise une transcription remonte à une lecture de la pièce, pas
    à la pièce. Or c'est justement la lecture qui est faillible : c'est elle
    que la citation doit permettre de contredire.
    """
    low = target.lower().replace("\\", "/")
    if low.startswith("wiki/") or "/wiki/" in low:
        return "une note du vault"
    if ".ocr." in low:
        return "une transcription OCR"
    if ".transcription." in low:
        # Le cas le plus trompeur : une série de captures n'a AUCUNE autre
        # lecture que celle qu'un agent en a faite à l'œil. Sa transcription
        # n'a donc pas de seconde voix qui la contredise — c'est précisément
        # pour ça qu'elle ne peut pas tenir lieu d'original.
        return "une transcription de captures"
    if ".standardise" in low:
        return "une version standardisée"
    return ""


def _in_pdf(piece: Path, quote: str, anchor: str | None) -> str:
    """'' si la citation est bien dans le PDF (et à la page annoncée), sinon le défaut."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pdftext", Path(__file__).with_name("pdf-text.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pages, _ = module.pages_of(piece)
    except Exception as problem:                      # noqa: BLE001 — diagnostic, pas de reprise
        return f"couche de texte du PDF illisible ({problem})"
    if not pages:
        return ("PDF sans couche de texte : citation non contrôlable mécaniquement, "
                "à vérifier à l'œil sur la pièce")

    pieces = _fragments(quote)
    wanted = re.match(r"p\.\s*(\d+)", anchor or "")
    if wanted:
        number = int(wanted.group(1))
        if not 1 <= number <= len(pages):
            return f"page {number} annoncée, le PDF en compte {len(pages)}"
        if all(f in _flatten(pages[number - 1]) for f in pieces):
            return ""
        found = next((n for n, page in enumerate(pages, 1)
                      if all(f in _flatten(page) for f in pieces)), None)
        return (f"citation présente mais PAS page {number} (elle est page {found})"
                if found else f"citation INTROUVABLE dans le PDF : « {quote[:60]}… »")

    if any(all(f in _flatten(page) for f in pieces) for page in pages):
        return ""
    return f"citation INTROUVABLE dans le PDF : « {quote[:60]}… »"


class Citation:
    """Une citation, son auteur, et les deux pointeurs de son bloc d'attribution."""

    def __init__(self, line: int, text: str, author: str,
                 standardised: tuple[str, str] | None, original: tuple[str, str] | None):
        self.line, self.text, self.author = line, text, author
        self.standardised, self.original = standardised, original


def _quote_above(lines: list[str], index: int) -> str:
    """La citation qui précède la ligne d'attribution : le bloc `>` juste au-dessus.

    On s'ancre sur l'attribution et non sur la citation, parce que l'attribution
    a une forme reconnaissable — un chemin entre accents graves — alors que la
    citation en a deux : entre guillemets dans `enseignements/`, en simple
    citation markdown dans une compilation de `references/`.
    """
    collected, cursor = [], index - 1
    while cursor >= 0 and not lines[cursor].strip():
        cursor -= 1
    while cursor >= 0 and lines[cursor].startswith(">"):
        body = lines[cursor][1:].strip()
        if body.startswith("[!"):          # le bloc d'attribution lui-même
            break
        collected.append(body)
        cursor -= 1
    text = " ".join(reversed(collected)).strip()
    stripped = text.strip("«»\"' ")
    return stripped or text


def _author_above(lines: list[str], index: int) -> str:
    """L'auteur annoncé au-dessus d'une citation, dans une compilation.

    Une compilation titre chaque entrée — `**<date> — <auteur>** — <note>` —
    au lieu de porter l'auteur dans son attribution. Chercher l'auteur au seul
    endroit prévu par l'autre forme le déclarerait manquant partout.
    """
    cursor = index - 1
    while cursor >= 0 and (not lines[cursor].strip() or lines[cursor].startswith(">")):
        cursor -= 1
    if cursor < 0:
        return ""
    header = lines[cursor].strip()
    if not header.startswith(("**", "#", "-")):
        return ""
    parts = re.split(r"\s+[—–-]\s+", re.sub(r"[*#`]", "", header))
    return parts[1].strip() if len(parts) > 1 else ""


def _pointers(text: str) -> tuple[tuple[str, str] | None, tuple[str, str] | None]:
    """(pointeur de lecture, pointeur d'original) lus dans un texte d'attribution."""
    reading = original = None
    for found in _POINTER.finditer(text):
        entry = (found.group("chemin").strip(), (found.group("repere") or "").strip())
        if found.group("original"):
            original = entry
        elif reading is None:
            reading = entry
    return reading, original


class Citation:
    """Une citation, son auteur, et les deux pointeurs de son attribution."""

    def __init__(self, line: int, text: str, author: str,
                 standardised: tuple[str, str] | None, original: tuple[str, str] | None):
        self.line, self.text, self.author = line, text, author
        self.standardised, self.original = standardised, original


def _citations(note: Path) -> list[Citation]:
    """Les citations d'une note, quelle que soit la forme de leur attribution.

    Deux formes coexistent, et c'est voulu : dans `enseignements/`, un bloc
    `> [!source]` que l'indexation soustrait au vecteur ; dans une compilation
    de `references/`, une ligne en clair — ce fichier n'étant pas vectorisé, il
    n'y a rien à soustraire.
    """
    body = note.read_text(encoding="utf-8", errors="replace")
    lines = body.splitlines()
    found, consumed = [], set()

    for block in _BLOCK.finditer(body):
        index = body[:block.start()].count("\n")
        consumed.update(range(index, index + block.group(0).count("\n") + 1))
        reading, original = _pointers(block.group("corps"))
        found.append(Citation(index + 1, _quote_above(lines, index),
                              block.group("auteur").strip(" ·—-,"), reading, original))

    for number, raw in enumerate(lines):
        if number in consumed or not _PLAIN.match(raw) or "`" not in raw:
            continue
        reading, original = _pointers(raw)
        if reading is None:
            continue
        quote = _quote_above(lines, number)
        if not quote:
            continue
        found.append(Citation(number + 1, quote,
                              _author_above(lines, number), reading, original))

    return sorted(found, key=lambda c: c.line)


def _locate(vault: Path, target: str, locator: str, quote: str,
            label: str, role: str) -> tuple[str, bool]:
    """(défaut ou '', citation retrouvée). `role` nomme le pointeur dans le message."""
    piece = (vault / target).resolve()
    if piece.is_dir():
        # Une série de captures est un original légitime, mais elle n'a ni
        # lignes ni pages : le dossier ne désigne aucun endroit. Ce n'est pas
        # une absence, c'est un repère trop grossier — et le dire ainsi évite
        # de le confondre avec une pièce manquante.
        return (f"{label} — {role} : « {target} » est une série de {len(list(piece.iterdir()))} "
                "captures, pas un fichier. Citer la capture précise et son rang dans la "
                "série ; le contrôle mécanique s'arrête là, la vérification est visuelle."), False
    if not piece.is_file():
        return f"{label} — {role} introuvable : {target}", False

    if piece.suffix.lower() == ".pdf":
        problem = _in_pdf(piece, quote, locator)
        return (f"{label} — {role} : {problem} ({target})" if problem else ""), not problem

    try:
        lines = piece.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as trouble:
        return f"{label} — {role} illisible : {trouble}", False

    pieces = _fragments(quote)
    if not pieces:
        return "", False
    flat, origin = _map_lines(lines)
    position = flat.find(pieces[0])
    if position < 0:
        line = _recomposed(lines, quote)
        if line is None:
            return "", False                  # absente : l'appelant décide du message
        digits = _LINES.match(locator or "")
        where = (f"ligne {line}" if not digits
                 else ("" if int(digits.group(1)) == line
                       else f"— et son repère dit la ligne {digits.group(1)}, pas {line}"))
        return (f"{label} — {role} : citation RECOMPOSÉE, pas verbatim. Ses éléments sont "
                f"réunis {where or f'bien ligne {line}'} dans {target}, mais rejoints "
                "autrement. Entre guillemets, un texte doit être celui de la pièce."), True

    cursor = position
    for fragment in pieces[1:]:
        cursor = flat.find(fragment, cursor)
        if cursor < 0:
            return f"{label} — {role} : fragments dans le désordre dans {target}", True

    digits = _LINES.match(locator or "")
    if not digits:
        if (locator or "").startswith("#"):
            return "", True
        return (f"{label} — {role} : repère de ligne manquant sur {target}, qui est "
                "adressable par ligne (`grep -n`)"), True
    wanted, real = int(digits.group(1)), origin[position]
    if real != wanted:
        return (f"{label} — {role} : citation présente dans {target} mais PAS à la "
                f"ligne {wanted} : elle commence ligne {real}"), True
    return "", True


def check(vault: Path, notes: list[Path]) -> tuple[list[str], list[str], int, int]:
    """(défauts, non contrôlés, citations contrôlées, citations sans bloc)."""
    faults, skipped, checked, bare = [], [], 0, 0

    for note in notes:
        for citation in _citations(note):
            label = f"{note.name}:{citation.line}"
            if not citation.standardised:
                bare += 1
                faults.append(
                    f"{label} — aucun bloc `> [!source]` sous la citation : "
                    f"« {citation.text[:60]}… ». Rien ne permet de la contrôler sans "
                    "relire la pièce entière.")
                continue
            if not citation.author:
                faults.append(f"{label} — bloc d'attribution sans auteur. Rapporter un "
                              "propos sans dire de qui il est le rend attribuable à "
                              "n'importe qui.")

            checked += 1
            target, locator = citation.standardised
            problem, present = _locate(vault, target, locator, citation.text, label,
                                       "version standardisée")
            if problem:
                faults.append(problem)
            elif not present:
                faults.append(f"{label} — citation INTROUVABLE dans la version "
                              f"standardisée {target} : « {citation.text[:60]}… »")

            if not citation.original:
                faults.append(f"{label} — aucun original déclaré. La version standardisée "
                              "est une LECTURE de la pièce : sans l'original, la citation "
                              "ne permet pas de contredire cette lecture.")
                continue

            raw, raw_locator = citation.original
            derived = _derived(raw)
            if derived:
                faults.append(f"{label} — l'original déclaré est {derived}, pas une pièce "
                              f"brute : {raw}")
                continue

            problem, present = _locate(vault, raw, raw_locator, citation.text, label,
                                       "original")
            if problem:
                faults.append(problem)
            elif not present:
                # Le défaut qu'aucune relecture de note n'attrape : présente dans
                # la version standardisée, absente de l'original — la
                # standardisation a altéré la citation.
                faults.append(f"{label} — citation absente de l'original {raw} alors "
                              "qu'elle figure dans la version standardisée : c'est la "
                              "STANDARDISATION qui l'a altérée, pas le repère qui est faux.")
    return faults, skipped, checked, bare


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage : python3 verify-citations.py <vault> [<note.md> …]", file=sys.stderr)
        return 3
    vault = Path(sys.argv[1])
    if not vault.is_dir():
        print(f"ERREUR : vault introuvable : {vault}", file=sys.stderr)
        return 3

    if len(sys.argv) > 2:
        notes = [Path(a) for a in sys.argv[2:]]
    else:
        # `enseignements/` porte les citations d'une pièce ; `references/` porte
        # les compilations de `--all-references`, qui sont précisément le
        # livrable destiné à être opposé — donc celui qu'il faut le plus
        # vérifier. Ne balayer que le premier laissait le second sans contrôle.
        notes = sorted((vault / "wiki" / "enseignements").glob("*.md"))
        notes += sorted((vault / "references").glob("*.md"))
    notes = [n for n in notes if n.is_file()]
    if not notes:
        print("Aucune note d'enseignements à contrôler.", file=sys.stderr)
        return 2

    faults, skipped, checked, bare = check(vault, notes)

    for line in skipped:
        print(f"· {line}")
    for line in faults:
        print(f"✗ {line}")

    total = checked + bare + len(skipped)
    if not total:
        print(f"{len(notes)} note(s) lue(s), aucune citation trouvée.", file=sys.stderr)
        return 2
    if not checked and not faults:
        print(f"{len(notes)} note(s) : aucune citation contrôlable mécaniquement "
              f"({len(skipped)} hors portée). Ce n'est pas un succès, "
              "c'est une absence de contrôle.", file=sys.stderr)
        return 2

    print(f"\n{len(notes)} note(s) · {checked} citation(s) retrouvée(s) à leur repère · "
          f"{len(faults)} défaut(s) · {len(skipped)} hors portée")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
