# providers/hosted/mistral — Mistral La Plateforme

## Pourquoi ce dossier existe

Le dossier du fournisseur Mistral (tier Experiment gratuit, l'unique fournisseur
du registre) : son identité, son endpoint et ses modèles vivent ici, et uniquement
ici — y compris sa capacité OCR (`/ocr`), propriétaire Mistral, hors protocole
OpenAI. Clé : `MISTRAL_API_KEY` (userConfig du plugin) ; changer de modèle =
éditer la classe.

Contenu, brièvement :

- `provider.py` — `MistralProvider` (déclaration + méthode `ocr()`) et `OcrResponse`
- `__init__.py` — marqueur de package (en-tête de chemin uniquement)

## Documentation détaillée par fichier

### `provider.py`

`MistralProvider(OpenAICompatibleProvider)` : attributs purement déclaratifs
(`name`, `base_url`, `default_embedding_model` — `mistral-embed`,
1024 dimensions) — le comportement embed vient de `providers/base.py`.

S'y ajoute la capacité OCR, seule mécanique propre à ce fournisseur :
`ocr(document_payload)` POste `{model, document}` sur `/ocr`
(`mistral-ocr-latest`, timeout 300 s) via la `_post_json` héritée (DRY : auth,
erreurs, Retry-After déjà factorisés) et retourne `OcrResponse`
(`page_markdowns` triés par `index`, `model`, `pages_processed`). Hors du contrat
`LLMProvider` : jamais de fallback sur l'OCR — l'appelant
(`services/document_ocr`) épingle CE fournisseur, comme `semantic_index` pour les
embeddings. `OcrResponse` vit ici et pas dans `schema.py` : ce schéma-là est le
contrat agnostique des fournisseurs interchangeables, l'OCR n'existe que chez Mistral.
