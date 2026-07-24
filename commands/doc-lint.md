---
description: Vérifier la cohérence du vault Obsidian — contradictions, orphelins, INDEX, conflits Drive, inbox
---

# /doc-lint — maintenance du vault

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas d'échec : transmettre
   le message d'erreur tel quel et S'ARRÊTER. Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (règles de maintenance : sources immuables, LOG append-only, INDEX à jour).

## Vérifications — via sub-agent qui ne remonte que le rapport

Lancer un agent (type Explore, en avant-plan) chargé de produire un rapport
structuré sur `$VAULT`, avec ces cinq vérifications (la 6e se fait en contexte
principal après) :

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

6. **Cohérence vectorielle** (exécutée en contexte principal, PAS par le
   sub-agent) :
   - `.index/embeddings.jsonl` absent → « index sémantique jamais construit »
     (information ; remède : `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"`).
   - Présent → lire ses métadonnées (ligne 1 du fichier : provider, modèle,
     dimension, version) et les reporter. Diagnostic de suivi : comparer le
     `created_at` le plus récent du mapping aux dernières entrées `ingest` de
     `LOG.md` — des ingests postérieurs aux vecteurs = indexation non suivie
     (le verdict définitif reste le hash, jamais les dates).

## Rapport et corrections

1. Présenter le rapport par catégorie (vide = le dire aussi : « rien à signaler »).
2. Proposer les corrections : compléter `INDEX.md`, relier ou supprimer les
   orphelines, résoudre les conflits Drive (comparer les versions, garder la
   bonne, supprimer l'autre), rappeler les `> [!warning]` à trancher.
   Pour la cohérence vectorielle : proposer `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"`
   (coût API : uniquement les chunks au hash inconnu) — le rapport JSON fait foi :
   `embedded_chunks > 0` = vecteurs manquants/périmés qui viennent d'être
   réparés (notes éditées hors circuit) ; la réécriture complète purge par
   construction les vecteurs orphelins.
   Pour un conflit Drive sur `.index/` : si la ligne 1 (métadonnées) des deux
   fichiers est identique, fusion mécanique — union des lignes de chunks,
   dédoublonnage par `hash` (deux lignes de même hash sont identiques par
   construction), réécriture atomique, suppression du fichier de conflit ;
   sinon, garder `embeddings.jsonl`, supprimer le conflit, relancer
   `vault-index.sh`.
   N'appliquer QUE ce que l'utilisateur valide.
3. Ajouter en fin de `$VAULT/LOG.md` :
   `## [YYYY-MM-DD] lint | <n> problème(s) détecté(s), <m> corrigé(s)`
   suivi, si `vault-index.sh` a tourné, d'une ligne
   `vecteurs : <embedded_chunks> recalculés, <reused_chunks> réutilisés`.
