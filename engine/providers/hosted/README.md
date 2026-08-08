# providers/hosted — L'inférence hébergée chez un tiers (au token)

## Pourquoi ce dossier existe

Regroupe les fournisseurs dont **l'inférence tourne chez eux** : on paie (ou pas —
tiers gratuits aujourd'hui) à la requête, sans rien héberger. C'est le cœur du
modèle de coût du projet : l'usage d'apprentissage est intermittent, donc au token
gratuit. **Modulaire** : un dossier par fournisseur, sa classe
déclarative dans `provider.py` (résolue par convention — voir
`providers/README.md`).

Contenu, brièvement :

- `mistral/` — La Plateforme, tier Experiment (l'unique fournisseur :
  embeddings et OCR)
- `__init__.py` — docstring d'orientation, aucune logique

## Documentation détaillée par fichier

### `__init__.py`

Marqueur de package + docstring d'orientation. Aucune logique, aucun registre :
la résolution des fournisseurs est assurée par `providers/__init__.py`.
