---
description: Vérifier la cohérence du vault Obsidian — compteurs en tête, wikilinks pendants, doublons suspectés, contradictions, orphelins, INDEX, conflits Drive, inbox
context: fork
agent: Explore
background: false
---

# /doc-lint — maintenance du vault

Cette commande s'exécute en fork : tout ce fichier s'adresse au sub-agent.
Tu es un sub-agent isolé — l'agent principal ne voit que ton rapport final.
Tu ne modifies RIEN dans le vault : les corrections sont appliquées par
l'agent principal à partir de ton rapport — les mécaniques d'office, les
destructrices après autorisation. Ton rapport porte donc un **verdict** sur
chaque point, jamais une question ouverte.

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas
   d'échec : ton rapport final est le message d'erreur tel quel — S'ARRÊTER.
   Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (règles de maintenance : sources immuables, LOG append-only, INDEX à jour).

**Ne jamais `cd` dans le vault.** L'outil Bash conserve son répertoire d'un
appel à l'autre : un `cd` y laisse la session ENTIÈRE, l'utilisateur le voit
dans son invite, et tout ce qui se résout depuis le projet casse — à commencer
par `.claude/vault-path.local`. Travailler en **chemins absolus**, ou isoler le
déplacement dans un sous-shell : `(cd "$VAULT" && …)`.

## Vérifications (les treize)

1. **Callouts** — deux natures que la convention d'`INSTRUCTIONS-CLAUDE.md`
   sépare par leur durée de vie ; ne jamais les additionner :
   - `> [!question]` dans `wiki/` = **contradiction en souffrance**, à
     trancher → lister fichier + extrait. C'est le seul des deux qui appelle
     une action.
   - `> [!warning]` dans `wiki/` = **mise en garde documentaire**,
     permanente → compter seulement, et le dire ; ne rien réclamer.
     Sa place est `wiki/enseignements/`. Un `[!warning]` trouvé dans
     `wiki/sources/` est **mal placé** : cette couche porte le texte de la
     pièce, pas le commentaire qu'on en fait, et l'y laisser fait remonter de
     l'éditorial sur une recherche de contenu → lister à part.
   - `> [!question]` trouvé dans `wiki/sources/` ou `wiki/enseignements/` =
     **défaut de placement** : ces couches sont immuables, le callout ne
     pourra jamais y être retiré une fois tranché → lister à part (remède dans
     les corrections).
   - **Héritage des versions ≤ 1.14.0**, où `> [!warning]` servait aux deux
     usages : hors des couches immuables, lire le corps de chaque `[!warning]` et
     signaler ceux qui décrivent en réalité deux affirmations incompatibles —
     ce sont des contradictions à requalifier en `[!question]`. Un
     `[!warning]` qui énonce une réserve sur une pièce est conforme, ne pas
     le toucher.
   - Enfin, vérifier que `$VAULT/INSTRUCTIONS-CLAUDE.md` mentionne bien
     `[!question]` : les fichiers racine d'un vault ne sont jamais écrasés par
     `/vault-init`, donc un vault créé avant 1.15.0 porte encore l'ancienne
     convention. Absent → le signaler (remède dans les corrections). En cas
     de désaccord entre ce fichier et la présente commande, **c'est la
     commande qui fait foi** : elle vient du plugin, donc de la version
     installée.
2. **Pages orphelines** : pour chaque note de `wiki/concepts/` et `wiki/entites/`,
   chercher `[[<nom-du-fichier-sans-extension>` **et**
   `[[<dossier>/<nom-du-fichier-sans-extension>` dans tout le vault (hors la
   note elle-même). Les deux formes existent — un slug partagé entre deux
   dossiers oblige à préfixer —, et ne chercher que la première déclarerait
   orphelines des notes correctement pointées.
3. **Wikilinks pendants et ambigus** : recenser les cibles de tous les
   `[[...]]` des notes de `wiki/` — la cible est ce qui précède un éventuel
   `|` (texte affiché) ou `#` (section).
   Une cible peut être un **nom nu** (`note-a`) ou **préfixée du dossier**
   (`sources/2026-06-23-x`). Résoudre les deux formes avant de conclure —
   traiter une cible préfixée comme un nom nu introuvable ferait passer pour
   pendants tous les liens croisés du vault.
   Deux défauts distincts, à lister séparément :
   - **pendant** — la cible ne correspond à aucun fichier du vault (nom sans
     extension, chemin relatif à `wiki/` compris) ni à aucun alias déclaré
     dans un frontmatter `aliases:` → lister note + lien. C'est le miroir de
     la vérification 2 : l'orpheline n'est pas pointée, le lien pendant
     pointe dans le vide.
   - **ambigu** — la cible est un **nom nu** dont le slug existe dans
     **plusieurs dossiers** de `wiki/`. C'est le cas de tout le corpus, où
     chaque pièce a sa note dans `sources/` ET dans `enseignements/` : un
     `[[<slug>]]` nu y désigne deux fichiers. Obsidian n'avertit pas, il en
     choisit un silencieusement — le lien n'est donc jamais compté pendant,
     et la moitié du graphe peut pointer sur la mauvaise couche sans que rien
     ne le signale. Ne pas se contenter d'inspecter les deux notes de la
     paire : ces liens nus viennent surtout de `concepts/` et `entites/`,
     qui citent une pièce sans se préoccuper de sa couche. Lister note +
     lien + les deux cibles possibles → à préfixer.
     La règle : un renvoi à ce que dit une pièce vise
     `[[enseignements/<slug>]]` ; seul un renvoi au texte intégral vise
     `[[sources/<slug>]]`.
   - **faux wikilink** — la cible est **impossible** : elle contient un
     guillemet, une virgule, une accolade, un crochet. Ce n'est pas un lien
     mal écrit, c'est du **texte que le rendu prend pour un lien** — typiquement
     du JSON ou du code cité dans une pièce, où un tableau imbriqué produit
     `[[` en ouverture et `]]` en fermeture. Obsidian fabrique alors des nœuds
     fantômes dans le graphe, et un scan de wikilinks trop restrictif ne les
     voit ni comme pendants ni comme ambigus : ils passent entre les deux.
     Scanner `[[...]]` **sans présumer de la forme de la cible**, et lister à
     part — le remède n'est pas de corriger un lien, c'est d'**entourer le
     passage d'une clôture de code** ` ``` `. Dans une clôture, rien n'est
     interprété.
     Exception : ce qui est **déjà** dans une clôture de code n'est pas un
     défaut. Suivre l'état ouvert/fermé des ` ``` ` en parcourant le fichier,
     sinon on signale ce qui est déjà réglé.
   Vérifier enfin que `$VAULT/INSTRUCTIONS-CLAUDE.md` énonce bien cette règle
   pour **tout** lien vers une pièce, et pas seulement entre les deux notes
   de la paire : les vaults créés avant 1.21.1 portent une version qui
   déclarait le nom nu valable « partout ailleurs », ce qui reproduit le
   défaut à chaque écriture. Formulation ancienne → le signaler (remède dans
   les corrections).
4. **Renvois à sens unique** : une note qui se déclare **le complément
   d'une autre** — « page de regroupement complétant `[[X]]` », « suite de
   `[[X]]` », « détail de `[[X]]` », ou tout wikilink dans sa première phrase
   qui la présente comme dépendant d'une page-parent — doit être pointée EN
   RETOUR par cette page-parent. Vérifier la réciprocité, lister les couples
   asymétriques.
   Ce n'est pas de la symétrie pour la symétrie, et ce défaut échappe à la
   vérification 2 : la page complémentaire est pointée par d'autres notes,
   donc elle n'est pas orpheline. Mais quelqu'un — humain ou agent — qui
   arrive sur la page-parent ne saura jamais que le complément existe, et une
   recherche qui remonte la parente ne l'atteindra pas en suivant ses liens.
   Mesuré au banc : c'est la seule question sur vingt-deux dont une attendue
   était introuvable, moteur hors de cause.
5. **Trous d'INDEX** : chaque note de `wiki/` doit apparaître dans `INDEX.md` —
   lister les absentes. Inversement, lister les entrées d'`INDEX.md` pointant
   vers des fichiers disparus.
6. **Fichiers de conflit Drive** : chercher les motifs `* (1).md`, `* (2).md` et
   `*conflit*` dans tout le vault → lister. Chercher aussi les doublons du mapping
   vectoriel (`embeddings (1).jsonl`, `*conflit*`) dans **chaque**
   `wiki/<dossier>/.index/` → lister séparément (résolution spécifique, voir
   corrections).
7. **inbox/ en attente** : lister les fichiers non ingérés (information, pas erreur).
8. **Frontmatter obligatoire** (modèle de note d'`INSTRUCTIONS-CLAUDE.md`) :
   pour chaque note de `wiki/`, vérifier la présence de `type` + `date` +
   `auteur` + `description`, plus `origine` pour les sources et `question`
   pour les synthèses
   → lister les notes non conformes avec leurs propriétés manquantes.
   Vérifier aussi que `type` s'accorde au dossier (`type: entite` sous
   `entites/`, `type: source` sous `sources/`, `type: enseignements` sous
   `enseignements/`…) : un désaccord fausse l'INDEX et trahit une note écrite
   au mauvais endroit.
9. **Cohérence vectorielle** — il y a **un index par dossier de `wiki/`**
   (`concepts/`, `entites/`, `syntheses/`, `enseignements/`, `sources/`), pas
   un index global.
   La liste fait foi :
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index-targets.sh"` (une cible par
   ligne, relative à `wiki/`) — chacune doit avoir son
   `<dossier>/.index/embeddings.jsonl`.
   - Cible sans index → « jamais indexée » : **ses notes sont invisibles à la
     recherche sémantique**, ce qui est plus grave qu'un index périmé (remède :
     la réindexation décrite dans les corrections). Lister ces cibles.
   - Reliquats à proposer à la suppression (dérivés jetables) : un
     `wiki/.index/` (index global unique des versions ≤ 1.15.x — il ferait
     doublon avec les index par dossier), et un `.index/` à la racine du vault
     (versions ≤ 1.5.3).
   - Pour chaque index présent → lire ses métadonnées (outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_info` avec
     `directory: $VAULT/wiki/<cible>` — purement local, zéro quota — sinon
     ligne 1 du fichier : provider, modèle, dimension, version, `chunk_chars`)
     et les reporter. Deux divergences à ne PAS confondre :
     - **provider, modèle ou dimension divergents** entre deux index = les
       vecteurs n'ont pas été construits avec le même moteur, et les scores de
       ces dossiers ne veulent plus rien dire l'un par rapport à l'autre.
       Ce sont des scores **faux** → réindexation complète, à signaler comme
       une erreur ;
     - **`chunk_chars` divergent** = même moteur, même espace vectoriel, donc
       des scores **justes** — mais établis sur un grain inégal : un dossier
       découpé fin rend des extraits plus précis qu'un dossier découpé large,
       et leurs rangs ne se comparent plus à qualité égale. À signaler comme
       un **constat**, pas comme une panne : la recherche continue de
       fonctionner, et cet état est normal pendant une reconstruction en
       cours. Remède : réindexer les cibles restées à l'ancienne valeur.
       Champ absent (`null`) = index construit avant que la granularité soit
       consignée — granularité **inconnue**, pas index invalide.
     Diagnostic de suivi : comparer le `created_at` le plus récent du mapping
     aux dernières entrées `ingest` du journal (`LOG/*.md`, plus un `LOG.md`
     racine hérité s'il existe) — des ingests postérieurs aux
     vecteurs = indexation non suivie (le verdict définitif reste le hash,
     jamais les dates).

10. **Appariement des couches d'origine** — toute pièce ingérée produit deux
   notes de même slug, `sources/<slug>.md` et `enseignements/<slug>.md`.
   Lister les **orphelines d'appariement** : un texte intégral dont personne
   n'a tiré d'enseignement (pièce ingérée puis abandonnée), et surtout un
   enseignement sans son texte (le matériau qui l'appuie a disparu, la chaîne
   de vérification est rompue). Vérifier aussi que les deux se pointent
   mutuellement en wikilink et partagent le même `origine`.
   Enfin, dans `enseignements/`, une note **sans aucun titre `###`** : ses
   enseignements seraient indexés en un seul bloc au lieu d'un par
   enseignement — la granularité de recherche est perdue.
   Le wikilink croisé attendu est **préfixé du dossier**
   (`[[sources/<slug>]]`) : un lien croisé en nom nu est ambigu, les deux
   notes portant le même slug — le signaler comme à corriger.
11. **Parasites hors `wiki/`** — les autres vérifications ne regardent que
   `wiki/`, or Obsidian indexe TOUT le vault : ce qui traîne ailleurs pollue
   le graphe humain (l'index sémantique, lui, ne couvre que `wiki/`).
   Vérifier d'abord que `.obsidian/app.json` exclut bien **`archives/` et
   `inbox/`** : sans ces deux filtres, les pièces d'origine et la matière brute
   en attente apparaissent dans le graphe comme s'il s'agissait de notes.
   Filtre manquant → le signaler (remède dans les corrections).
   - `.md` inattendu à la **racine** du vault : tout sauf `INDEX.md`,
     `INSTRUCTIONS-CLAUDE.md`, `BENCH.md` et un `LOG.md` hérité → lister.
     Cas typique : un clic sur un nœud fantôme du graphe Obsidian crée une
     note vide à la racine (voir ci-dessous).
   - **`.md` posé directement dans `wiki/`** (hors d'un de ses dossiers) →
     lister. Ce n'est pas cosmétique : les index vivent dans les dossiers, donc
     une note à la racine de `wiki/` **n'est indexée par rien** et reste
     introuvable en recherche sémantique.
   - **Sous-dossier inattendu** dans l'un des cinq dossiers de `wiki/` →
     lister : le moteur indexant récursivement, ses notes se
     retrouveraient mêlées à celles du parent, ce que la séparation par
     dossier cherche justement à éviter.
   - **notes vides** (0 octet, ou frontmatter seul sans corps) n'importe où
     dans le vault → lister.
   - **nœuds fantômes — d'abord dans `wiki/`, ensuite dans `archives/`.**
     Une référence de fichier qui ne pointe nulle part
     (`![img-0.jpeg](…)`, `[[piece-jointe]]`…) apparaît dans le graphe
     Obsidian comme un rond, et un clic dessus **crée** la note vide
     correspondante — d'où des dossiers et des fichiers qui poussent à la
     racine du vault sans que personne ne les ait écrits.
     Dans **`wiki/`** c'est un défaut à corriger : un markdown converti par un
     outil tiers puis ingéré y apporte ses liens morts, et cette couche-là est
     dans le graphe. Lister chaque occurrence avec sa note.
     Dans **`archives/`** c'est sans conséquence tant que l'exclusion Obsidian
     est en place : compter seulement, et ne jamais modifier un fichier
     archivé — la couche est immuable.
12. **Doublons suspectés (pages vivantes)** : sur l'ensemble `wiki/concepts/`
   + `wiki/entites/` — les doublons traversent les deux dossiers
   (`Docker.md` dans l'un, `conteneurisation-docker.md` dans l'autre) :
   - collision de **noms normalisés** (casse, accents, tirets/underscores,
     pluriel final) entre noms de fichiers et alias `aliases:` ;
   - moteur sémantique disponible → pour chaque page vivante, `semantic_search`
     avec son titre + sa première phrase, en un seul appel
     `directories: ["$VAULT/wiki/concepts", "$VAULT/wiki/entites"]` (les deux : un
     doublon traverse les deux dossiers, et chacun a son propre index) : une
     AUTRE page vivante en tête des résultats avec un score nettement détaché
     du reste = paire suspectée. Ne comparer les scores qu'à l'intérieur d'un
     même index. Moteur indisponible → le noter, la normalisation des noms
     reste faite.
   Lister chaque paire avec sa raison (nom / sémantique / les deux), **et pour
   chacune ton verdict motivé** : doublon accidentel à fusionner, ou scission
   délibérée à conserver. Ouvrir les deux pages et le dire — deux pages qui
   traitent le même objet sous deux angles (ce qu'une pièce affirme d'un côté,
   ce que le corpus établit de l'autre) ne sont pas un doublon, et une réserve
   valable sur l'une deviendrait fausse au-dessus du contenu de l'autre. La
   convention « une idée par note » tranche la plupart des cas.
   Détection et verdict seulement — aucune fusion sans validation (voir
   corrections).
13. **Identifiants en clair dans le vault** — un vault vit sur un dossier
   **synchronisé** : ce qui y traîne part avec lui, et un secret oublié n'est
   plus un secret. Chercher dans TOUT le vault, `inbox/` et `archives/`
   compris (ce sont eux qui reçoivent les exports bruts, donc eux qui les
   ramassent) : fichiers `.env`, `.*_token`, `*token*`, `*secret*`,
   `*credential*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, et tout fichier dont
   le contenu porte une affectation du type `TOKEN=`, `API_KEY=`,
   `PASSWORD=`, ou une chaîne `sk-`/`ghp_`/`xox`.
   **Ne jamais afficher la valeur trouvée** — la citer dans un rapport la
   recopierait dans un transcript. Donner le chemin, la taille, et ce que le
   nom laisse penser.
   Ce n'est pas une erreur de vault, c'est une fuite : la lister **en tête du
   rapport**, avant les compteurs, quel que soit le reste.

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

`Suite prête : <chemin du fichier>. <n> correction(s) mécanique(s) à appliquer, <n> point(s) à autoriser.`

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

1. Le chemin `$VAULT` résolu, écrit en clair (l'agent principal ne connaît pas
   la sortie de vault-check).
2. **La ligne de compteurs**, sur une seule ligne — l'état de santé du vault
   d'un coup d'œil, comparable d'un lint à l'autre :
   `contradictions: n · liens pendants: n · renvois à sens unique: n ·
   doublons suspectés: n ·
   orphelines: n · trous d'INDEX: n · conflits Drive: n · inbox: n ·
   frontmatters incomplets: n · parasites: n · index manquants: n ·
   appariements rompus: n · notes: n (concepts n · entites n · sources n ·
   enseignements n · syntheses n)`.
   `contradictions` ne compte QUE les `[!question]` en souffrance, augmentés
   des `[!warning]` requalifiés — jamais les mises en garde documentaires,
   qui sont un état normal du vault et non une dette.
   Les **identifiants en clair** ne figurent pas dans cette ligne : ils la
   précèdent. Un compteur les rangerait parmi les dettes de maintenance, or
   ce n'en est pas une — c'est une fuite, et elle se lit avant le reste.
3. Le rapport par catégorie (vide = le dire aussi : « rien à signaler »).
4. Le **fichier de suite** décrit ci-dessus. Deux régimes, à ne jamais
   confondre :

   - **mécanique et réversible** — trous d'`INDEX.md`, liens pendants ou
     ambigus, frontmatters incomplets, parasites, réindexation, requalification
     d'un callout : **appliquer sans demander**. Rien de tout cela ne détruit
     quoi que ce soit, et attendre un accord ne fait que reporter la même
     correction ;
     S'y ajoutent les suppressions **sans perte possible** : note vide (0 octet
     ou frontmatter seul), fichier de conflit Drive sur un dérivé jetable,
     reliquat d'index d'une version antérieure. Il n'y a rien à sauver dans un
     fichier vide, et un dérivé se régénère — demander l'autorisation de les
     supprimer ne protège rien et coûte un aller-retour ;
   - **destructeur ou irréversible** — fusionner deux pages, supprimer un
     fichier qui porte du contenu, éditer une couche immuable : soumettre.
     Le vault n'est pas versionné : ces trois-là ne se défont pas. Une seule fois, avec ton
     verdict et ce qui le motive, et la question porte sur l'**autorisation**,
     jamais sur la réponse.

   **Ne jamais demander à l'utilisateur une information qu'il n'a pas.** Ce qui arrive dans
   `inbox/` y est déposé pour que le vault s'en serve, souvent sans que
   l'utilisateur ait lu la pièce : le contexte d'une note est dans le vault et
   dans les pièces, pas dans sa tête. Une question comme « cette scission est-elle
   voulue ? » ou « ces deux pages disent-elles la même chose ? » se répond en
   ouvrant les deux fichiers — c'est ton travail, pas le sien.
   Chaque point soumis porte donc **ton verdict et ce qui le motive**, et ne
   demande qu'une **autorisation d'agir** : « voici ce que j'ai constaté, voici
   ce que j'en conclus, j'applique ? ». Une question ouverte n'est légitime que
   si la réponse dépend de quelque chose que le vault ne contient pas — une
   intention, une pièce non versée, une décision à venir — et il faut alors dire
   pourquoi le vault ne suffit pas.

   Les corrections :
   - trous d'INDEX → **régénérer `INDEX.md` en entier** plutôt que le
     rapiécer (fichier dérivé : sections du template, une entrée
     `- [[<slug>]] — <description du frontmatter>` par note de `wiki/`) ;
     relier ou supprimer les orphelines ; résoudre les
     conflits Drive (comparer les versions, garder la bonne, supprimer
     l'autre — sauf sur `INDEX.md` : supprimer le fichier de conflit et
     régénérer, un conflit sur un dérivé ne coûte rien) ;
     rappeler les `> [!question]` à trancher — un callout tranché se
     résout par la convention d'`INSTRUCTIONS-CLAUDE.md` : valeur courante
     mise à jour dans le corps, ancienne version poussée en `## Historique`,
     callout retiré.
     **Un `[!question]` ne se tranche pas depuis le vault seul** : il oppose
     deux affirmations, et savoir laquelle la pièce porte suppose de remonter
     jusqu'à elle — transcription **et** original. C'est exactement le travail
     de `/doc-repair`, et il ne se refait pas ici. C'est l'**agent principal**
     qui délègue, une contradiction à la fois, à un sub-agent — le fork de lint
     n'a pas l'outil Agent :
     > Lis `${CLAUDE_PLUGIN_ROOT}/commands/doc-repair.md` et exécute-le sur le
     > vault `<$VAULT>` pour : note `<chemin>`, passage `<le passage exact>`,
     > valeur proposée `<l'autre affirmation du callout>`. Tu n'écris RIEN.
     Aucune pièce ne départage → le callout reste, c'est sa raison d'être.
     Le reste des vérifications ne passe PAS par là : un lien pendant, un trou
     d'INDEX ou un frontmatter incomplet se constatent dans le vault, remonter
     à la pièce pour eux ne serait qu'une dépense. Pour un `[!warning]` requalifié : le retyper en
     `[!question]` sur place, puis le traiter comme les autres. Pour un
     `[!question]` égaré dans une couche immuable : reporter le callout sur la
     page concept/entité concernée, puis **le retirer de la note source** —
     seule modification jamais autorisée hors `/doc-repair`, et seulement
     après validation explicite. Elle se justifie parce que l'immuabilité
     protège ce que la pièce dit : une contradiction n'est pas dans la
     pièce, elle est dans la relation entre la pièce et le vault. L'ôter
     restaure la fidélité de la source au lieu de l'entamer.
     Si `INSTRUCTIONS-CLAUDE.md` ignore encore `[!question]` : proposer d'y
     remplacer la puce « Contradiction entre une nouvelle information et
     l'existant » par la version en vigueur (les deux callouts distingués par
     leur durée de vie, `[!warning]` permanent et documentaire, `[!question]`
     temporaire et hors des couches immuables) — une seule édition, le reste du
     fichier n'est pas touché.
     Si `INSTRUCTIONS-CLAUDE.md` restreint encore le préfixe aux deux notes de
     la paire (« partout ailleurs … le nom nu reste la règle ») : proposer d'y
     remplacer ce passage par la version en vigueur — tout lien vers une pièce
     se préfixe, d'où qu'il parte, et le nom nu ne vaut que pour `concepts/`,
     `entites/` et `syntheses/`. Sans cette édition, la prochaine ingestion
     réécrira des liens ambigus quel que soit le nombre de liens corrigés
     aujourd'hui.
   - Pour chaque paire que TON verdict a qualifiée de doublon accidentel et
     dont l'utilisateur autorise la fusion — **fusion assistée**, dans cet ordre : il choisit la page survivante ; rapatrier le
     contenu utile de la page absorbée ; ajouter le nom de l'absorbée aux
     `aliases:` de la survivante (filet : tout wikilink oublié continue de
     résoudre dans Obsidian et n'est pas compté pendant) ; réécrire les
     wikilinks entrants `[[absorbée]]` / `[[absorbée|texte]]` vers la
     survivante (conserver le texte affiché) ; supprimer la page absorbée et
     son entrée d'INDEX ; re-vérifier les liens pendants sur les fichiers
     touchés ; enchaîner la **réindexation incrémentale** (mêmes outils que la
     cohérence vectorielle ci-dessus) — la réécriture complète de l'index
     purge les vecteurs de la page absorbée et vectorise la survivante
     enrichie ; moteur indisponible → noter « indexation à rattraper » (le
     prochain `/doc-query` la fera).
   - Pour un nœud fantôme dans `wiki/` : remplacer la référence morte par un
     marqueur textuel inerte (`[figure N — non extraite]`), et supprimer la
     note vide que le clic a créée. Sur une couche immuable, c'est une
     exception justifiée et à journaliser : cette couche est fidèle au texte de
     la pièce, pas aux liens brisés du convertisseur qui l'a produite, et le
     marqueur conserve l'information que la référence portait.
   - Pour les parasites : `.md` inattendu à la racine ou note vide →
     proposer la suppression (rien à sauver dans un fichier vide), ou son
     déplacement dans `wiki/` avec un frontmatter conforme si l'utilisateur
     reconnaît une note qu'il voulait écrire. `.md` posé à la racine de
     `wiki/` → proposer son déplacement dans le dossier qui convient, puis
     l'indexation de ce dossier : tant qu'elle reste là, la note est
     introuvable en recherche sémantique. Nœuds fantômes d'`archives/` →
     le remède n'est pas dans le vault mais dans **Obsidian** : Paramètres →
     Fichiers et liens → Filtres d'exclusion → ajouter `archives/` **et**
     `inbox/`. Les
     archives sortent alors du graphe et de la recherche Obsidian, sans être
     touchées ni perdues — c'est exactement leur statut (pièces d'origine
     conservées, hors index). Sans cette exclusion, chaque clic sur un rond
     fantôme recrée une note vide à la racine.
   - Pour chaque wikilink pendant : cible renommée ou mal orthographiée →
     corriger le lien vers la page existante ; page réellement manquante →
     proposer sa création ou le délier (texte simple) — jamais de page coquille
     créée juste pour éteindre le compteur.
   - Pour un **faux wikilink** : entourer le passage d'une clôture de code
     (` ```json `, ` ``` `…) — **sans modifier un seul caractère du texte**.
     C'est ce qui rend l'exception acceptable dans une couche immuable : la
     couche est fidèle au texte de la pièce, pas aux artefacts de rendu de
     l'outil qui l'affiche, et la clôture n'ajoute que des délimiteurs autour.
     Mécanique et réversible : appliquer d'office.
   - Pour un **renvoi à sens unique** : ajouter le lien manquant sur la
     page-parent, dans la phrase qui s'y prête — jamais une ligne « Voir
     aussi » posée en fin de note, qui ne dit pas ce que le complément
     apporte. Mécanique et réversible : appliquer d'office.
   - Pour chaque wikilink **ambigu** : préfixer la cible du dossier voulu, en
     laissant le texte affiché intact — `[[x|la pièce]]` devient
     `[[enseignements/x|la pièce]]`, et le rendu ne bouge pas. Choisir la
     couche sur ce que la phrase fait dire au lien : « ce que la pièce
     affirme » → `enseignements/`, « le texte intégral » → `sources/`. Puis
     réindexer les dossiers touchés : le corps des notes a changé, donc leurs
     chunks aussi.
   - Pour les frontmatters non conformes : proposer une valeur déduite du
     contenu de la note ou du journal (`date` : à défaut, la première mention
     de la note dans `LOG/` ou un `LOG.md` racine hérité ; `description`
     manquante : rapatrier celle de l'entrée `INDEX.md` existante, sinon la
     déduire du contenu) — jamais de valeur inventée sans le signaler.
   - Pour un **identifiant en clair** : ne pas se contenter de supprimer le
     fichier. Un secret qui a séjourné dans un dossier synchronisé est à
     considérer comme **compromis**, et l'effacer n'annule pas ce qui a déjà
     été répliqué. L'ordre est : dire à l'utilisateur de le **révoquer chez
     l'émetteur**, puis sortir le fichier du vault. La suppression se propose,
     elle ne s'applique pas d'office : c'est peut-être le seul exemplaire.
   - Pour la cohérence vectorielle : proposer la réindexation **des seules
     cibles en défaut** — outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
     `directory: $VAULT/wiki/<cible>` **explicite**, un appel par cible
     (jamais `$VAULT/wiki` seul : le moteur indexe récursivement et
     vectoriserait deux fois les sous-dossiers) si le plugin agentic-toolbox
     est installé, sinon
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"` — avec le chemin de
     la cible en argument, ou sans argument pour tout reprendre (clone + venv)
     (coût API : uniquement les chunks au hash inconnu) — le rapport JSON fait
     foi : `embedded_chunks > 0` = vecteurs manquants/périmés qui viennent
     d'être réparés (notes éditées hors circuit) ; la réécriture complète
     purge par construction les vecteurs orphelins.
     Les reliquats (`wiki/.index/`, `.index/` racine) se suppriment sans
     précaution : ce sont des dérivés, rien ne s'y trouve qui ne se
     reconstruise.
   - Pour un conflit Drive sur un `wiki/<dossier>/.index/` : si la ligne 1 (métadonnées) des
     deux fichiers est identique, fusion mécanique — union des lignes de
     chunks, dédoublonnage par `hash` (deux lignes de même hash sont
     identiques par construction), réécriture atomique, suppression du fichier
     de conflit ; sinon, garder `embeddings.jsonl`, supprimer le conflit,
     relancer la réindexation.
   - Une fois les corrections traitées, ajouter en fin de
     `$VAULT/LOG/YYYY-MM-DD.md` (le fichier du jour — le créer au besoin ;
     jamais dans un `LOG.md` racine hérité, gelé) :
     `## [YYYY-MM-DD] lint | <n> problème(s) détecté(s), <m> corrigé(s)`
     suivi, si la réindexation a tourné, d'une ligne
     `vecteurs : <embedded_chunks> recalculés, <reused_chunks> réutilisés`.
