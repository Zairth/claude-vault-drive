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
le signale. Sur un document contractuel, l'écart observé porte sur des mots
isolés — un OCR « corrige » les coquilles de l'auteur —, ce qui est pire
qu'une erreur franche : le texte cité entre guillemets n'est plus celui de la
pièce, et rien ne le distingue.

Les outils habituels (`pdftotext`, `pandoc`) ne sont pas toujours installés, et
demander leur installation à l'utilisateur pour ingérer un fichier serait un
obstacle. D'où cette extraction en bibliothèque standard seule : flux
décompressés en zlib, glyphes traduits par les tables `/ToUnicode` que le PDF
embarque pour ses polices sous-ensemblées.

Ce qu'il faut savoir sur les PDF réels. Un même texte se dessine de plusieurs
façons, et n'en supporter qu'une revient à déclarer « scan » des documents
parfaitement lisibles :

* **les chaînes de caractères** s'écrivent entre parenthèses `(Bonjour)` ou en
  hexadécimal `<0025004F>`. Les suites bureautiques les plus répandues
  n'émettent QUE de l'hexadécimal ;
* **la largeur d'un code** dépend de la police : deux octets pour une police
  composite (`/Type0`), un seul pour une police simple. Lire les unes comme les
  autres ne rend rien d'exploitable ;
* **une police se nomme localement** : le `/F1` d'une page n'est pas celui de la
  suivante. La correspondance se résout page par page, par l'arbre des pages ;
* **un document mis en page** dessine son texte dans des formulaires que la page
  appelle, et non dans le flux de la page.

Limite assumée : pas de reconstruction de mise en page. Les lignes sont
retrouvées par la position verticale réelle du texte, mais colonnes et tableaux
ressortent cellule après cellule. La standardisation qui suit leur rend leur
structure ; c'est son métier, pas celui-ci.
"""
import re
import sys
import zlib
from pathlib import Path

_MIN_USEFUL_CHARS = 200      # en dessous : aucune couche de texte
_MIN_CHARS_PER_PAGE = 200    # en dessous : couche présente mais décorative
_MIN_TRANSLATED = 0.97       # en dessous : couche présente mais illisible

# Pourquoi une densité et pas seulement un total. Un diaporama exporté en PDF
# porte une couche de texte — ses titres — alors que tout son contenu est en
# images. Mesuré : 352 caractères sur 11 pages, contre 4 736 par page pour un
# export tableur. Se fier au total ferait déclarer « PDF texte » un document
# dont on perdrait 95 % du contenu, silencieusement. Le rapport entre les deux
# cas est de l'ordre de cent : n'importe quel seuil intermédiaire tranche.

# Pourquoi un taux de traduction en plus. Une police peut être appelée sans que
# sa table `/ToUnicode` couvre tous les glyphes qu'elle dessine : le texte sort
# alors amputé de lettres isolées — accents et apostrophes en premier — sans
# rien qui le signale, et le résultat se lit comme du texte fautif plutôt que
# comme une extraction ratée. Deux garde-fous valent mieux qu'un seuil seul :
# chaque glyphe perdu laisse une marque « � », comptée et annoncée, de sorte
# qu'une lacune reste visible dans le fichier produit ; le seuil, lui, ne
# tranche que le cas franc. Mesuré sur quinze documents : huit à 100 %, sept
# entre 99,2 % et 100 % — tirets et parenthèses omis par le producteur.
#
# Ce taux a aussi servi à trouver un défaut qu'il ne mesure pas. Un document
# tombait à 93 % : la cause n'était pas des tables incomplètes mais des tables
# **interverties**, et les glyphes que le taux comptait manquants n'étaient que
# la part visible d'un texte par ailleurs faux. Un chiffre bas signale donc
# qu'il faut aller voir, pas seulement qu'il faut passer à l'OCR.


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


def _unicode_table(objects: dict[int, bytes], number: int) -> dict[int, str]:
    """Table {code glyphe → caractère} lue dans un flux `/ToUnicode`."""
    data, table = _stream(objects, number), {}
    for block in re.finditer(rb"beginbfchar(.*?)endbfchar", data, re.S):
        for code, target in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)):
            text = target.decode()
            glyph = "".join(chr(int(text[i:i + 4], 16)) for i in range(0, len(text), 4))
            # Une police fait parfois pointer un glyphe sur U+0000 : c'est une
            # absence de traduction, pas un caractère. La retenir insérerait un
            # octet nul dans un texte qu'on croit propre.
            if glyph.strip("\0"):
                table[int(code, 16)] = glyph
    for block in re.finditer(rb"beginbfrange(.*?)endbfrange", data, re.S):
        for low, high, base in re.findall(
                rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)):
            start = int(base.decode()[:4], 16)
            for code in range(int(low, 16), int(high, 16) + 1):
                table[code] = chr(start + code - int(low, 16))
    return table


def _font(objects: dict[int, bytes], number: int) -> tuple[dict[int, str], int]:
    """(table de traduction, largeur d'un code en octets) pour un objet police."""
    body = objects.get(number, b"")
    width = 2 if re.search(rb"/Subtype\s*/Type0", body) else 1
    reference = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", body)
    table = _unicode_table(objects, int(reference.group(1))) if reference else {}
    return table, width


def _resolve(objects: dict[int, bytes], blob: bytes) -> bytes:
    """Le corps d'un dictionnaire, qu'il soit écrit sur place ou référencé."""
    reference = re.match(rb"\s*(\d+)\s+0\s+R", blob)
    return objects.get(int(reference.group(1)), b"") if reference else blob


def _value(body: bytes, key: bytes) -> bytes:
    """Valeur de `key` : une référence `N 0 R`, un `<< … >>` ou un `[ … ]`."""
    found = re.search(re.escape(key) + rb"\s*", body)
    if not found:
        return b""
    rest = body[found.end():]
    reference = re.match(rb"(\d+)\s+0\s+R", rest)
    if reference:
        return rest[:reference.end()]
    for opening, closing in ((b"<<", b">>"), (b"[", b"]")):
        if not rest.startswith(opening):
            continue
        depth, index = 0, 0
        while index < len(rest):
            if rest[index:index + len(opening)] == opening:
                depth += 1
                index += len(opening)
            elif rest[index:index + len(closing)] == closing:
                depth -= 1
                index += len(closing)
                if depth == 0:
                    return rest[:index]
            else:
                index += 1
    return b""


def _page_order(objects: dict[int, bytes]) -> list[tuple[int, bytes]]:
    """(page, ressources héritées) dans l'ordre de l'arbre, pas du fichier.

    L'ordre des objets dans le fichier n'est pas celui des pages : lire l'un
    pour l'autre rend un document dont les pages sont mêlées, ce qui ne se voit
    pas sur un formulaire mais fait perdre le fil d'un texte suivi.
    """
    catalog = next((n for n, body in objects.items()
                    if re.search(rb"/Type\s*/Catalog", body)), None)
    root = re.search(rb"/Pages\s+(\d+)\s+0\s+R", objects.get(catalog, b"")) if catalog else None
    order, seen = [], set()

    def walk(number: int, inherited: bytes) -> None:
        if number in seen or number not in objects:
            return
        seen.add(number)
        body = objects[number]
        resources = _value(body, b"/Resources") or inherited
        kids = _value(body, b"/Kids")
        if kids:
            for child in re.findall(rb"(\d+)\s+0\s+R", kids):
                walk(int(child), resources)
        elif re.search(rb"/Type\s*/Page[^s]", body):
            order.append((number, resources))

    if root:
        walk(int(root.group(1)), b"")
    if not order:  # catalogue illisible : repli sur l'ordre du fichier
        order = [(n, b"") for n, body in sorted(objects.items())
                 if re.search(rb"/Type\s*/Page[^s]", body)]
    return order


def _named(objects: dict[int, bytes], resources: bytes, key: bytes) -> dict[str, int]:
    """{nom local → objet} pour la section `/Font` ou `/XObject` de ressources."""
    section = _resolve(objects, _value(resources, key))
    return {name.decode("latin-1"): int(target)
            for name, target in re.findall(rb"/([^\s/<>\[\]()]+)\s+(\d+)\s+0\s+R", section)}


_SELECT = re.compile(rb"/([^\s/<>\[\]()]+)(\s+[-\d.]+\s+Tf)")


def _expand(objects: dict[int, bytes], resources: bytes, content: bytes,
            scope: str, fonts: dict[str, int], depth: int = 0) -> bytes:
    """Développe les formulaires appelés, chaque niveau gardant ses polices.

    Un document mis en page — plaquette, rapport composé, magazine — ne dessine
    pas son texte dans le flux de la page mais dans des formulaires que la page
    appelle par `/Nom Do`. Sans cette descente, la page paraît vide alors que
    tout son texte est là, tables de traduction comprises.

    Développer ne suffit pas : `/F1` désigne une police **dans le formulaire
    qui l'emploie**, et le `/F1` de la page en désigne une autre. Verser les
    unes et les autres dans un même dictionnaire fait gagner la dernière lue,
    et le texte ressort alors traduit par la mauvaise table — non pas amputé,
    ce qui se verrait, mais **faux** : un « : » rendu « f », un trait d'union
    rendu « l ». Chaque niveau reçoit donc un préfixe, et les sélections de
    police du flux sont réécrites avec lui.
    """
    for name, target in _named(objects, resources, b"/Font").items():
        fonts[scope + name] = target
    content = _SELECT.sub(lambda m: b"/" + scope.encode("latin-1") + m.group(1) + m.group(2),
                          content)
    forms = _named(objects, resources, b"/XObject")
    if depth > 6 or not forms:
        return content

    def descend(call: re.Match) -> bytes:
        target = forms.get(call.group(1).decode("latin-1"))
        if target is None or not re.search(rb"/Subtype\s*/Form", objects.get(target, b"")):
            return b""  # une image : rien à lire
        own = _resolve(objects, _value(objects[target], b"/Resources")) or resources
        return (b"\nq\n" + _expand(objects, own, _stream(objects, target),
                                   f"{scope}{target}~", fonts, depth + 1) + b"\nQ\n")

    return re.sub(rb"/([^\s/<>\[\]()]+)\s+Do", descend, content)


def _pages(objects: dict[int, bytes]) -> list[tuple[bytes, dict[str, int]]]:
    """(flux de contenu développé, polices nommées) pour chaque page, dans l'ordre."""
    out = []
    for number, inherited in _page_order(objects):
        body = objects[number]
        resources = _resolve(objects, _value(body, b"/Resources") or inherited)
        streams = [int(n) for n in re.findall(rb"(\d+)\s+0\s+R", _value(body, b"/Contents"))]
        content = b"".join(_stream(objects, n) for n in streams)
        fonts: dict[str, int] = {}
        out.append((_expand(objects, resources, content, "", fonts), fonts))
    return out


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


_NUMBER = rb"[-\d.]+\s+"
_TOKEN = re.compile(
    rb"/([^\s/<>\[\]()]+)\s+[-\d.]+\s+Tf"                    # 1  police choisie
    rb"|\(((?:\\.|[^()\\])*)\)"                               # 2  chaîne littérale
    rb"|<([0-9A-Fa-f\s]*)>\s*(?=Tj|TJ|\]|<|\(|[-\d.])"        # 3  chaîne hexadécimale
    rb"|" + _NUMBER * 3 + rb"([-\d.]+)\s+" + _NUMBER + rb"([-\d.]+)\s+Tm"   # 4,5 matrice texte
    rb"|" + _NUMBER * 3 + rb"([-\d.]+)\s+" + _NUMBER + rb"([-\d.]+)\s+cm"   # 6,7 matrice page
    rb"|[-\d.]+\s+([-\d.]+)\s+T[dD]"                          # 8  déplacement de ligne
    rb"|(T\*)"                                                # 9  ligne suivante
    rb"|(?<![A-Za-z])(q|Q)(?![A-Za-z])",                      # 10 pile d'état graphique
    re.S)


def extract(pdf_path: Path) -> tuple[str, float]:
    """(texte, part des glyphes effectivement traduits)."""
    pages, rate = pages_of(pdf_path)
    return "\n\n".join(pages), rate


def pages_of(pdf_path: Path) -> tuple[list[str], float]:
    """(texte de chaque page pris à part, part des glyphes traduits).

    Rendre les pages séparément plutôt qu'un texte joint permet de situer une
    citation **par page**, seul repère qu'un PDF admette : il n'a pas de
    lignes, il a une mise en page.
    """
    objects = _objects(pdf_path.read_bytes())
    known, drawn, translated, pages = {}, 0, 0, []

    for content, fonts in _pages(objects):
        if b"Tf" not in content:
            continue
        table, width, parts = {}, 1, []
        scale, shift, stack = 1.0, 0.0, []   # matrice de la page
        text_scale, text_shift = 1.0, 0.0    # matrice du texte
        last_baseline = None

        def write(data: bytes) -> None:
            """Ajoute une chaîne, précédée d'un saut si la ligne a changé."""
            nonlocal drawn, translated, last_baseline
            baseline = shift + scale * text_shift
            if last_baseline is not None and abs(baseline - last_baseline) > 0.6:
                parts.append("\n")
            last_baseline = baseline
            codes = ([(data[i] << 8) | data[i + 1] for i in range(0, len(data) - 1, 2)]
                     if width == 2 else list(data))
            drawn += len(codes)
            translated += sum(1 for code in codes if code in table)
            # Un glyphe sans traduction laisse une marque : une lettre qui
            # disparaît en silence se relit comme une faute de l'auteur.
            parts.append("".join(table.get(code, "�") for code in codes))

        for token in _TOKEN.finditer(content):
            if token.group(1):
                target = fonts.get(token.group(1).decode("latin-1"))
                if target is not None:
                    if target not in known:
                        known[target] = _font(objects, target)
                    table, width = known[target]
            elif token.group(2) is not None:
                write(_unescape(token.group(2)))
            elif token.group(3) is not None:
                digits = re.sub(rb"\s", b"", token.group(3))
                write(bytes.fromhex((digits + b"0" if len(digits) % 2 else digits).decode()))
            elif token.group(4) is not None:
                text_scale, text_shift = float(token.group(4)), float(token.group(5))
            elif token.group(6) is not None:
                scale, shift = scale * float(token.group(6)), shift + scale * float(token.group(7))
            elif token.group(8) is not None:
                text_shift += float(token.group(8)) * text_scale
            elif token.group(9):
                text_shift += text_scale
            elif token.group(10) == b"q":
                stack.append((scale, shift))
            elif token.group(10) == b"Q" and stack:
                scale, shift = stack.pop()

        page = re.sub(r"[ \t]+\n", "\n", "".join(parts))
        if page.strip():
            pages.append(page)

    return pages, (translated / drawn if drawn else 0.0)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    pdf_path = Path(sys.argv[1])
    if not pdf_path.is_file():
        print(f"ERREUR : fichier introuvable : {pdf_path}", file=sys.stderr)
        return 2

    text, rate = extract(pdf_path)
    size = len(text.strip())
    if size < _MIN_USEFUL_CHARS:
        print(f"Aucune couche de texte exploitable dans ce PDF ({size} caractères) — "
              "c'est un scan ou une image : passer par l'OCR.", file=sys.stderr)
        return 1

    pages = max(len(_page_order(_objects(pdf_path.read_bytes()))), 1)
    density = size // pages
    if density < _MIN_CHARS_PER_PAGE:
        print(f"Couche de texte trop maigre pour être le contenu ({size} caractères sur "
              f"{pages} pages, soit {density} par page) — diaporama ou document dont le fond "
              "est en images : passer par l'OCR.", file=sys.stderr)
        return 1

    if rate < _MIN_TRANSLATED:
        print(f"Couche de texte présente mais incomplètement traduisible "
              f"({rate:.1%} des glyphes seulement ; les autres sortent en « � ») — "
              "le document embarque ses polices sans table de correspondance "
              "complète : passer par l'OCR.", file=sys.stderr)
        return 1

    lost = text.count("�")
    if lost:
        print(f"AVERTISSEMENT : {lost} glyphe(s) sans traduction dans le PDF, sortis en "
              f"« � » ({rate:.2%} traduits). Le document les dessine sans les déclarer ; "
              "vérifier ces positions sur la pièce avant d'en citer le texte.", file=sys.stderr)

    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(text, encoding="utf-8")
        print(f"{len(text)} caractères extraits → {sys.argv[2]}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
