---
description: Mesurer la qualité de recherche du vault — banc de questions de référence (BENCH.md), score mécanique comparable d'un run à l'autre
argument-hint: "[creer]"
context: fork
agent: Explore
background: false
---

# /doc-bench — le mètre étalon de la recherche

Cette commande s'exécute en fork : tout ce fichier s'adresse au sub-agent.
Tu es un sub-agent isolé — l'agent principal ne voit que ton rapport final.
Tu ne modifies RIEN dans le vault : les écritures (BENCH.md, LOG) sont
appliquées par l'agent principal, après validation de l'utilisateur.

Le banc mesure la **couche de récupération seule** — celle que des évolutions
du moteur (fusion scorée, décroissance) modifieraient — jamais la qualité des
réponses rédigées : un run est mécanique et reproductible (aucun jugement dans
le score), et coûte une vectorisation API par question.

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas
   d'échec : ton rapport final est le message d'erreur tel quel — S'ARRÊTER.
   Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer.

## Deux modes

- `$ARGUMENTS` contient `creer`, OU `$VAULT/BENCH.md` est absent → **création** ;
- sinon → **mesure**.

## Mode création — proposer le banc

1. Lire `INDEX.md` et parcourir `wiki/` (au moins les frontmatters
   `description`) pour cartographier ce que le vault sait.
2. Rédiger **~20 questions** (vault petit → réduire : viser une question pour
   2-3 notes, minimum 5) couvrant, en les mélangeant :
   - des factuelles dont la réponse vit dans une note de `sources/` ;
   - des transversales (plusieurs notes, syntheses) ;
   - des centrées sur un concept ou une entité ;
   - et plusieurs formulées en **synonymes** — jamais les mots exacts des
     notes : ce sont elles qui départagent la sémantique de grep.
3. Pour chaque question : les **notes attendues** (1 à 3, wikilinks) — celles
   qu'une bonne recherche doit remonter.
4. Rapport : le banc complet en clair, et un bloc `Pour l'agent principal` —
   faire valider les questions à l'utilisateur (retirer/reformuler/ajouter),
   puis écrire `$VAULT/BENCH.md` au format ci-dessous et ajouter en fin de
   `$VAULT/LOG/YYYY-MM-DD.md` (fichier du jour, créé au besoin) :
   `## [YYYY-MM-DD] bench | banc créé : <n> questions`. Un `BENCH.md`
   existant (relance avec `creer`) → proposer complément ou refonte, jamais
   d'écrasement sans validation.

Format de `BENCH.md` (racine du vault — hors index sémantique par
construction, jamais modifié par les runs de mesure) :

```markdown
# BENCH — questions de référence

Banc de mesure de la recherche (/doc-bench). Figé entre deux validations :
les runs le lisent, ne l'écrivent jamais.

## Q1 — <la question>
attendu : [[note-a]], [[note-b]]
```

## Mode mesure — scorer la récupération

1. **Réindexation incrémentale d'abord** (mesurer sur un index à jour) —
   outil MCP `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
   `directory: $VAULT/wiki` **explicite**, sinon
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"`. Moteur indisponible
   → ouvrir le rapport par « ⚠ sémantique indisponible (<raison>) — score
   grep seul » et sauter les mesures sémantiques.
2. Parser `BENCH.md` (questions + attendus). Une attendue pointant vers une
   note disparue → « banc à mettre à jour », question **exclue du score**
   (le signaler, ne jamais la compter en échec).
3. Pour chaque question, mécaniquement :
   - **sémantique** : `semantic_search` top 5 (`question` telle quelle,
     `directory: $VAULT/wiki` explicite) → rang de la première attendue
     (1-5, ou absente) ;
   - **grep** : les mots pleins de la question (sans articles ni mots-outils)
     sur `wiki/` → attendues touchées ou non.
4. **Scores** (mêmes définitions à chaque run — c'est ce qui les rend
   comparables) :
   - `sémantique@5` : x/n questions avec ≥ 1 attendue dans le top 5, et le
     rang moyen des touchées ;
   - `grep` : x/n questions avec ≥ 1 attendue touchée ;
   - `couverture` : x/n questions dont TOUTES les attendues sont trouvées
     (sémantique et grep confondus).

## Rapport final (ton retour à l'agent principal)

1. Le chemin `$VAULT` résolu, écrit en clair.
2. L'avertissement « sémantique indisponible », le cas échéant.
3. La ligne de score :
   `sémantique@5 x/n (rang moyen r) · grep x/n · couverture x/n`.
4. Le tableau par question : rang sémantique, grep, verdict — et pour chaque
   question en échec, ce que la recherche a renvoyé **à la place** (c'est le
   carburant des évolutions du moteur : fusion scorée, décroissance).
5. Les attendues disparues (« banc à mettre à jour »), le cas échéant.
6. Bloc `Pour l'agent principal` : proposer d'ajouter en fin de
   `$VAULT/LOG/YYYY-MM-DD.md` (fichier du jour, créé au besoin) :
   `## [YYYY-MM-DD] bench | sémantique@5 x/n · grep x/n · couverture x/n`
   suivi d'une ligne listant les questions en échec. Rien d'autre à écrire —
   un run ne modifie jamais `BENCH.md`.
