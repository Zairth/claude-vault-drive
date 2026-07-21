---
description: Interroger le vault Obsidian via sub-agent — réponse citée, synthèse optionnelle
argument-hint: <question>
---

# /doc-query — interroger le vault

## Préambule obligatoire

1. Exécuter `bash .claude/scripts/vault-check.sh`. En cas d'échec : transmettre
   le message d'erreur tel quel et S'ARRÊTER. Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (conventions de notes et règles de maintenance pour la synthèse optionnelle).

## Recherche — TOUJOURS via sub-agent, jamais en contexte principal

Lancer un agent (type Explore, en avant-plan) avec exactement ce prompt, en
substituant `$VAULT` et `$ARGUMENTS` :

> Tu cherches dans un vault de notes markdown situé à : $VAULT
> Question : $ARGUMENTS
>
> 1. Lis `INSTRUCTIONS-CLAUDE.md` (section « Règles de recherche ») puis
>    `INDEX.md`, à la racine du vault.
> 2. Repère les entrées pertinentes de l'INDEX, ouvre ces notes, suis leurs
>    wikilinks `[[...]]`.
> 3. Complète par grep sur les mots-clés de la question ET leurs synonymes /
>    variantes françaises.
> 4. Ta réponse finale contient UNIQUEMENT : la réponse à la question (concise,
>    en français), puis une section `Sources` listant les chemins relatifs des
>    notes utilisées. Ne recopie jamais des notes entières.
> 5. Si rien de pertinent : dis-le explicitement et liste ce qui s'en rapproche.

## Restitution

1. Présenter la réponse et ses sources à l'utilisateur.
2. Proposer : « Sauvegarder cette réponse en synthèse dans le vault ? »
3. Si oui :
   - écrire `$VAULT/wiki/syntheses/<slug>.md` — frontmatter (`type: synthese`,
     `date`, `question`), corps = la réponse, section `## Références` = les
     chemins des sources ;
   - ajouter la note dans `$VAULT/INDEX.md`, section Synthèses ;
   - ajouter en fin de `$VAULT/LOG.md` : `## [YYYY-MM-DD] synthese | <slug>`.
