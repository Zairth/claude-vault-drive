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

**Un index par dossier.** `concepts/`, `entites/`, `syntheses/` et `sources/`
portent chacun son `.index/embeddings.jsonl`, donc son propre espace
vectoriel : les notes ne concourent qu'entre semblables, ce qui empêche une
entité de dix lignes d'être écrasée par un extrait d'une source de trois
cents. En contrepartie, chaque index interrogé coûte un embedding de la
question.

1. Si `$ARGUMENTS` contient le jeton `--no-index`, le retirer de la question et
   sauter l'étape 2 (échappatoire : interroger sans réindexer).
2. Indexer — **chaque dossier de `wiki/`, séparément** (ni `archives/`, ni
   `inbox/`, ni les fichiers racine ; jamais un dossier voisin `dans:`, qui
   est en lecture seule et dont l'indexation appartient à son équipe).
   Incrémental : seuls les chunks nouveaux/modifiés coûtent un appel API.
   Deux portes d'entrée, dans cet ordre :
   - **MCP** (plugin agentic-toolbox installé) : d'abord obtenir la liste des
     dossiers à indexer —
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index-targets.sh"` (une cible
     par ligne, relative à `wiki/`) —, puis un appel
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` par cible,
     avec `directory: $VAULT/wiki/<cible>` **explicite** — jamais de dossier
     implicite, et jamais `$VAULT/wiki` seul : le moteur indexe
     récursivement, ce qui vectoriserait deux fois les sous-dossiers ;
   - **wrapper** sinon : `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"`
     sans argument (il boucle lui-même sur les cibles ; sortie : un bloc
     `## <cible>` par dossier).
3. Chercher — même cascade, dans **chaque dossier indexé** (ou le seul dossier
   voisin, pour `dans:`) :
   - **MCP** : `mcp__plugin_agentic-toolbox_toolbox__semantic_search` par
     cible (`question`, `directory` explicite), `top_k` 3 par défaut — quatre
     index à cinq résultats noieraient le signal sous le volume ;
   - **wrapper** sinon :
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-search.sh" "<question>" "" 3`
     (2e argument vide = toutes les cibles ; le renseigner pour une cible
     `dans:` ou pour restreindre volontairement à une catégorie).
4. Repli grep explicite : si l'étape 2 ou 3 échoue (moteur indisponible — ni
   outils MCP dans la session ni clone local —, index absent — cas normal d'un
   voisin `dans:` jamais indexé), continuer SANS résultats sémantiques et
   ouvrir le rapport final par : « ⚠ recherche sémantique indisponible
   (<raison en quelques mots>), résultats par mots-clés uniquement ». Jamais
   d'échec silencieux, jamais d'autre fournisseur d'embeddings.
   Une cible en échec sur plusieurs n'est pas un repli : poursuivre avec les
   autres et le signaler en une ligne (« index <cible> indisponible »).
5. Les résultats (`relative_path`, `section`, `score`, `excerpt`) constituent
   les « pistes sémantiques ». **`relative_path` est relatif à la cible**, pas
   à `wiki/` : le chemin réel est `wiki/<cible>/<relative_path>`.
   **Ne jamais fusionner ni comparer les scores entre deux index** — ce sont
   des classements distincts sur des corpus disjoints, et les mêler
   reviendrait à inventer une fusion que rien ne justifie. Garder les pistes
   **groupées par cible**, dans l'ordre rendu.
   (Index d'une version ≤ 1.15.x encore en place : un `wiki/.index/` unique,
   qui produirait des résultats en doublon — le signaler comme reliquat à
   supprimer et l'ignorer.)

## Recherche

La question à traiter est `$ARGUMENTS`, nettoyée des jetons `dans:` et
`--no-index`.

1. Lire `INDEX.md` à la racine de la cible (si présent).
2. Pistes sémantiques (s'il y en a) : ouvrir ces notes EN PREMIER, aux
   sections indiquées, puis suivre leurs wikilinks `[[...]]`. Ensuite, repérer
   les entrées pertinentes de l'INDEX et les ouvrir de la même façon.
3. **Grep, TOUJOURS, en plus du sémantique — jamais à la place.** Les deux
   couches ne trouvent pas la même chose : le vectoriel rapproche par le sens
   et rate le terme exact ; le grep touche le terme exact et rate la
   reformulation. Chercher les mots pleins de la question ET leurs synonymes /
   variantes françaises dans tout `wiki/`. **Ouvrir au moins une note issue du
   grep**, même si la sémantique a déjà remonté des pistes : une note qui
   contient littéralement les mots de la question est le résultat le plus
   pertinent qui soit, et aucun score ne le dira. Si le grep et la sémantique
   désignent la même note, c'est un signal fort — la traiter en priorité.
4. **Question exhaustive** — « tous les… », « combien de fois… », « liste tous
   les… » : aucun classement ne peut y répondre, et s'y fier produirait une
   réponse fausse d'aspect crédible. Un index rend les K meilleurs résultats,
   jamais l'ensemble des résultats qualifiants : en demander 3 en rend 3, même
   si quarante notes conviennent. Sur ce type de question, les pistes et
   l'INDEX ne servent qu'à **désigner quoi ouvrir** — l'exhaustivité vient de
   la lecture, jamais du classement. Trop de notes pour un seul lecteur → le
   dire dans le rapport et nommer ce qui n'a pas été couvert ; jamais de
   silence sur une couverture partielle.
5. Ne jamais recopier des notes entières.
6. Si rien de pertinent : le dire explicitement et lister ce qui s'en
   rapproche.

## Rapport final (ton retour à l'agent principal)

Exactement ces blocs, dans cet ordre :

1. L'avertissement de repli grep, le cas échéant — et, sur une question
   exhaustive, ce qui a effectivement été lu en entier (une couverture
   partielle se dit, elle ne se devine pas).
2. La réponse à la question (concise, en français).
3. `Sources` : les chemins relatifs des notes utilisées.
4. Un bloc `Pour l'agent principal`, avec le chemin `$VAULT` résolu écrit en
   clair (l'agent principal ne connaît pas la sortie de vault-check) :
   - présenter la réponse et ses sources à l'utilisateur, puis proposer :
     « Sauvegarder cette réponse en synthèse dans le vault ? » ;
   - si oui : écrire `$VAULT/wiki/syntheses/<slug>.md` — frontmatter
     (`type: synthese`, `date`, `auteur` — repérable dans les notes existantes
     du vault, sinon le demander —, `description` — la réponse en quelques
     mots —, `question`, plus `perimetre: <dossier>` si
     la recherche visait une cible `dans:`), corps = la réponse, section
     `## Références` = un wikilink `[[<slug>]]` par note utilisée (jamais de
     chemin brut — seuls les wikilinks créent des liens dans le graphe
     Obsidian ; une source hors vault, cible `dans:`, reste en chemin brut) ;
     ajouter la note dans
     `$VAULT/INDEX.md`, section Synthèses (`- [[<slug>]] — <description>`,
     celle du frontmatter) ; ajouter en fin de `$VAULT/LOG/YYYY-MM-DD.md` (le
     fichier du jour — le créer au besoin ; jamais dans un `LOG.md` racine
     hérité, gelé) : `## [YYYY-MM-DD] synthese | <slug>` — le tout en
     respectant les conventions de `$VAULT/INSTRUCTIONS-CLAUDE.md`.
