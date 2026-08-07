#!/usr/bin/env python3
"""Relève les signatures électroniques d'un PDF, sans dépendance ni réseau.

Usage : python3 pdf-signatures.py <fichier.pdf>

Codes de sortie :
  0 — au moins une signature apposée ; le relevé est sur stdout
  1 — aucun champ de signature : la pièce n'est pas signée électroniquement
  2 — champ(s) de signature présent(s) mais vide(s) : préparée, non signée
  3 — fichier introuvable ou illisible

Pourquoi ce script existe. Une signature électronique ne s'écrit pas dans le
texte du document : elle vit dans une structure du fichier que ni l'extraction
de texte ni l'OCR ne rencontrent jamais. Un document signé peut donc n'afficher
que des noms dactylographiés sous des mentions de fonction — et se lire, pour
qui n'a que son texte, exactement comme un document non signé.

L'inversion est silencieuse et elle porte sur ce qui fait foi. Elle ne se
corrige pas en lisant mieux le texte : il n'y a rien à y lire. Elle se corrige
en allant regarder ailleurs, ce que fait ce script.

Ce qu'il établit, et ce qu'il n'établit pas. Il établit qu'une signature est
**présente**, par qui elle se déclare, à quelle date, et si elle **couvre tout
le fichier**. Il ne valide **aucune chaîne de certificats** : dire « signé »
sur la foi de ce relevé, c'est dire « le fichier porte une signature », jamais
« la signature est valide ». La distinction n'est pas une précaution de style
— une signature présente et invalide est précisément ce qu'un contrôle sérieux
doit pouvoir dire.

Ce que couvre une signature. Une signature ne porte que sur les octets que son
`/ByteRange` désigne. Tout ce qui a été ajouté au fichier après elle échappe à
sa garantie. Quand plusieurs signatures se succèdent, seules les dernières
couvrent l'ensemble — c'est normal. Ce qui ne l'est pas, c'est qu'**aucune** ne
couvre la fin du fichier : le document a alors été modifié après avoir été
signé, et le script le dit.
"""
import re
import sys
from pathlib import Path


def _objects(raw: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(2)
            for m in re.finditer(rb"(\d+)\s+0\s+obj(.*?)endobj", raw, re.S)}


def _string(body: bytes, key: bytes) -> str:
    """Valeur texte de `key`, littérale `(…)` ou hexadécimale `<…>`, UTF-16 compris."""
    found = re.search(re.escape(key) + rb"\s*(?:\(((?:\\.|[^()\\])*)\)|<([0-9A-Fa-f\s]*)>)",
                      body, re.S)
    if not found:
        return ""
    if found.group(1) is not None:
        data = re.sub(rb"\\(.)", rb"\1", found.group(1))
    else:
        digits = re.sub(rb"\s", b"", found.group(2))
        data = bytes.fromhex((digits + b"0" if len(digits) % 2 else digits).decode())
    if data[:2] in (b"\xfe\xff", b"\xff\xfe"):
        return data.decode("utf-16", "replace").strip("﻿")
    return data.decode("latin-1")


def _date(stamp: str) -> str:
    """`D:20260721122354Z` → `2026-07-21 12:23:54 UTC`, sinon la valeur brute."""
    found = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?(.*)", stamp)
    if not found:
        return stamp or "date absente"
    year, month, day, hour, minute, second, zone = found.groups()
    clock = f" {hour or '00'}:{minute or '00'}:{second or '00'}"
    zone = zone.strip("'")
    if zone in ("Z", ""):
        suffix = " UTC"
    else:
        suffix = f" UTC{zone[0]}{zone[1:].replace(chr(39), ':')}" if zone[:1] in "+-" else ""
    return f"{year}-{month}-{day}{clock}{suffix}"


def _coverage(raw: bytes) -> tuple[int, int]:
    """(dernier octet couvert par une signature, taille du fichier)."""
    covered = 0
    for found in re.finditer(rb"/ByteRange\s*\[([^\]]*)\]", raw):
        numbers = [int(n) for n in re.findall(rb"\d+", found.group(1))]
        if len(numbers) >= 4:
            covered = max(covered, numbers[2] + numbers[3])
    return covered, len(raw)


def survey(pdf_path: Path) -> tuple[list[dict], int]:
    """(signatures apposées, nombre de champs de signature restés vides)."""
    raw = pdf_path.read_bytes()
    objects = _objects(raw)

    signed, empty = [], 0
    for body in objects.values():
        if re.search(rb"/FT\s*/Sig", body) and not re.search(rb"/V\s+\d+\s+0\s+R", body):
            empty += 1

    for number, body in sorted(objects.items()):
        if not re.search(rb"/Type\s*/Sig[^n]", body) and b"/ByteRange" not in body:
            continue
        if b"/ByteRange" not in body:
            continue
        subfilter = re.search(rb"/SubFilter\s*/([\w.]+)", body)
        signed.append({
            "objet": number,
            "nom": _string(body, b"/Name"),
            "motif": _string(body, b"/Reason"),
            "lieu": _string(body, b"/Location"),
            "contact": _string(body, b"/ContactInfo"),
            "date": _date(_string(body, b"/M")),
            "format": subfilter.group(1).decode() if subfilter else "non déclaré",
        })
    return signed, empty


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage : python3 pdf-signatures.py <fichier.pdf>", file=sys.stderr)
        return 3
    pdf_path = Path(sys.argv[1])
    if not pdf_path.is_file():
        print(f"ERREUR : fichier introuvable : {pdf_path}", file=sys.stderr)
        return 3

    try:
        signed, empty = survey(pdf_path)
    except OSError as problem:
        print(f"ERREUR : fichier illisible : {problem}", file=sys.stderr)
        return 3

    if not signed:
        if empty:
            print(f"{empty} champ(s) de signature présent(s), aucun rempli — la pièce est "
                  "préparée pour signature mais n'est PAS signée.")
            return 2
        print("Aucun champ de signature dans ce fichier : la pièce ne porte pas de "
              "signature électronique. Une signature manuscrite scannée, elle, ne se "
              "voit qu'à l'image.", file=sys.stderr)
        return 1

    print(f"{len(signed)} signature(s) électronique(s) apposée(s) :")
    for index, entry in enumerate(signed, 1):
        who = entry["nom"] or entry["motif"] or "signataire non déclaré"
        print(f"  {index}. {who}")
        print(f"     date déclarée : {entry['date']}")
        print(f"     format        : {entry['format']}")
        for label, key in (("motif", "motif"), ("lieu", "lieu"), ("contact", "contact")):
            if entry[key] and entry[key] != who:
                print(f"     {label:<13} : {entry[key]}")
    if empty:
        print(f"\n{empty} champ(s) de signature resté(s) vide(s) : un emplacement ouvert et "
              "non rempli. À distinguer d'une partie à qui aucun emplacement n'a été ouvert.")

    covered, total = _coverage(pdf_path.read_bytes())
    if covered < total:
        print(f"\nATTENTION : aucune signature ne couvre la fin du fichier "
              f"({covered} octets couverts sur {total}, soit {total - covered} ajoutés "
              "ensuite). Le document a été modifié après avoir été signé.")

    print("\nCe relevé établit la PRÉSENCE des signatures et ce qu'elles déclarent. "
          "Il ne valide AUCUNE chaîne de certificats : ne jamais en conclure que la "
          "signature est valide, seulement qu'elle est là.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
