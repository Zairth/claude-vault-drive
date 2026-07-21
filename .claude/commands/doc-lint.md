---
description: Vérifier la cohérence du vault Obsidian — contradictions, orphelins, INDEX, conflits Drive, inbox
---

# /doc-lint — maintenance du vault

## Préambule obligatoire

1. Exécuter `bash .claude/scripts/vault-check.sh`. En cas d'échec : transmettre
   le message d'erreur tel quel et S'ARRÊTER. Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (règles de maintenance : sources immuables, LOG append-only, INDEX à jour).

## Vérifications — via sub-agent qui ne remonte que le rapport

Lancer un agent (type Explore, en avant-plan) chargé de produire un rapport
structuré sur `$VAULT`, avec ces cinq vérifications :

1. **Contradictions en souffrance** : chercher `> [!warning]` dans `wiki/` →
   lister fichier + extrait du callout.
2. **Pages orphelines** : pour chaque note de `wiki/concepts/` et `wiki/entites/`,
   chercher `[[<nom-du-fichier-sans-extension>` dans tout le vault (hors la note
   elle-même). Aucune occurrence = orpheline.
3. **Trous d'INDEX** : chaque note de `wiki/` doit apparaître dans `INDEX.md` —
   lister les absentes. Inversement, lister les entrées d'`INDEX.md` pointant
   vers des fichiers disparus.
4. **Fichiers de conflit Drive** : chercher les motifs `* (1).md`, `* (2).md` et
   `*conflit*` dans tout le vault → lister.
5. **inbox/ en attente** : lister les fichiers non ingérés (information, pas erreur).

## Rapport et corrections

1. Présenter le rapport par catégorie (vide = le dire aussi : « rien à signaler »).
2. Proposer les corrections : compléter `INDEX.md`, relier ou supprimer les
   orphelines, résoudre les conflits Drive (comparer les versions, garder la
   bonne, supprimer l'autre), rappeler les `> [!warning]` à trancher.
   N'appliquer QUE ce que l'utilisateur valide.
3. Ajouter en fin de `$VAULT/LOG.md` :
   `## [YYYY-MM-DD] lint | <n> problème(s) détecté(s), <m> corrigé(s)`.
