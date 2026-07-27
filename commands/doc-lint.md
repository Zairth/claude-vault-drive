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

## Vérifications (les neuf)

1. **Contradictions en souffrance** : chercher `> [!warning]` dans `wiki/` →
   lister fichier + extrait du callout.
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
   `*conflit*` dans tout le vault → lister. Chercher aussi dans `wiki/.index/` les
   doublons du mapping vectoriel (`embeddings (1).jsonl`, `*conflit*`) → lister
   séparément (résolution spécifique, voir corrections).
6. **inbox/ en attente** : lister les fichiers non ingérés (information, pas erreur).
7. **Frontmatter obligatoire** (modèle de note d'`INSTRUCTIONS-CLAUDE.md`) :
   pour chaque note de `wiki/`, vérifier la présence de `type` + `date` +
   `auteur` + `description`, plus `origine` pour les sources et `question`
   pour les synthèses
   → lister les notes non conformes avec leurs propriétés manquantes.
8. **Cohérence vectorielle** :
   - `wiki/.index/embeddings.jsonl` absent → « index sémantique jamais
     construit » (information ; remède : la réindexation décrite dans les
     corrections). Un `.index/` à la racine du vault est un reliquat des
     versions ≤ 1.5.3 (l'index vit désormais dans `wiki/.index/`) → proposer
     sa suppression (dérivé jetable).
   - Présent → lire ses métadonnées (outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_info` avec
     `directory: $VAULT/wiki` — purement local, zéro quota — sinon ligne 1 du
     fichier : provider, modèle, dimension, version) et les reporter.
     Diagnostic de suivi : comparer le `created_at` le plus récent du mapping
     aux dernières entrées `ingest` du journal (`LOG/*.md`, plus un `LOG.md`
     racine hérité s'il existe) — des ingests postérieurs aux
     vecteurs = indexation non suivie (le verdict définitif reste le hash,
     jamais les dates).

9. **Doublons suspectés (pages vivantes)** : sur l'ensemble `wiki/concepts/`
   + `wiki/entites/` — les doublons traversent les deux dossiers
   (`Docker.md` dans l'un, `conteneurisation-docker.md` dans l'autre) :
   - collision de **noms normalisés** (casse, accents, tirets/underscores,
     pluriel final) entre noms de fichiers et alias `aliases:` ;
   - moteur sémantique disponible → pour chaque page vivante, `semantic_search`
     avec son titre + sa première phrase (`directory: $VAULT/wiki` explicite) :
     une AUTRE page vivante en tête des résultats avec un score nettement
     détaché du reste = paire suspectée. Moteur indisponible → le noter, la
     normalisation des noms reste faite.
   Lister chaque paire avec sa raison (nom / sémantique / les deux).
   Détection seulement — aucune fusion sans validation (voir corrections).

## Rapport final (ton retour à l'agent principal)

1. Le chemin `$VAULT` résolu, écrit en clair (l'agent principal ne connaît pas
   la sortie de vault-check).
2. **La ligne de compteurs**, sur une seule ligne — l'état de santé du vault
   d'un coup d'œil, comparable d'un lint à l'autre :
   `liens pendants: n · doublons suspectés: n · orphelines: n ·
   trous d'INDEX: n · conflits Drive: n · inbox: n ·
   frontmatters incomplets: n · notes: n (concepts n · entites n ·
   sources n · syntheses n)`.
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
     rappeler les `> [!warning]` à trancher — un callout tranché se
     résout par la convention d'`INSTRUCTIONS-CLAUDE.md` : valeur courante
     mise à jour dans le corps, ancienne version poussée en `## Historique`,
     callout retiré.
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
   - Pour chaque wikilink pendant : cible renommée ou mal orthographiée →
     corriger le lien vers la page existante ; page réellement manquante →
     proposer sa création ou le délier (texte simple) — jamais de page coquille
     créée juste pour éteindre le compteur.
   - Pour les frontmatters non conformes : proposer une valeur déduite du
     contenu de la note ou du journal (`date` : à défaut, la première mention
     de la note dans `LOG/` ou un `LOG.md` racine hérité ; `description`
     manquante : rapatrier celle de l'entrée `INDEX.md` existante, sinon la
     déduire du contenu) — jamais de valeur inventée sans le signaler.
   - Pour la cohérence vectorielle : proposer la réindexation — outil MCP
     `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` avec
     `directory: $VAULT/wiki` **explicite** (jamais de dossier implicite)
     si le plugin agentic-toolbox est installé, sinon
     `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"` (clone + venv)
     (coût API : uniquement les chunks au hash inconnu) — le rapport JSON fait
     foi : `embedded_chunks > 0` = vecteurs manquants/périmés qui viennent
     d'être réparés (notes éditées hors circuit) ; la réécriture complète
     purge par construction les vecteurs orphelins.
   - Pour un conflit Drive sur `wiki/.index/` : si la ligne 1 (métadonnées) des
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
