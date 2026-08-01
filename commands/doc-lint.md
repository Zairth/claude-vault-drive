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
l'agent principal, après validation de l'utilisateur, à partir de ton rapport.

## Préambule obligatoire

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas
   d'échec : ton rapport final est le message d'erreur tel quel — S'ARRÊTER.
   Sinon, la sortie est `$VAULT`.
2. Lire intégralement `$VAULT/INSTRUCTIONS-CLAUDE.md` et s'y conformer
   (règles de maintenance : sources immuables, LOG append-only, INDEX à jour).

## Vérifications (les onze)

1. **Callouts** — deux natures que la convention d'`INSTRUCTIONS-CLAUDE.md`
   sépare par leur durée de vie ; ne jamais les additionner :
   - `> [!question]` dans `wiki/` = **contradiction en souffrance**, à
     trancher → lister fichier + extrait. C'est le seul des deux qui appelle
     une action.
   - `> [!warning]` dans `wiki/` = **mise en garde documentaire**,
     permanente → compter seulement, et le dire ; ne rien réclamer.
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
   chercher `[[<nom-du-fichier-sans-extension>` dans tout le vault (hors la note
   elle-même). Aucune occurrence = orpheline.
3. **Wikilinks pendants** : recenser les cibles de tous les `[[...]]` des
   notes de `wiki/` — la cible est ce qui précède un éventuel `|` (texte
   affiché) ou `#` (section). Une cible qui ne correspond à aucun fichier du
   vault (nom sans extension) ni à aucun alias déclaré dans un frontmatter
   `aliases:` est pendante → lister note + lien. C'est le miroir de la
   vérification 2 : l'orpheline n'est pas pointée, le lien pendant pointe
   dans le vide.
4. **Trous d'INDEX** : chaque note de `wiki/` doit apparaître dans `INDEX.md` —
   lister les absentes. Inversement, lister les entrées d'`INDEX.md` pointant
   vers des fichiers disparus.
5. **Fichiers de conflit Drive** : chercher les motifs `* (1).md`, `* (2).md` et
   `*conflit*` dans tout le vault → lister. Chercher aussi les doublons du mapping
   vectoriel (`embeddings (1).jsonl`, `*conflit*`) dans **chaque**
   `wiki/<dossier>/.index/` → lister séparément (résolution spécifique, voir
   corrections).
6. **inbox/ en attente** : lister les fichiers non ingérés (information, pas erreur).
7. **Frontmatter obligatoire** (modèle de note d'`INSTRUCTIONS-CLAUDE.md`) :
   pour chaque note de `wiki/`, vérifier la présence de `type` + `date` +
   `auteur` + `description`, plus `origine` pour les sources et `question`
   pour les synthèses
   → lister les notes non conformes avec leurs propriétés manquantes.
   Vérifier aussi que `type` s'accorde au dossier (`type: entite` sous
   `entites/`, `type: source` sous `sources/`, `type: enseignements` sous
   `enseignements/`…) : un désaccord fausse l'INDEX et trahit une note écrite
   au mauvais endroit.
8. **Cohérence vectorielle** — il y a **un index par dossier de `wiki/`**
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
     ligne 1 du fichier : provider, modèle, dimension, version) et les
     reporter. **Provider, modèle ou dimension divergents entre deux index**
     = incohérence à signaler : les vecteurs n'ont pas été construits avec le
     même moteur, et les scores de ces dossiers ne veulent plus rien dire
     l'un par rapport à l'autre → réindexation complète.
     Diagnostic de suivi : comparer le `created_at` le plus récent du mapping
     aux dernières entrées `ingest` du journal (`LOG/*.md`, plus un `LOG.md`
     racine hérité s'il existe) — des ingests postérieurs aux
     vecteurs = indexation non suivie (le verdict définitif reste le hash,
     jamais les dates).

9. **Appariement des couches d'origine** — toute pièce ingérée produit deux
   notes de même slug, `sources/<slug>.md` et `enseignements/<slug>.md`.
   Lister les **orphelines d'appariement** : un texte intégral dont personne
   n'a tiré d'enseignement (pièce ingérée puis abandonnée), et surtout un
   enseignement sans son texte (le matériau qui l'appuie a disparu, la chaîne
   de vérification est rompue). Vérifier aussi que les deux se pointent
   mutuellement en wikilink et partagent le même `origine`.
   Enfin, dans `enseignements/`, une note **sans aucun titre `###`** : ses
   enseignements seraient indexés en un seul bloc au lieu d'un par
   enseignement — la granularité de recherche est perdue.
10. **Parasites hors `wiki/`** — les autres vérifications ne regardent que
   `wiki/`, or Obsidian indexe TOUT le vault : ce qui traîne ailleurs pollue
   le graphe humain (l'index sémantique, lui, ne couvre que `wiki/`).
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
   - **nœuds fantômes venus d'`archives/`** : les markdown OCR y référencent
     des images qui n'ont pas été extraites
     (`![img-0.jpeg](img-0.jpeg)`, `[[piece-jointe]]`…). Obsidian affiche ces
     cibles introuvables comme des ronds dans le graphe, et un clic dessus
     **crée** la note vide correspondante. Compter les cibles distinctes de ce
     type dans `archives/` et, s'il y en a, rappeler le remède durable dans
     les corrections. Ne jamais modifier un fichier d'`archives/` : la couche
     est immuable.
11. **Doublons suspectés (pages vivantes)** : sur l'ensemble `wiki/concepts/`
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
   Lister chaque paire avec sa raison (nom / sémantique / les deux).
   Détection seulement — aucune fusion sans validation (voir corrections).

## Rapport final (ton retour à l'agent principal)

1. Le chemin `$VAULT` résolu, écrit en clair (l'agent principal ne connaît pas
   la sortie de vault-check).
2. **La ligne de compteurs**, sur une seule ligne — l'état de santé du vault
   d'un coup d'œil, comparable d'un lint à l'autre :
   `contradictions: n · liens pendants: n · doublons suspectés: n ·
   orphelines: n · trous d'INDEX: n · conflits Drive: n · inbox: n ·
   frontmatters incomplets: n · parasites: n · index manquants: n ·
   appariements rompus: n · notes: n (concepts n · entites n · sources n ·
   enseignements n · syntheses n)`.
   `contradictions` ne compte QUE les `[!question]` en souffrance, augmentés
   des `[!warning]` requalifiés — jamais les mises en garde documentaires,
   qui sont un état normal du vault et non une dette.
3. Le rapport par catégorie (vide = le dire aussi : « rien à signaler »).
4. Un bloc `Pour l'agent principal` — proposer les corrections à l'utilisateur
   et n'appliquer QUE ce qu'il valide :
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
     callout retiré. Pour un `[!warning]` requalifié : le retyper en
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
   - Pour chaque paire de doublons que l'utilisateur confirme — **fusion
     assistée**, dans cet ordre : il choisit la page survivante ; rapatrier le
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
   - Pour les parasites : `.md` inattendu à la racine ou note vide →
     proposer la suppression (rien à sauver dans un fichier vide), ou son
     déplacement dans `wiki/` avec un frontmatter conforme si l'utilisateur
     reconnaît une note qu'il voulait écrire. `.md` posé à la racine de
     `wiki/` → proposer son déplacement dans le dossier qui convient, puis
     l'indexation de ce dossier : tant qu'elle reste là, la note est
     introuvable en recherche sémantique. Nœuds fantômes d'`archives/` →
     le remède n'est pas dans le vault mais dans **Obsidian** : Paramètres →
     Fichiers et liens → Filtres d'exclusion → ajouter `archives/`. Les
     archives sortent alors du graphe et de la recherche Obsidian, sans être
     touchées ni perdues — c'est exactement leur statut (pièces d'origine
     conservées, hors index). Sans cette exclusion, chaque clic sur un rond
     fantôme recrée une note vide à la racine.
   - Pour chaque wikilink pendant : cible renommée ou mal orthographiée →
     corriger le lien vers la page existante ; page réellement manquante →
     proposer sa création ou le délier (texte simple) — jamais de page coquille
     créée juste pour éteindre le compteur.
   - Pour les frontmatters non conformes : proposer une valeur déduite du
     contenu de la note ou du journal (`date` : à défaut, la première mention
     de la note dans `LOG/` ou un `LOG.md` racine hérité ; `description`
     manquante : rapatrier celle de l'entrée `INDEX.md` existante, sinon la
     déduire du contenu) — jamais de valeur inventée sans le signaler.
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
