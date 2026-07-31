---
description: Corriger une information dans le vault et rebrancher toute sa chaîne — vérification contre la pièce d'origine, propagation, réindexation
argument-hint: <chemin de la note> "<passage exact>" "<nouvelle valeur>"
context: fork
agent: Explore
background: false
---

# /doc-repair — corriger une information sans casser le vault

Cette commande s'exécute en fork : tout ce fichier s'adresse au sub-agent.
Tu es un sub-agent isolé — l'agent principal ne voit que ton rapport final, et
tu ne peux pas dialoguer avec l'utilisateur : **tu ne modifies RIEN**. Tu
instruis la correction et tu proposes ; c'est l'agent principal qui écrit,
après validation.

`/doc-lint` balaie tout le vault à la recherche d'incohérences ; celle-ci part
d'une incohérence **déjà repérée par l'utilisateur** et remonte sa chaîne
jusqu'au bout. L'une ratisse, l'autre creuse.

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas
   d'échec : ton rapport final est le message d'erreur tel quel — S'ARRÊTER.
   Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` — la structure en trois
   degrés de fidélité et la convention `## Historique` gouvernent tout ce qui
   suit.
3. `$ARGUMENTS` porte trois éléments : le **chemin de la note**, le **passage
   exact** à corriger (copié-collé), la **nouvelle valeur**. L'un d'eux
   manque ou le passage est introuvable dans la note → ton rapport le dit et
   liste les passages approchants trouvés dans cette note — S'ARRÊTER.

## Instruction de la correction

### 1. Localiser

Ouvrir la note visée, situer le passage : sa section, sa ligne, ce qu'il
affirme exactement. Un passage présent plusieurs fois dans la même note →
lister toutes ses occurrences et leur contexte, sans en choisir une.

### 2. Chercher partout ailleurs

Une même affirmation vit rarement à un seul endroit : elle a pu être recopiée
dans une page de concept, reprise dans une synthèse, tirée d'un enseignement.
**Une correction partielle est pire que pas de correction** — elle laisse le
vault en contradiction avec lui-même, et la version fautive continue de
remonter en recherche.

Chercher dans tout `wiki/` : le passage littéral, puis ses **termes rares**
(la valeur fautive elle-même est en général le meilleur motif — un montant,
une date, un nom), enfin la valeur *nouvelle*, qui peut déjà figurer ailleurs
et révéler que le vault se contredisait déjà.

### 3. Remonter la chaîne jusqu'à la pièce

C'est ce qui distingue cette commande d'un simple remplacement. Le vault a
trois degrés de fidélité, et la correction doit être **vérifiée** avant d'être
proposée :

1. la note visée et toutes celles qui portent la même affirmation ;
2. `wiki/sources/<slug>.md` — le **texte intégral** de la pièce. Le passage y
   figure-t-il ? Sous quelle forme ?
3. `archives/<pièce>` — **la pièce elle-même**, désignée par `origine`. La
   rouvrir et lire le passage à la source.

Puis conclure, et **le dire explicitement dans le rapport** :

- **la pièce dit la nouvelle valeur** → la note la trahissait. Correction
  confirmée par la pièce : c'est le cas le plus sûr, dis-le ;
- **la pièce dit l'ancienne valeur** → le vault était fidèle, et c'est
  l'information qui a changé depuis. Ce n'est pas une erreur de
  restitution : convention `## Historique` (voir 4) ;
- **la pièce ne dit ni l'un ni l'autre**, ou est illisible sur ce point →
  **le signaler comme tel** et ne rien affirmer. Proposer quand même la
  correction si l'utilisateur la demande, mais accompagnée d'un
  `> [!warning]` disant que la pièce ne la confirme pas. On ne fabrique pas
  une certitude qu'on n'a pas.

Pièce d'origine inaccessible (Drive non monté, fichier disparu) → le dire, et
traiter la correction comme non vérifiée.

### 4. Qualifier la correction

Deux natures, deux traitements — c'est le point qui décide de ce qu'on écrit :

- **Erreur de restitution** — la note trahit ce que dit la pièce. La valeur
  fautive n'a jamais été vraie : on la remplace, **sans** `## Historique`.
  Conserver une erreur dans l'historique reviendrait à la présenter comme une
  vérité passée.
- **Information périmée** — la pièce disait vrai, ce n'est plus le cas
  aujourd'hui. Convention d'`INSTRUCTIONS-CLAUDE.md` : valeur courante mise à
  jour dans le corps, ancienne poussée en `## Historique`
  (`- [YYYY-MM-DD] <ancienne affirmation> — remplacée par : <la nouvelle,
  wikilink vers sa source>`).
  Attention : une couche immuable ne reçoit pas d'`## Historique`. Une pièce
  ne périme pas — elle dit ce qu'elle dit à sa date. Si l'information a
  changé, c'est la page de concept ou d'entité qui porte la valeur courante,
  et la note d'origine reste telle quelle.

Doute entre les deux → ne pas trancher : présenter les deux lectures dans le
rapport et laisser l'utilisateur choisir.

### 5. Recenser ce qu'il faut rebrancher

Sans écrire quoi que ce soit, dresser la liste :

- **les notes à modifier**, chacune avec son chemin, le passage exact et son
  remplacement ;
- **les couches immuables touchées** (`sources/`, `enseignements/`) —
  signalées **à part** : les corriger est l'exception, pas la règle. Elle se
  justifie quand la note trahit la pièce, puisque l'immuabilité protège la
  fidélité et qu'une restitution fautive l'entame déjà. Elle ne se justifie
  jamais pour une information périmée ;
- **les wikilinks** qui deviendraient pendants si un titre `###` ou un nom de
  note change ;
- **l'entrée `INDEX.md`** si une `description` de frontmatter est touchée ;
- **les dossiers à réindexer** — uniquement ceux dont une note change ;
- **les contradictions révélées** : si la recherche a montré que deux notes
  se contredisaient déjà, le dire — c'est un `> [!question]` à poser, pas une
  correction à faire en douce.

**`archives/` n'apparaît jamais dans cette liste.** La pièce d'origine est la
preuve : si elle est fausse, c'est un fait sur la pièce, à consigner dans une
page de concept. On corrige ce que le vault a dit de la pièce, jamais la
pièce.

## Rapport final (ton retour à l'agent principal)

Exactement ces blocs, dans cet ordre :

1. **Le verdict de vérification** en une ligne : `confirmée par la pièce`,
   `contredite par la pièce`, `non vérifiable (<raison>)` — et la nature
   retenue : `erreur de restitution` ou `information périmée`.
2. **Ce qui a été trouvé** : le passage dans la note visée, et toutes les
   autres notes qui portent la même affirmation. Une ligne par note — chemin,
   passage, ce qu'il faut y mettre. Jamais leur contenu intégral : l'agent
   principal ouvrira ce dont il a besoin.
3. **Le plan de correction**, ordonné, avec pour chaque étape le chemin
   concerné. Les modifications de couches immuables regroupées à part et
   justifiées une par une.
4. Un bloc `Pour l'agent principal`, avec le chemin `$VAULT` résolu écrit en
   clair :
   - présenter le verdict et le plan à l'utilisateur, et **n'appliquer que
     ce qu'il valide** — étape par étape s'il touche une couche immuable ;
   - après application : réindexer les seuls dossiers modifiés (outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
     `directory: $VAULT/wiki/<dossier>` explicite, un appel par dossier ;
     sinon `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh" "<dossier>"`) ;
   - re-vérifier les wikilinks des fichiers touchés ;
   - ajouter en fin de `$VAULT/LOG/YYYY-MM-DD.md` (fichier du jour, créé au
     besoin ; jamais dans un `LOG.md` racine hérité, gelé) :
     `## [YYYY-MM-DD] repair | <ce qui a été corrigé>` suivi d'une ligne
     listant les fichiers modifiés et le verdict de vérification. Une
     correction de couche immuable **doit** figurer au journal : c'est ce qui
     la distingue d'une édition silencieuse.
