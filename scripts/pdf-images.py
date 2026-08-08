#!/usr/bin/env python3
"""Extrait les images d'un PDF, pour qu'on puisse les REGARDER.

Usage : python3 pdf-images.py <fichier.pdf> <dossier de sortie> [--min <pixels>]
Sortie : un fichier par image retenue, et un relevé sur stdout.

Codes de sortie :
  0 — au moins une image extraite
  1 — aucune image de taille utile dans ce PDF
  2 — des images sont là mais aucune n'a pu être décodée
  3 — fichier introuvable ou illisible

Pourquoi ce script existe. Un document contient parfois, en annexe, une image
qui est **sa seule preuve** : une capture d'écran, une photo, un extrait de
relevé. Le texte du document ne fait que la légender.

Deux traitements la détruisent, et ce sont les deux que le plugin appliquait :

* **l'OCR l'aplatit.** Un moteur d'OCR est réglé pour une mise en page de
  document ; sur une capture d'interface il rend un flux linéaire où la
  disposition a disparu. Constaté : un horodatage de survol, affiché à côté
  d'une ligne surlignée, s'est retrouvé collé au texte d'un autre message et
  lu comme la date de la pièce. L'erreur portait sur un jour, sur l'unique
  preuve du document, et rien dans le texte produit ne la signalait ;
* **l'extraction de la couche de texte l'ignore.** Elle rend la légende et
  rien d'autre : « Annexe I : … envoyé le 03/07/2026 ». Le lecteur croit tenir
  la pièce, il ne tient que ce que son auteur en dit.

D'où ce script : sortir les images pour qu'un lecteur les **ouvre**. Une
capture se lit avec des yeux — c'est la seule voie qui ne suppose pas que la
légende dit vrai.

Ce qu'il retient. Les images au-dessus d'un seuil de surface, parce qu'un PDF
en contient des dizaines qui ne sont que des puces, des filets et des logos :
les extraire toutes noierait la pièce utile. Le seuil est réglable, et le
relevé dit toujours combien d'images ont été écartées — un écart annoncé n'est
pas un écart silencieux.

Bibliothèque standard seule : les flux `DCTDecode` SONT des fichiers JPEG et
s'écrivent tels quels ; les flux `FlateDecode` sont des pixels bruts, qu'on
enveloppe dans un PNG écrit à la main (en-tête, données, somme de contrôle).
"""
import binascii
import re
import struct
import sys
import zlib
from pathlib import Path

_MIN_PIXELS = 40_000          # ~200×200 : en dessous, c'est un ornement
_CHANNELS = {"DeviceRGB": 3, "DeviceGray": 1, "CalRGB": 3, "CalGray": 1, "DeviceCMYK": 4}


def _objects(raw: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(2)
            for m in re.finditer(rb"(\d+)\s+0\s+obj(.*?)endobj", raw, re.S)}


def _raw_stream(body: bytes) -> bytes:
    found = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
    return found.group(1) if found else b""


def _number(body: bytes, key: bytes, default: int = 0) -> int:
    found = re.search(re.escape(key) + rb"\s+(\d+)", body)
    return int(found.group(1)) if found else default


def _colour_channels(objects: dict[int, bytes], body: bytes) -> int:
    """Nombre de composantes par pixel, en suivant une éventuelle référence."""
    named = re.search(rb"/ColorSpace\s*/(\w+)", body)
    if named:
        return _CHANNELS.get(named.group(1).decode(), 0)
    # `/ColorSpace [/ICCBased 12 0 R]` : la forme TABLEAU, la plus répandue chez
    # les producteurs qui embarquent un profil colorimétrique. Ne chercher que la
    # référence nue ou le nom direct la manque, et l'image sort « non décodable »
    # alors qu'elle est parfaitement lisible.
    wrapped = re.search(rb"/ColorSpace\s*\[\s*/ICCBased\s+(\d+)\s+0\s+R", body)
    if wrapped:
        return _number(objects.get(int(wrapped.group(1)), b""), b"/N", 0)
    reference = re.search(rb"/ColorSpace\s+(\d+)\s+0\s+R", body)
    if reference:
        target = objects.get(int(reference.group(1)), b"")
        # /ICCBased déclare son nombre de composantes dans /N.
        return _number(target, b"/N", 0) or _CHANNELS.get(
            (re.search(rb"/(\w+)", target).group(1).decode() if re.search(rb"/(\w+)", target) else ""), 0)
    return 0


def _png(width: int, height: int, channels: int, depth: int, pixels: bytes) -> bytes | None:
    """Enveloppe des pixels bruts dans un PNG minimal, sans dépendance."""
    colour_type = {1: 0, 3: 2, 4: None}.get(channels)   # gris, RVB ; CMJN non couvert
    if colour_type is None or depth not in (8, 16):
        return None
    row = width * channels * depth // 8
    if len(pixels) < row * height:
        return None
    # Chaque ligne d'un PNG est précédée de son octet de filtre — ici « aucun ».
    body = b"".join(b"\x00" + pixels[y * row:(y + 1) * row] for y in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, depth, colour_type, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(body, 6)) + chunk(b"IEND", b""))


def extract(pdf_path: Path, out_directory: Path, minimum: int) -> tuple[list[str], int, int]:
    """(fichiers écrits, images écartées car trop petites, images non décodées)."""
    objects = _objects(pdf_path.read_bytes())
    written, ignored, failed = [], 0, 0
    out_directory.mkdir(parents=True, exist_ok=True)

    for number in sorted(objects):
        body = objects[number]
        if not re.search(rb"/Subtype\s*/Image", body):
            continue
        if re.search(rb"/ImageMask\s+true", body):
            continue        # un masque n'est pas une image, c'est un pochoir
        width, height = _number(body, b"/Width"), _number(body, b"/Height")
        if width * height < minimum:
            ignored += 1
            continue

        stream = _raw_stream(body)
        filters = [f.decode() for f in re.findall(rb"/(\w*Decode)", body)]
        stem = f"{pdf_path.stem}-image-{number:04d}"

        if "DCTDecode" in filters:                      # le flux EST un JPEG
            target = out_directory / f"{stem}.jpg"
            target.write_bytes(stream)
        elif "JPXDecode" in filters:                    # JPEG 2000, écrit tel quel
            target = out_directory / f"{stem}.jp2"
            target.write_bytes(stream)
        elif "FlateDecode" in filters:
            try:
                pixels = zlib.decompress(stream)
            except zlib.error:
                failed += 1
                continue
            image = _png(width, height, _colour_channels(objects, body),
                         _number(body, b"/BitsPerComponent", 8), pixels)
            if image is None:
                failed += 1
                continue
            target = out_directory / f"{stem}.png"
            target.write_bytes(image)
        else:
            failed += 1
            continue
        written.append(f"{target.name}  {width}×{height}")
    return written, ignored, failed


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage : python3 pdf-images.py <fichier.pdf> <dossier> [--min <pixels>]",
              file=sys.stderr)
        return 3
    pdf_path, out_directory = Path(sys.argv[1]), Path(sys.argv[2])
    if not pdf_path.is_file():
        print(f"ERREUR : fichier introuvable : {pdf_path}", file=sys.stderr)
        return 3
    minimum = _MIN_PIXELS
    if "--min" in sys.argv:
        try:
            minimum = int(sys.argv[sys.argv.index("--min") + 1])
        except (IndexError, ValueError):
            print("ERREUR : --min attend un nombre de pixels", file=sys.stderr)
            return 3

    try:
        written, ignored, failed = extract(pdf_path, out_directory, minimum)
    except OSError as problem:
        print(f"ERREUR : fichier illisible : {problem}", file=sys.stderr)
        return 3

    if written:
        print(f"{len(written)} image(s) extraite(s) → {out_directory}/")
        for line in written:
            print(f"  {line}")
        print("\nLes OUVRIR avec l'outil Read : une capture se lit avec des yeux. "
              "Ni l'OCR ni la couche de texte ne rendent une disposition — et c'est "
              "souvent la disposition qui porte le fait.")
    if ignored:
        print(f"\n{ignored} image(s) écartée(s), sous le seuil de {minimum} pixels "
              "(puces, filets, logos). Relancer avec --min plus bas pour les voir.",
              file=sys.stderr)
    if failed:
        print(f"{failed} image(s) présente(s) mais non décodable(s) sans dépendance "
              "— leur existence est un fait à signaler, pas à taire.", file=sys.stderr)

    if written:
        return 0
    return 2 if failed else 1


if __name__ == "__main__":
    sys.exit(main())
