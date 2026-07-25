---
description: Vérifier la cohérence du vault Obsidian — contradictions, orphelins, INDEX, conflits Drive, inbox
context: fork
agent: Explore
background: false
---

# /doc-lint — maintenance du vault

Cette commande s'exécute en fork : tout ce fichier s'adresse au sub-agent.
Tu es un sub-agent isolé — l'agent principal ne voit que ton rapport final.
Tu ne modifies RIEN dans le vault : les corrections sont appliquées par
l'agent principal, après validation de l'utilisateur, à partir de ton rapport.

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas
   d'échec : ton rapport final est le message d'erreur tel quel — S'ARRÊTER.
   Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (règles de maintenance : sources immuables, LOG append-only, INDEX à jour).

## Vérifications (les sept)

1. **Contradictions en souffrance** : chercher `> [!warning]` dans `wiki/` →
   lister fichier + extrait du callout.
2. **Pages orphelines** : pour chaque note de `wiki/concepts/` et `wiki/entites/`,
   chercher `[[<nom-du-fichier-sans-extension>` dans tout le vault (hors la note
   elle-même). Aucune occurrence = orpheline.
3. **Trous d'INDEX** : chaque note de `wiki/` doit apparaître dans `INDEX.md` —
   lister les absentes. Inversement, lister les entrées d'`INDEX.md` pointant
   vers des fichiers disparus.
4. **Fichiers de conflit Drive** : chercher les motifs `* (1).md`, `* (2).md` et
   `*conflit*` dans tout le vault → lister. Chercher aussi dans `.index/` les
   doublons du mapping vectoriel (`embeddings (1).jsonl`, `*conflit*`) → lister
   séparément (résolution spécifique, voir corrections).
5. **inbox/ en attente** : lister les fichiers non ingérés (information, pas erreur).
6. **Frontmatter obligatoire** (modèle de note d'`INSTRUCTIONS-CLAUDE.md`) :
   pour chaque note de `wiki/`, vérifier la présence de `type` + `date` +
   `auteur`, plus `origine` pour les sources et `question` pour les synthèses
   → lister les notes non conformes avec leurs propriétés manquantes.
7. **Cohérence vectorielle** :
   - `.index/embeddings.jsonl` absent → « index sémantique jamais construit »
     (information ; remède : la réindexation décrite dans les corrections).
   - Présent → lire ses métadonnées (outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_info` avec
     `directory: $VAULT` — purement local, zéro quota — sinon ligne 1 du
     fichier : provider, modèle, dimension, version) et les reporter.
     Diagnostic de suivi : comparer le `created_at` le plus récent du mapping
     aux dernières entrées `ingest` de `LOG.md` — des ingests postérieurs aux
     vecteurs = indexation non suivie (le verdict définitif reste le hash,
     jamais les dates).

## Rapport final (ton retour à l'agent principal)

1. Le chemin `$VAULT` résolu, écrit en clair (l'agent principal ne connaît pas
   la sortie de vault-check).
2. Le rapport par catégorie (vide = le dire aussi : « rien à signaler »).
3. Un bloc `Pour l'agent principal` — proposer les corrections à l'utilisateur
   et n'appliquer QUE ce qu'il valide :
   - compléter `INDEX.md`, relier ou supprimer les orphelines, résoudre les
     conflits Drive (comparer les versions, garder la bonne, supprimer
     l'autre), rappeler les `> [!warning]` à trancher.
   - Pour les frontmatters non conformes : proposer une valeur déduite du
     contenu de la note ou de `LOG.md` (`date` : à défaut, la première mention
     de la note dans le LOG) — jamais de valeur inventée sans le signaler.
   - Pour la cohérence vectorielle : proposer la réindexation — outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
     `directory: $VAULT` **explicite** (jamais son défaut `VAULT_PATH`, global)
     si le plugin agentic-toolbox est installé, sinon
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"` (clone + venv)
     (coût API : uniquement les chunks au hash inconnu) — le rapport JSON fait
     foi : `embedded_chunks > 0` = vecteurs manquants/périmés qui viennent
     d'être réparés (notes éditées hors circuit) ; la réécriture complète
     purge par construction les vecteurs orphelins.
   - Pour un conflit Drive sur `.index/` : si la ligne 1 (métadonnées) des
     deux fichiers est identique, fusion mécanique — union des lignes de
     chunks, dédoublonnage par `hash` (deux lignes de même hash sont
     identiques par construction), réécriture atomique, suppression du fichier
     de conflit ; sinon, garder `embeddings.jsonl`, supprimer le conflit,
     relancer la réindexation.
   - Une fois les corrections traitées, ajouter en fin de `$VAULT/LOG.md` :
     `## [YYYY-MM-DD] lint | <n> problème(s) détecté(s), <m> corrigé(s)`
     suivi, si la réindexation a tourné, d'une ligne
     `vecteurs : <embedded_chunks> recalculés, <reused_chunks> réutilisés`.
