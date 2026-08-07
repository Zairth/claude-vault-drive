#!/usr/bin/env python3
"""Recompte les entrées datées d'une source dans la note qui en est issue.

Une série datée — relevé d'activité, journal, suivi de tickets, export d'outil,
toute suite d'entrées horodatées — est la seule forme de source qui porte sa
propre preuve d'intégralité : chaque entrée est ancrée par une date et une
heure, et cette ancre survit à la standardisation.

Ce qu'on vérifie, et pourquoi. Une source volumineuse est découpée en tranches
confiées à des lecteurs distincts, qui écrivent chacun leur part. Rien ne
garantit qu'elles ont toutes été rendues : une tranche perdue produit une note
parfaitement plausible, seulement plus courte, et aucun contrôle de forme ne le
voit — ni les wikilinks, ni le frontmatter, ni la taille, qu'on n'a rien à
quoi comparer. Le recomptage des ancres est le seul contrôle qui réponde à la
question « est-ce que tout y est ? » par autre chose qu'une impression.

Le script ne lit ni ne rapporte de contenu : uniquement des horodatages et des
comptes. Aucun appel réseau.

Toutes les pièces ne portent pas d'horodatage exploitable : un relevé rédigé en
prose date ses entrées en toutes lettres, un récapitulatif les numérote. Elles
portent alors une **autre** ancre — empreinte de commit, numéro de facture,
référence de ticket — et `--ancre` permet de recompter dessus. Sans cette
échappatoire, ces pièces sortent en « vérification sans objet », qui a
l'apparence d'un succès : c'est le pire résultat possible pour un contrôle
d'intégralité.

Usage :
    python3 verify-entries.py --source <f> [<f>…] --note <f> [<f>…]
    python3 verify-entries.py --source <f> [<f>…]          # recensement seul
    python3 verify-entries.py --ancre '<motif>' --source <f> --note <f>

Codes de sortie :
    0  la note porte toutes les ancres de la source
    1  des ancres manquent — elles sont listées
    2  la source ne porte aucune ancre exploitable : vérification sans objet
       (cas normal d'une source non datée, ce n'est pas un échec)
    3  erreur d'appel ou fichier illisible

Décalage horaire : une source en UTC rendue en heure locale ferait échouer la
comparaison en bloc, et le rapport annoncerait une perte totale là où rien n'est
perdu. Le script essaie les décalages entiers et retient celui qui explique le
mieux les correspondances, puis l'annonce.
"""
import itertools
import json
import re
import sys
from collections import Counter
from datetime import datetime, time, timedelta
from pathlib import Path

# Une ancre est ramenée à la minute : les formats de rendu abrègent souvent les
# secondes, et une comparaison plus fine ne mesurerait que ça.
_ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})[T ](\d{1,2}):(\d{2})")
_NUM = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})[,]?\s+(\d{1,2})[:h](\d{2})")
# Une série standardisée porte le plus souvent sa date en titre et l'heure
# seule sous chaque entrée : les deux moitiés doivent se rejoindre.
_ISO_DAY = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})(?![\d:T-])")
_NUM_DAY = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})(?![\d:/.-])")
_HOUR = re.compile(r"(\d{1,2})[:h](\d{2})(?!\d)")
# Ponctuation qui peut précéder une ancre en tête de ligne : puce, titre, gras,
# crochet d'export. Au-delà, la date est citée dans le corps d'une entrée et
# n'en ouvre pas une nouvelle.
_LEAD = " \t[(*_->#|"
_LEAD_MAX = 6

# Clés portant l'horodatage d'une entrée, par ordre de préférence. Une seule
# ancre par objet : `edited_*` et consorts dateraient une retouche, pas l'entrée.
_TS_KEYS = ("timestamp", "datetime", "created_at", "createdat", "date",
            "sent_at", "sentat", "published_at", "time", "ts")

_MAX_LISTED = 40


def _mk(year, month, day, hour, minute):
    if year < 100:
        year += 2000
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


def _parse_iso(value):
    m = _ISO.search(value)
    if not m:
        return None
    y, mo, d, h, mi = (int(g) for g in m.groups())
    return _mk(y, mo, d, h, mi)


def _month_first(text):
    """Ordre des composants d'une date numérique. Un premier terme > 12 tranche
    pour le jour d'abord ; à défaut on suppose le jour d'abord, convention
    majoritaire hors Amérique du Nord."""
    pairs = [(int(m.group(1)), int(m.group(2)))
             for m in itertools.chain(_NUM.finditer(text), _NUM_DAY.finditer(text))]
    return bool(pairs) and not any(a > 12 for a, _ in pairs) \
        and any(b > 12 for _, b in pairs)


def _anchors_from_text(text):
    """Ancres d'un texte, ligne à ligne.

    Une entrée ouvre sa ligne : une date citée dans le corps d'une autre entrée
    n'est pas une entrée de plus, et la compter ferait conclure à une perte qui
    n'existe pas. Deux formes se rencontrent, souvent dans le même fichier :
    l'horodatage complet en tête de ligne, et — c'est la forme que produit la
    standardisation d'une série — la **date en titre**, l'**heure seule** sous
    chaque entrée. La date courante est donc retenue de ligne en ligne, et
    complète les heures nues qui la suivent.

    Les deux formes ne coexistent pas : un fichier date chaque entrée, ou date
    ses titres. Les heures nues ne sont donc retenues que si aucun horodatage
    complet n'a été trouvé — sans quoi un horaire cité dans le corps d'une
    entrée (« rendez-vous 09h30 ») compterait pour une entrée de plus, et la
    source paraîtrait plus grosse que la note. Un fichier qui mélangerait les
    deux formes serait sous-compté, donc signalé : une alerte à instruire vaut
    mieux qu'une lacune qui passe."""
    month_first = _month_first(text)
    anchors, carried, current_day = [], [], None

    for line in text.splitlines():
        body, prefix = line, ""
        for _ in range(_LEAD_MAX):
            if body[:1] in _LEAD and body[:1] != "":
                prefix, body = prefix + body[:1], body[1:]
            else:
                break
        if not body:
            continue
        is_heading = "#" in prefix

        match = _ISO.match(body)
        if match:
            anchor = _mk(*(int(g) for g in match.groups()))
            if anchor:
                anchors.append(anchor)
                current_day = anchor.date()
            continue

        match = _NUM.match(body)
        if match:
            a, b, year, hour, minute = (int(g) for g in match.groups())
            day, month = (b, a) if month_first else (a, b)
            anchor = _mk(year, month, day, hour, minute)
            if anchor:
                anchors.append(anchor)
                current_day = anchor.date()
            continue

        # Date sans heure : un titre de journée, ou une entrée dont la source
        # n'affichait pas l'heure. Ce qui suit sur la ligne tranche — un titre
        # ne porte que sa date, une entrée porte son texte.
        match = _ISO_DAY.match(body)
        if not match:
            match = _NUM_DAY.match(body)
            if match:
                a, b, year = (int(g) for g in match.groups())
                day, month = (b, a) if month_first else (a, b)
                day_only = _mk(year, month, day, 0, 0)
            else:
                day_only = None
        else:
            day_only = _mk(*(int(g) for g in match.groups()), 0, 0)

        if match:
            if day_only:
                current_day = day_only.date()
                rest = body[match.end():].strip(" \t—–-:·|")
                if rest and not is_heading:
                    anchors.append(day_only)
            continue

        match = _HOUR.match(body)
        if match and current_day is not None:
            hour, minute = int(match.group(1)), int(match.group(2))
            if hour < 24 and minute < 60:
                carried.append(datetime.combine(current_day,
                                                time(hour=hour, minute=minute)))

    if anchors:
        return anchors, "horodatage complet par entrée"
    if carried:
        return carried, "date en titre + heure seule"
    return [], "aucune"


def _anchor_of_object(node):
    lowered = {k.lower(): v for k, v in node.items()}
    for key in _TS_KEYS:
        value = lowered.get(key)
        if isinstance(value, str):
            anchor = _parse_iso(value) or next(iter(_anchors_from_text(value)[0]), None)
            if anchor:
                return anchor
    return None


def _anchors_from_json(data):
    """Une ancre par entrée. Un export d'API est presque toujours une liste
    d'objets datés : dans ce cas on ne descend pas dans leurs sous-objets — les
    horodatages qu'ils portent (retouche, contenu joint, ressource citée)
    datent un détail de l'entrée, pas une entrée de plus."""
    if isinstance(data, list) and any(isinstance(item, dict) for item in data):
        return [a for a in (_anchor_of_object(item) for item in data
                            if isinstance(item, dict)) if a], "entrées JSON datées"

    found = []

    def walk(node):
        if isinstance(node, dict):
            anchor = _anchor_of_object(node)
            if anchor:
                found.append(anchor)
                return
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return found, "entrées JSON datées"


def anchors_of(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        print(f"illisible : {path} ({error})", file=sys.stderr)
        raise SystemExit(3)
    if path.suffix.lower() == ".json":
        try:
            return _anchors_from_json(json.loads(text))
        except json.JSONDecodeError:
            pass  # JSON malformé ou par lignes : le texte reste exploitable
    return _anchors_from_text(text)


def _best_offset(source, note):
    """Décalage horaire entier qui explique le mieux les correspondances."""
    best = (0, -1)
    for hours in range(-12, 15):
        shifted = Counter(a + timedelta(hours=hours) for a in source)
        common = sum((shifted & note).values())
        if common > best[1]:
            best = (hours, common)
    return best


def custom_anchors(path, pattern):
    """Ancres arbitraires : chaque correspondance compte pour une entrée.
    Le motif tient lieu d'horodatage quand la pièce n'en porte pas
    d'exploitable — l'ordre chronologique n'a alors plus de sens, seul le
    dénombrement en garde un."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        print(f"illisible : {path} ({error})", file=sys.stderr)
        raise SystemExit(3)
    return [m.group(0).lower() for m in pattern.finditer(text)]


def _compare_custom(sources, notes, pattern):
    src, note = Counter(), Counter()
    for path in sources:
        found = custom_anchors(path, pattern)
        src.update(found)
        print(f"source  {path.name:<44} {len(found):>6} correspondances")
    if not src:
        print("\nLe motif ne correspond à rien dans la source — motif à revoir.")
        return 2
    print(f"\nSource : {len(src)} ancres distinctes")
    if not notes:
        return 0
    for path in notes:
        found = custom_anchors(path, pattern)
        note.update(found)
        print(f"note    {path.name:<44} {len(found):>6} correspondances")
    missing = src - note
    extra = note - src
    print(f"\nRetrouvées : {sum((src & note).values())}/{sum(src.values())}")
    if extra:
        print(f"EN TROP dans la note : {sum(extra.values())} "
              "(ancre absente de la source — recopie fautive ?)")
        for a in sorted(extra)[:_MAX_LISTED]:
            print(f"  {a}")
    if not missing:
        print("Intégralité vérifiée : aucune ancre manquante.")
        return 1 if extra else 0
    print(f"MANQUANTES : {sum(missing.values())} ancres")
    for a in sorted(missing)[:_MAX_LISTED]:
        print(f"  {a}")
    return 1


def main(argv):
    sources, notes, bucket, pattern = [], [], None, None
    expect_pattern = False
    for arg in argv:
        if expect_pattern:
            try:
                pattern = re.compile(arg, re.IGNORECASE)
            except re.error as error:
                print(f"motif invalide : {error}", file=sys.stderr)
                return 3
            expect_pattern = False
        elif arg == "--ancre":
            expect_pattern, bucket = True, None
        elif arg == "--source":
            bucket = sources
        elif arg == "--note":
            bucket = notes
        elif bucket is None:
            print(__doc__.split("Usage :")[1].split("Codes")[0].strip(),
                  file=sys.stderr)
            return 3
        else:
            bucket.append(Path(arg))
    if expect_pattern:
        print("--ancre attend un motif", file=sys.stderr)
        return 3
    if not sources:
        print("aucune source : --source <fichier> [<fichier>…]", file=sys.stderr)
        return 3

    if pattern is not None:
        return _compare_custom(sources, notes, pattern)

    source_anchors = []
    for path in sources:
        found, _ = anchors_of(path)
        source_anchors += found
        print(f"source  {path.name:<44} {len(found):>6} entrées datées")

    if not source_anchors:
        print("\nAucune ancre datée dans la source — vérification sans objet.")
        print("  Si la pièce EST une série, elle porte une autre ancre "
              "(empreinte, numéro, référence) : la donner en `--ancre '<motif>'`.")
        print("  Sinon — un contrat, un rapport — il n'y a rien à recompter, "
              "et ce code n'est pas un succès : c'est une absence de contrôle.")
        return 2

    span = f"{min(source_anchors):%Y-%m-%d} → {max(source_anchors):%Y-%m-%d}"
    print(f"\nSource : {len(source_anchors)} entrées datées, {span}")

    if not notes:
        return 0

    note_anchors, note_forms, disordered = [], set(), []
    for path in notes:
        found, form = anchors_of(path)
        # Ordre non chronologique : un CONSTAT, jamais un verdict. La note
        # doit suivre l'ordre de sa pièce, et une pièce peut être
        # antichronologique par nature — un journal de versions, un export qui
        # ouvre sur son avis de chiffrement. Trancher suppose d'ouvrir
        # l'archive, ce que ce script ne fait pas. Il signale, il n'accuse pas.
        if found != sorted(found):
            inversions = sum(1 for a, b in zip(found, found[1:]) if b < a)
            direction = "antichronologique" if found == sorted(found, reverse=True) \
                else f"{inversions} rupture(s) d'ordre"
            disordered.append((path.name, direction))
        note_anchors += found
        note_forms.add(form)
        print(f"note    {path.name:<44} {len(found):>6} entrées datées"
              f"   [{form}]")

    # La forme prescrite porte la date complète sur chaque entrée. Toute autre
    # a été reconstituée par déduction : le compte reste bon, mais il repose
    # sur une lecture du format et non sur une lecture de la note.
    if note_forms - {"horodatage complet par entrée", "entrées JSON datées"}:
        print("⚠ note hors forme prescrite (date complète attendue sur chaque "
              "entrée) : comptage déduit, à confirmer avant de conclure")

    for name, direction in disordered:
        print(f"· {name} : entrées non chronologiques — {direction}. "
              "Constat, pas défaut : la note doit suivre l'ordre de SA PIÈCE, "
              "qui peut être antichronologique. À comparer à l'archive.")

    source_count = Counter(source_anchors)
    note_count = Counter(note_anchors)
    offset, common = _best_offset(source_anchors, note_count)

    shifted = Counter({a + timedelta(hours=offset): n
                       for a, n in source_count.items()})
    missing = shifted - note_count

    total = len(source_anchors)
    print(f"\nRetrouvées : {common}/{total}"
          + (f"  (décalage horaire retenu : {offset:+d} h)" if offset else ""))

    if not missing:
        print("Intégralité vérifiée : aucune entrée manquante.")
        return 0

    absent = sorted(missing.elements())
    print(f"MANQUANTES : {len(absent)} entrées")
    for anchor in absent[:_MAX_LISTED]:
        print(f"  {anchor:%Y-%m-%d %H:%M}")
    if len(absent) > _MAX_LISTED:
        print(f"  … et {len(absent) - _MAX_LISTED} autres")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
