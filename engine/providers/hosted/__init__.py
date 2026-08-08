# providers/hosted/__init__.py
"""Fournisseurs d'inférence hébergés chez un tiers (au token) — un dossier par fournisseur.

Chaque dossier contient un `provider.py` (sous-classe déclarative
d'OpenAICompatibleProvider) : la source unique de vérité du fournisseur.
La liste des fournisseurs est PROVIDER_REGISTRY dans providers/registry.py."""
