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

**Ne jamais `cd` dans le vault.** L'outil Bash conserve son répertoire d'un
appel à l'autre : un `cd` y laisse la session ENTIÈRE, l'utilisateur le voit
dans son invite, et tout ce qui se résout depuis le projet casse — à commencer
par `.claude/vault-path.local`. Travailler en **chemins absolus**, ou isoler le
déplacement dans un sous-shell : `(cd "$VAULT" && …)`.

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

**Un index par dossier.** Les cinq dossiers de `wiki/` portent chacun leur
`.index/embeddings.jsonl`, donc leur propre espace vectoriel : les notes ne
concourent qu'entre semblables, ce qui empêche une entité de dix lignes d'être
écrasée par un extrait d'un texte intégral de trois cents. Et surtout, ça
permet de **chercher dans une couche sans l'autre**.
Cette séparation ne coûte rien à la requête : depuis agentic-toolbox 4.1.0, un
seul appel porte plusieurs dossiers et **la question n'est vectorisée qu'une
fois**. Interroger cinq index coûte exactement le même appel réseau qu'un
seul.

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
     **Script indisponible** (refusé par les permissions, introuvable) → ne pas
     renoncer à indexer : la liste se retrouve en listant les sous-dossiers de
     `$VAULT/wiki/` qui contiennent au moins un `.md`. C'est exactement ce que
     le script calcule ; il existe pour centraliser la règle, pas pour la
     détenir. Le signaler en une ligne, et continuer.
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` par cible,
     avec `directory: $VAULT/wiki/<cible>` **explicite** — jamais de dossier
     implicite, et jamais `$VAULT/wiki` seul : le moteur indexe
     récursivement, ce qui vectoriserait deux fois les sous-dossiers ;
   - **wrapper** sinon : `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"`
     sans argument (il boucle lui-même sur les cibles ; sortie : un bloc
     `## <cible>` par dossier).
3. Chercher — même cascade, dans **chaque dossier indexé** (ou le seul dossier
   voisin, pour `dans:`) :
   - **MCP** : `mcp__plugin_agentic-toolbox_toolbox__semantic_search` en **un
     seul appel**, avec `directories: ["$VAULT/wiki/<cible1>", …]` — la
     question n'est vectorisée qu'une fois quel que soit le nombre de
     dossiers, et c'est le seul coût API d'une recherche. Ne jamais appeler
     l'outil une fois par dossier. `top_k` 3 par défaut : cinq index à cinq
     résultats noieraient le signal sous le volume.
     La réponse est une **liste de groupes** `{directory, results}`, dans
     l'ordre demandé — le résultat d'un dossier se lit donc dans le groupe
     dont le `directory` est le sien, jamais dans un classement global ;
   - **wrapper** sinon :
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-search.sh" "<question>" "" 3`
     (2e argument vide = toutes les cibles en un appel ; le renseigner pour une
     cible `dans:` ou pour restreindre volontairement à une catégorie).
   - **Restreindre le périmètre est un geste utile**, pas une optimisation :
     une question sur une personne se cherche dans `entites/`, une question
     sur une notion dans `concepts/`. Élargir ensuite si ça ne suffit pas.
4. Repli grep explicite : si l'étape 2 ou 3 échoue (moteur indisponible — ni
   outils MCP dans la session ni clone local —, index absent — cas normal d'un
   voisin `dans:` jamais indexé), continuer SANS résultats sémantiques et
   ouvrir le rapport final par : « ⚠ recherche sémantique indisponible
   (<raison en quelques mots>), résultats par mots-clés uniquement ». Jamais
   d'échec silencieux, jamais d'autre fournisseur d'embeddings.
   Une cible en échec sur plusieurs n'est pas un repli : poursuivre avec les
   autres et le signaler en une ligne (« index <cible> indisponible »).
5. Les résultats (`relative_path`, `section`, `score`, `excerpt`) constituent
   les « pistes sémantiques ». **`relative_path` est relatif au `directory` de
   son groupe**, pas à `wiki/` : le chemin réel est
   `wiki/<cible>/<relative_path>`.
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
   reformulation.

   Chercher les mots pleins de la question (mots-outils écartés), **sur leur
   racine et sans tenir compte de la casse ni des accents** :
   `grep -riE "h[ée]berg"` plutôt que `grep "hébergé"` — la racine attrape le
   pluriel, le suffixe et la forme fléchie sans les énumérer, et c'est ce qui
   rattrape la plupart des ratés d'une correspondance exacte. Étendre aux
   synonymes et variantes françaises.
   **Écarter les termes trop répandus** : un mot présent dans la plupart des
   notes ne discrimine rien — un patronyme suffit à ramener la moitié d'un
   vault. Ce sont les termes rares de la question qui portent le sens ; que
   les touches viennent d'eux.

   **Ouvrir TOUTES les touches retenues, puis trier** : ne retenir que celles qui
   apportent un fait, ou un savoir explicitement énoncé, répondant à la
   question. Ton contexte est jetable — l'agent principal ne verra que ton
   rapport —, donc lire large et rendre étroit est exactement ton métier : ne
   présélectionne jamais sur un nom de fichier ou sur une intuition.
   Encore trop de touches → **resserrer le motif** — exiger plusieurs termes
   rares ensemble plutôt qu'un seul — puis ouvrir tout ce qu'il rend, et dire
   dans le rapport comment il a été resserré. Jamais d'échantillonnage.
   Deux indices pour le tri : une note qui contient **littéralement** les mots
   de la question est souvent le meilleur résultat possible, et aucun score de
   similarité ne le dira ; une note désignée **par les deux couches** est un
   signal fort.
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

**Ton rapport EST ce que l'utilisateur lit.** Cette commande s'exécute en
fork : ta sortie lui est présentée telle quelle. Il n'y a pas d'agent principal
qui trierait ce qui le concerne de ce qui ne le concerne pas — **une consigne
écrite dans ton rapport sera affichée**, quel que soit son titre.

Deux tentatives l'ont établi : interdire l'affichage dans ce fichier n'a rien
changé (l'agent principal ne le lit pas), et titrer le bloc
« NE PAS AFFICHER » n'a rien changé non plus (il a été affiché avec son titre).
La conclusion est structurelle, pas rédactionnelle : **il ne doit plus y avoir
de bloc de consignes dans le rapport.**

Donc les consignes détaillées — chemins absolus, frontmatter à écrire, outils à
appeler — vont **sur disque**, dans
`${TMPDIR:-/tmp}/claude-vault-suite-<session ou horodatage>.md`, hors du projet
et hors du vault. Ce fichier porte tout ce qu'il faut pour exécuter la suite.

Et ton rapport se termine par **une seule ligne**, lisible par un humain autant
que par un agent :

`Suite prête : <chemin du fichier>. Sauvegarder cette réponse en synthèse dans le vault ?`

Rien d'autre. **Le fichier de suite est supprimé dans les trois cas**, parce
qu'une consigne sans décision est un piège : elle traîne, et la fois suivante
on ne sait plus si elle attend encore.

- **oui** → le fichier est ouvert, appliqué, puis supprimé ;
- **non** → supprimé sans être appliqué. Rien n'a été écrit dans le vault, et
  la réponse reste dans la conversation : elle se redemande en une phrase ;
- **pas de réponse** → **reposer la question une fois**, au tour suivant, en
  une ligne. Toujours pas de réponse claire → **traiter comme un refus** et
  supprimer. C'est le défaut sûr : rien n'a été écrit, donc rien n'est perdu,
  et relancer indéfiniment coûterait plus cher à l'utilisateur que de refaire
  la synthèse le jour où il la veut vraiment.

La purge du hook `UserPromptSubmit` reste le dernier filet, pour le cas où la
session s'interrompt avant qu'une décision ait pu être prise — pas pour tenir
lieu de nettoyage ordinaire.

Exactement ces blocs, dans cet ordre :

1. L'avertissement de repli grep, le cas échéant — et, sur une question
   exhaustive, ce qui a effectivement été lu en entier (une couverture
   partielle se dit, elle ne se devine pas).
2. La réponse à la question (concise, en français).
3. `Notes retenues` — **toutes** celles que tu as jugées pertinentes, pas
   seulement celles qui portent la réponse : c'est le matériau que l'agent
   principal pourra ouvrir lui-même s'il en a besoin. Une ligne chacune :
   - le **chemin relatif au vault**, pour qu'il puisse l'ouvrir sans te
     redemander ;
   - **d'où elle vient** — `sémantique` (avec son dossier et son rang),
     `grep`, ou **`les deux`**, qui est le signal de pertinence le plus fort
     dont il dispose ;
   - **une phrase** disant ce qu'elle apporte à la question.
   Ne jamais recopier leur contenu : c'est toute la raison d'être du fork. Le
   contexte principal reçoit une carte, pas le territoire — il ouvre ce dont
   il a besoin, quand il en a besoin.
   Les notes ouvertes puis écartées comme non pertinentes ne figurent pas
   ici : dire seulement combien l'ont été, par couche.
4. Le **fichier de suite** décrit ci-dessus, avec le chemin `$VAULT` résolu écrit en
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
     Enfin **réindexer `syntheses/`** (outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
     `directory: $VAULT/wiki/syntheses`, sinon
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh" "$VAULT/wiki/syntheses"`).
     Sans ça, la synthèse n'entre dans l'espace vectoriel qu'à la **recherche
     suivante**, qui réindexe avant de chercher : elle existe, elle est dans
     l'INDEX, le bras lexical la trouve — mais elle est absente de la
     similarité jusque-là. L'indexation est incrémentale, donc elle ne coûte
     que les chunks de cette note, et ce coût aurait été payé au prochain
     `/doc-query` de toute façon. Échec non bloquant : la synthèse reste
     valide, et la prochaine recherche rattrapera.
