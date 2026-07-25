---
description: Interroger le vault Obsidian — exécution en fork (contexte principal préservé), réponse citée, synthèse optionnelle
argument-hint: <question>
context: fork
agent: Explore
background: false
---

# /doc-query — interroger le vault

Cette commande s'exécute en fork : tout ce fichier s'adresse au sub-agent.
Tu es un sub-agent isolé — l'agent principal ne voit que ton rapport final, et
tu ne peux pas dialoguer avec l'utilisateur : tout ce qui appelle une décision
de sa part se formule dans le rapport, jamais en question bloquante.

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas
   d'échec : ton rapport final est le message d'erreur tel quel — S'ARRÊTER.
   Sinon, la sortie est le chemin du vault — appelé `$VAULT` ci-dessous.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (section « Règles de recherche » notamment).

## Cible de recherche optionnelle (dossier voisin du vault)

Si `$ARGUMENTS` contient un jeton `dans:<dossier>` (ex. `dans:marketing`) :

1. Le retirer de la question. La cible devient le dossier voisin du vault :
   `<parent de $VAULT>/<dossier>` (correspondance insensible à la casse parmi
   les dossiers réellement présents ; introuvable → ton rapport final liste
   les dossiers voisins disponibles et invite à relancer avec le bon nom —
   S'ARRÊTER).
2. La cible n'est pas forcément un vault structuré : si
   `INSTRUCTIONS-CLAUDE.md` ou `INDEX.md` y manquent, explorer par listing +
   grep + lecture ciblée, sans ces étapes.
3. **Aucune écriture dans la cible** (lecture seule). La sauvegarde en
   synthèse, si l'utilisateur la demande ensuite, ira toujours dans
   `$VAULT/wiki/syntheses/` (voir le bloc « Pour l'agent principal »).

Sans jeton `dans:`, la cible est `$VAULT` (comportement normal).

Prérequis d'accès : la permission `additionalDirectories` doit couvrir le
dossier parent (ex. autoriser `<parent>` plutôt que `<parent>/<vault>` seul).

## Recherche sémantique

1. Si `$ARGUMENTS` contient le jeton `--no-index`, le retirer de la question et
   sauter l'étape 2 (échappatoire : interroger sans réindexer).
2. Indexer — toujours `$VAULT`, même quand la cible est un dossier voisin
   `dans:` (un voisin est en lecture seule : on ne l'indexe JAMAIS, son équipe
   s'en charge). Indexation incrémentale : seuls les chunks nouveaux/modifiés
   coûtent un appel API. Deux portes d'entrée vers le moteur, dans cet ordre :
   - **MCP** (plugin agentic-toolbox installé) : outil
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build`, en passant
     `directory: $VAULT` **explicitement** — ne jamais compter sur son défaut
     `VAULT_PATH` (config globale du plugin, alors qu'ici le vault est celui
     du projet) ;
   - **wrapper** sinon : `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"`
     (clone local + venv du moteur).
3. Chercher — même cascade :
   - **MCP** : outil `mcp__plugin_agentic-toolbox_toolbox__semantic_search`
     (`question`, `directory: <cible>` explicite) ;
   - **wrapper** sinon :
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-search.sh" "<question>" "<cible>"`
     (le 2e argument ne sert que pour une cible `dans:` ; l'omettre sinon).
4. Repli grep explicite : si l'étape 2 ou 3 échoue (moteur indisponible — ni
   outils MCP dans la session ni clone local —, index absent — cas normal d'un
   voisin `dans:` jamais indexé), continuer SANS résultats sémantiques et
   ouvrir le rapport final par : « ⚠ recherche sémantique indisponible
   (<raison en quelques mots>), résultats par mots-clés uniquement ». Jamais
   d'échec silencieux, jamais d'autre fournisseur d'embeddings.
5. Filtrer les résultats venant de `LOG.md`, `INDEX.md`,
   `INSTRUCTIONS-CLAUDE.md`, `inbox/` ou `archives/` (bruit d'indexation).
   Les résultats restants (`relative_path`, `section`, `score`, `excerpt`)
   constituent les « pistes sémantiques » de la recherche ci-dessous.

## Recherche

La question à traiter est `$ARGUMENTS`, nettoyée des jetons `dans:` et
`--no-index`.

1. Lire `INDEX.md` à la racine de la cible (si présent).
2. Pistes sémantiques (s'il y en a) : ouvrir ces notes EN PREMIER, aux
   sections indiquées, puis suivre leurs wikilinks `[[...]]`. Ensuite, repérer
   les entrées pertinentes de l'INDEX et les ouvrir de la même façon.
3. Compléter par grep sur les mots-clés de la question ET leurs synonymes /
   variantes françaises.
4. Ne jamais recopier des notes entières.
5. Si rien de pertinent : le dire explicitement et lister ce qui s'en
   rapproche.

## Rapport final (ton retour à l'agent principal)

Exactement ces blocs, dans cet ordre :

1. L'avertissement de repli grep, le cas échéant (étape 4 ci-dessus).
2. La réponse à la question (concise, en français).
3. `Sources` : les chemins relatifs des notes utilisées.
4. Un bloc `Pour l'agent principal`, avec le chemin `$VAULT` résolu écrit en
   clair (l'agent principal ne connaît pas la sortie de vault-check) :
   - présenter la réponse et ses sources à l'utilisateur, puis proposer :
     « Sauvegarder cette réponse en synthèse dans le vault ? » ;
   - si oui : écrire `$VAULT/wiki/syntheses/<slug>.md` — frontmatter
     (`type: synthese`, `date`, `question`, plus `perimetre: <dossier>` si la
     recherche visait une cible `dans:`), corps = la réponse, section
     `## Références` = les chemins des sources ; ajouter la note dans
     `$VAULT/INDEX.md`, section Synthèses ; ajouter en fin de `$VAULT/LOG.md` :
     `## [YYYY-MM-DD] synthese | <slug>` — le tout en respectant les
     conventions de `$VAULT/INSTRUCTIONS-CLAUDE.md`.
