---
description: Interroger le vault Obsidian via sub-agent — réponse citée, synthèse optionnelle
argument-hint: <question>
---

# /doc-query — interroger le vault

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas d'échec : transmettre
   le message d'erreur tel quel et S'ARRÊTER. Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (conventions de notes et règles de maintenance pour la synthèse optionnelle).

## Cible de recherche optionnelle (dossier voisin du vault)

Si `$ARGUMENTS` contient un jeton `dans:<dossier>` (ex. `dans:marketing`) :

1. Le retirer de la question. La cible devient le dossier voisin du vault :
   `<parent de $VAULT>/<dossier>` (correspondance insensible à la casse parmi
   les dossiers réellement présents ; introuvable → lister les dossiers voisins
   disponibles et demander à l'utilisateur).
2. Dans le prompt du sub-agent ci-dessous, remplacer `$VAULT` par la cible. La
   cible n'est pas forcément un vault structuré : préciser au sub-agent que si
   `INSTRUCTIONS-CLAUDE.md` ou `INDEX.md` y manquent, il explore par listing +
   grep + lecture ciblée, sans ces étapes.
3. **Aucune écriture dans la cible.** La sauvegarde en synthèse, si demandée,
   va toujours dans `$VAULT/wiki/syntheses/` (ajouter `perimetre: <dossier>` au
   frontmatter).

Sans jeton `dans:`, la cible est `$VAULT` (comportement normal).

Prérequis d'accès : la permission `additionalDirectories` doit couvrir le
dossier parent (ex. autoriser `<parent>` plutôt que `<parent>/<vault>` seul).

## Recherche sémantique (avant de lancer le sub-agent)

1. Si `$ARGUMENTS` contient le jeton `--no-index`, le retirer de la question et
   sauter l'étape 2 (échappatoire : interroger sans réindexer).
2. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"` — toujours sur `$VAULT`, même
   quand la cible est un dossier voisin `dans:` (un voisin est en lecture seule :
   on ne l'indexe JAMAIS, son équipe s'en charge). Indexation incrémentale :
   seuls les chunks nouveaux/modifiés coûtent un appel API.
3. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-search.sh" "<question>" "<cible>"`
   (le 2e argument ne sert que pour une cible `dans:` ; l'omettre sinon).
4. Repli grep explicite : si l'étape 2 ou 3 échoue (moteur indisponible, index
   absent — cas normal d'un voisin `dans:` jamais indexé), continuer SANS
   résultats sémantiques et ajouter à la réponse finale : « ⚠ recherche
   sémantique indisponible (<raison en quelques mots>), résultats par mots-clés
   uniquement ». Jamais d'échec silencieux, jamais d'autre fournisseur
   d'embeddings.
5. Filtrer les résultats venant de `LOG.md`, `INDEX.md`,
   `INSTRUCTIONS-CLAUDE.md` ou `inbox/` (bruit d'indexation). Les résultats
   restants (`relative_path`, `section`, `score`, `excerpt`) constituent les
   « pistes sémantiques ». Formater chaque piste en une ligne unique au format :
   `chemin#section (score) — extrait`. Construire la liste complète sous la forme
   `$PISTES_SEMANTIQUES` (chaîne multilignes), ou écrire `aucune` en cas de repli
   grep **ou** de liste vide après filtrage (recherche fonctionnelle, sans
   résultat exploitable — pas d'avertissement de repli dans ce cas). Cette
   valeur sera injectée dans le prompt du sub-agent ci-dessous.

## Recherche — TOUJOURS via sub-agent, jamais en contexte principal

Lancer un agent (type Explore, en avant-plan) avec exactement ce prompt, en
substituant `$VAULT` et `$QUESTION` (la question nettoyée des jetons `dans:`
et `--no-index`) :

> Tu cherches dans un vault de notes markdown situé à : $VAULT
> Question : $QUESTION
>
> 1. Lis `INSTRUCTIONS-CLAUDE.md` (section « Règles de recherche ») puis
>    `INDEX.md`, à la racine du vault.
> 2. Pistes sémantiques (si fournies ci-dessous) : ouvre ces notes EN PREMIER,
>    aux sections indiquées, puis suis leurs wikilinks `[[...]]`. Ensuite,
>    repère les entrées pertinentes de l'INDEX et ouvre-les de la même façon.
>
>    Pistes : $PISTES_SEMANTIQUES
>    (format : chemin#section (score) — extrait ; « aucune » si repli grep)
> 3. Complète par grep sur les mots-clés de la question ET leurs synonymes /
>    variantes françaises.
> 4. Ta réponse finale contient UNIQUEMENT : la réponse à la question (concise,
>    en français), puis une section `Sources` listant les chemins relatifs des
>    notes utilisées. Ne recopie jamais des notes entières.
> 5. Si rien de pertinent : dis-le explicitement et liste ce qui s'en rapproche.

## Restitution

1. Présenter la réponse et ses sources à l'utilisateur — précédées de
   l'avertissement de repli grep si la recherche sémantique était indisponible.
2. Proposer : « Sauvegarder cette réponse en synthèse dans le vault ? »
3. Si oui :
   - écrire `$VAULT/wiki/syntheses/<slug>.md` — frontmatter (`type: synthese`,
     `date`, `question`), corps = la réponse, section `## Références` = les
     chemins des sources ;
   - ajouter la note dans `$VAULT/INDEX.md`, section Synthèses ;
   - ajouter en fin de `$VAULT/LOG.md` : `## [YYYY-MM-DD] synthese | <slug>`.
