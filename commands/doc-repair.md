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
2. `wiki/sources/<slug>.md` — le **texte intégral standardisé**. Le passage y
   figure-t-il ? Sous quelle forme ?
3. **La pièce archivée, et il y en a souvent DEUX.** Le frontmatter des notes
   d'origine porte jusqu'à deux chemins, et ils ne disent pas la même chose :
   - `origine:` — ce dont la note a été faite : la **transcription** archivée
     (sortie d'OCR, lecture d'une capture, export markdown) ;
   - `original:` — **la pièce qui fait foi**, quand elle diffère : le PDF, le
     scan, l'image. Absent = la transcription est la pièce.

   **Ouvrir les deux quand les deux existent, et dans cet ordre : d'abord la
   transcription, puis l'original.** L'original ne s'ouvre pas n'importe
   comment : **router selon son format**, exactement comme `/doc-ingest` le
   fait en entrée — un fichier ne se lit pas de la même façon selon ce qu'il
   est, et se tromper de voie donne un contrôle qui ne contrôle rien.
   - **Capture d'écran** (`.png`, `.jpg`, `.webp`, `.heic`…) → l'**ouvrir
     directement** avec l'outil Read, qui affiche les images. Jamais d'OCR :
     réglé pour un document, il aplatit une interface en flux linéaire et fait
     disparaître la disposition — c'est même souvent là qu'est née l'erreur
     qu'on vérifie.
   - **PDF, scan** → attention, c'est le cas piégeux. La transcription
     archivée **est déjà la sortie d'OCR de ce PDF** : la relancer rendrait le
     même texte, avec la même erreur. Un OCR ne se contrôle pas par lui-même.
     Passer par une **voie de lecture différente** — un extracteur de texte
     local (`pdftotext`, `pdftk`, `pandoc`) s'il est présent sur la machine.
     Rien de tel disponible → **ne pas relancer l'OCR** : le dire, et déclarer
     la vérification **partielle** en précisant que l'original n'a pas pu être
     lu autrement que par le moteur qui a produit la transcription.
   - **Bureautique binaire** (`.docx`, `.xlsx`, `.pptx`…) → convertir avec ce
     qui est présent (`libreoffice --headless --convert-to txt|csv`,
     `pandoc`), lire la conversion. Aucun convertisseur → vérification
     partielle.
   - **Texte** (`.md`, `.txt`, `.csv`, `.eml`, code…) → lire tel quel.
   - **Audio, vidéo** → hors périmètre : vérification partielle, le dire. Une transcription est une lecture
   automatique : elle saute une ligne, confond un caractère, aplatit un
   tableau. Vérifier une correction contre elle seule, c'est vérifier contre la
   même machine qui a peut-être produit l'erreur — le contrôle ne prouve rien.
   Et si la transcription et l'original divergent sur le passage, **c'est
   l'original qui tranche**, et cette divergence est elle-même une trouvaille :
   elle affecte tout ce que la transcription a produit, pas seulement ce
   passage → le dire dans le rapport et proposer un `> [!warning]` sur la note
   d'enseignements.
   `original:` illisible pour toi (format non ouvrable, PDF non converti) → le
   dire, et traiter la vérification comme **partielle** : confirmée par la
   transcription, non confirmée par la pièce.

Puis conclure, et **le dire explicitement dans le rapport** :

- **la pièce dit la nouvelle valeur** → la note la trahissait. Correction
  confirmée par la pièce : c'est le cas le plus sûr, dis-le ;
- **la pièce dit l'ancienne valeur** → le vault était fidèle, et c'est
  l'information qui a changé depuis. Ce n'est pas une erreur de
  restitution : convention `## Historique` (voir 4) ;
- **la pièce ne dit ni l'un ni l'autre**, ou est illisible sur ce point →
  **le signaler comme tel** et ne rien affirmer. Proposer quand même la
  correction demandée, mais accompagnée d'un `> [!warning]` disant que la
  pièce ne la confirme pas. On ne fabrique pas une certitude qu'on n'a pas.

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

Doute entre les deux → **trancher quand même**, en disant sur quoi tu te
fondes : la pièce est datée et le vault ne l'est pas, la valeur nouvelle est
attestée ailleurs, la formulation fautive n'a jamais eu de support. Renvoyer
le choix à l'utilisateur ne l'aide pas — il n'a pas lu la pièce, c'est toi qui
viens de la rouvrir. Vraiment indépartageable → le dire, retenir la lecture la
mieux étayée, et proposer un `> [!question]` qui garde l'autre en mémoire.

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
   - appliquer d'office ce qui est **mécanique et réversible** (une valeur
     corrigée dans une page vivante, un wikilink, une entrée d'INDEX) ;
     demander l'autorisation pour ce qui **touche une couche immuable ou
     supprime quelque chose**, en une fois, verdict à l'appui — jamais en
     demandant à l'utilisateur de choisir à ta place ;
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
