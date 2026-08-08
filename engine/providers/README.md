# providers — Le « cerveau » LLM : protocole, registre et fournisseurs

## Pourquoi ce dossier existe

Tout ce qui permet au projet de parler à un LLM vit ici, en un seul package : le
protocole OpenAI-compatible (écrit une fois), le registre, et les fournisseurs
concrets — **un dossier par fournisseur** comme repère visuel, tous dans
`hosted/<name>/` (l'inférence tourne chez un tiers, au token). Aujourd'hui un
seul fournisseur : Mistral (embeddings, OCR — tier gratuit) ; la structure
registre + héritage reste le chemin d'ajout d'un fournisseur.

**DRY** : UNE seule liste de fournisseurs — `PROVIDER_REGISTRY` (`registry.py`) :
imports statiques, une seule liste, dans le code. Ajouter un fournisseur hébergé
= un dossier + un `provider.py` de 3 lignes + son import et son entrée dans le
registre. **Agnostique** : l'appelant résout un fournisseur par son nom via la
façade et ne manipule que les types de `schema.py`.

**Embeddings — jamais de fallback** : des vecteurs produits par deux modèles
différents ne sont pas comparables. L'appelant épingle UN fournisseur via
`resolve_embedding_provider(name)` (`registry.py` — LE point unique du contrat :
fournisseur connu, OpenAI-compatible et `embedding_configuration_issue()` vide,
sinon `LLMError` explicite) et échoue explicitement s'il est indisponible
(consommateur type : `services/semantic_index/`).

Contenu, brièvement :

- `__init__.py` — la façade publique (`resolve_embedding_provider`, ...) + recette d'ajout
- `base.py` — contrat `LLMProvider` + mécanique HTTP OpenAI-compatible (une seule fois)
- `schema.py` — le type agnostique échangé avec l'appelant (`EmbeddingResponse`)
- `errors.py` — hiérarchie d'exceptions du module
- `registry.py` — le registre des fournisseurs + résolution par nom + diagnostic
- `hosted/` — les fournisseurs (voir leurs README)

## Documentation détaillée par fichier

### `__init__.py`

La façade : ré-exporte `resolve_embedding_provider`, `describe_providers`,
`PROVIDER_REGISTRY`, `EmbeddingResponse` et les exceptions. Les appelants
importent d'ici et de nulle part ailleurs. Son docstring porte la recette
d'ajout d'un fournisseur.

### `base.py`

Deux niveaux d'héritage. `LLMProvider` (ABC) : le contrat minimal —
`configuration_issue()` (None si appelable, sinon la raison humaine : une seule
méthode porte le booléen ET son explication). `OpenAICompatibleProvider` :
l'unique implémentation HTTP (`_post_json` — auth Bearer, normalisation des
erreurs, Retry-After compris — partagée par `embed()` et l'OCR Mistral), points
de variation isolés dans des méthodes `resolve_*` surchargeables ; chaque classe
concrète référence EXPLICITEMENT son champ de clé (`api_key = settings.x_api_key`).

`embed()` (endpoint `/embeddings`, appel par lots) : pas de fallback possible
sur les embeddings, l'appelant choisit sa classe concrète —
`default_embedding_model` (None par défaut) et `embedding_configuration_issue()`
disent qui le supporte ; le modèle d'embedding reste ÉPINGLÉ, jamais résolu live
(contrat des index). Les propriétés du protocole (chemin `/embeddings`, timeout)
sont des attributs de classe surchargeables — pas de fichier de constantes.

### `schema.py`

`EmbeddingResponse` (vecteurs ordonnés + propriété `dimension` — LA valeur à
épingler avec le modèle dans les métadonnées d'un index). L'appelant ne dépend
que de ce type.

### `errors.py`

`LLMError` (base) → `ProviderRequestError` (échec d'UN fournisseur : porte
`status_code`, `detail` et `retry_after_seconds`).

### `registry.py`

`PROVIDER_REGISTRY` : LA liste des fournisseurs — imports statiques, une seule
liste, dans le code. `resolve_embedding_provider(name)` : LE fournisseur épinglé
pour l'embedding, appelable, sinon `LLMError` explicite — point unique du
non-fallback, consommé par `services/semantic_index`. `describe_providers()` :
état de chaque fournisseur (pour l'outil MCP `llm_check`), zéro réseau.
