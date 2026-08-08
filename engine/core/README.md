# core — Socle transversal du projet

## Pourquoi ce dossier existe

Tout le projet a besoin de la même chose : une configuration typée. `core` la
centralise pour qu'il n'existe qu'**une seule source de vérité** (DRY) : aucun
module ne lit l'environnement lui-même, tout le monde importe d'ici. `core` ne
dépend d'aucun autre dossier du projet (couche la plus basse).

Contenu, brièvement :

- `settings.py` — les Settings pydantic, uniques lecteurs de l'environnement

## Documentation détaillée par fichier

### `settings.py`

`Settings` (pydantic-settings) expose des champs typés : la clé du fournisseur
LLM gratuit (chaque classe provider référence EXPLICITEMENT son champ :
`api_key = settings.x_api_key`). Tout arrive en variables d'environnement :
`userConfig` du plugin en production, variables shell pour un test en dev. Un validateur
`mode="before"` normalise les valeurs vides (`""`) ou non substituées
(`"${user_config...}"`) en absentes — la protection vaut pour TOUS les chemins
d'accès à la config, pas seulement le point d'entrée du plugin. Les secrets sont
des `SecretStr` : ils ne fuitent pas dans les repr. L'instance module-level
`settings` est le singleton du projet.
