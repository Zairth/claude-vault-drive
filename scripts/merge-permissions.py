#!/usr/bin/env python3
"""Fusionne les permissions du plugin dans le `.claude/settings.local.json` du projet.

Appelé par vault-init.sh, qui fournit trois variables d'environnement :
`SETTINGS_FILE`, `VAULT_PATH`, `SCRIPTS_GLOB`. Sort en 1 sans rien écrire si le
fichier existant est illisible ou d'une forme inattendue — ne jamais écraser
une configuration qu'on ne comprend pas.

Deux permissions, et pourquoi elles sont nécessaires :

- `additionalDirectories` : le vault vit **hors du projet**, souvent sur un
  disque synchronisé. Sans cette entrée, aucune commande ne peut le lire.
- `allow` sur les scripts du plugin : chaque commande `/doc-*` appelle
  plusieurs scripts. Refusés un par un par le classificateur de permissions,
  ils font **dégrader** la commande au lieu de l'arrêter — elle improvise un
  repli, et le résultat est plausible mais amoindri, ce qui est le pire des
  cas. Constaté : une recherche sémantique menée sur des index périmés parce
  que la réindexation avait été refusée.

Le joker sur le numéro de version (`.../<plugin>/*/scripts/*`) évite de refaire
l'opération à chaque mise à jour du plugin — le cache en crée un dossier par
version.

Le périmètre est volontairement étroit : ce dossier de scripts, rien d'autre.
Ils lisent le vault ; seul `vault-index.sh` y écrit, et uniquement dans les
`.index/`, qui sont des dérivés régénérables.

Fichier LOCAL et non versionné : ces chemins sont propres à la machine, et une
permission n'a pas à être imposée aux autres consommateurs du dépôt.
"""
import json
import os
import sys
from pathlib import Path


def main() -> int:
    settings_path = Path(os.environ["SETTINGS_FILE"])
    vault_path = os.environ["VAULT_PATH"]
    scripts_glob = os.environ.get("SCRIPTS_GLOB", "")

    settings = {}
    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 1
        if not isinstance(settings, dict):
            return 1

    permissions = settings.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        return 1

    directories = permissions.setdefault("additionalDirectories", [])
    if isinstance(directories, list) and vault_path not in directories:
        directories.append(vault_path)

    if scripts_glob:
        allowed = permissions.setdefault("allow", [])
        if isinstance(allowed, list):
            # bash ET python3 : le plugin livre les deux (pdf-text.py).
            for interpreter in ("bash", "python3"):
                rule = f"Bash({interpreter} {scripts_glob}:*)"
                if rule not in allowed:
                    allowed.append(rule)

    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
