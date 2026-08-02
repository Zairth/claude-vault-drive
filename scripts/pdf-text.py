#!/usr/bin/env python3
"""Extrait la couche de texte d'un PDF, sans dépendance ni réseau.

Usage : python3 pdf-text.py <fichier.pdf> [sortie.txt]
Sortie sur stdout si aucune sortie n'est donnée. Code 1 si le PDF ne porte
aucune couche de texte exploitable (c'est le signal qu'il faut un OCR).

Pourquoi ce script existe. Un PDF produit par un logiciel — export tableur,
traitement de texte, facture générée — contient le texte tel que le logiciel
l'a écrit. L'extraire est exact, gratuit et instantané. Le passer à l'OCR
revient à le photographier pour deviner ce qu'on pouvait lire, et un OCR se
trompe **systématiquement** : il remplace partout la même valeur par la même
autre, ce qui produit un résultat plausible, cohérent avec lui-même, et faux.
Mesuré sur un export tableur de 40 lignes : les 18 « Haute » d'une colonne de
priorité lues « Moyenne », soit une colonne entière inversée sans que rien ne
le signale.

Les outils habituels (`pdftotext`, `pandoc`) ne sont pas toujours installés, et
demander leur installation à l'utilisateur pour ingérer un fichier serait un
obstacle. D'où cette extraction en bibliothèque standard seule : flux
décompressés en zlib, glyphes traduits par les tables `/ToUnicode` que le PDF
embarque pour ses polices sous-ensemblées.

Limite assumée : pas de reconstruction de mise en page. La sortie est le texte
dans l'ordre où le PDF le dessine — cellule après cellule pour un tableau. La
standardisation qui suit lui rend sa structure ; c'est son métier, pas celui-ci.
"""
import re
import sys
import zlib
from pathlib import Path

_MIN_USEFUL_CHARS = 200      # en dessous : aucune couche de texte
_MIN_CHARS_PER_PAGE = 200    # en dessous : couche présente mais décorative

# Pourquoi une densité et pas seulement un total. Un diaporama exporté en PDF
# porte une couche de texte — ses titres — alors que tout son contenu est en
# images. Mesuré : 352 caractères sur 11 pages, contre 4 736 par page pour un
# export tableur. Se fier au total ferait déclarer « PDF texte » un document
# dont on perdrait 95 % du contenu, silencieusement. Le rapport entre les deux
# cas est de l'ordre de cent : n'importe quel seuil intermédiaire tranche.


def _objects(raw: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(2)
            for m in re.finditer(rb"(\d+)\s+0\s+obj(.*?)endobj", raw, re.S)}


def _stream(objects: dict[int, bytes], number: int) -> bytes:
    found = re.search(rb"stream\r?\n(.*?)endstream", objects.get(number, b""), re.S)
    if not found:
        return b""
    try:
        return zlib.decompress(found.group(1))
    except zlib.error:
        return found.group(1)  # flux non compressé


def _unicode_tables(objects: dict[int, bytes]) -> dict[int, dict[int, str]]:
    """Une table {code glyphe → caractère} par objet police qui en déclare une."""
    tables = {}
    for number, body in objects.items():
        reference = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", body)
        if not reference:
            continue
        data, table = _stream(objects, int(reference.group(1))), {}
        for block in re.finditer(rb"beginbfchar(.*?)endbfchar", data, re.S):
            for code, target in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)):
                text = target.decode()
                table[int(code, 16)] = "".join(
                    chr(int(text[i:i + 4], 16)) for i in range(0, len(text), 4))
        for block in re.finditer(rb"beginbfrange(.*?)endbfrange", data, re.S):
            for low, high, base in re.findall(
                    rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)):
                start = int(base.decode()[:4], 16)
                for code in range(int(low, 16), int(high, 16) + 1):
                    table[code] = chr(start + code - int(low, 16))
        if table:
            tables[number] = table
    return tables


def _unescape(literal: bytes) -> bytes:
    out, index = bytearray(), 0
    while index < len(literal):
        if literal[index:index + 1] == b"\\" and index + 1 < len(literal):
            escaped = literal[index + 1:index + 2]
            out += {b"n": b"\n", b"r": b"\r", b"t": b"\t"}.get(escaped, escaped)
            index += 2
        else:
            out += literal[index:index + 1]
            index += 1
    return bytes(out)


def _page_count(raw: bytes) -> int:
    pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))
    if pages:
        return pages
    counts = [int(n) for n in re.findall(rb"/Count\s+(\d+)", raw)]
    return max(counts) if counts else 1


def extract(pdf_path: Path) -> str:
    raw = pdf_path.read_bytes()
    objects = _objects(raw)
    tables = _unicode_tables(objects)
    # /Font1 12 0 R → quelle table appliquer quand le flux sélectionne /Font1
    resources = {name.decode(): int(number)
                 for body in objects.values()
                 for name, number in re.findall(rb"/(\w+)\s+(\d+)\s+0\s+R", body)}

    pages = []
    for number in sorted(objects):
        content = _stream(objects, number)
        if b"Tf" not in content:
            continue
        current, parts = None, []
        for token in re.finditer(rb"/(\w+)\s+[\d.]+\s+Tf|\(((?:\\.|[^()\\])*)\)", content, re.S):
            if token.group(1):
                current = tables.get(resources.get(token.group(1).decode(), -1))
            elif current:
                data = _unescape(token.group(2))
                parts.append("".join(current.get((data[i] << 8) | data[i + 1], "")
                                     for i in range(0, len(data) - 1, 2)))
        if any(parts):
            pages.append("".join(parts))
    return "\n\n".join(pages)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    pdf_path = Path(sys.argv[1])
    if not pdf_path.is_file():
        print(f"ERREUR : fichier introuvable : {pdf_path}", file=sys.stderr)
        return 2

    text = extract(pdf_path)
    size = len(text.strip())
    if size < _MIN_USEFUL_CHARS:
        print(f"Aucune couche de texte exploitable dans ce PDF ({size} caractères) — "
              "c'est un scan ou une image : passer par l'OCR.", file=sys.stderr)
        return 1

    pages = _page_count(pdf_path.read_bytes())
    density = size // max(pages, 1)
    if density < _MIN_CHARS_PER_PAGE:
        print(f"Couche de texte trop maigre pour être le contenu ({size} caractères sur "
              f"{pages} pages, soit {density} par page) — diaporama ou document dont le fond "
              "est en images : passer par l'OCR.", file=sys.stderr)
        return 1

    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(text, encoding="utf-8")
        print(f"{len(text)} caractères extraits → {sys.argv[2]}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
