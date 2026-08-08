# services/document_ocr — Documents (PDF, scans) → markdown (OCR Mistral)

## Pourquoi ce dossier existe

Convertit n'importe quel PDF ou image scannée en fichier markdown, via le modèle
OCR de Mistral (`mistral-ocr-latest`, inclus dans le tier Experiment gratuit).
Sortie pensée pour le reste de la boîte à outils : le `.md` produit est
directement indexable par `services/semantic_index` ou injectable dans un prompt.

**Le contrat central — fournisseur épinglé, jamais de fallback** : l'OCR n'existe
pas dans le protocole OpenAI et un seul fournisseur le propose
(Mistral, endpoint `/ocr` propriétaire). Le fournisseur est donc ÉPINGLÉ :
mistral indisponible (clé absente, quota, réseau) → `DocumentOcrError` explicite
— même philosophie que les embeddings de `semantic_index`.

**DRY** : l'appel HTTP passe par `MistralProvider.ocr()`
(`providers/hosted/mistral/provider.py`) qui réutilise la mécanique
`_post_json` de `providers/base.py` — auth, erreurs normalisées et
Retry-After déjà factorisés, rien n'est dupliqué ici. Le document part en data URI
base64 (aucun upload préalable, rien de stocké chez Mistral) ; limite API : 50 Mo.

Point d'entrée : l'outil MCP `ocr_convert` (document, output) du plugin.

La sortie est écrasée si elle existe : relancer = régénérer (la source fait foi,
le markdown n'est qu'une projection). Les figures du document ne sont pas
extraites : le markdown ne sort donc **jamais** avec une syntaxe d'image — chaque
`![...](...)` de l'OCR est remplacé par un marqueur textuel inerte
(`[figure 1 — non extraite]`). Pourquoi : le `.md` finit dans un vault Obsidian,
qui indexe tout ; une référence vers un fichier jamais produit y devient un nœud
fantôme du graphe, qu'un clic transforme en note vide. Extraire réellement les
sous-images reste la piste d'extension si le besoin apparaît.

Contenu, brièvement :

- `__init__.py` — la façade publique (`convert_to_markdown`, `OcrConversionReport`, `DocumentOcrError`)
- `service.py` — orchestration : lecture/encodage du fichier, appel OCR épinglé, écriture du `.md`
- `errors.py` — `DocumentOcrError`, l'échec explicite du module

## Documentation détaillée par fichier

### `__init__.py`

La façade : ré-exporte `convert_to_markdown`, `OcrConversionReport` et
`DocumentOcrError`. Les appelants importent d'ici et de nulle part ailleurs.

### `service.py`

`convert_to_markdown(document_path, output_path=None)` : vérifie le fichier
(existence, taille ≤ 50 Mo — échec local AVANT tout appel réseau), construit le
bloc `document` du protocole OCR Mistral (data URI base64 ; `.pdf` →
`document_url`, `.png`/`.jpg`/`.jpeg`/`.avif` → `image_url`), vérifie que mistral
est configuré (`configuration_issue()` — zéro appel réseau condamné), appelle
`MistralProvider.ocr()`, concatène le markdown des pages (ordre du document),
remplace les références d'images par des marqueurs numérotés
(`_replace_image_references` — aucune référence pendante ne sort du module) et
l'écrit — défaut : `<document>.md` à côté de la source (dossiers de destination
créés au besoin). Retourne `OcrConversionReport` (`source_path`, `output_path`,
`pages` — le coût API réel, l'OCR se facture à la page —, `model`). Tout échec
est traduit en `DocumentOcrError` avec la marche à suivre (pas de fallback).

### `errors.py`

`DocumentOcrError`, unique exception du module : ce module échoue toujours
explicitement, le message porte la raison humaine et la marche à suivre.
