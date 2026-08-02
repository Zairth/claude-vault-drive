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

Puis, en contexte principal : **écrire directement** `$VAULT/BENCH.md` au
format ci-dessous — l'utilisateur n'a pas lu le corpus, faire valider vingt
questions qu'il n'a pas les moyens de juger ne vérifie rien. Contrôler
soi-même, avant d'écrire, que chaque attendue existe et qu'aucune question ne
reprend les mots exacts de sa note (elle serait trouvée par un grep et ne
mesurerait rien). Puis
ajouter en fin de `$VAULT/LOG/YYYY-MM-DD.md` (fichier du jour, créé au besoin) :
`## [YYYY-MM-DD] bench | banc créé : <n> questions`. Un `BENCH.md` existant
(relance avec `creer`) → jamais d'écrasement : le banc est un étalon, le
remplacer rendrait incomparables tous les runs passés. Compléter, et signaler
les questions dont une attendue a disparu.

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
   « ⚠ sémantique indisponible (<raison>) — score partiel » et sauter les
   mesures sémantiques. Le moteur portant AUSSI le bras bm25, son absence
   emporte les deux colonnes : il ne reste que le `+1 saut` et le repli grep,
   hors score.
2. Pour chaque question, mécaniquement :
   - **sémantique** : `semantic_search` top 3, **un seul appel** portant
     `directories: [toutes les cibles]`. **La question part
     CARACTÈRE POUR CARACTÈRE telle qu'elle est écrite dans `BENCH.md`** :
     ni reformulée, ni corrigée, ni « rendue plus naturelle ». Pas de virgule
     ajoutée, pas d'inversion sujet-verbe. Un banc est un étalon : deux runs
     qui n'envoient pas la même chaîne ne mesurent pas la même chose, et
     l'écart qu'on cherche à lire — un rang, parfois moins — est plus petit
     que celui qu'une reformulation introduit. Copier la ligne du fichier,
     ne rien en faire d'autre. La réponse
     rend un groupe par dossier.
     Les espaces vectoriels étant disjoints, **les scores ne se comparent pas
     d'une cible à l'autre** : le rang d'une attendue est son rang **dans
     l'index de son propre dossier**, jamais dans un classement global
     reconstitué. Une attendue de `entites/` au rang 1 de `entites/` compte
     comme rang 1, quel que soit le score des pistes de `sources/`.
     → rang de la première attendue (1-3, ou absente) ;
   - **bm25** : `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-lexical.sh"
     "<la question, telle quelle>" "" 3` — **un seul appel**, toutes les
     cibles, top 3 par dossier, exactement la même fenêtre que le bras
     sémantique. Comme lui, le rang d'une attendue est son rang **dans son
     propre dossier**. → rang de la première attendue (1-3, ou absente).
     C'est le **vrai** bras lexical, celui que le hook et `/doc-query`
     emploient — pas une approximation. La différence n'est pas cosmétique :
     BM25 pondère par IDF et **normalise par la longueur du document**, donc
     il ne souffre pas du défaut d'un grep naïf, où les pièces les plus
     longues remontent en contenant mécaniquement tous les mots.
     Ce qu'on cherche ici n'est pas son score propre — il est attendu plus bas
     que le sémantique — mais sa **contribution marginale**, en deux chiffres
     à reporter explicitement :
     - les questions où bm25 touche une attendue que le sémantique **rate** :
       c'est la couverture qu'une fusion ajouterait ;
     - les questions où bm25 la classe **mieux** que le sémantique : c'est le
       gain de rang qu'une fusion apporterait.
     Deux zéros = la fusion lexical/sémantique n'a rien à offrir sur ce
     corpus, et c'est la seule façon de trancher cette question, qui n'a
     jamais été mesurée. Moteur indisponible → le dire, sauter la colonne, ne
     pas lui substituer un grep maison : ce ne serait pas la même mesure.
   - **grep** (facultatif, **hors score**) : si le moteur est indisponible,
     un repli lisible — les mots de 5 caractères ou plus, accents repliés,
     casse ignorée, attendue touchée dès la moitié d'entre eux. À reporter
     comme tel, jamais dans la ligne de score : mesuré, ce critère appliqué
     implicitement puis figé a rendu 11, 10 puis 6 sur un corpus **strictement
     identique**. Un chiffre non reproductible est pire qu'absent — il se
     compare quand même ;
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
   - `bm25@3` : x/n questions avec ≥ 1 attendue dans le top 3 de son dossier,
     et le rang moyen des touchées — mêmes définitions que `sémantique@3`,
     donc directement comparables l'une à l'autre ;
   - `couverture` : x/n questions dont TOUTES les attendues sont trouvées
     (remontées, wikilinks et bm25 confondus).
4. **Rapport** : la ligne de score
   `sémantique@3 x/n (rang moyen r) · +1 saut x/n · bm25@3 x/n (rang moyen r) ·
   couverture x/n`, suivie de la ligne de contribution marginale :
   `bm25 seul : n question(s) · bm25 mieux classée : n question(s)` ;
   le tableau par question (dossier et rang de l'attendue, note pivot du
   +1 saut, rang bm25, verdict) ; **une ligne de répartition par couche** — d'où
   viennent les touches, tous dossiers confondus. C'est elle qui dira si les
   textes intégraux de `sources/` étouffent les enseignements ou les
   complètent, question qu'aucun score global ne répond ; pour chaque échec, ce que la recherche a renvoyé **à la place**
   (c'est le carburant des évolutions du moteur) ; les attendues disparues.

## Mode réel (`reel`) — mesurer ce que /doc-query répond

`$ARGUMENTS` peut restreindre le run à un sous-ensemble (`reel Q3 Q7 Q17`).

1. **Annoncer le coût et attendre l'accord** : « <n> questions → <n> sub-agents
   lecteurs, chacun ouvre plusieurs notes ». C'est la seule question de cette
   commande, et elle porte sur une dépense, pas sur un jugement. Au-delà de
   ~10 questions, proposer aussi un sous-ensemble : les questions en échec au
   dernier run mécanique, plus quelques réussies comme témoin.
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
  `## [YYYY-MM-DD] bench | sémantique@3 x/n (rang moyen r) · +1 saut x/n · bm25@3 x/n · couverture x/n`
- réel :
  `## [YYYY-MM-DD] bench-reel | réel x/n · citations complètes x/n`

suivi d'une ligne listant les questions en échec. Rien d'autre à écrire.
