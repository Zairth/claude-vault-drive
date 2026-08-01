---
description: Mesurer la qualité de recherche du vault — banc de questions de référence (BENCH.md) ; mode mécanique reproductible, ou mode réel jouant /doc-query lui-même
argument-hint: "[creer | reel [Q3 Q7 ...]]"
---

# /doc-bench — le mètre étalon de la recherche

**Instrument facultatif.** Rien dans le plugin ne l'exige : le vault
s'initialise, s'alimente et s'interroge sans jamais l'ouvrir, et aucun réglage
n'attend d'être calibré. Il sert à qui veut **vérifier ou améliorer** la
qualité de recherche sur son propre corpus — repérer une régression après une
mise à jour du moteur, ou décider si un changement vaut d'être gardé. La
plupart des vaults n'en auront jamais besoin.

Le banc est une liste de questions figée (`BENCH.md`, à la racine du vault),
chacune avec les notes qu'une bonne recherche doit remonter. Trois modes :

| mode | ce qu'il mesure | déterministe | coût |
|---|---|---|---|
| `creer` | — (propose et fige le banc) | — | lecture du vault |
| *(défaut)* | la **couche de récupération** isolée | oui | 1 vectorisation / question |
| `reel` | ce que **`/doc-query` cite vraiment** | non | 1 sub-agent lecteur / question |

Les deux mesures ont des métiers distincts et **leurs scores ne se comparent
jamais l'un à l'autre** :

- le mode par défaut est mécanique — aucun jugement n'entre dans le score,
  donc il détecte un gain de +1 entre deux versions du moteur ;
- le mode `reel` est plus proche du vécu — c'est lui qui dit si le vault
  répond, donc s'il faut investir dans la recherche — mais son propre bruit
  (le jugement de l'agent varie d'un run à l'autre) noierait un petit gain.

Un run de mesure, quel que soit le mode, **ne modifie jamais `BENCH.md`** :
toute retouche du banc passe par `creer` ou par une validation explicite.

## Préambule obligatoire (tous modes)

1. Exécuter `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-check.sh"`. En cas
   d'échec : transmettre le message d'erreur tel quel et S'ARRÊTER. Sinon, la
   sortie est `$VAULT`.
2. Mode `creer` (explicite, ou `$VAULT/BENCH.md` absent) → section
   « Mode création ». Sinon, lire `$VAULT/BENCH.md` : questions et attendues.
   Une attendue pointant vers une note disparue → question **exclue du score**,
   signalée « banc à mettre à jour », jamais comptée en échec.
3. `$ARGUMENTS` contient `reel` → section « Mode réel » ; sinon → section
   « Mode mécanique ».

## Mode création — proposer le banc

Déléguer à un **sub-agent** (outil Agent, type `Explore`, avant-plan) pour
garder le contexte principal propre. Sa mission :

1. Lire `$VAULT/INSTRUCTIONS-CLAUDE.md`, puis `INDEX.md` et parcourir `wiki/`
   (au moins les frontmatters `description`) pour cartographier le vault.
2. Rédiger **~20 questions** (vault petit → réduire : viser une question pour
   2-3 notes, minimum 5) couvrant, en les mélangeant :
   - des factuelles dont la réponse vit dans un enseignement ;
   - au moins une dont la réponse n'existe QUE dans le texte intégral d'une
     source, qu'aucun enseignement n'a retenue — c'est elle qui mesure
     l'utilité de cette couche ;
   - des transversales (plusieurs notes, syntheses) ;
   - des centrées sur un concept ou une entité ;
   - et plusieurs formulées en **synonymes** — jamais les mots exacts des
     notes : ce sont elles qui départagent la sémantique de grep.
3. Pour chaque question : les **notes attendues** (1 à 3, wikilinks) — celles
   qu'une bonne recherche doit remonter. Une note qui répond réellement mais
   n'est pas attendue fabriquera un faux échec : mieux vaut un attendu large
   qu'un attendu incomplet, mais jamais une note « à peu près liée ».
   **Attendre la couche la plus travaillée qui réponde** : si l'information
   tient dans un enseignement ou une page de concept, c'est elle l'attendue —
   pas le texte intégral de la source, qui la contient aussi mais noyée. Le
   texte intégral n'est attendu que pour une question à laquelle lui seul
   répond (un détail qu'aucun enseignement n'a retenu).
4. Retourner le banc complet.

Puis, en contexte principal : faire valider les questions à l'utilisateur
(retirer/reformuler/ajouter), écrire `$VAULT/BENCH.md` au format ci-dessous, et
ajouter en fin de `$VAULT/LOG/YYYY-MM-DD.md` (fichier du jour, créé au besoin) :
`## [YYYY-MM-DD] bench | banc créé : <n> questions`. Un `BENCH.md` existant
(relance avec `creer`) → proposer complément ou refonte, jamais d'écrasement
sans validation.

Format de `BENCH.md` (racine du vault — hors index sémantique par
construction) :

```markdown
# BENCH — questions de référence

Banc de mesure de la recherche (/doc-bench). Figé entre deux validations :
les runs le lisent, ne l'écrivent jamais.

## Q1 — <la question>
attendu : [[note-a]], [[note-b]]
```

## Mode mécanique (défaut) — scorer la récupération

Déléguer l'intégralité de la mesure à un **sub-agent** (outil Agent, type
`Explore`, avant-plan) : il produit le rapport, le contexte principal ne voit
ni les recherches ni les notes. Sa mission :

1. **Réindexation incrémentale d'abord** (mesurer sur un index à jour) —
   il y a **un index par dossier de `wiki/`** : obtenir la liste par
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index-targets.sh"`, puis un
   `mcp__plugin_agentic-toolbox_toolbox__semantic_index_build` par cible avec
   `directory: $VAULT/wiki/<cible>` **explicite** ; sinon
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-index.sh"` sans argument, qui
   boucle lui-même. Moteur indisponible → ouvrir le rapport par
   « ⚠ sémantique indisponible (<raison>) — score grep seul » et sauter les
   mesures sémantiques.
2. Pour chaque question, mécaniquement :
   - **sémantique** : `semantic_search` top 3, **un seul appel** portant
     `directories: [toutes les cibles]` (`question` telle quelle) — la réponse
     rend un groupe par dossier.
     Les espaces vectoriels étant disjoints, **les scores ne se comparent pas
     d'une cible à l'autre** : le rang d'une attendue est son rang **dans
     l'index de son propre dossier**, jamais dans un classement global
     reconstitué. Une attendue de `entites/` au rang 1 de `entites/` compte
     comme rang 1, quel que soit le score des pistes de `sources/`.
     → rang de la première attendue (1-3, ou absente) ;
   - **grep** : les mots pleins de la question (sans articles ni mots-outils)
     sur `wiki/` → attendues touchées ou non ;
   - **+1 saut** : les wikilinks `[[...]]` des notes remontées contiennent-ils
     une attendue absente de ces remontées ? C'est ce que la cascade de
     `/doc-query` fait gratuitement (elle suit les wikilinks des notes
     remontées) : l'écart avec `sémantique@3` chiffre ce que le graphe
     rattrape déjà, et donc ce qu'une expansion par backlinks apporterait — ou
     non. L'INDEX est volontairement exclu du calcul : il liste TOUTES les
     notes, un saut par l'INDEX trouverait tout et ne mesurerait rien.
3. **Scores** (mêmes définitions à chaque run — c'est ce qui les rend
   comparables) :
   - `sémantique@3` : x/n questions avec ≥ 1 attendue dans le top 3 de son
     dossier, et le rang moyen des touchées ;
   - `+1 saut` : x/n questions avec ≥ 1 attendue remontée **ou** dans les
     wikilinks des notes remontées ;
   - `grep` : x/n questions avec ≥ 1 attendue touchée ;
   - `couverture` : x/n questions dont TOUTES les attendues sont trouvées
     (remontées, wikilinks et grep confondus).
4. **Rapport** : la ligne de score
   `sémantique@3 x/n (rang moyen r) · +1 saut x/n · grep x/n · couverture x/n` ;
   le tableau par question (dossier et rang de l'attendue, note pivot du
   +1 saut, grep, verdict) ; **une ligne de répartition par couche** — d'où
   viennent les touches, tous dossiers confondus. C'est elle qui dira si les
   textes intégraux de `sources/` étouffent les enseignements ou les
   complètent, question qu'aucun score global ne répond ; pour chaque échec, ce que la recherche a renvoyé **à la place**
   (c'est le carburant des évolutions du moteur) ; les attendues disparues.

## Mode réel (`reel`) — mesurer ce que /doc-query répond

`$ARGUMENTS` peut restreindre le run à un sous-ensemble (`reel Q3 Q7 Q17`).

1. **Annoncer le coût et attendre l'accord** : « <n> questions → <n> sub-agents
   lecteurs, chacun ouvre plusieurs notes ». Au-delà de ~10 questions,
   proposer aussi un sous-ensemble : les questions en échec au dernier run
   mécanique, plus quelques réussies comme témoin.
2. Indexer **une seule fois** pour tout le run (mêmes outils qu'au mode
   mécanique). Moteur indisponible → prévenir que le run mesurerait
   `/doc-query` en repli grep, donc incomparable à un run normal, et demander
   confirmation.
3. Lancer les questions par vagues de 4 au plus (outil Agent, avant-plan).
   Chaque lecteur reçoit exactement cette mission :

   > Lis `${CLAUDE_PLUGIN_ROOT}/commands/doc-query.md` et exécute sa section
   > « Recherche » pour la question suivante, sur le vault `<$VAULT>` :
   > `<la question>`. Le vault vient d'être indexé — ne le réindexe pas.
   > N'écris RIEN dans le vault. Ne rédige pas la réponse en détail : ce qui
   > est mesuré, ce sont les notes sur lesquelles tu l'aurais fondée. Retourne
   > UNIQUEMENT deux lignes :
   > `sources : <slugs séparés par des virgules, dans l'ordre où tu les citerais>`
   > `verdict : repondu | partiel | rien-trouve`

   Le lecteur lit la procédure dans le fichier de commande lui-même : la
   mesure suit `/doc-query` automatiquement, sans copie à maintenir ici.
4. **Scores** : `réel` (x/n questions dont les sources citées contiennent ≥ 1
   attendue) · `citations complètes` (x/n avec TOUTES les attendues) ·
   `à vide` (x/n rendues `rien-trouve`).
5. **Rapport** : la ligne de score ; par question, sources citées, attendues
   manquantes, verdict ; les notes citées hors attendus qui répondent
   réellement (attendus manquants au banc, à faire valider — ou bruit) ; et la
   confrontation au dernier run mécanique **sans additionner les deux
   scores** : une question ratée mécaniquement mais réussie ici prouve que la
   cascade (wikilinks, INDEX, grep) rattrape la récupération ; l'inverse
   pointe un classement correct mais mal exploité.

## Fin de run (les deux modes de mesure)

Présenter le rapport, puis proposer d'ajouter en fin de
`$VAULT/LOG/YYYY-MM-DD.md` (fichier du jour, créé au besoin) :

- mécanique :
  `## [YYYY-MM-DD] bench | sémantique@3 x/n · +1 saut x/n · grep x/n · couverture x/n`
- réel :
  `## [YYYY-MM-DD] bench-reel | réel x/n · citations complètes x/n`

suivi d'une ligne listant les questions en échec. Rien d'autre à écrire.
