---
description: Initialiser le vault Obsidian du projet courant — config locale, .gitignore, arborescence, template
argument-hint: "/chemin/du/vault"
---

# /vault-init — initialiser le vault du projet courant

1. Si `$ARGUMENTS` est vide : demander le chemin du vault à l'utilisateur
   (ex. `/mnt/g/Mon Drive/<Section>/<MonVault>` pour un vault partagé via
   Google Drive, ou n'importe quel dossier local) et S'ARRÊTER.
2. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-init.sh" "$ARGUMENTS"`
   depuis la racine du projet.
3. Transmettre la sortie telle quelle (succès comme échec — le script est
   idempotent et ses erreurs sont explicites, ne rien improviser par-dessus).
4. Si `.claude/settings.local.json` vient d'être créé : rappeler qu'il faut
   relancer la session Claude Code pour charger la permission
   `additionalDirectories`, puis que `/doc-ingest`, `/doc-query` et
   `/doc-lint` seront prêts.
