# Changelog — claude-vault-drive

Ce que contient chaque mise à jour du plugin : la raison en une ligne, puis le
détail des changements — de quoi savoir si elle vaut le coup avant de
l'installer. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/), versions en
[semver](https://semver.org/lang/fr/) (patch = fix/docs, minor = feature).

Installer une mise à jour : `/plugin marketplace update zairth_store` puis
`/reload-plugins` (le cache n'est invalidé que si la version change).

## [1.48.0] — 2026-08-07

**Raison de l'update** : le livrable le plus important de `--all-references` — la compilation qui porte les pièces — était le seul qu'aucun contrôle ne vérifiait.

### Ajouté
- **`verify-citations.py` balaie aussi `references/`.** Il ne connaissait que
  `wiki/enseignements/`. Or une compilation est précisément le document destiné
  à être opposé : c'est celui dont les repères doivent le plus être
  re-vérifiables. Lancé sur une compilation réelle, il ne rendait rien —
  « aucune citation trouvée » — et ses 53 pointeurs n'avaient été contrôlés par
  personne.
- **Deux formes d'attribution reconnues.** Dans `enseignements/`, le bloc
  `> [!source]` que l'indexation soustrait au vecteur ; dans une compilation,
  une ligne en clair — ce fichier n'étant pas vectorisé, il n'y a rien à
  soustraire. Le contrôle s'ancre désormais sur l'**attribution** et non sur la
  citation : l'attribution a une forme reconnaissable — un chemin entre accents
  graves —, la citation en a deux.
  L'auteur se lit aussi dans le **titre d'entrée** d'une compilation
  (`**<date> — <auteur>**`) : le chercher au seul endroit prévu par l'autre
  forme le déclarait manquant sur toutes les entrées.
- **Repère toléré à la lecture, prescrit à l'écriture.** `Ligne 292`, `l. 292`
  et `L292` désignent la même chose et des fichiers existants portent chacune
  des formes ; la commande n'en prescrit qu'une. Laxiste au contrôle, strict à
  l'écriture : c'est ce qui évite de casser l'existant sans laisser la forme
  dériver.

- **Trois natures d'original, et une seule est adressable par ligne.** Un
  export texte se cite à la ligne ; un PDF se cite sans ligne ; une **série de
  captures** ne se cite ni par l'une ni par l'autre. Le contrôle distinguait
  mal ce dernier cas d'une pièce manquante : un dossier de captures est un
  original légitime, mais le dossier ne désigne aucun endroit. Il le dit
  maintenant pour ce que c'est — série de N captures, citer la capture précise
  et son rang, la vérification s'achève à l'œil.
- **Une transcription n'est jamais un original**, `.transcription.md` compris.
  Le contrôle ne refusait que `.ocr.` et les versions standardisées. Le cas des
  captures est le plus trompeur : leur transcription n'a aucune autre lecture
  qui la contredise, puisqu'un agent l'a produite à l'œil — c'est exactement ce
  qui l'empêche de tenir lieu de pièce.

- **Dire qu'une partie d'`archives/` est invisible depuis Obsidian.** Son
  explorateur n'affiche que les formats qu'il sait rendre : un export brut en
  `.json` ou en `.txt` n'apparaît pas, bien qu'il soit là et intact — et ce
  sont souvent les pièces qui font le plus foi. Constaté en usage : on conclut
  de l'absence à l'écran que la pièce manque. Le template le dit désormais, et
  renvoie à l'explorateur du système pour ouvrir un original de ce type.

### Modifié
- **`/doc-query --all-references`** — la forme de l'attribution d'une
  compilation est désormais **écrite dans la commande**, au caractère près.
  Elle ne l'était pas : l'agent l'inventait, et il écrivait `l. 292` là où le
  vault tient `Ligne 292`. Une abréviation de développeur sur une pièce
  destinée à être lue par un tiers lui demande de deviner.

## [1.47.1] — 2026-08-07

**Raison de l'update** : la documentation écrivait les commandes en forme courte (`/doc-query`), qui échoue avec `Unknown command`. Un utilisateur suivant le README à la lettre ne pouvait rien lancer.

### Corrigé
- **`/doc-query --all-references` — une question porte souvent plusieurs
  demandes, et elles ne se valent pas.** La règle ne connaissait qu'un critère
  par question : trouver un terme littéral pour l'une des demandes dispensait
  de fait des autres. « Comment X a géré l'arrivée de Y, combien de fois s'est-il
  plaint, et a-t-il été de bonne foi ? » en contient trois, dont deux sans
  aucun terme cherchable. Chacune doit désormais être déclarée pour ce qu'elle
  est.
  **Et une demande qui appelle un nombre est traitée à part** : « combien de
  fois » produit un chiffre, et un chiffre se lit comme une mesure même quand
  c'est un avis. La définition de ce qu'on compte n'est pas dans le corpus,
  elle vient du lecteur — elle s'écrit, avec ce qu'elle exclut. Un chiffre
  livré sans sa définition est la seule façon, dans ce mode, de faire passer un
  jugement pour une preuve.
- **`--all-references` — une seule ligne de temps, tous canaux confondus.** Le
  rapport annonçait l'ordre chronologique et la règle n'interdisait pas de
  grouper par canal : chaque changement de groupe produisait alors un retour en
  arrière, constaté d'une heure cinquante-trois sur un rapport réel. Au-delà de
  la cohérence, l'entrelacement **est** la matière : ce qui a été dit en privé à
  la minute où autre chose se disait en public ne se lit que sur une ligne
  unique.
- **`--all-references` — une pièce brute ne se cherche pas comme un markdown.**
  L'obligation de remonter à l'original existait mais restait lettre morte,
  faute de dire comment. Un export au format JSON échappe ses guillemets en
  `\"` et ses retours à la ligne en `\n` littéraux : chercher la citation telle
  qu'elle est écrite dans la note n'y rend rien, et **l'échec est silencieux**
  — on conclut « absente de la pièce » alors qu'elle y est. Mesuré sur un
  export réel : 108 guillemets échappés, 248 retours à la ligne.
- **`--all-references` — deux fichiers, jamais un seul.** La règle disait où va
  chaque livrable mais jamais qu'il ne fallait pas les réunir : un fichier
  portant à la fois la compilation et la synthèse n'a plus de bon endroit où
  aller. Dans `syntheses/`, il traîne les entrées recopiées dans l'index —
  mesuré sur un cas réel, 48 entrées dont 39 déjà vectorisées par
  `wiki/sources/`, soit 81 % du fichier compté deux fois. Dans `references/`,
  c'est la synthèse qui devient introuvable, alors qu'elle est la seule prose
  neuve du lot.
- **Forme d'appel des commandes.** Celles d'un plugin s'appellent par leur nom
  complet, préfixé : `/claude-vault-drive:doc-query …`. Le README et
  `PREREQUIS.md` le disent désormais **avant la première commande montrée**, et
  non après — un lecteur rencontrait `/doc-ingest` deux écrans plus haut que
  l'explication. Les deux documents continuent d'écrire la forme abrégée dans
  leur prose, en le déclarant : préfixer 78 occurrences les rendrait
  illisibles, et c'est la lisibilité qui fait lire un README.

## [1.47.0] — 2026-08-07

**Raison de l'update** : une citation sans auteur ni point de retour n'est pas une preuve, c'est une affirmation. La contrôler supposait de relire la pièce entière — donc personne ne la contrôlait.

### Ajouté
- **Bloc d'attribution sous chaque citation**, dans `enseignements/` :

  ```
  > « <citation verbatim ≤ 125 caractères> »

  > [!source]- <auteur>, <date de l'entrée>
  > `wiki/sources/<slug>.md` Ligne <n>
  > original `archives/<pièce brute>` Ligne <n>
  ```

  Trois questions distinctes dont aucune ne se déduit des deux autres :
  **qui** l'a dit, **dans quelle pièce**, **où exactement**.
  **Deux pointeurs, deux rôles.** La note de `wiki/sources/` est toujours
  adressable ligne à ligne, quelle que soit la pièce : elle donne le repère
  précis. L'**original** est la pièce brute, celle qui n'a subi aucun
  traitement : c'est elle qui fait foi. Sans lui, la citation ne remonte qu'à
  une *lecture* de la pièce — or c'est la lecture qui est faillible, et qu'il
  faut pouvoir contredire.
  L'exigence se gradue selon ce que le format porte, parce que réclamer d'un
  format ce qu'il n'a pas ne produit que des repères inventés : ligne
  obligatoire sur une pièce lisible ligne à ligne, **rien pour un PDF** — il
  n'a pas de lignes, il a une mise en page, et `p. <n>` n'y est qu'un bonus.
- **`scripts/verify-citations.py`** — le contrôle qui rend la règle tenable.
  Ajouter un repère résout un problème et en crée un pire : un repère est un
  chiffre, et un chiffre se fabrique sans effort. Une ligne inventée donne à
  une citation approximative l'**apparence** d'une citation vérifiée.
  Le script rouvre les deux pièces et regarde. Défauts distingués : citation
  sans bloc · bloc sans auteur · repère faux, la ligne réelle étant donnée ·
  ligne manquante sur une pièce qui en admet une · citation introuvable ·
  original absent · original désignant une transcription au lieu d'une pièce
  brute. Sorties `0` / `1` / `2` (rien de contrôlable) / `3`.
  De la double vérification sort un contrôle qui n'existe nulle part ailleurs :
  une citation **présente dans la version standardisée et absente de
  l'original** n'a ni mauvais repère ni mauvais texte — c'est la
  **standardisation** qui l'a altérée. Aucune relecture de note n'attrape ça.
  **Deux comportements que seule l'épreuve sur un vault réel a révélés.** Une
  note condense parfois une entrée en n'en gardant que les valeurs, rejointes
  par d'autres séparateurs et avec une date reformatée : la déclarer
  introuvable serait un faux positif, l'accepter comme une citation en serait
  un autre. Elle est donc localisée et **nommée pour ce qu'elle est** —
  recomposée, pas verbatim. Et les **échappements** d'un export comptent autant
  que les blancs : un format JSON stocke ses guillemets en `\"` et ses retours
  à la ligne en `\n` littéraux. Mesuré sur un export réel — 108 guillemets
  échappés, 248 retours à la ligne — sans les défaire, **aucune** citation de
  la note concernée n'était retrouvable dans la pièce brute ; en les défaisant,
  28 sur 29 le sont à la ligne près.
  La localisation se fait **au caractère**, pas dans une fenêtre de quelques
  lignes autour du repère : une fenêtre valide un repère faux dès qu'il tombe à
  côté de peu, c'est-à-dire exactement le cas à attraper. Citation élidée
  comparée fragment par fragment dans l'ordre, blancs normalisés, le reste au
  caractère près.
- **Le bloc d'attribution est tenu hors du texte vectorisé.** L'indexation
  passe `--exclude-callout source` au moteur, qui l'accepte depuis sa 4.7.0.
  Mesuré sur un corpus réel : section médiane 221 caractères, bloc
  d'attribution 110 — la moitié du vecteur serait des chemins et des chiffres.
  Un vecteur étant une moyenne, ce bloc tirerait tous les chunks d'une note
  vers une même direction et abîmerait la discrimination.
  **Moteur plus ancien : l'option est retirée de l'appel, pas l'indexation.**
  Les blocs sont alors vectorisés avec le texte — une perte de finesse se
  rattrape par une mise à jour, un index qu'on n'a pas pu construire non.
  Un avertissement le dit sur `stderr`.
  Mesuré sur une note réelle migrée : 32 chunks avant comme après — aucun
  perdu —, **27,5 % de caractères vectorisés en moins**, aucun bloc
  d'attribution restant dans un vecteur, et le contenu intégral toujours rendu
  par la recherche.
  Deux règles en découlent, portées par la convention et non par le moteur :
  **l'auteur d'une citation figure aussi parmi les wikilinks de sa section**
  — sinon son nom sort du vecteur et « les messages où telle personne se
  plaint » cesse de remonter —, et **rien de cherchable n'entre dans ce bloc**.

### Modifié
- **`/doc-ingest`** — le dossier d'ingestion porte l'attribution complète de
  chaque citation, et **la ligne s'obtient par `grep -n`, jamais à l'estime**.
- **`/doc-lint`** — quatorzième vérification : citations sans attribution,
  repère faux, original manquant ou désignant une transcription. Le code `2` y
  est traité comme partout ailleurs — **une absence de contrôle, pas un
  succès**. Deux défauts que le script ne voit pas et que le lint relève :
  auteur absent des wikilinks de sa section, et contenu cherchable enfermé dans
  le bloc exclu.
- **`/doc-query --all-references`** — chaque entrée rendue porte son auteur, la
  note de `wiki/sources/` avec sa ligne, et l'original. Une entrée qui sert de
  contre-argument doit pouvoir être rouverte dans la source non traitée, sans
  quoi elle ne vaut que ce que vaut sa transcription. Ce rapport n'étant pas
  une note du vault, l'attribution s'y écrit en clair.
- **`vault-template/INSTRUCTIONS-CLAUDE.md`** — la règle entre dans les
  conventions du vault, à côté de la limite de 125 caractères.
- **`scripts/pdf-text.py`** — le texte est disponible page par page
  (`pages_of`), ce qui permet de situer une citation dans un PDF. Sortie en
  ligne de commande inchangée, vérifiée identique à l'octet sur quinze PDF.

## [1.46.0] — 2026-08-07

**Raison de l'update** : une signature électronique ne s'écrit pas dans le texte d'un PDF. Lue par extraction ou par OCR, une pièce signée est indiscernable d'une pièce qui ne l'est pas — et le vault concluait « non signée » à partir d'un silence.

### Ajouté
- **`scripts/pdf-signatures.py`** — relevé des signatures électroniques d'un
  PDF, bibliothèque standard seule, aucun réseau. Rend pour chaque signature
  le signataire déclaré, la date, le lieu, le format, et vérifie si le
  `/ByteRange` **couvre tout le fichier**. Codes de sortie : `0` signatures
  apposées, `1` aucun champ de signature, `2` champs ouverts mais vides —
  pièce préparée, non signée —, `3` fichier illisible.
  Le cas qui motive l'ajout est ordinaire et il est grave : le texte d'un
  document signé n'affiche souvent que des noms dactylographiés sous des
  mentions de fonction. Ni l'extraction ni l'OCR ne peuvent voir autre chose,
  parce que la signature n'est pas dans le texte — elle est dans une structure
  du fichier. Une note qui affirme « non signée » sur cette base n'énonce pas
  un constat mais une **conclusion tirée d'un silence**, et elle porte sur ce
  qui fait foi.
- **Détection des ajouts postérieurs à la signature.** Une signature ne
  garantit que les octets que son `/ByteRange` désigne. Quand aucune ne
  couvre la fin du fichier, le document a été modifié après avoir été signé,
  et le relevé le dit avec le nombre d'octets concernés. Le cas des signatures
  successives, où seules les dernières couvrent l'ensemble, est traité comme
  normal et ne déclenche rien.

### Modifié
- **`/doc-ingest`** — le relevé se lance sur **tout** PDF, y compris celui qui
  part à l'OCR : un scan signé est un cas ordinaire, et c'est justement celui
  où le texte ne dira rien. Ne jamais déduire du texte qu'une pièce n'est pas
  signée.
- **`/doc-repair`** — quand la contradiction porte sur la signature ou la date
  d'une pièce, ni le texte ni l'OCR ne peuvent la trancher : le relevé est la
  seule voie.
- **Réserve tenue partout** : le relevé établit la **présence** d'une
  signature, jamais sa validité. Aucune chaîne de certificats n'est vérifiée,
  et écrire « signée » sans cette précision transforme un constat de structure
  en garantie juridique. Une signature présente et invalide est précisément ce
  qu'un contrôle sérieux doit pouvoir dire.

## [1.45.0] — 2026-08-07

**Raison de l'update** : l'extracteur de couche de texte ne reconnaissait qu'une seule des façons dont un PDF écrit ses caractères, et déclarait « scan » des documents parfaitement lisibles. Mesuré sur un lot de quinze PDF : treize partaient à l'OCR pour rien.

### Corrigé
- **Chaînes hexadécimales.** Un PDF écrit ses chaînes entre parenthèses
  `(Bonjour)` ou en hexadécimal `<0025004F>`. Seule la première forme était
  lue. Les suites bureautiques les plus répandues n'émettent que la seconde :
  l'extraction rendait **zéro caractère**, le script concluait « c'est un
  scan », et l'ingestion basculait sur l'OCR alors que le texte exact était
  disponible. C'est la cause principale des treize sur quinze.
- **Largeur d'un code selon la police.** Les codes étaient lus sur deux
  octets sans condition. C'est juste pour une police composite (`/Type0`),
  faux pour une police simple, dont les codes tiennent sur un octet — le texte
  en ressortait inexploitable. La largeur se déduit désormais du type de la
  police.
- **Résolution des polices par portée.** La correspondance `/F1 → police`
  était construite à plat sur tout le fichier, en écrasant les doublons. Or ce
  nom est **local** : le `/F1` de la page 3 n'est pas celui de la page 1, et
  celui d'un formulaire n'est ni l'un ni l'autre. Mesuré sur un document
  contractuel : 273 collisions, donc autant d'occasions d'appliquer la
  mauvaise table de traduction. Chaque portée — page, puis chaque formulaire
  appelé — garde désormais ses propres polices.
  C'est le plus sournois des défauts corrigés ici, parce que son symptôme
  n'est pas l'absence mais l'**erreur** : sur un document mis en page, un
  « : » ressortait « f » et un trait d'union « l ». Une lettre qui manque se
  voit ; une lettre remplacée, non. Vérifié depuis contre le texte que rend un
  lecteur de PDF : **4 060 caractères, 100,0000 % de concordance, zéro écart**
  — là où la version précédente en donnait une lecture fausse par endroits.
- **Ordre des pages.** Les pages étaient prises dans l'ordre des objets du
  fichier, qui n'est pas celui de la lecture. Un texte suivi en ressortait
  mêlé. L'arbre des pages est désormais parcouru.
- **Glyphes pointant sur U+0000.** Certaines polices y font pointer un glyphe
  non défini ; la valeur était retenue telle quelle et insérait un octet nul
  dans un fichier qu'on croyait propre.

### Ajouté
- **Descente dans les formulaires.** Un document mis en page ne dessine pas
  son texte dans le flux de la page mais dans des formulaires que la page
  appelle. La page paraissait vide alors que tout son texte était là, tables
  de traduction comprises.
- **Reconstitution des lignes.** La sortie était un flux continu sans
  retours. Les lignes sont retrouvées par la position verticale réelle du
  texte, matrices de transformation comprises. Colonnes et tableaux ressortent
  toujours cellule après cellule — c'est la standardisation qui leur rend leur
  structure.
- **Marque « � » sur tout glyphe non traduit, comptée et annoncée.** Une
  police peut être appelée sans que sa table de correspondance couvre tous les
  glyphes qu'elle dessine. Le texte sortait alors amputé de caractères
  isolés — tirets, apostrophes, accents —, ce qui se relit comme une faute de
  l'auteur et non comme une extraction ratée. Chaque perte laisse désormais
  une marque visible dans le fichier produit, et un avertissement sur
  `stderr`. En dessous de 97 % de glyphes traduits, l'extraction est refusée
  et la pièce repart à l'OCR : sur le lot mesuré, huit documents à 100 %, sept
  entre 99,2 % et 100 %. Ce taux a par ailleurs servi à trouver le défaut de
  portée ci-dessus, qu'il ne mesurait pas : un document à 93 % ne souffrait
  pas de tables incomplètes mais de tables interverties. Un chiffre bas dit
  qu'il faut aller voir, pas seulement qu'il faut passer à l'OCR.

### Modifié
- **`/doc-ingest`** — ne jamais présumer du résultat sans avoir lancé la
  commande, et reporter les `�` tels quels plutôt que de les combler.
- **`/doc-repair`** — la voie de lecture indépendante se lance **même** quand
  la pièce a été ingérée par OCR : c'est le cas où elle a le plus à dire. Une
  position marquée `�` reste non tranchée et se déclare comme telle.

## [1.44.0] — 2026-08-07

**Raison de l'update** : la 1.43.0 faisait trier les séries datées vers l'ordre chronologique. C'était une erreur : `wiki/sources/` doit suivre l'ordre de SA PIÈCE, qui peut être antichronologique par nature.

### Modifié
- **L'invariant d'une série n'est pas « chronologique », c'est « conforme à la
  pièce ».** La 1.43.0 posait que trier n'était pas s'écarter de la pièce mais
  appliquer la standardisation. Faux dès que la pièce elle-même est
  antichronologique — et c'est fréquent : un journal de versions descend du
  plus récent, un export place son avis de chiffrement en tête tout en
  l'horodatant à l'heure de l'export, une capture montre un événement système
  hors rang. Ce sont des **propriétés observables de la pièce** ; les corriger
  efface une information au lieu d'en ajouter.
  Le modèle définit d'ailleurs cette couche comme le texte intégral « fidèle et
  sans tri », et place la lisibilité chronologique ailleurs — dans
  `enseignements/` et les pages vivantes, qui organisent librement ce qu'elles
  retiennent.
  Vérifié sur un vault réel : sur sept notes que le lint donnait pour fautives,
  **six reproduisaient fidèlement leur archive**. Les trier aurait écarté six
  notes de leur pièce pour en réparer une.
- **La comparaison se fait section par section, jamais document contre
  document.** Une même pièce porte couramment plusieurs listes de sens
  opposés : un relevé ouvre sur un récapitulatif croissant puis déroule un
  détail décroissant. Comparer la liste de la note au mauvais tableau conclut à
  une divergence qui n'existe pas — constaté deux fois de suite sur la même
  pièce, par deux lecteurs indépendants. Le **nombre d'entrées** désigne la
  bonne section sans ambiguïté : 71 contre 71 ne se confond pas avec un
  récapitulatif de 21 lignes.
- **Le contrôle compare donc la note à sa pièce archivée, plus au calendrier.**
  Ordres identiques → aucun défaut, signalé une fois comme réserve
  documentaire pour que le prochain lint ne le rejoue pas. Ordres divergents →
  défaut de transcription réel, réparé d'office : là, réaligner rétablit la
  fidélité au lieu de l'entamer.
- **`/doc-ingest` ne trie plus rien** : la note reproduit l'ordre de la pièce.
  Une pièce franchement antichronologique se signale par un `> [!warning]` en
  enseignements — réserve documentaire, pas défaut à réparer.
- **Le fork n'écrit plus qu'il a « appliqué » ce qu'il n'a pas pu appliquer.**
  La 1.43.1 lui demandait d'annoncer « corrections appliquées » plutôt que « à
  appliquer », pour que l'agent principal agisse. Mais le fork n'applique
  rien — il ne le peut pas —, et l'affirmer était donc faux : le mensonge
  tenait tant que l'agent principal échouait à agir, et l'utilisateur lisait
  « corrigé » sur ce qui ne l'était pas. Le rapport porte désormais un
  **impératif adressé à qui exécute**, avec la mention qui lève l'ambiguïté —
  « à exécuter maintenant, sans demander d'autorisation ». C'est cette mention
  qui décide, pas le temps du verbe.
- **La liste d'actions échappe à la règle de concision.** Les deux exigences
  sont opposées et se rencontraient sans être distinguées : un rapport court
  sert qui lit, une liste précise sert qui exécute. Un rapport comprimé avec
  des actions vagues force à rouvrir le vault — on économise des lignes pour
  dépenser un aller-retour. La concision porte sur les sections **sans
  trouvaille**, jamais sur les actions, qui se décrivent assez pour être faites
  sans rien rouvrir : un fichier, une ligne, le remplacement exact.
- **Correction d'une affirmation fausse des trois commandes en fork.** Elles
  déclaraient qu'écrire sur disque était « impossible, tu es en lecture seule
  stricte et n'as aucun outil d'écriture ». C'est faux : l'agent `Explore` n'a
  ni `Edit` ni `Write`, mais il a **`Bash`** — un `cat > fichier` passe. La
  tentative d'origine avait échoué pour une autre raison, et il en avait été
  tiré une impossibilité technique qui n'existe pas. Une contrainte inventée
  ferme des options qu'on n'examine plus.
  Ce n'est donc pas une impossibilité mais un **choix**, désormais énoncé comme
  tel : le rapport est ce que l'utilisateur lit, et le renvoyer vers un fichier
  lui retirerait la seule chose qui lui permette de juger le travail. On écrit
  sur disque quand le **volume** l'exige, jamais pour cacher un raisonnement.
- **`verify-entries.py` rend l'ordre en constat, plus en avertissement.**
  Trancher suppose d'ouvrir l'archive, ce que ce script ne fait pas : il
  signale que la note n'est pas chronologique et rappelle que la comparaison
  se fait contre la pièce. Il ne conclut plus à un défaut.

## [1.43.1] — 2026-08-07

**Raison de l'update** : la règle « appliquer d'office » était écrite dans le fichier que seul le fork lit — et le fork ne peut pas écrire. Deux lints de suite ont annoncé des corrections sans en appliquer une seule.

### Corrigé
- **Les corrections d'office passent par le rapport, seul canal vers qui peut
  écrire.** `doc-lint.md` s'exécute en fork : tout son contenu s'adresse au
  sub-agent, qui est en lecture seule stricte. L'agent principal, lui, ne lit
  jamais ce fichier. Une règle écrite là et adressée à lui n'atteignait donc
  personne — deux rapports ont annoncé « ce qui s'applique d'office, sans rien
  demander », et rien n'a été appliqué ni la première ni la seconde fois.
  Les corrections mécaniques doivent désormais figurer dans le rapport comme
  une **liste d'actions exécutables** — un fichier, un geste précis —, sous un
  titre qui dit qu'elles s'appliquent *maintenant*. « Corrections appliquées »,
  jamais « à appliquer » : c'est cette formulation que l'agent principal lit,
  et elle décide de ce qu'il fait. Elles n'entrent jamais dans la question
  finale, qui rendrait conditionnel ce qui ne demande aucune autorisation.
- **Une entrée sans heure ne bloque plus la remise en ordre.** La condition
  exigeait un horodatage complet partout ; en pratique, la ligne système d'un
  export porte une date sans heure et faisait renoncer à trier toute la note.
  Le tri est **stable** et une entrée sans heure vaut « début de son jour » :
  elle garde son rang relatif. Seule une entrée **sans date** bloque encore —
  là, plus rien ne dit où elle va.
- **Le balayage couvre toutes les notes de `sources/`**, et non les seules
  déjà signalées : un rapport en a listé sept et manqué la huitième, qu'aucun
  autre contrôle n'aurait rattrapée.

## [1.43.0] — 2026-08-06

**Raison de l'update** : le lint signalait les séries à l'envers sans les réparer, au motif qu'écrire dans une couche immuable se soumet — un raisonnement faux, puisqu'un tri ne touche à aucune ligne.

### Modifié
- **`/doc-lint` remet les séries datées dans l'ordre, d'office.** La règle
  précédente les comptait et les soumettait : « réordonner réécrit une couche
  immuable ». C'était mal raisonné. L'immuabilité protège **ce que la pièce
  dit** ; une permutation ne touche à aucune ligne, et la règle d'ingestion
  pose depuis la 1.41.0 que l'ordre se déduit des **horodatages**, jamais de la
  séquence du fichier. Trier n'est donc pas s'écarter de la pièce, c'est
  appliquer la standardisation qui aurait dû l'être.
  Quatre conditions, vérifiables avant d'écrire, et qui renvoient à la
  soumission si l'une manque : chaque entrée porte un horodatage complet ; la
  pièce d'origine est dans `archives/`, ce qui rend le geste rattrapable ; le
  **multiensemble des lignes est identique** avant et après, vérifié après
  écriture et non affirmé ; le dossier est réindexé, le découpage suivant
  l'ordre du fichier.
  Trois formes se rencontrent et le tri les règle toutes : série entièrement
  retournée, **titres de jour retournés avec entrées ordonnées à l'intérieur**
  — la plus fréquente sur un journal de versions, une rupture par changement
  de jour —, et ruptures éparses. Mesuré sur un vault réel : 7 séries
  fautives, dont un relevé de 332 entrées à 121 titres retournés.

## [1.42.3] — 2026-08-06

**Raison de l'update** : initialiser depuis le dossier du vault lui-même envoie la config locale — qui n'est faite que de chemins de la machine — sur le dossier synchronisé, sans que rien ne le dise.

### Ajouté
- **`/doc-lint` repère un `.claude/` à la racine du vault.** C'est de la
  configuration de **poste** dans un dossier **partagé** — chemins de la
  machine, emplacement du cache des plugins, liste des plugins actifs —,
  répliquée par la synchronisation et fausse partout ailleurs.
  **Aucun réglage ne l'empêche**, et c'est toute la raison du contrôle :
  `settings.json` est écrit par Claude Code dès qu'une session s'ouvre dans le
  dossier du vault. Le plugin n'a pas la main dessus ; il ne peut que le voir
  après coup. Un avertissement à l'initialisation ne couvre que les deux
  fichiers que le plugin écrit lui-même, pas celui-là.
  Le remède dépend de l'origine — résidu d'une session ouverte au mauvais
  endroit, ou montage assumé où le vault est le projet — donc la suppression
  se soumet, jamais d'office.
- **`/vault-init` prévient quand le projet et le vault sont le même dossier.**
  Le montage fonctionne — le portier remonte l'arborescence pour trouver
  `vault-path.local` — et il est légitime pour qui travaille seul. Mais
  `.claude/` part alors sur le dossier synchronisé, or il ne contient **que**
  des chemins propres à la machine : l'emplacement du vault, et celui du cache
  des plugins. Un second poste synchronisant ce vault les recevrait faux, et
  les deux machines se disputeraient le même fichier.
  Une note à l'initialisation, rien de bloquant. Constaté en usage : un
  `/vault-init` lancé depuis le dossier du vault avait écrit sa configuration
  dedans, pendant qu'on la cherchait dans le projet d'où la session semblait
  partir.

## [1.42.2] — 2026-08-06

**Raison de l'update** : le rapport de lint justifiait aussi longuement les contrôles qui passent que ceux qui échouent — huit sections vides sur douze, et dix lignes utiles noyées dans cent cinquante.

### Corrigé
- **Le rapport de `/doc-lint` est proportionné à ce qu'il trouve.** La règle
  disait « vide = le dire aussi », sans dire que ça devait tenir en une ligne :
  d'où des paragraphes entiers, tableaux compris, pour démontrer qu'une
  catégorie n'a **rien** à signaler. Sur un vault sain, l'essentiel du rapport
  devenait la justification de son propre silence.
  Désormais : rien trouvé → **une ligne** ; quelque chose trouvé → le détail
  utile à la décision, et rien de plus. On justifie ce qu'on a trouvé, jamais
  ce qu'on n'a pas trouvé — le détail d'un contrôle qui passe n'apprend rien
  et noie celui qui échoue. Le corps du contrôle n'est pas le corps du
  rapport : ce qui a été ouvert et recoupé reste dans le contexte du fork,
  qui est jetable, c'est sa fonction.
  **Une seule exception, étroite** : une décision qui serait reprise à zéro au
  prochain lint — une paire suspectée puis délibérément conservée, un
  `[!warning]` examiné puis non requalifié. Une ligne avec son motif, de quoi
  ne pas refaire le travail, pas de quoi le rejouer.
- **Les corrections mécaniques s'appliquent AVANT la présentation, et se
  rapportent au passé.** Le régime existait — « appliquer sans demander » —,
  mais rien ne disait *quand*. Constaté : un rapport listant « ce qui
  s'applique d'office, sans rien demander », suivi d'une question finale… et
  rien d'appliqué. Une liste d'intentions placée au-dessus d'une question
  devient conditionnelle, et tout attend la réponse, y compris ce qui ne
  demandait aucune autorisation. On rapporte donc « 3 wikilinks déliés »,
  jamais « à délier », et la question ne porte que sur ce qui reste.
- **Une seule question finale, jamais composée.** Deux autorisations → deux
  phrases numérotées, chacune répondant par oui ou non. Rien à autoriser → pas
  de question, un verdict.

## [1.42.1] — 2026-08-06

**Raison de l'update** : rien n'interdisait les wikilinks dans le journal, et une page citée par le seul journal passait pour reliée.

### Corrigé
- **Le journal ne porte plus de wikilinks — les notes s'y nomment en clair.**
  Rien ne le disait, d'où un résultat irrégulier : une entrée d'ingestion en
  posait trois, celle de la veille aucune. Une entrée de journal relie les
  pages touchées le même jour, ce qui est une **coïncidence de calendrier et
  non un rapport de sens** : les `[[...]]` y fabriquent des arêtes qui
  n'énoncent rien, et rendent le journal d'autant plus central dans le graphe
  qu'on s'en sert. Le contrôle 11 de `/doc-lint` les signale et les délie, sur
  tout le journal — le défaut étant irrégulier, le fichier du jour ne suffit
  pas.
- **Le contrôle des orphelines s'arrête à `wiki/`.** Il cherchait « dans tout
  le vault », donc un renvoi venu de `LOG/` ou d'une compilation de
  `references/` suffisait à déclarer une page reliée. C'est un faux négatif
  silencieux : la page reste isolée dans le savoir tout en étant comptée
  saine. Être orpheline, c'est n'être atteignable depuis aucune
  **connaissance** — le journal dit qu'on a touché une page un jour, pas
  qu'elle s'articule à quoi que ce soit, et une compilation est régénérable et
  citerait n'importe quoi.

## [1.42.0] — 2026-08-06

**Raison de l'update** : le lint demandait l'autorisation d'aller chercher une réponse, donc faisait arbitrer sans elle ; et son contrôle d'ordre pouvait s'appliquer aux titres de jour, qui progressent, plutôt qu'aux entrées, qui reculent.

### Modifié
- **`/doc-lint` enchaîne `/doc-repair` d'office sur les contradictions.** La
  délégation était spécifiée mais soumise à autorisation : on demandait la
  permission **avant** d'aller voir, donc on faisait arbitrer sans la réponse
  en main — précisément ce que ce plugin refuse partout ailleurs. Or
  `/doc-repair` est un fork qui **n'écrit rien** : il ouvre la pièce et rend un
  verdict. Le lancer ne détruit rien et ne coûte que des jetons. Ce qui se
  soumet, désormais, c'est l'**application** du verdict.
  Avec un tri préalable, pour ne pas dépenser en vain : le lint a lu les
  callouts, il dit lesquels une pièce d'`archives/` peut plausiblement trancher
  (« quel est le texte exact de tel article ») et lesquels attendent une pièce
  **nouvelle** (« tel message a-t-il causé tel effet »). Les seconds ne
  partent pas en délégation, le callout reste : c'est sa raison d'être.
  Un lint qui rend « 9 tranchées, 4 en attente d'une pièce » a fait le travail ;
  un lint qui rend « 13 à trancher » l'a seulement déplacé.
- **L'ordre d'une série vient des horodatages, pas de la séquence du fichier.**
  La règle disait « remettre d'aplomb » sans dire d'où l'ordre se déduit. Le
  cas insidieux n'est pas la source entièrement retournée mais l'**entrée
  isolée hors de son rang** : un export place ses messages système en tête de
  fichier tout en les horodatant à l'heure de l'export, donc après le premier
  vrai message du jour. Reportées telles quelles, ces lignes donnent une note
  dont les titres progressent impeccablement et dont les entrées reculent à
  l'intérieur d'un jour. Trier sur l'horodatage règle les deux formes d'un
  coup.

### Corrigé
- **Le contrôle d'ordre porte sur les lignes d'entrée, jamais sur les titres de
  jour.** La formulation — « comparer la suite des horodatages à elle-même
  triée » — ne disait pas de quels horodatages il s'agissait. Appliquée aux
  titres `### AAAA-MM-JJ`, elle ne voit rien : ils peuvent progresser
  parfaitement pendant que les entrées **à l'intérieur** de chaque jour
  reculent.
  Constaté sur un vault réel : le contrôle a signalé 2 séries retournées et
  déclaré saines les 19 autres — dont **cinq** dont les entrées sont en
  désordre, titres impeccables. La cause y est différente et vaut d'être
  connue : ce ne sont pas des sources antéchronologiques mais des messages
  système que l'export horodate à l'ouverture du fichier, donc placés avant le
  vrai premier message de la journée.
  Les deux formes du défaut sont maintenant décrites par leur origine — série
  entièrement retournée, ou ruptures éparses — pour qu'un rapport dise laquelle
  et pourquoi.

## [1.41.0] — 2026-08-05

**Raison de l'update** : deux invariants d'une série datée n'étaient écrits nulle part — son sens de lecture et son fuseau —, et aucun compteur ne les rattrape.

### Ajouté
- **`verify-entries.py --ancre '<motif>'` recompte sur autre chose qu'un
  horodatage.** Une pièce rédigée en prose date ses entrées en toutes lettres,
  un récapitulatif les numérote : le recomptage sortait alors en « vérification
  sans objet », **qui a l'apparence d'un succès**. C'est le pire résultat
  possible pour un contrôle d'intégralité — constaté sur deux relevés, dont la
  fidélité n'a pu être établie qu'en recoupant à la main une autre ancre.
  Le motif tient lieu d'horodatage : empreinte, numéro de pièce, référence de
  ticket. Ce mode détecte en plus les ancres **en trop** dans la note, absentes
  de la source — une entrée recopiée de travers, que le dénombrement des
  horodatages ne peut pas voir.
  Le message de sortie 2 sépare désormais les deux cas qu'il confondait : la
  pièce n'est pas une série (rien à recompter), ou elle en est une et porte une
  autre ancre (la donner). Et il dit ce que le code veut dire : pas un succès,
  une absence de contrôle.
- **Le contrôle 8 de `/doc-lint` balaie le vault à la recherche de séries à
  l'envers.** Le recomptage ne voit que ce qui s'ingère ; les notes écrites
  avant ne repassent jamais par là. Vérifié sur un vault réel : **six séries
  déjà écrites** étaient antichronologiques, dont deux relevés de 332 et 71
  entrées — reportées fidèlement depuis des pièces qui rendent le plus récent
  en premier. Le lint les compte et les soumet ; il ne réordonne pas d'office,
  réécrire une couche immuable ne se fait jamais sans autorisation.
- **Le recomptage signale une série écrite à l'envers.** Constaté en usage : un
  export rendu en ordre antichronologique passe **tous** les contrôles — le
  total est juste, chaque entrée est là, aucun trou —, et pourtant l'échange se
  lit à rebours et se cite mal. `verify-entries.py` a déjà les ancres en main :
  il vérifie maintenant qu'elles progressent, et distingue les deux formes du
  défaut — série entièrement retournée, ou ruptures d'ordre éparses, dont il
  donne le nombre. Coût nul, aucun appel de plus.

### Modifié
- **Une série se standardise du plus ancien au plus récent.** L'ordre n'était
  spécifié nulle part : `/doc-query` l'exigeait pour son rapport, mais rien ne
  le demandait à l'écriture de la note. Un lecteur qui reportait l'ordre d'une
  source paginée à rebours ne violait donc aucune règle. C'en est une
  maintenant : on remet d'aplomb, on ne reporte pas.
- **Le fuseau horaire d'une série se déclare en `fuseau:`, et ne se convertit
  jamais.** Une API horodate volontiers en UTC, un export d'application rend
  l'heure locale de l'appareil. Mêlées sans le dire, deux séries produisent une
  chronologie fausse du décalage — et rien ne la signale, les heures ayant
  l'air normales. La note de `sources/` porte donc `UTC`, `UTC+02:00`, ou
  `heure locale, fuseau non porté par la pièce`.
  Pas de conversion : `sources/` est immuable et fidèle, et convertir depuis un
  décalage que la pièce ne donne pas écrit une supposition qu'on ne saura plus
  distinguer d'un fait. Fuseau indéterminable → un `> [!warning]` dans la note
  d'enseignements, réserve documentaire valant pour toute lecture croisée.

## [1.40.0] — 2026-08-05

**Raison de l'update** : le graphe Obsidian n'était coloré que si l'utilisateur le faisait à la main, et un chemin Windows donné à `/vault-init` créait un dossier au nom absurde dans le projet en annonçant « vault initialisé » — sans une seule erreur.

### Ajouté
- **`/vault-init` colore le graphe Obsidian par dossier.** Un réglage à faire
  à la main jusqu'ici, décrit dans le README et donc sauté par la plupart :
  sans lui, tous les nœuds se ressemblent et le graphe ne montre pas la
  structure du vault. Cinq groupes sont écrits dans `.obsidian/graph.json` —
  bleu `sources/`, vert `enseignements/`, ambre `concepts/`, violet
  `entites/`, rouge `syntheses/`.
  Le fichier porte aussi les réglages personnels (zoom, forces, filtres) :
  il n'est **jamais écrasé**. Les groupes ne sont écrits que si `colorGroups`
  est vide — des groupes déjà définis sont un choix, pas un défaut à remplacer
  —, le reste du fichier est préservé intact, et un `graph.json` illisible est
  laissé tel quel avec la marche à suivre manuelle. Même discipline que la
  fusion d'`app.json`.

### Corrigé
- **Un chemin Windows est converti, plus pris au pied de la lettre.**
  `G:\Mon Drive\Produit` devient `/mnt/g/Mon Drive/Produit`. Sans conversion,
  cette chaîne ne produisait **aucune erreur** : elle ne contient pas un seul
  `/`, donc `dirname` rend `.`, le contrôle du dossier parent passe, et
  `mkdir -p` crée un dossier dont le **nom** contient les antislashs, au milieu
  du projet. La commande annonçait ensuite « ✅ vault initialisé et vérifié »
  — sur un vault qui n'était pas là où l'utilisateur le croyait, et le
  contrôle final confirmait, puisque le dossier existait bel et bien.
  C'est le geste naturel de qui copie le chemin depuis l'explorateur Windows.
  La conversion est annoncée en une ligne ; un chemin déjà POSIX passe
  inchangé.
- **Le diagnostic de lecteur non monté donne les commandes exactes.** Le
  message renvoyait un `sudo mount -t drvfs <lettre>: /mnt/<lettre>` à
  compléter soi-même. `/vault-init` reconnaît maintenant le cas — vault sous
  `/mnt/<lettre>/` dont le point de montage est absent — et rend les deux
  commandes prêtes à coller, avec la bonne lettre : le montage immédiat, et la
  ligne `/etc/fstab` qui le rend permanent. Le `mkdir` du point de montage
  n'est proposé que s'il manque réellement — c'est un dossier ordinaire du
  disque WSL, créé une fois il persiste, et après un redémarrage seul le
  montage est à refaire. Une commande superflue ferait douter du reste du
  diagnostic. Point de montage **déjà présent
  dans `/etc/fstab`** → c'est `sudo mount -a` qui est proposé, le montage ayant
  échoué au démarrage.
  Il ne les exécute pas : monter un lecteur et éditer `/etc/fstab` demandent
  root, touchent toute la machine et ne concernent que WSL. Ce script n'écrit
  que dans le projet et le vault — c'est une décision d'administration, on la
  prépare, on ne la prend pas.
- **Le portier `vault-check.sh` diagnostique aussi.** C'est lui qui parle après
  un redémarrage de WSL — le lecteur n'est plus monté, et il rejette **toutes**
  les commandes jusqu'au remontage, alors que `/vault-init` ne se lance qu'une
  fois. Il portait le même modèle à compléter ; il rend maintenant la commande
  copiable telle quelle, avec la bonne lettre, et distingue trois cas : lecteur
  non monté (`sudo mount -t drvfs G: /mnt/g`, ou `sudo mount -a` si le point de
  montage est déjà dans `/etc/fstab` — le montage a alors échoué au démarrage,
  souvent parce que le lecteur n'était pas encore lancé), lecteur monté mais
  dossier disparu (déplacé, renommé, synchronisation en cours), et chemin hors
  de `/mnt`.
  **Aucun des deux scripts ne monte quoi que ce soit** : `mount` exige root, un
  script appelé par une commande n'a pas de terminal pour demander un mot de
  passe, et `sudo -n` n'est disponible que si l'utilisateur l'a configuré. Ce
  qu'ils peuvent faire, c'est ne plus laisser chercher.
- **Un `vault-path.local` cassé peut enfin être réparé en relançant.** « Ne
  jamais écraser » protège une configuration valide ; appliqué à une
  configuration **fausse**, ça interdisait de la corriger : relancer
  `/vault-init` avec le bon chemin conservait l'ancien, puis échouait sur
  « vault introuvable » sans dire que le chemin conservé était le coupable.
  Désormais, un chemin enregistré qui **ne désigne aucun dossier** est remplacé
  et le remplacement est annoncé. Un chemin valide reste protégé — la commande
  dit alors comment le changer volontairement.

## [1.39.6] — 2026-08-05

**Raison de l'update** : l'entrée de la 1.39.4 laissait croire que le plugin installe agentic-toolbox lui-même.

### Corrigé
- **Formulation de l'entrée 1.39.4** : « agentic-toolbox est installé dès le
  bloc de démarrage » se lit comme une dépendance tirée automatiquement. Ce
  n'en est pas une, et ce ne peut pas en être une — le manifeste de marketplace
  ne porte aucun champ de dépendance, un plugin ne peut donc pas en installer
  un autre. C'est une **troisième ligne à taper**, comme les deux autres. Le
  README, lui, était juste ; seule sa description dans le journal était
  trompeuse.

## [1.39.5] — 2026-08-05

**Raison de l'update** : `/doc-ingest` sans argument affichait un tableau des lots et attendait une réponse tapée, là où une case à cocher suffisait.

### Corrigé
- **`/doc-ingest` sans argument pose une vraie question à choix.** La règle
  disait seulement « demander à l'utilisateur ce qu'il veut ingérer », ce qui
  laissait le rendu libre : en pratique, un tableau des lots à recopier à la
  main. La commande ne s'exécutant pas en fork, elle peut poser une question
  sélectionnable — et c'est ce qu'elle fait désormais, en multi-sélection.
  Les lots du sas deviennent les options, regroupées si nécessaire pour tenir
  dans les quatre choix du format, **ordonnées du moins cher au plus cher** et
  décrites par ce qui décide : nombre de fichiers, volume, coût dominant
  (couche de texte gratuite, OCR facturé, série de captures lue image par
  image). Le premier est marqué « recommandé » — un lot de PDF à couche de
  texte valide toute la chaîne pour presque rien, une série de captures est le
  poste le plus lourd. L'entrée libre reste offerte pour un chemin hors du sas.
  Sas vide → une seule question ouverte, le chemin de la source : il n'y a rien
  à proposer.

## [1.39.4] — 2026-08-05

**Raison de l'update** : agentic-toolbox était renvoyé en fin de README comme une option parmi d'autres, alors que c'est lui qui fait la différence entre chercher par mots-clés et chercher par le sens.

### Modifié
- **La commande d'installation d'agentic-toolbox figure dès le bloc de
  démarrage** — une troisième ligne à taper, pas une dépendance tirée
  automatiquement : un plugin ne peut pas en installer un autre, le manifeste
  de marketplace ne porte aucun champ de dépendance. Elle est accompagnée de ce
  qu'il apporte concrètement : sans lui la recherche trouve ce qu'on a su nommer et
  rate la reformulation ; avec lui, « qui a validé le budget ? » remonte une
  note qui parle d'accord donné sur une enveloppe, sans partager un seul mot
  avec la question. Plus la lecture des documents scannés, sans quoi un PDF
  photographié n'est qu'une image.
  Son coût est annoncé au même endroit — `uv` et une clé Mistral gratuite — au
  lieu d'être découvert après coup. Il reste facultatif : sans lui rien ne
  casse, les commandes annoncent leur repli au lieu de faire semblant.

## [1.39.3] — 2026-08-05

**Raison de l'update** : le démarrage du README s'arrêtait à « le vault est prêt » — sur un vault vide, sans dire comment lui donner quoi que ce soit à lire.

### Ajouté
- **Le démarrage va jusqu'à la première ingestion.** Les deux façons de
  présenter ses sources sont désormais écrites : les déposer dans le sas
  `inbox/` puis `/doc-ingest inbox/`, ou donner un chemin quelconque sans rien
  déplacer.
  Avec la condition qui manquait et qui se paie comptant : **un dossier hors du
  vault et hors du projet est refusé** tant qu'il ne figure pas dans
  `additionalDirectories` — c'est le cas courant quand les sources sont rangées
  à côté du vault plutôt que dedans.
  Précisé aussi que `/doc-ingest` sans argument **ne prend pas `inbox/`
  entier** : il liste son contenu et demande, plutôt que d'avaler un lot que
  personne n'a chiffré.

## [1.39.2] — 2026-08-05

**Raison de l'update** : le mode `--all-references` n'apparaissait nulle part dans le README, et le modèle listait `references/` sans dire qu'il n'est créé qu'à la demande.

### Ajouté
- **Le README documente `--all-references` et `references/`.** La 1.39.0 les
  avait livrés sans les décrire : ni la table des commandes, ni la section
  d'usage, ni l'arborescence ne les mentionnaient. Une fonctionnalité qu'aucune
  documentation n'annonce n'existe que pour qui a lu le CHANGELOG.

### Corrigé
- **Le modèle dit que `references/` est créé à la demande.** Le schéma de
  structure le présentait au même titre qu'`inbox/` ou `archives/`, que
  `/vault-init` pose d'emblée. Il n'apparaît en réalité qu'à la première
  compilation acceptée, comme `BENCH.md` au premier `/doc-bench` — les dossiers
  posés à l'initialisation servent tous à chaque ingestion, celui-ci
  n'appartient qu'à un mode facultatif dont la plupart des vaults n'auront
  jamais besoin. Le comportement ne change pas, seule sa description était
  fausse.

## [1.39.1] — 2026-08-05

**Raison de l'update** : `/vault-init` n'inscrivait toujours pas les autorisations de scripts — la variable dont il déduisait leur chemin n'existe pas dans son environnement.

### Corrigé
- **`/vault-init` déduit la racine du plugin de l'emplacement de son propre
  script, plus de `CLAUDE_PLUGIN_ROOT`.** La commande l'invoque par
  `bash "${CLAUDE_PLUGIN_ROOT}/scripts/vault-init.sh"` : le chemin est
  **substitué dans la ligne de commande**, donc le script le reçoit en argument
  — mais la variable n'est pas exportée dans son environnement. Le script la
  lisait vide, sautait les règles `allow` sans un mot, et n'écrivait que
  l'accès au vault.
  C'est exactement la panne que la 1.37.0 prétendait réparer, reproduite à
  l'identique sur un vault neuf : les commandes se font refuser leurs scripts
  un par un et **dégradent** au lieu de s'arrêter. `$script_directory`, calculé
  depuis `BASH_SOURCE`, est toujours juste ; la variable ne sert plus que de
  préférence si elle existe.
  Vault déjà initialisé avec un `allow` vide → relancer `/vault-init`, il est
  idempotent.

## [1.39.0] — 2026-08-04

**Raison de l'update** : un classement rend les K meilleurs résultats, jamais l'ensemble — et le `date` du frontmatter, décrit comme « date de création », faisait repartir tout un lot daté du jour de l'ingestion.

### Ajouté
- **`/doc-query … --all-references` rend les entrées, pas les notes.** Le mode
  normal cherche *ce qui répond* et rédige une réponse appuyée sur des notes ;
  celui-ci cherche *tout ce qui concerne* et rend **les entrées elles-mêmes**,
  datées et attribuées, citables une par une. La forme canonique de la 1.38.0
  est ce qui le rend possible : chaque entrée porte sa date complète et son
  auteur sur sa ligne.
  Le déroulé, dans cet ordre : **le grep d'abord**, seule couche qui rende
  toutes les occurrences plutôt qu'un classement ; puis des **vagues
  sémantiques**, la première avec la question **non reformulée** — les mots de
  l'utilisateur sont le signal le plus fort, la reformuler d'emblée reviendrait
  à chercher la question d'un autre —, les suivantes sous un angle différent
  chacune, en filtrant les chemins déjà retenus. **Arrêt quand une vague
  n'apporte plus aucun fichier neuf**, jamais à un nombre fixe : un compteur
  gaspille ou tronque, et une troncature silencieuse est le pire résultat
  possible pour ce mode. Chaque fichier retenu est lu **en entier**, jamais son
  seul extrait.
  La règle qui écarte les termes trop répandus **s'inverse** ici : le terme
  fréquent qui désigne le sujet est le critère de sélection. Sans terme
  littéral, le mode le dit en tête de rapport — le périmètre repose alors sur
  le seul jugement, et l'exhaustivité n'est pas garantie. Les limites sont
  écrites dans la commande plutôt que sous-entendues : le grep garantit le
  littéral, les vagues élargissent, le lecteur juge — mais un jugement n'est
  pas une preuve, et rien ne rattrape ce qui n'a jamais été ingéré.
- **`references/`, une compilation d'entrées hors index sémantique.** Le
  résultat de `--all-references` ne va **pas** dans `wiki/syntheses/` : ce
  dossier est indexé et porte des réponses, pas des extraits. Y déverser des
  entrées déjà présentes dans `wiki/sources/` vectoriserait deux fois le même
  texte, ferait remonter le même passage en double à toute recherche suivante,
  et transformerait le dossier des conclusions en le plus gros du vault.
  Une compilation vit donc hors de `wiki/` — l'indexation ne parcourant que ses
  cinq dossiers, il n'y a rien à configurer —, n'entre pas dans `INDEX.md`, et
  se **régénère** : relancer la commande la refait, plus complète si le vault a
  grandi. Rien ne s'y maintient. Une ligne au journal, et c'est tout.
  Elle reste en revanche **dans le graphe Obsidian**, contrairement à
  `archives/` et `inbox/` : c'est un document construit, qui cite ses notes et
  renvoie à sa synthèse.
- **Compilation et synthèse se proposent ensemble et se pointent
  mutuellement.** L'une sans l'autre laisse le travail à moitié fait — des
  entrées que personne n'a conclues, ou une conclusion dont on ne peut plus
  produire les pièces. Elles partagent leur slug et se lient dans les deux
  sens, exactement comme `sources/` et `enseignements/` le font pour une pièce :
  même idiome, même raison — un doute sur la thèse se remonte aux entrées, une
  entrée se replace dans ce qu'elle sert à établir. Deux liens dans la
  compilation, et deux seulement : la synthèse en tête, un renvoi par note
  citée en fin de fichier — jamais un lien par entrée, deux cents liens vers la
  même note ne faisant qu'un nœud illisible.

- **Le contrôle 8 de `/doc-lint` compare `date` au préfixe du nom de fichier**
  sur `sources/` et `enseignements/`, le nom faisant foi. Un écart se signale
  **par lot** avec le jour commun trouvé : quand la date d'ingestion a remplacé
  celle des pièces, toutes les notes du lot portent le même jour, et c'est cette
  forme-là qui rend le défaut reconnaissable d'un coup d'œil.

### Corrigé
- **`date` porte la date de la pièce, sur les couches d'origine.** La règle
  était explicite pour le nom de fichier — « la date de la pièce, jamais la date
  d'ingestion » — et muette pour le frontmatter, où elle disait seulement « date
  de création ». L'ambiguïté s'est résolue du mauvais côté : constaté sur un
  premier lot réel, **onze notes sur onze** portaient le jour de la session
  alors que leur slug portait la vraie date, de janvier à août.
  Le défaut est invisible à la lecture — la note est datée, elle a l'air juste —
  et fausse tout raisonnement chronologique comme toute citation. `date` vaut
  désormais explicitement la date de la pièce pour `type: source` et
  `type: enseignements`, la date de création de la page pour les couches
  vivantes, et **rien du tout** pour une pièce non datée, exactement comme il
  n'y a pas de préfixe : une date d'ingestion mise là daterait la lecture en
  faisant croire qu'elle date la pièce.

## [1.38.0] — 2026-08-04

**Raison de l'update** : une source découpée entre plusieurs lecteurs n'avait aucun moyen de prouver qu'elle était entrée en entier — une tranche jamais rendue produit une note valide, seulement plus courte.

### Ajouté
- **Recomptage des entrées d'une série datée** (`scripts/verify-entries.py`).
  Un relevé d'activité, un journal, un suivi de tickets, un export d'API sont
  les seules sources qui portent leur propre preuve d'intégralité : chaque
  entrée est ancrée par un horodatage, et cette ancre survit à la
  standardisation. Le script compare les ancres de la source à celles de la
  note produite et **nomme celles qui manquent**. Aucun contrôle de forme ne
  pouvait le faire : ni les wikilinks, ni le frontmatter, ni la taille, qu'on
  n'a rien à quoi comparer.
  Il lit le JSON (une ancre par entrée, sans descendre dans les sous-objets,
  qui datent un détail et non une entrée de plus) et le texte (les ancres qui
  ouvrent une ligne priment sur les dates citées dans un corps d'entrée).
  Une source rendue dans un autre fuseau ferait conclure à une perte totale :
  le script essaie les décalages entiers, retient celui qui explique le mieux
  les correspondances, et l'annonce. Bibliothèque standard seule, aucun appel
  réseau. Sortie 0 complet · 1 il manque, avec la liste · 2 source non datée,
  vérification sans objet.
  Branché sur l'auto-vérification de `/doc-ingest`, et reporté au compte rendu
  (`<n>/<n> entrées`).
- **Report d'attribution dans une série de captures.** Une interface qui groupe
  les entrées consécutives d'un même auteur n'affiche son nom qu'une fois : les
  suivantes arrivent nues, et le nom ne réapparaît qu'au changement d'auteur ou
  à une rupture d'horaire. Un nom absent ne veut pas dire « auteur inconnu »
  mais « le même que la ligne précédente » — le lecteur reporte le dernier
  auteur connu, y compris **d'une capture à la suivante**, et l'écrit en toutes
  lettres. C'est ce que la standardisation sert à faire : rendre explicite ce
  que l'affichage élidait. Sans point de report, l'entrée reste non attribuée
  avec un `> [!warning]` — jamais d'attribution par ressemblance, une entrée mal
  attribuée étant pire qu'une entrée sans auteur : la seconde se voit, la
  première se cite.
- **Contrôles de continuité d'une série de captures.** Une vue qui défile,
  capturée depuis un outil sans export, n'a aucune source à laquelle se
  recouper — le texte n'existe pas avant que le lecteur ne l'écrive. Trois
  contrôles la bornent quand même : continuité de la **numérotation** (avant
  toute lecture, sans rien ouvrir), **recouvrement de bord** entre deux
  captures consécutives — déclaré jointure par jointure, une rupture étant un
  fait sur la couverture et non un détail de lecture —, et **monotonie des
  dates** sur toute la série. Ils ne prouvent pas la fidélité du texte, rien ne
  le peut ; ils font la différence entre une couverture inconnue et une
  couverture bornée.

### Modifié
- **Une entrée de série datée s'écrit sur une ligne, dans une forme unique :**
  `- AAAA-MM-JJ HH:MM — <auteur> : <texte>`. La date complète figure sur chaque
  ligne, même sous un titre quotidien qui la porte déjà. Le découpage sémantique
  coupe où il veut dans une longue journée, et le titre ne voyage pas avec
  l'extrait : une entrée qui ne portait que son heure remontait sans son jour,
  donc impossible à citer. La forme commune rend aussi une plage de dates
  cherchable d'une pièce à l'autre (`grep '^- 2026-04'`), et l'intégralité
  vérifiable sans rien inférer. Onze caractères par entrée, et une répétition
  qui entre dans le vecteur de chaque extrait — négligeable devant un extrait
  qu'on ne pouvait pas dater. Le titre quotidien reste : c'est lui qui découpe.
  Le recomptage annonce la forme qu'il a reconnue et **avertit** quand une note
  n'est pas dans la forme prescrite — le compte reste bon, mais il repose alors
  sur une lecture du format et non de la note.
- **Un export d'API en JSON est projeté sur ses champs utiles avant d'être
  mesuré et découpé.** L'enveloppe d'une réponse d'API — identifiants internes,
  drapeaux, tableaux vides, objets de relation — pèse couramment neuf dixièmes
  du fichier sans porter une ligne de contenu. Mesurer le brut faisait franchir
  le seuil de gros volume à des sources qui ne l'atteignent pas, et multipliait
  d'autant le nombre de lecteurs : dix fois plus de tranches pour le même
  texte, chacune payée en contexte et en temps.
- **`/doc-query` : un terme fréquent redevient un critère valide en
  énumération.** La règle écartait les termes répandus, ce qui est juste sur
  une question thématique et faux dès que la question demande *tout ce qui
  concerne* un acteur, un module, un produit — là, ce terme fréquent **est** le
  critère de sélection, et l'écarter revient à chercher autre chose que ce qui
  est demandé.
- **README : ce que fait le plugin, puis comment l'installer, dans les trente
  premières lignes.** Il ouvrait sur l'architecture — orchestration en
  sub-agent, `context: fork`, degrés de fidélité — et l'installation arrivait
  à la ligne 128. Le nouveau début dit à quoi ça sert en cinq lignes, donne les
  trois commandes pour démarrer, puis un tableau des cinq commandes avec les
  deux qui servent au quotidien mises en avant. Rien n'est retiré : les
  sections d'architecture suivent, et l'installation complète devient
  « installation détaillée ».
- **`/doc-bench` annonce d'abord ce sur quoi on peut agir.** Il se présentait
  par la détection de régression du moteur — moitié qu'un utilisateur ne peut
  que constater, le moteur n'étant pas dans ce dépôt. L'autre moitié passe
  devant : le banc dit si les notes sont assez maillées et assez découpées pour
  être retrouvées, et un échec renvoie à un wikilink absent ou à une section
  trop longue, tous deux à portée de main.
- **`/doc-query` : le périmètre du grep est écrit.** Il n'était spécifié nulle
  part, donc décidé au cas par cas. Par défaut `wiki/`, seule couche à la fois
  complète et indexée ; `archives/` seulement quand la question porte sur ce
  qu'une pièce portait littéralement, et en l'annonçant ; `inbox/` jamais — ce
  qui s'y trouve n'est ni standardisé ni vérifié, le citer reviendrait à en
  faire un fait du vault.

## [1.37.0] — 2026-08-02

**Raison de l'update** : refusés par le classificateur de permissions, les scripts du plugin font DÉGRADER une commande au lieu de l'arrêter — le résultat reste plausible, en moins bon.

### Ajouté
- **`/vault-init` autorise les scripts du plugin.** Il n'inscrivait que l'accès
  au vault (`additionalDirectories`) ; chaque commande `/doc-*` appelle en plus
  plusieurs scripts, refusés un par un tant que rien ne les autorise. Le coût
  n'est pas un échec franc mais une **dégradation silencieuse** : la commande
  improvise un repli et rend un résultat amoindri. Constaté en usage réel — une
  recherche sémantique menée sur des index périmés parce que la réindexation
  avait été refusée.
  Deux règles sont ajoutées (`bash` et `python3`), avec un **joker sur le
  numéro de version** pour survivre aux mises à jour du plugin. Périmètre
  étroit : ce dossier de scripts, rien d'autre.
  La fusion (`scripts/merge-permissions.py`) préserve un fichier existant, est
  idempotente, et **refuse d'écrire** si le JSON est illisible plutôt que
  d'écraser une configuration qu'elle ne comprend pas.

### Corrigé
- **Les commandes en fork ne transmettent plus de consignes du tout.** La
  1.35.0 les faisait écrire sur disque : **impossible**, un fork `Explore` est
  en lecture seule stricte et n'a aucun outil d'écriture. C'était la troisième
  tentative après l'interdiction dans le fichier de commande (invisible pour le
  destinataire) et le titre « NE PAS AFFICHER » (affiché avec son titre).
  Il n'y a en réalité rien à transmettre : les conventions d'écriture sont dans
  `INSTRUCTIONS-CLAUDE.md`, que l'agent principal peut lire, et le reste est
  déjà dans le rapport. Le rapport se termine par **deux lignes** — le chemin
  du vault, seule chose qui ne se devine pas, et la question ou le verdict.

## [1.36.0] — 2026-08-02

**Raison de l'update** : le script listant les dossiers à indexer a été refusé par les permissions en pleine recherche — la commande s'en est sortie en improvisant, ce qui n'est pas une garantie.

### Ajouté
- **`/doc-query` sait se passer du script de listing des cibles.** Refusé par
  les permissions ou introuvable, il ne fait plus renoncer à l'indexation : la
  liste se retrouve en listant les sous-dossiers de `wiki/` qui contiennent au
  moins un `.md` — c'est exactement ce que le script calcule. Il existe pour
  **centraliser** la règle, pas pour la détenir.
  Constaté en usage réel : le repli avait été improvisé correctement, en
  lisant la liste dans `INSTRUCTIONS-CLAUDE.md`. Il est désormais spécifié,
  pour ne plus dépendre du jugement du moment.

## [1.35.0] — 2026-08-02

**Raison de l'update** : deux tentatives d'interdire l'affichage du bloc de consignes ont échoué — dans une commande en fork, la sortie du sub-agent EST ce que l'utilisateur lit.

### Corrigé
- **Une synthèse est indexée dès son écriture.** `/doc-query` écrivait la note,
  son entrée d'INDEX et sa ligne de journal, mais ne réindexait pas : la
  synthèse n'entrait dans l'espace vectoriel qu'à la **recherche suivante**,
  qui réindexe avant de chercher. Elle existait, l'INDEX la listait, le bras
  lexical la trouvait — mais elle était absente de la similarité jusque-là.
  L'indexation étant incrémentale, elle ne coûte que les chunks de cette note,
  et ce coût aurait été payé au prochain `/doc-query` de toute façon.

### Modifié
- **Les consignes de suite passent sur disque, le rapport n'en garde qu'une
  ligne.** Les trois commandes en fork terminaient par un bloc destiné à
  l'exécution — chemins absolus, frontmatter à écrire, outils à appeler. La
  1.29.0 a interdit de l'afficher dans le fichier de commande : sans effet, le
  destinataire ne le lit pas. La 1.33.0 a titré le bloc
  « NE PAS AFFICHER » dans le rapport : sans effet non plus, il a été affiché
  **avec son titre**.
  La conclusion est structurelle et non rédactionnelle : dans une commande en
  fork, **la sortie du sub-agent est ce que l'utilisateur lit**, et aucune
  formulation ne changera ça. Le bloc ne doit donc plus exister dans le
  rapport. Les consignes détaillées sont écrites dans un fichier temporaire
  hors du projet et hors du vault, et le rapport se termine par **une seule
  ligne** — lisible par un humain autant qu'exploitable par un agent :
  `Suite prête : <chemin>. <la question ou le verdict>`.
  Rien n'est écrit dans le vault tant que l'utilisateur n'a pas répondu.
  **Le fichier de suite est supprimé dans les trois cas** — appliqué après un
  oui, effacé sans être appliqué après un non, et effacé aussi en l'absence de
  réponse : la question est reposée **une fois**, puis le silence vaut refus.
  Une consigne sans décision est un piège, elle traîne et la fois suivante on
  ne sait plus si elle attend encore ; et relancer indéfiniment coûterait plus
  cher que de refaire la synthèse le jour où on la veut. Rien n'ayant été écrit
  dans le vault, le refus par défaut ne perd rien.
  La purge du hook `UserPromptSubmit` — qui balayait déjà les mémoires de
  pistes et couvre désormais les deux familles de résidus — reste le dernier
  filet, pour la session interrompue avant toute décision, pas pour tenir lieu
  de nettoyage ordinaire.

## [1.34.0] — 2026-08-02

**Raison de l'update** : rien n'empêchait un identifiant contenu dans une source d'être recopié tel quel dans une couche immuable, indexée et synchronisée.

### Ajouté
- **`/doc-ingest` masque les identifiants dans la note, jamais dans la pièce.**
  Une source peut contenir un mot de passe, un jeton, une clé — typiquement un
  `.env` recopié dans un message. Ces valeurs ne sont pas de l'information sur
  le sujet, ce sont des **accès vivants** : les écrire dans `wiki/sources/` les
  place dans une couche immuable, indexée et répliquée, donc impossible à
  retirer proprement.
  La valeur est remplacée par `[identifiant masqué — voir la pièce archivée]`,
  **le nom de la variable est conservé**, et la pièce reste intacte dans
  `archives/`, hors de l'index. Ce n'est pas une entorse à la fidélité mais sa
  condition : la couche est fidèle à ce que la pièce **dit**, et la valeur
  d'une clé ne dit rien du sujet.
  Un `> [!warning]` le consigne dans la note d'enseignements — qu'une pièce
  contienne des identifiants est un fait sur la pièce. Et le compte rendu le
  dit en clair, avec le seul remède qui vaille : la révocation chez l'émetteur,
  pas le masquage.
  La règle vient d'un cas réel : une note du corpus portait déjà ce masquage,
  décidé par la session qui l'avait ingérée. Ce qui marchait par jugement
  devient une consigne, et l'auto-vérification de fin d'ingestion la contrôle.

## [1.33.0] — 2026-08-02

**Raison de l'update** : le correctif de la 1.29.0 n'a rien changé — il était écrit à un endroit que l'agent principal ne lit pas.

### Corrigé
- **Le garde-fou du bloc de consignes voyage désormais dans le rapport.** Les
  trois commandes en fork terminent par des consignes destinées à l'agent
  principal ; la 1.29.0 lui interdisait de les afficher — mais **dans le
  fichier de commande, que seul le sub-agent reçoit**. En fork, l'agent
  principal ne voit que le rapport : une consigne écrite ailleurs lui est
  invisible. Mesuré : le bloc a continué d'être recopié à l'utilisateur, mot
  pour mot, sous la version corrigée.
  Le sub-agent titre maintenant le bloc
  `## Pour l'agent principal — CONSIGNES D'EXÉCUTION, NE PAS AFFICHER` et
  l'ouvre par une ligne qui le redit. L'interdit part avec le contenu, au lieu
  d'attendre dans un fichier que le destinataire n'ouvre jamais.

## [1.32.0] — 2026-08-02

**Raison de l'update** : la règle de découpage d'une série datée était rangée dans la branche « capture d'écran » et prescrivait un titre par message — ce que la pratique a contredit, avec raison.

### Modifié
- **Le découpage d'une série datée dépend de la densité, plus du format.** La
  règle vivait dans la branche « capture d'écran » et ne s'appliquait donc pas
  à un export texte ou JSON, alors que la question est la même : *quel morceau
  veut dire quelque chose tout seul ?* Elle est remontée à la standardisation,
  où elle vaut pour toutes les formes de source.
  Et elle change de contenu : elle imposait **un titre par entrée**, ce qui
  donnerait des centaines d'extraits d'une ligne sur une conversation. Deux cas
  désormais — **conversation → un titre par jour**, messages horodatés en
  dessous ; **relevé ou journal d'entrées substantielles → un titre par
  entrée**. Constaté sur un corpus réel : deux conversations ingérées, l'une
  depuis six captures d'écran et l'autre depuis un export texte de 479
  messages, ont toutes deux été structurées par jour — la pratique avait déjà
  tranché contre la règle écrite.
- **L'export de messagerie en JSON est nommé dans le routage.** Il se lit sans
  conversion, mais il n'a aucune structure markdown : c'est la standardisation
  qui doit la lui donner, sans quoi plusieurs centaines de messages partent en
  un seul bloc. Les métadonnées techniques — identifiants, empreintes, URL de
  pièces jointes — ne sont pas du contenu et s'écartent, sauf celles qui datent
  ou attribuent.

## [1.31.0] — 2026-08-02

**Raison de l'update** : le hook des pistes reproposait les mêmes notes à chaque question sur un même sujet — ce n'est pas le volume qui pollue une session, c'est la redondance.

### Modifié
- **Le hook `UserPromptSubmit` ne propose jamais deux fois la même note dans
  une session.** Il se déclenche à chaque prompt et remonte, sur un sujet
  suivi, les trois mêmes notes à chaque fois : trois questions sur une même
  pièce réinjectaient trois fois les mêmes extraits. Le coût en jetons n'était
  pas le problème — mesuré, ~200 jetons par déclenchement, environ la moitié
  des prompts, soit 1 % d'une fenêtre d'un million sur cent tours. Le problème
  est que du contexte périmé reste et concurrence le reste pour l'attention.
  Une mémoire de session (fichier éphémère hors du projet **et** hors du
  vault, nommé par `session_id`) retient ce qui a déjà été proposé.
  **Et quand les trois meilleures sont déjà connues, le hook se tait** — il ne
  descend pas au rang 4 ou 7 pour avoir quelque chose à dire. Proposer du bruit
  sous prétexte de ne pas rester muet serait exactement le défaut qu'on
  corrige. Mesuré : même question posée trois fois → 741 octets, puis 0, puis
  0 ; question sur un autre sujet → 781 octets.
  La mémoire **se nettoie elle-même** : à chaque passage, celles de plus de
  sept jours sont supprimées. Aucun hook ne se déclenche de façon fiable à la
  fermeture d'une session, et s'en remettre au nettoyage de `/tmp` par le
  système ne garantirait rien. Sept jours et non un : une session reprise le
  lendemain doit retrouver sa mémoire.

## [1.30.0] — 2026-08-02

**Raison de l'update** : du JSON cité dans une pièce fabriquait des nœuds fantômes dans le graphe Obsidian, et la vérification des wikilinks ne les voyait pas — ils tombaient entre « pendant » et « ambigu ».

### Ajouté
- **`/doc-lint` détecte les faux wikilinks.** Une cible qui contient un
  guillemet, une virgule ou une accolade n'est pas un lien mal écrit : c'est du
  **texte que le rendu prend pour un lien**. Un tableau JSON imbriqué cité dans
  une pièce ouvre et ferme deux crochets d'affilée — `[[` puis `]]` — et
  Obsidian en fait des nœuds fantômes. Le scan précédent présumait de la forme d'une
  cible, donc ne les comptait ni pendants ni ambigus : ils passaient entre les
  deux mailles, et un vault propre sur onze contrôles polluait quand même le
  graphe.
  Le remède n'est pas de corriger un lien mais d'**entourer le passage d'une
  clôture de code** — mécanique, appliqué d'office, et acceptable même en couche
  immuable puisque **aucun caractère du texte n'est modifié** : la couche est
  fidèle au texte de la pièce, pas aux artefacts de rendu de l'outil qui
  l'affiche. Ce qui est déjà clôturé n'est pas signalé.

### Modifié
- **`/doc-ingest` clôture le code à la standardisation.** Une exception, et une
  seule, à la règle « on ne touche pas au texte » : tout passage de code ou de
  données cité dans une pièce — JSON, YAML, extrait de programme — s'entoure
  d'une clôture ` ``` `. La clôture n'ajoute que des délimiteurs. Sans elle, le
  rendu interprète ce qui n'est pas fait pour l'être, et l'auto-vérification de
  fin d'ingestion le contrôle désormais.

## [1.29.0] — 2026-08-02

**Raison de l'update** : le bloc « Pour l'agent principal » était recopié tel quel à l'utilisateur — il recevait la mécanique interne à la place de l'interaction attendue.

### Corrigé
- **Le bloc « Pour l'agent principal » ne s'affiche plus.** Les trois commandes
  en fork (`/doc-query`, `/doc-lint`, `/doc-repair`) terminent leur rapport par
  un bloc de consignes destiné à l'agent principal : chemins absolus, noms
  d'outils MCP, frontmatter à écrire, question à poser. Rien n'interdisait de
  le relayer, et un agent principal recevant un rapport le relaie
  naturellement en entier. Résultat : l'utilisateur lisait
  « présenter la réponse à l'utilisateur, puis proposer : Sauvegarder cette
  réponse en synthèse ? » **au lieu qu'on la lui pose**. Les trois commandes
  disent maintenant explicitement que ce bloc s'exécute et ne se recopie
  jamais.

## [1.28.1] — 2026-08-02

**Raison de l'update** : le README décrivait un plugin qui n'existe plus — sur un dépôt public, c'est le point d'entrée.

### Corrigé
- **README remis en cohérence.** Il annonçait encore la validation
  conversationnelle de `/doc-ingest` (supprimée en 1.22.0), le routage
  « document ou PDF → OCR » (faux depuis la 1.23.0, un PDF à couche de texte
  ne passe plus par l'OCR) et des corrections de `/doc-lint` « validées avec
  l'utilisateur » (faux depuis la 1.22.0, les mécaniques s'appliquent
  d'office). Quelqu'un qui le lisait s'attendait donc à valider ses
  enseignements un par un et à voir ses PDF partir à l'OCR.
  Ajoutés : les identifiants en clair et les renvois à sens unique dans la
  liste des vérifications, les deux régimes de correction, `pdf-text.py` dans
  l'arborescence, et le masquage du hook PreCompact.

## [1.28.0] — 2026-08-02

**Raison de l'update** : le hook PreCompact dépose les tours de conversation dans un dossier synchronisé — un identifiant collé dans un prompt y était archivé tel quel. Le détecter après coup arrivait trop tard.

### Ajouté
- **Le hook PreCompact masque les identifiants avant d'écrire.** Il excluait
  déjà les sorties d'outils, là où vivent la plupart des secrets ; restaient les
  tours de conversation eux-mêmes. Sont masqués : les affectations
  `NOM=valeur` / `NOM: valeur` dont le nom porte `TOKEN`, `SECRET`, `PASSWORD`,
  `API_KEY`, `PRIVATE_KEY`, `CREDENTIAL`, `AUTH`… ; les en-têtes
  `Authorization: Bearer|Basic` ; les formes propres à un émetteur, qui se
  reconnaissent sans nom de variable (`sk-`, `ghp_`, `hf_`, `xox…`, `AKIA…`,
  `AIza…`) ; et les blocs de clé privée PEM, corps compris.
  **Le nom de la variable est conservé, seule la valeur part** : `DB_PASSWORD=`
  sans sa valeur garde ce que le tour voulait dire sans en transporter le
  secret. Le hook annonce le nombre de masquages effectués.
  Le masquage est **volontairement trop large**, parce que l'asymétrie des
  erreurs est totale : un faux positif coûte un mot masqué dans un mémo de
  travail qu'on relira de toute façon à l'ingestion ; un faux négatif écrit un
  identifiant vivant dans un dossier répliqué. Il ne garantit rien pour autant —
  un secret sans forme reconnaissable et sans nom de variable passe au travers.
  C'est une réduction de surface ; le contrôle 13 de `/doc-lint` reste le filet
  derrière.

## [1.27.0] — 2026-08-02

**Raison de l'update** : le moteur consigne enfin la granularité de découpage de ses index, et deux runs de banc ont exposé un `cd` qui emportait le répertoire de la session entière.

### Ajouté
- **`/doc-lint` compare la granularité de découpage entre index.** Le moteur
  consigne désormais `chunk_chars` dans les métadonnées, et le contrôle de
  cohérence vectorielle le lit comme les trois autres champs — mais **pas avec
  la même conséquence**, et la distinction est le cœur du contrôle : un
  provider ou un modèle divergent rend des scores **faux**, donc c'est une
  erreur ; une granularité divergente rend des scores **justes** établis sur un
  grain inégal, donc c'est un constat. La recherche continue de fonctionner, et
  cet état est même normal pendant une reconstruction en cours. Champ absent =
  granularité inconnue, jamais index invalide.

### Corrigé
- **`vault-check.sh` cherche la config en remontant l'arborescence.**
  `CLAUDE_PROJECT_DIR` n'est pas toujours défini — certains sub-agents ne le
  propagent pas — et le répertoire courant peut être un sous-dossier du projet.
  Le script remontait alors bredouille et déclarait le vault absent : constaté
  sur `vault-index-targets.sh`, puis sur `vault-lexical.sh`. La remontée règle
  les deux cas pour quelques `test -f`, et le message d'erreur nomme désormais
  les deux remèdes au lieu d'un seul chemin.
- **Les commandes ne déplacent plus le répertoire de la session.** L'outil Bash
  conserve son répertoire d'un appel à l'autre : un `cd` dans le vault y
  laissait la session entière — visible dans l'invite de l'utilisateur, qui
  passait du nom de son projet au chemin du vault — et cassait tout ce qui se
  résout depuis le projet, `.claude/vault-path.local` en tête. Les cinq
  commandes l'interdisent désormais explicitement : chemins absolus, ou
  sous-shell.

## [1.26.0] — 2026-08-02

**Raison de l'update** : la colonne lexicale du banc mesurait un grep artisanal, pas le bras BM25 du moteur — donc elle ne pouvait rien dire de la seule question qu'elle aurait dû trancher : est-ce qu'une fusion lexical/sémantique apporterait quelque chose.

### Modifié
- **Le banc mesure `bm25@3` au lieu d'un grep artisanal.** La colonne appelle
  désormais `vault-lexical.sh` — le **vrai** bras lexical, celui que le hook et
  `/doc-query` emploient — sur la même fenêtre que le bras sémantique : top 3
  par dossier, rang lu dans son propre dossier. Les deux colonnes deviennent
  donc directement comparables.
  La différence n'est pas cosmétique. BM25 pondère par IDF et **normalise par
  la longueur du document** ; le grep artisanal, lui, faisait remonter les
  trois pièces les plus longues du vault, qui contiennent mécaniquement tous
  les mots de n'importe quelle question. On avait failli conclure de ce défaut
  que le bras lexical n'apportait rien — alors que c'est précisément ce que
  BM25 corrige par construction.
- **Deux chiffres de contribution marginale** accompagnent la colonne :
  combien de questions bm25 touche que le sémantique rate (la couverture
  qu'une fusion ajouterait), et combien elle classe mieux (le gain de rang).
  Deux zéros tranchent la question de la fusion, qui n'a jamais été mesurée —
  elle avait été écartée sur un raisonnement.
- **La ligne `grep` sort du score.** Elle survit comme repli lisible quand le
  moteur est absent, jamais comme mesure : appliquée implicitement puis figée,
  elle a rendu 11, 10 puis 6 sur un corpus **strictement identique**. Un
  chiffre non reproductible est pire qu'absent, il se compare quand même.
  Le moteur portant les deux bras, son indisponibilité emporte désormais les
  deux colonnes.

## [1.25.0] — 2026-08-02

**Raison de l'update** : le banc a trouvé une note introuvable — non pas parce que le moteur la classait mal, mais parce que sa page-parent ne la mentionnait pas. Aucune vérification ne regardait ça.

### Ajouté
- **`/doc-lint`, treizième vérification : renvois à sens unique.** Une note qui
  se déclare le complément d'une autre — « page de regroupement complétant
  `[[X]]` », « suite de `[[X]]` » — doit être pointée en retour par cette
  page-parent. Le défaut échappe au contrôle des orphelines : la page
  complémentaire est pointée par d'autres notes, donc elle passe pour saine.
  Mais qui arrive sur la parente ne saura jamais que le complément existe, et
  une recherche qui remonte la parente ne l'atteindra pas en suivant ses liens.
  Mesuré : sur un banc de 22 questions, c'est la **seule** dont une attendue
  était hors de portée, moteur hors de cause. Deux couples concernés sur un
  vault de 148 notes — ce n'est pas un cas de figure exotique.
  Correction mécanique, appliquée d'office : le lien manquant est ajouté dans
  la phrase qui s'y prête, jamais en « Voir aussi » de fin de note, qui ne dit
  pas ce que le complément apporte.

### Corrigé
- **`vault-check.sh` lit `CLAUDE_PROJECT_DIR`, plus `$PWD`.** Le script
  résolvait la config du vault depuis le répertoire courant : appelé par un
  sub-agent ou un wrapper qui avait changé de dossier, il déclarait le vault
  absent alors qu'il était parfaitement accessible. Constaté sur
  `vault-index-targets.sh` sans argument. Repli sur `$PWD` hors de Claude
  Code, pour l'appel manuel.
- **Le critère de `grep` du banc est figé** : mots de 5 caractères ou plus,
  accents repliés, casse ignorée, cherchés dans le corps entier de la note ;
  attendue touchée dès la moitié des mots. Il n'était pas écrit — deux runs
  sur un corpus **strictement identique** ont rendu 11/22 puis 10/22, et
  l'écart s'est lu comme une régression alors que le grep ne passe même pas
  par le moteur. Un chiffre non reproductible est pire qu'absent : il se
  compare quand même.

## [1.24.1] — 2026-08-02

**Raison de l'update** : un run de banc a reformulé les questions au lieu de les envoyer telles quelles — un étalon dont la question change d'un run à l'autre ne mesure plus rien de comparable.

### Corrigé
- **`/doc-bench` envoie la question caractère pour caractère.** La consigne
  disait « question telle quelle » entre parenthèses ; un run l'a lue comme
  une indication de sens et a « rendu les questions plus naturelles »
  (inversions sujet-verbe, virgules ajoutées). L'écart qu'un banc doit lire —
  un rang, parfois moins — est plus petit que celui qu'une reformulation
  introduit. La règle est désormais explicite et motivée.

## [1.24.0] — 2026-08-02

**Raison de l'update** : le vault vit sur un dossier synchronisé, donc un jeton d'accès oublié dans `inbox/` part avec lui — rien ne le cherchait. Et une partie de ce qui attendait une autorisation n'avait rien à perdre.

### Ajouté
- **`/doc-lint`, douzième vérification : identifiants en clair.** Un vault
  vit sur un dossier synchronisé — ce qui y traîne part avec lui, et un secret
  oublié n'est plus un secret. Le contrôle balaie tout le vault, `inbox/` et
  `archives/` compris puisque ce sont eux qui reçoivent les exports bruts :
  `.env`, `.*_token`, `*secret*`, `*credential*`, `*.pem`, `*.key`, `id_rsa*`,
  et les contenus portant `TOKEN=`, `API_KEY=`, `sk-`, `ghp_`, `xox`.
  La valeur trouvée n'est **jamais affichée** — la citer la recopierait dans un
  transcript ; seuls le chemin et la taille sont donnés. Le résultat se lit
  **avant la ligne de compteurs**, sans y figurer : ce n'est pas une dette de
  maintenance, c'est une fuite.
  Le remède n'est pas la suppression : un secret qui a séjourné dans un
  dossier synchronisé est **compromis**, et l'effacer n'annule pas ce qui est
  déjà répliqué. L'ordre est de le révoquer chez l'émetteur, puis de sortir le
  fichier — et la suppression se propose, elle ne s'applique pas d'office :
  c'est peut-être le seul exemplaire.

### Modifié
- **Les suppressions sans perte possible passent en automatique.** Une note
  vide, un fichier de conflit Drive sur un dérivé jetable, un reliquat d'index
  d'une version antérieure : il n'y a rien à sauver dans un fichier vide et un
  dérivé se régénère. Demander l'autorisation ne protégeait rien et coûtait un
  aller-retour. Restent soumis les trois actes qui ne se défont pas — fusionner
  deux pages, supprimer un fichier qui porte du contenu, écrire dans une couche
  immuable — le vault n'étant pas versionné.
- **Le compte rendu d'ingestion dit ce qui a été reporté** :
  `<n> point(s) reportés à /doc-lint`. Ils étaient comptés sans être annoncés,
  donc invisibles.
- **Description du plugin ramenée à une ligne.** Elle faisait 623 caractères
  dans la liste `/plugin`, où chaque entrée doit tenir sur une ligne, et
  annonçait encore un « sub-agent lecteur conversationnel » supprimé en
  1.22.0. Le détail vit dans le README et `PREREQUIS.md`.

## [1.23.0] — 2026-08-02

**Raison de l'update** : un PDF produit par un logiciel était envoyé à l'OCR comme s'il n'avait pas de texte — mesuré sur un export tableur, une colonne entière inversée sans que rien ne le signale.

### Ajouté
- **`scripts/pdf-text.py`** — extraction de la couche de texte d'un PDF, en
  bibliothèque standard seule : aucun `pip install`, aucun réseau, aucune clé.
  Flux décompressés en zlib, glyphes traduits par les tables `/ToUnicode` que
  le PDF embarque pour ses polices sous-ensemblées. Sort en 0 avec le texte,
  en 1 avec un message explicite quand la couche est absente — c'est le code
  de sortie qui aiguille vers l'OCR, pas une appréciation.
  Deux refus, pas un seul : couche absente (scan), **et couche trop maigre pour
  être le contenu**. Un diaporama exporté en PDF porte ses titres en texte
  pendant que tout son fond est en images — mesuré, 348 caractères sur 11
  pages, contre 4 736 par page pour un export tableur. Se fier au total seul
  ferait déclarer « PDF texte » un document dont on perdrait l'essentiel,
  silencieusement ; c'est la **densité par page** qui tranche.

### Modifié
- **Un PDF n'est plus envoyé à l'OCR par défaut.** `/doc-ingest` teste d'abord
  la couche de texte. Un PDF produit par un logiciel — export tableur,
  traitement de texte, facture générée — contient le texte tel que ce logiciel
  l'a écrit : l'extraire est exact, gratuit et instantané. Le passer à l'OCR
  revient à le photographier pour deviner ce qu'on pouvait lire.
  Ce que ça coûtait, mesuré sur un export de 40 lignes : les **18 « Haute »**
  d'une colonne de priorité lues **« Moyenne »**, soit 35 « Moyenne » pour 17
  réelles — une colonne entière inversée. L'erreur est invisible parce que le
  résultat reste plausible et cohérent avec lui-même. L'OCR garde son terrain :
  le scan, la photo, la page dont il n'existe aucune autre lecture que l'image
  — et cette lecture-là se signale désormais par un `> [!warning]` dans la note
  d'enseignements.
- **`/doc-repair` vérifie l'original par cette même voie.** La transcription
  archivée d'un PDF **est** sa sortie d'OCR : la relancer rendrait la même
  erreur, un OCR ne se contrôle pas par lui-même. Vrai scan ou `python3`
  absent → vérification déclarée **partielle**, jamais un repli sur l'OCR.
- **L'agent principal contre-vérifie le rapport de `/doc-repair`** avant
  d'écrire un constat chiffré ou nominatif dans une couche immuable. Un
  rapport de sub-agent est un témoignage, pas une preuve : rouvrir la pièce par
  la voie indépendante et recompter soi-même. Écart → la pièce gagne. Mesuré
  sur un rapport réel : deux affirmations fausses sur huit, dont celle qui
  devait être gravée.
- **Une divergence transcription/original déclenche une réingestion**, pas une
  réécriture à la main : elle condamne tout ce que la transcription a produit.
  `/doc-repair` pose le `> [!warning]` qui empêche l'erreur de remonter en
  recherche, puis `/doc-ingest` relit la pièce par la voie correcte.

## [1.22.0] — 2026-08-02

**Raison de l'update** : les commandes demandaient à l'utilisateur de trancher des questions dont la réponse est dans les pièces qu'il n'a pas lues — c'est à la commande de décider, et à elle seule d'enchaîner ses contrôles.

### Modifié
- **Plus aucune commande ne demande son avis à l'utilisateur.** Ce qui arrive
  dans `inbox/` y est déposé pour que le vault s'en serve, le plus souvent sans
  que l'utilisateur ait ouvert la pièce : lui faire valider des enseignements,
  un regroupement de fichiers ou une paire de pages qu'il n'a pas lus ne
  vérifie rien, ça déplace la charge sur celui qui a le moins de contexte.
  Deux régimes désormais, partout :
  - **mécanique et réversible** (INDEX, wikilinks, frontmatters, parasites,
    réindexation, requalification d'un callout) → appliqué d'office ;
  - **destructeur ou irréversible** (fusionner, supprimer, éditer une couche
    immuable) → soumis **une fois**, avec le verdict et ce qui le motive. La
    question porte sur l'autorisation d'agir, jamais sur la réponse.

  Ne subsistent que les questions dont la réponse n'est nulle part dans le
  vault : le chemin du vault, quoi ingérer, l'`auteur` d'une note, l'ancrage
  d'une série de captures non datées, une version texte quand aucun
  convertisseur n'est disponible. Et elles ne bloquent plus : sans réponse,
  l'ingestion se poursuit avec un `> [!warning]`.
- **`/doc-ingest` : la validation conversationnelle disparaît.** Elle est
  remplacée par un contrôle que la commande fait elle-même — chaque
  enseignement est-il porté par la source, ce qui est douteux se consigne en
  `> [!question]` au lieu de bloquer, rien ne s'invente pour combler. Une
  contradiction avec l'existant se tranche sur les pièces (la plus récente, la
  plus directe, celle qui fait foi) et ne remonte en callout que si aucune ne
  départage.
- **`/doc-ingest` enchaîne `/doc-lint`** en fin de course, une fois par
  ingestion : l'auto-vérification de la 1.21.0 ne voit que les notes écrites,
  certains défauts ne se voient qu'à l'échelle du vault. Les corrections
  mécaniques sont appliquées dans la foulée ; le reste est compté, pas soumis.
  Échec non bloquant.
- **`/doc-lint`** rend un **verdict** sur chaque paire de doublons suspectés —
  doublon accidentel ou scission délibérée — au lieu de demander si la scission
  est voulue. Deux pages traitant le même objet sous deux angles (ce qu'une
  pièce affirme / ce que le corpus établit) ne sont pas un doublon, et une
  réserve valable sur l'une deviendrait fausse au-dessus de l'autre.
- **`/doc-repair`** tranche entre erreur de restitution et information périmée
  au lieu de présenter les deux lectures ; indépartageable → la lecture la
  mieux étayée, et un `> [!question]` qui garde l'autre en mémoire.
- **`/doc-repair` vérifie contre la transcription ET contre l'original.** Le
  frontmatter d'une note d'origine porte jusqu'à deux chemins : `origine:`,
  ce dont la note a été faite (la transcription archivée), et `original:`, la
  pièce qui fait foi quand elle diffère. La commande n'ouvrait que le premier —
  or vérifier une correction contre une transcription seule, c'est la vérifier
  contre la machine qui a peut-être produit l'erreur. Les deux sont ouverts
  désormais, l'original tranche, et une divergence entre les deux devient
  elle-même une trouvaille : elle affecte tout ce que la transcription a
  produit. Original illisible → vérification déclarée **partielle**.
  L'original est ouvert **selon son format**, comme `/doc-ingest` route ses
  entrées : une capture se lit à l'œil (jamais d'OCR), un binaire bureautique
  se convertit, un texte se lit tel quel. Cas piégeux traité à part, le PDF :
  sa transcription archivée **est** sa sortie d'OCR, donc relancer l'OCR
  rendrait la même erreur — un OCR ne se contrôle pas par lui-même. La
  vérification passe par une voie différente (`pdftotext`, `pandoc`) ou se
  déclare partielle.
- **`/doc-lint` délègue à `/doc-repair`** pour trancher un `> [!question]`,
  une contradiction à la fois : elle oppose deux affirmations, et savoir
  laquelle la pièce porte suppose de remonter jusqu'à elle. Le reste des
  vérifications n'y passe pas — un lien pendant ou un trou d'INDEX se constate
  dans le vault, remonter à la pièce ne serait qu'une dépense.
- **`/doc-bench creer`** écrit le banc directement, après avoir vérifié
  lui-même que chaque attendue existe et qu'aucune question ne reprend les mots
  exacts de sa note. Un `BENCH.md` existant n'est plus jamais écrasé : c'est un
  étalon, le remplacer rendrait incomparables tous les runs passés.

## [1.21.2] — 2026-08-01

**Raison de l'update** : le modèle de vault réclamait encore une réserve « sur la note de source » alors que sa propre convention des callouts l'interdit — chaque pièce non datée reposait donc un commentaire éditorial dans la couche de texte pur.

### Corrigé
- **`INSTRUCTIONS-CLAUDE.md` se contredisait sur la place des réserves.** La
  convention des callouts pose qu'un `> [!warning]` vit dans
  `wiki/enseignements/`, sous son propre `###`, et jamais dans
  `wiki/sources/` — une réserve n'est pas ce que la pièce dit, c'est ce qu'on
  en constate. La règle de nommage, elle, demandait encore un `> [!warning]`
  « sur la note de source » pour une pièce non datée. Les deux phrases sont
  alignées, et `/doc-ingest` précise la même chose au moment d'écrire.
  L'enjeu n'est pas cosmétique : dans `sources/`, la réserve est noyée dans le
  préambule d'un texte intégral et n'est pas retrouvable seule ; sous son
  `###` dans `enseignements/`, elle devient un extrait indexé, et « quelles
  pièces ne sont pas datées ? » a une réponse.

## [1.21.1] — 2026-08-01

**Raison de l'update** : une convention mal bornée faisait écrire des wikilinks ambigus vers les pièces, et aucune vérification ne pouvait les voir — ils résolvent, donc ils ne sont jamais pendants.

### Corrigé
- **Wikilinks ambigus vers les pièces.** Une pièce a deux notes de même slug,
  l'une dans `sources/`, l'autre dans `enseignements/` : un `[[<slug>]]` nu
  en désigne donc deux à la fois. Obsidian n'avertit pas, il en choisit une
  silencieusement — et comme le lien résout, aucun contrôle de lien pendant ne
  le signale. La convention du vault n'imposait le préfixe qu'**entre les deux
  notes de la paire** et déclarait le nom nu valable « partout ailleurs » : les
  pages de `concepts/` et `entites/`, qui citent une pièce sans se préoccuper
  de sa couche, reproduisaient donc le défaut à chaque écriture.
  Corrigé aux trois endroits : le modèle `INSTRUCTIONS-CLAUDE.md` étend la
  règle à **tout lien vers une pièce, d'où qu'il parte** ; `/doc-ingest`
  l'applique à l'écriture et la contrôle en auto-vérification ; `/doc-lint`
  la vérifie sur tout le vault.

### Modifié
- `/doc-lint` : la vérification des wikilinks distingue désormais deux
  défauts, **pendant** (la cible n'existe pas) et **ambigu** (la cible est un
  nom nu porté par plusieurs dossiers), listés séparément. Elle signale aussi
  un `INSTRUCTIONS-CLAUDE.md` resté sur l'ancienne formulation — les fichiers
  racine d'un vault n'étant jamais écrasés par `/vault-init`, un vault créé
  avant cette version continuerait sinon à produire des liens ambigus quel que
  soit le nombre de liens corrigés.

## [1.21.0] — 2026-08-01

**Raison de l'update** : les défauts d'écriture — lien pendant, note absente de l'INDEX, appariement rompu — n'étaient découverts qu'au `/doc-lint` suivant, donc parfois plusieurs ingestions plus tard, quand le contexte qui aurait permis de les comprendre avait disparu.

### Ajouté
- `/doc-ingest` : **auto-vérification en fin d'écriture**, bornée aux seules
  notes que l'ingestion vient de produire — wikilinks pendants, appariement
  `sources`/`enseignements`, entrées d'INDEX, références de fichier mortes,
  présence des titres `###`. Les écarts sont corrigés avant le compte rendu et
  mentionnés dedans.
  Ce n'est **pas** un `/doc-lint` automatique : celui-là balaie tout le vault,
  coûte un fork entier et ne fait que rapporter. Ici le contrôle porte sur ce
  que cette ingestion pouvait casser, l'agent a déjà ces fichiers sous la main,
  et il corrige au lieu de signaler. C'est le moment le moins cher — le défaut
  n'a pas eu le temps de se propager aux ingestions suivantes.

### Modifié
- `/doc-ingest`, compte rendu : **quatre lignes au plus, et rien à faire après
  l'avoir lu.** Il confirme, il ne fait pas travailler — plus de liste de
  fichiers, plus de tableau de callouts, plus de question posée. Ce qui est
  entré en nombres, les contradictions en attente en un chiffre (`/doc-lint`
  les listera le jour venu), ce que l'auto-vérification a corrigé si elle a
  corrigé quelque chose, et l'indexation. Le détail reste disponible sur
  demande. Une ingestion qui s'est bien passée est un non-événement.

## [1.20.1] — 2026-08-01

**Raison de l'update** : le hook `UserPromptSubmit` parlait sous chaque message, y compris quand la conversation n'avait rien à voir avec le vault — au point de donner l'impression que le vault était le sujet permanent de la session. Premier défaut observé depuis qu'il fonctionne réellement (1.19.0).

### Corrigé
- La cause : BM25 rend **toujours** quelque chose, un top-K n'ayant aucun
  plancher de pertinence. Et — mesuré sur un corpus réel — **le score ne
  distingue pas** une question sur le vault d'une phrase de conversation :
  « je fais quoi maintenant du coup » y obtient 6,44 quand « qui détient quelle
  part du capital » n'obtient que 5,27, un mot rare et hors sujet pesant autant
  qu'un mot rare et pertinent. Aucun seuil ni rapport de scores ne les sépare.
  Ce qui les sépare est le **vocabulaire** : le hook exige désormais qu'au moins
  un mot long du prompt figure dans `INDEX.md` **et y soit caractéristique** —
  présent dans au plus un dixième des entrées. Ce plafond se recalcule sur
  l'INDEX du moment, donc rien à régler, et il écarte les mots que le vault
  emploie partout sans écarter ceux qui le désignent. Vérifié sur dix prompts :
  neuf classés correctement, et la porte s'exécute **avant** tout appel au
  moteur. Trois pistes au plus, contre six.

## [1.20.0] — 2026-08-01

**Raison de l'update** : une ingestion de douze pièces a demandé une heure. La cause n'était pas la lecture ni l'analyse, mais la standardisation : le sub-agent **retapait en jetons produits** un texte déjà présent sur le disque. Pour un document de soixante-dix kilo-octets, c'est le recopier mot pour mot — et c'était le poste de dépense principal de chaque ingestion.

### Modifié
- **Les réserves documentaires quittent `wiki/sources/` pour
  `wiki/enseignements/`**, sous leur propre titre `###`. Une réserve — pièce
  tronquée, non signée, non datée — n'est pas ce que la pièce *dit*, c'est ce
  qu'on en *constate* : elle était du mauvais côté. Deux effets : `sources/`
  redevient du texte de pièce pur, donc cherchable comme tel sans qu'un
  commentaire éditorial s'y mêle — mesuré, ce bloc pesait jusqu'à un cinquième
  d'une note et fabriquait quinze extraits quasi identiques d'une note à
  l'autre ; et la réserve devient un extrait indexé à elle seule, donc
  retrouvable, là où elle se noyait dans un préambule. `/doc-lint` signale
  désormais un `> [!warning]` resté dans `sources/`.
  Le critère reste : ce qui change ce que la pièce vaut, pas les coquilles ni
  les fautes d'accord.
- **Une seule chaîne pour toute source** :
  `pièce → transcription fidèle → standardisation → wiki/sources/`. Seule la
  première flèche change de nature — transcription **donnée** pour un markdown
  déposé, produite par l'**OCR** pour un document paginé, écrite par le
  **lecteur** pour une image. Les deux suivantes sont identiques : copie,
  titres, dépôt. Une image reçoit donc elle aussi sa transcription fidèle
  archivée, là où elle n'en avait aucune : vérifier sa version structurée
  exigeait jusqu'ici de **relire toutes les captures**, bien plus cher que de
  relancer un OCR. Deux passes, mais une seule génération.
- `/doc-ingest` : **le texte déjà disponible est copié, plus jamais
  régénéré.** Markdown déposé, sortie d'OCR, export converti → copie, puis
  retouches ciblées (hiérarchie de titres, références mortes, frontmatter). La
  génération ne subsiste que là où il n'y a rien à copier : une image. Un
  fichier déjà propre ne demande plus qu'un frontmatter. « Standardiser » n'est
  pas « reproduire » : le travail est de rendre la structure exploitable, pas
  de recopier ce qui l'est déjà.
- **Le critère du `> [!warning]` est resserré** à ce qui change la valeur de la
  pièce — tronquée, non datée, non signée, signataire manquant, OCR partiel,
  en-tête d'une autre société, propos rapporté. Plus de fautes d'accord, de
  coquilles ni de guillemets non fermés : ce sont des défauts du texte, pas de
  la pièce. Ce bloc étant vectorisé comme le reste, une relecture typographique
  recopiée dans chaque note y fabriquait un extrait quasi identique d'une note
  à l'autre, qui remontait sur des questions sans rapport. Mesuré : quinze
  extraits sur quatre cent vingt, jusqu'à un cinquième d'une note.

### Ajouté
- **« Standardiser » reçoit un critère vérifiable** : le découpage sémantique
  se faisant par titre markdown, une source bien standardisée est celle où
  **aucun bloc dépassant la taille de chunk ne reste sans titre**. La structure
  réelle de la pièce devient la hiérarchie de titres, et chaque unité de sens
  un extrait retrouvable — sinon le moteur coupe où il peut, au milieu d'un
  article. C'est le seul objectif de l'étape : on ne réécrit pas, on ne résume
  pas, on ne corrige pas ; on donne les titres qui permettront de retrouver le
  texte par morceaux.
- **Séries d'entrées datées** — relevé, journal, suite d'échanges : la
  standardisation pose **un titre `###` par entrée**, ce qui en fait un extrait
  indexé à elle seule et donc retrouvable individuellement ; sans ces titres,
  toute la série part en un ou deux extraits. Chaque titre porte **le fichier
  dont l'entrée vient** : une série reste UNE note — la découper en une note
  par fichier donnerait des notes de trois lignes qui ne veulent rien dire
  seules —, et cette mention y rétablit la traçabilité plus finement qu'un
  découpage ne le ferait. Et quand les entrées ne portent
  qu'une date partielle — une heure sans jour, un jour sans année —,
  **l'ancrage est demandé à l'utilisateur** avant standardisation et reporté en
  frontmatter, jamais déduit : une année devinée dans une couche immuable ne se
  verra plus jamais.

## [1.19.1] — 2026-08-01

**Raison de l'update** : deux règles manquaient à la structure livrée en 1.19.0, et la première rendait `/doc-lint` faux. Les deux notes d'une pièce partageant leur slug, un wikilink en nom nu entre elles désigne deux fichiers à la fois : la forme correcte est préfixée du dossier — mais le lint cherchait des cibles en nom nu, et aurait donc compté pendants tous les liens croisés d'un vault conforme, et orphelines des notes correctement pointées.

### Corrigé
- `/doc-lint`, vérifications 2 et 3 : les cibles de wikilink existent sous deux
  formes — **nom nu** (`note-a`) et **préfixée du dossier**
  (`sources/2026-06-23-x`) —, et la seconde est obligatoire entre `sources/` et
  `enseignements/`. Les deux sont désormais résolues avant de conclure. La
  vérification d'appariement signale à l'inverse un lien croisé écrit en nom
  nu, qui serait ambigu.
- `INSTRUCTIONS-CLAUDE.md` et `/doc-ingest` énoncent cette forme au lieu de la
  laisser deviner.

- **`inbox/` était visible dans le graphe Obsidian.** Seul `archives/` en était
  exclu, alors que le sas relève exactement de la même règle : ni les pièces
  d'origine ni la matière brute en attente ne sont des notes. `/vault-init`
  exclut désormais les deux, et `/doc-lint` vérifie que les deux filtres sont
  bien en place.

- **Les références de fichier mortes étaient recopiées dans `wiki/`.** Un
  markdown déjà converti par un outil tiers y apporte ses `![img-0.jpeg](…)`
  vers des images jamais extraites ; la couche de texte intégral les
  transcrivait fidèlement, et comme `wiki/` est dans le graphe Obsidian —
  contrairement à `archives/` —, chacune y devenait un nœud fantôme dont un
  clic crée une note vide. `/doc-ingest` les remplace désormais par un marqueur
  textuel inerte (`[figure N — non extraite]`) dès la standardisation :
  l'information est conservée, le lien mort disparaît. Cette couche est fidèle
  au texte, pas aux liens brisés de son convertisseur. `/doc-lint` cherche
  maintenant ces nœuds **dans `wiki/` en priorité**, où ils sont un défaut à
  corriger, et non plus seulement dans `archives/`, où l'exclusion Obsidian
  suffit.

### Modifié
- Règle de nommage : le préfixe `YYYY-MM-DD-` porte la **date de la pièce**,
  jamais celle de l'ingestion. Une pièce **non datée** n'est pas préfixée —
  aucune date n'est inventée ni déduite pour satisfaire la forme, et l'absence
  devient elle-même une information, doublée d'un `> [!warning]`.

## [1.19.0] — 2026-08-01

**Raison de l'update** : le moteur agentic-toolbox avait retiré sa ligne de commande à sa version 2.0.0 (recentrage MCP-only). Le plugin l'appelait pourtant encore à trois endroits — ses wrappers d'indexation et de recherche, et le repli OCR — qui étaient donc **morts depuis des mois**. Le hook `UserPromptSubmit` en dépendait : il échouait à chaque prompt et ses gardes silencieuses avalaient l'échec, si bien qu'il n'a jamais rien fait. Le moteur expose de nouveau une porte en ligne de commande (4.1.0), et sa recherche prend désormais plusieurs dossiers en un seul appel (4.0.0).

### Ajouté
- Badges en tête du README : nature du dépôt, **version lue directement dans
  `plugin.json`** (donc jamais périmée — rien à mettre à jour à la main),
  licence, et mode d'installation.
- `scripts/vault-lexical.sh` — recherche **par mots-clés (BM25)** dans les
  dossiers de `wiki/`. **Aucun appel API, aucune clé, aucun index préalable**,
  et rien ne quitte la machine : l'index se construit en mémoire à la requête
  et se jette. Complémentaire du sémantique — il trouve le terme exact, pas la
  reformulation — et pondère par IDF, donc un mot présent dans la moitié du
  corpus n'y pèse presque rien.
- `scripts/vault-ocr.sh` — conversion OCR d'un document, repli de l'outil MCP.

### Modifié
- **Le hook `UserPromptSubmit` fonctionne enfin**, et passe au lexical. Une
  recherche sémantique sous chaque prompt coûtait un embedding à chaque fois —
  un poste de dépense permanent — et exigeait un index déjà construit. BM25 ne
  coûte rien et répond dès le premier prompt d'un vault neuf. Il interroge donc
  les cinq dossiers au lieu de deux. Réserve connue : sur un corpus de quelques
  fichiers, l'IDF s'écrase et le classement ne discrimine rien — le hook se
  tait plutôt que d'injecter du bruit.
- **Recherche sémantique en un seul appel** : `directories` (liste) remplace
  `directory`, et la réponse est une liste de groupes `{directory, results}`.
  La question n'est vectorisée **qu'une fois** quel que soit le nombre de
  dossiers — c'est le seul coût API d'une recherche. Interroger les cinq index
  coûte donc exactement le même appel réseau qu'un seul, et restreindre le
  périmètre (`entites/` pour une question sur une personne) devient un geste
  utile plutôt qu'une économie.
- `/doc-bench` est présenté comme un **instrument facultatif** — dans la
  commande, dans le README et dans le message de fin de `/vault-init`, qui le
  sort de la liste des commandes du parcours. Rien ne l'exige : le vault
  fonctionne sans, et aucun réglage n'attend d'être calibré sur le corpus de
  l'utilisateur.
- `toolbox-env.sh` : le moteur est résolu **dans le cache des plugins**, déduit
  de `CLAUDE_PLUGIN_ROOT` plutôt que codé en dur — un hook reçoit la racine de
  CE plugin, pas celle du moteur. Ordre : chemin imposé par le projet, puis
  plugin voisin (version la plus haute), puis clone local. L'invocation passe
  par `uv` : **aucun venv à créer ni à maintenir**, le dossier du moteur étant
  de toute façon un cache réécrit à chaque mise à jour.

## [1.18.0] — 2026-07-29

**Raison de l'update** : trois corrections de fond. Le vectoriel avait pris toute la place dans la cascade de recherche, au point de reléguer le grep au rang de repli — or les deux couches ne trouvent pas la même chose, l'une rapproche par le sens et rate le terme exact, l'autre touche le terme exact et rate la reformulation. `/doc-ingest` plafonnait par ailleurs chaque source à 2-5 enseignements, bridage hérité d'un temps où une note longue inondait le classement avec plusieurs de ses extraits : le regroupement des résultats par fichier règle ce point à la recherche, il n'y a plus de raison de jeter de l'information à l'écriture. Enfin, une couche de notes introduite en 1.16.0 dépassait le périmètre d'un outil générique.

### Ajouté
- **`wiki/sources/` porte désormais le texte intégral standardisé** de chaque
  pièce, et **`wiki/enseignements/`** ce qu'on en retient — un titre `###` par
  enseignement, donc un extrait indexé par enseignement, ni dilué dans ses
  voisins ni coupé en deux. Avec `archives/`, cela fait **trois degrés de
  fidélité** pour une même pièce : ce qu'on retient, le texte fidèle, la pièce
  elle-même. Un doute se remonte toujours dans ce sens, et **plus rien de ce
  qui est ingéré n'est perdu** — ce qu'aucun enseignement n'a retenu reste
  cherchable dans le texte. Les deux notes partagent le slug et se pointent
  mutuellement ; `archives/` reste hors index.
  Contrepartie assumée : le texte intégral des pièces est vectorisé, donc plus
  de chunks à chaque ingestion et un volume nettement supérieur transmis au
  fournisseur d'embeddings.
- Le texte intégral **ne traverse aucun contexte** : le sub-agent lecteur
  l'écrit lui-même dans le sas (`inbox/<slug>.standardise.md`) et ne remonte
  que son chemin et le dossier d'ingestion. L'agent principal déplace le
  fichier sans le relire. Ingestion abandonnée → le sas est nettoyé.
- **`/doc-repair <note> "<passage>" "<nouvelle valeur>"`** — nouvelle commande.
  Là où `/doc-lint` ratisse le vault, celle-ci part d'une incohérence repérée
  et **remonte sa chaîne** : elle cherche toutes les notes portant la même
  affirmation, **vérifie la correction contre la pièce d'origine**, puis la
  qualifie — erreur de restitution (on remplace, sans `## Historique` : une
  erreur n'est pas une vérité passée) ou information périmée (valeur courante
  mise à jour, ancienne poussée en `## Historique`). Elle rend un plan
  ordonné : notes à modifier, wikilinks à refaire, entrée d'INDEX, dossiers à
  réindexer — et n'écrit rien elle-même. `archives/` n'est jamais modifié : on
  corrige ce que le vault a dit de la pièce, jamais la pièce. Une correction
  de couche immuable est journalisée, ce qui la distingue d'une édition
  silencieuse.
- `/doc-lint` : neuvième vérification — **appariement des couches d'origine**.
  Un texte sans enseignement, un enseignement sans son texte, un wikilink
  manquant entre les deux, ou une note d'enseignements sans aucun titre `###`
  (ses extraits seraient indexés en un seul bloc). Compteur
  `appariements rompus` dans la ligne d'état.
- `/doc-bench` : le banc attend désormais **la couche la plus travaillée qui
  réponde**, et son rapport ajoute une **répartition des touches par couche** —
  seule façon de voir si les textes intégraux étouffent les enseignements ou
  les complètent.

### Modifié
- `/doc-query` : **le grep est systématique, en plus du sémantique et jamais à
  sa place**. Le sub-agent **ouvre toutes ses touches, puis trie** et ne remonte
  que ce qui apporte un fait ou un savoir explicitement énoncé : son contexte
  est jetable — l'agent principal ne voit que le rapport —, donc lire large et
  rendre étroit est son métier, et aucune présélection ne se fait sur un nom de
  fichier — le nom de fichier est un indice faible, c'est le contenu qui
  tranche. Le motif cherche sur la **racine** des termes, sans tenir compte de
  la casse ni des accents — ce qui rattrape le pluriel, l'accent oublié et le
  suffixe différent — et **écarte les termes trop répandus**, qui ne
  discriminent rien : un patronyme suffit à ramener la moitié d'un vault. Trop
  de touches malgré ça → resserrer et le dire dans le rapport, jamais
  échantillonner. Deux indices pour le tri : une note contenant littéralement
  les mots de la question est souvent le meilleur résultat possible, et une
  note désignée par les deux couches est un signal fort.
- `/doc-query`, rapport final : le bloc `Sources` devient **`Notes retenues`**
  — toutes celles jugées pertinentes, pas seulement celles qui portent la
  réponse. Chacune avec son chemin relatif au vault, **d'où elle vient**
  (sémantique et son rang, grep, ou les deux) et une phrase sur ce qu'elle
  apporte. Leur contenu n'est jamais recopié : le contexte principal reçoit
  une carte, pas le territoire, et ouvre ce dont il a besoin quand il en a
  besoin.
- `/doc-ingest` : **le nombre d'enseignements devient proportionnel à la
  source**, sans plafond. Le critère est la qualité — une idée par
  enseignement, aucun qui n'apporte un fait durable, aucun remplissage — et
  non plus un compte. La limite de 125 caractères par citation verbatim ne
  bouge pas : elle porte sur la longueur d'une citation, pas sur leur nombre.
- `/doc-ingest`, gros volume : le sub-agent synthétiseur **assemble** les
  dossiers partiels au lieu de les comprimer. Il dédoublonne et organise, en
  gardant une section par partie de la source.
- `/doc-ingest`, validation : au-delà d'une dizaine d'enseignements, la
  validation se fait **par tranches** — une liste de quarante lignes validée
  d'un bloc n'est plus une validation.
- Retrait d'une couche de notes introduite en 1.16.0, qui répondait à un
  besoin particulier n'ayant pas sa place dans un outil générique.
- Formulation générique du routage des captures d'écran et du regroupement
  d'un lot en sources : ces règles tiennent par la propriété technique qui les
  motive, sans référence à un type de contenu particulier.

## [1.17.0] — 2026-07-29

**Raison de l'update** : ingérer `inbox/` en lot répartissait un lecteur par fichier. Correct quand chaque fichier est une source, faux quand plusieurs fichiers n'en forment qu'une — chacun produisait alors une note creuse.

### Modifié
- `/doc-ingest`, montage « lot de fichiers » : **regrouper le lot en sources
  avant de répartir les lecteurs**, et faire valider ce regroupement
  (« <n> fichiers → <m> sources »). Une source n'est pas forcément un
  fichier : sous-dossier commun, préfixe de nom, numérotation continue ou
  dates qui se suivent signalent des fichiers d'un même ensemble, qu'un seul
  lecteur ouvre dans l'ordre. Dans le doute, demander plutôt que découper —
  un mauvais découpage se paie en réingestion complète.

## [1.16.0] — 2026-07-28

**Raison de l'update** : deux angles morts découverts en mesurant. Un index unique sur tout `wiki/` faisait concourir des notes de natures et de tailles incomparables — deux runs de banc ont montré les notes courtes systématiquement écrasées par les gros extraits des notes longues. Et toute source non textuelle passait par l'OCR, y compris les captures d'écran, pour lesquelles il n'est pas fait.

### Ajouté
- **Un index sémantique par dossier de `wiki/`** (`concepts/.index/`,
  `entites/.index/`, `syntheses/.index/`, `sources/.index/`) au lieu d'un index
  unique. Chaque dossier devient un espace vectoriel séparé : les notes ne
  concourent qu'entre semblables, et une entité de dix lignes ne peut plus être
  écrasée par un extrait d'une source de trois cents. C'est une séparation
  structurelle, pas un réglage de score — elle attaque la cause du défaut
  mesuré au banc plutôt que ses symptômes.
  Nouveau `scripts/vault-index-targets.sh` : source unique des dossiers à
  indexer. `vault-index.sh` et `vault-search.sh` bouclent dessus sans argument,
  et acceptent toujours un dossier unique en échappatoire.
- **Règle des questions exhaustives** dans `/doc-query` et le template :
  « tous les… », « combien de fois… » ne peuvent PAS être résolues par un
  classement — un index rend les K meilleurs résultats, jamais l'ensemble des
  résultats qualifiants. L'exhaustivité vient de la lecture des notes
  retenues, et une couverture partielle se dit explicitement dans le rapport.
- `/doc-lint` : cohérence vectorielle par dossier (cible jamais indexée =
  notes invisibles à la recherche) ; détection des `.md` posés à la racine de
  `wiki/` et des sous-dossiers inattendus — tous échappent à l'indexation ;
  reliquats `wiki/.index/` (≤ 1.15.x) à supprimer ; divergence de
  provider/modèle/dimension entre deux index ; compteur `index manquants`.
- `/doc-ingest` : **routage de la source selon sa nature**, avant tout
  traitement. PDF, scan, document multi-pages → OCR, c'est son terrain.
  Capture d'écran (`.png`, `.jpg`, `.webp`, `.heic`…) → **jamais d'OCR** : un
  OCR documentaire est réglé pour une mise en page de document et rend, sur
  une capture d'interface, un flux linéaire où la disposition a disparu. Le
  sub-agent lecteur ouvre l'image directement et en produit la version
  standardisée, avec pour
  consigne de **signaler tout passage illisible plutôt que de le deviner** —
  ce qui devient un `> [!warning]` sur la note source. Texte/markdown → tel
  quel ; URL → montage nominal.
- `/doc-ingest` : des captures formant **un même ensemble** comptent pour une
  seule source, qu'un seul lecteur ouvre dans l'ordre (une dizaine au plus,
  au-delà montage gros volume).
- `/doc-ingest` : le routage couvre désormais **toutes les natures de
  source**, avec une conduite explicite quand on ne sait pas. Texte lisible
  tel quel (`.md`, `.txt`, `.csv`, `.json`, `.html`, `.eml`, code) transmis
  sans conversion ; **bureautique binaire** (`.xlsx`, `.docx`, `.pptx`,
  `.odt`…) convertie d'abord avec ce qui est présent sur la machine, sinon on
  demande une version texte ou PDF — jamais de binaire présenté à un lecteur,
  jamais de contenu deviné ; **archive** décompressée puis traitée comme un
  lot ; **audio et vidéo** déclarés hors périmètre ; **format non identifié**
  passé à `file`, puis question à l'utilisateur. Une ingestion ratée pollue
  une couche immuable : dans le doute, on demande.

### Modifié
- `/doc-ingest`, archivage : pour une capture, ce sont **les images
  elles-mêmes** qui sont archivées et que pointe `origine:`. Aucun markdown
  intermédiaire n'est produit — donc plus aucune référence d'image pendante
  (`![img-N.jpeg]`) injectée dans le graphe Obsidian par cette voie.
- `/doc-bench` : le score devient `sémantique@3`, mesuré **par dossier** — les
  espaces vectoriels étant disjoints, le rang d'une attendue est son rang dans
  l'index de son propre dossier, jamais dans un classement global reconstitué.
  Les scores d'avant 1.16.0 ne sont plus comparables.
- Le hook `UserPromptSubmit` n'interroge plus que `concepts/` et `entites/` :
  il se déclenche à chaque prompt, et chaque index interrogé coûte un
  embedding — les pistes qu'on veut là sont du savoir consolidé, pas des
  extraits bruts. La recherche large reste le métier de `/doc-query`.

## [1.15.0] — 2026-07-28

**Raison de l'update** : un seul callout `> [!warning]` servait à deux choses incompatibles — la réserve documentaire sur une pièce (OCR partiel, capture non datée), qui est définitive, et la contradiction non tranchée, qui est une tâche en attente. `/doc-lint` les additionnait : sur un vault réel, 19 « contradictions en souffrance » dont la plupart n'appelaient aucune action, donc un compteur qu'on apprend à ignorer.

### Ajouté
- Convention de **deux callouts distingués par leur durée de vie**, dans
  `INSTRUCTIONS-CLAUDE.md` : `> [!warning]` = mise en garde documentaire,
  **permanente**, sur la pièce elle-même ; `> [!question]` = contradiction non
  tranchée, **temporaire**, retirée à l'arbitrage. Corollaire structurel : un
  `[!question]` ne se pose jamais dans `wiki/sources/`, couche immuable où il
  ne pourrait plus être retiré — sa place est sur la page concept/entité qui
  porte l'affirmation.
- `/doc-lint` : la vérification 1 compte les deux séparément et ne réclame que
  les `[!question]` ; détecte les `[!question]` mal placés dans
  `wiki/sources/` ; requalifie l'héritage ≤ 1.14.0 en lisant le corps de
  chaque `[!warning]` hors sources pour y reconnaître les vraies
  contradictions.
- `/doc-lint` : `contradictions: n` entre en tête de la ligne de compteurs —
  la dette réelle, mises en garde documentaires exclues.
- `/doc-lint` : auto-réparation de la convention — `/vault-init` n'écrasant
  jamais les fichiers racine, un vault antérieur garde l'ancienne règle ; le
  lint le détecte et propose l'unique édition qui remet
  `INSTRUCTIONS-CLAUDE.md` à jour. En cas de désaccord, la commande fait foi.

### Modifié
- `/doc-ingest` : pose désormais `> [!warning]` sur la note source (réserve
  sur la pièce) et `> [!question]` sur la page concept/entité (contradiction),
  jamais l'inverse ; le compte rendu sépare les deux natures.
- Retirer un `[!question]` égaré d'une note source devient la **seule**
  modification autorisée sur `wiki/sources/`, après validation explicite :
  l'immuabilité protège ce que la pièce dit, or une contradiction n'est pas
  dans la pièce mais dans sa relation au vault.

## [1.14.0] — 2026-07-28

**Raison de l'update** : toutes les vérifications de `/doc-lint` regardaient `wiki/` — un `.md` parasite à la racine du vault n'était examiné par rien. Et « `archives/` est hors index » n'était vrai que de l'index sémantique : Obsidian, lui, indexe tout le vault, si bien que les markdown OCR archivés injectent des nœuds fantômes dans le graphe humain, dont un simple clic crée une note vide à la racine.

### Ajouté
- `/doc-lint` : 9ᵉ vérification — **parasites hors `wiki/`** : `.md`
  inattendu à la racine du vault (tout sauf `INDEX.md`,
  `INSTRUCTIONS-CLAUDE.md`, `BENCH.md` et un `LOG.md` hérité), notes vides
  (0 octet ou frontmatter seul) n'importe où, et cibles introuvables
  référencées par les markdown OCR d'`archives/` — celles qui apparaissent en
  nœuds fantômes dans le graphe Obsidian. Compteur `parasites` ajouté à la
  ligne de tête. Correction proposée : suppression du parasite, et surtout le
  remède durable, qui n'est pas dans le vault mais dans Obsidian — exclure
  `archives/` (Paramètres → Fichiers et liens → Filtres d'exclusion). Les
  fichiers d'`archives/` ne sont jamais modifiés : la couche reste immuable.
- Règle correspondante dans l'`INSTRUCTIONS-CLAUDE.md` du template et dans le
  pas-à-pas Obsidian du README.
- **`/vault-init` pose le réglage lui-même** : `archives/` ajouté aux
  exclusions d'Obsidian (`userIgnoreFilters` de `.obsidian/app.json`), pour
  qu'un vault neuf naisse sans nœuds fantômes. Idempotent et non destructif —
  vault neuf : fichier écrit en bash pur (aucune dépendance) ; config
  existante : fusion qui préserve les autres réglages et ne duplique pas une
  exclusion déjà là ; config illisible ou `python3` absent : rien n'est
  touché, la manipulation manuelle est affichée. Obsidian préserve un
  `.obsidian/` existant à sa première ouverture, le réglage vaut donc aussi
  pour un vault jamais ouvert dans Obsidian.
- `PREREQUIS.md` : section 7 — `python3` (livré par défaut sur WSL/Linux/macOS)
  déclaré comme dépendance douce, avec ce qui s'en sert et ce qui se passe
  s'il manque (dégradation silencieuse, jamais d'erreur).
- **Avertissement de confidentialité** (`PREREQUIS.md` et `README.md`) : ce qui
  sort du vault (le texte de `wiki/` à l'indexation, la question à chaque
  `/doc-query`, les pièces à l'OCR) et le fait que le palier gratuit de Mistral
  autorise **par défaut** l'usage de ces appels pour entraîner ses modèles.
  Procédure d'opt-out (console → Administration → Confidentialité), à faire
  avant la première indexation puisqu'elle ne vaut que pour les interactions
  futures ; « modèles Labs » à laisser désactivé (ils autorisent
  l'entraînement quel que soit l'opt-out). Manquait entièrement — un vault
  peut contenir des données personnelles ou des pièces confidentielles.
  Couvre les **deux canaux** — le vault vers le fournisseur d'embeddings, et la
  session Claude Code vers Anthropic (régime selon la facturation : abonnement
  = entraînement sauf désactivation, clé API = jamais) — avec une capture de la
  page de réglage pour chacun, et le rappel que coller un rapport à la main
  court-circuite l'isolement en sub-agent de `/doc-query` et `/doc-lint`.
  Le README pose la règle générale : **pour chaque clé API utilisée avec le
  plugin**, décider explicitement du sort de ses données avant de la coller
  (entraînement, rétention, opt-out) — plusieurs paliers gratuits autorisent
  l'entraînement par défaut et le réglage ne vaut que pour les appels futurs.

## [1.13.0] — 2026-07-28

**Raison de l'update** : le banc ne mesurait qu'un proxy — la couche de récupération isolée — alors que ce qui compte est ce que `/doc-query` cite vraiment. Le mode `reel` mesure la chose elle-même, et le mode mécanique reprend son rôle propre : départager deux versions du moteur, là où un run réel est trop bruité pour ça.

### Ajouté
- **`/doc-bench reel`** : rejoue les questions de `BENCH.md` en faisant
  exécuter la cascade complète de `/doc-query` par un sub-agent lecteur par
  question (vagues de 4), qui ne remonte que les notes qu'il citerait — le
  contexte principal ne voit aucun contenu de note. Le lecteur lit la
  procédure de recherche **dans `doc-query.md` lui-même** : la mesure suit la
  commande sans copie à maintenir. Score
  `réel x/n · citations complètes x/n · à vide x/n`, confrontation qualitative
  au dernier run mécanique (quelle question la cascade rattrape, laquelle elle
  gâche), entrée `bench-reel` au journal. Coût annoncé et accord demandé avant
  de lancer ; sous-ensemble possible (`/doc-bench reel Q3 Q7 Q17`) ; une seule
  indexation pour tout le run.
- Règle posée en tête de la commande : **un score réel ne se compare qu'à un
  autre score réel**. Le mode mécanique reste gratuit et reproductible (il
  détecte un gain de +1 entre deux versions du moteur) ; le mode réel est plus
  proche du vécu mais non déterministe.

### Modifié
- `/doc-bench` n'est plus une commande en fork : elle **délègue** désormais
  chaque mode à des sub-agents (un pour la création, un pour la mesure
  mécanique, un lecteur par question en mode réel) — l'isolation du contexte
  principal est identique, mais la commande peut enfin porter le mode réel,
  qui a besoin de lancer des sub-agents. Les trois modes vivent ainsi dans un
  seul fichier, avec la règle de non-comparabilité des scores au même endroit.

## [1.12.0] — 2026-07-28

**Raison de l'update** : le premier banc réel a montré que le score ne mesurait pas ce que `/doc-query` fait vraiment — la cascade suit les wikilinks des notes remontées, et plusieurs « échecs » du banc sont en fait rattrapés par le graphe. La colonne `+1 saut` chiffre ce rattrapage, et décide ainsi sur mesure si une expansion par backlinks vaut la peine d'être construite.

### Ajouté
- `/doc-bench`, mode mesure : troisième colonne **`+1 saut`** — une attendue
  absente du top 5 sémantique mais citée en wikilink par une note de ce top 5
  compte comme atteinte, puisque la cascade de `/doc-query` la suit. Mécanique
  et sans coût API supplémentaire. L'INDEX est volontairement exclu du calcul
  (il liste toutes les notes : un saut par l'INDEX trouverait tout et ne
  mesurerait rien). Ligne de score et entrée de journal :
  `sémantique@5 x/n (rang moyen r) · +1 saut x/n · grep x/n · couverture x/n`.

## [1.11.2] — 2026-07-28

**Raison de l'update** : sur un vault fourni, le hook SessionStart ne livrait plus qu'un fragment de la carte — une sortie de hook n'est injectée telle quelle qu'en deçà d'environ 2 Ko, bien avant le garde-fou de 16 Ko du script, et la troncature brute s'arrêtait au milieu des concepts (entités, sources et synthèses invisibles).

### Corrigé
- **Hook SessionStart** : au-delà du budget d'injection, la carte est
  désormais **condensée** au lieu d'être coupée — les slugs seuls, sans les
  descriptions, répartis équitablement entre sections (la part non consommée
  par une section profite aux suivantes), `(+n autres)` là où ça déborde, et
  le chemin de l'`INDEX.md` complet en pied. La carte reste entière quel que
  soit le volume du vault ; les descriptions se lisent dans l'INDEX. Replis
  conservés : `python3` absent ou INDEX sans entrées reconnaissables →
  troncature brute annoncée comme telle.

## [1.11.1] — 2026-07-27

**Raison de l'update** : supprime l'erreur « Duplicate hooks file detected » au chargement du plugin — `hooks/hooks.json` est chargé automatiquement par Claude Code (emplacement standard), la déclaration explicite `hooks` du manifeste faisait doublon ; elle est retirée. Les hooks fonctionnaient déjà, seule l'erreur affichée disparaît.

### Corrigé
- `plugin.json` : champ `hooks` retiré — l'emplacement standard
  `hooks/hooks.json` suffit, le champ du manifeste ne doit référencer que des
  fichiers de hooks *additionnels*.

## [1.11.0] — 2026-07-27

**Raison de l'update** : la recherche devient mesurable — `/doc-bench` fige un banc de questions de référence propre au vault et produit un score mécanique comparable d'un run à l'autre : le prérequis pour juger les évolutions du moteur (fusion scorée, décroissance), qui n'entreront que si le banc les valide.

### Ajouté
- **`/doc-bench`** (fork isolé, comme `/doc-query` et `/doc-lint`) :
  - **mode création** (premier lancement, ou argument `creer`) : propose ~20
    questions tirées du contenu du vault — factuelles, transversales,
    centrées concepts/entités, et plusieurs formulées en synonymes (jamais
    les mots exacts des notes : ce sont elles qui départagent la sémantique
    de grep) — chacune avec ses 1-3 notes attendues ; validées avec
    l'utilisateur puis figées dans `BENCH.md` (racine du vault, hors index
    sémantique par construction) ;
  - **mode mesure** (lancements suivants) : réindexation incrémentale, puis
    pour chaque question — mécaniquement, sans jugement — top 5 sémantique et
    grep sur les mots pleins ; score
    `sémantique@5 x/n (rang moyen) · grep x/n · couverture x/n`, détail par
    question avec, pour les échecs, ce que la recherche a renvoyé à la
    place ; entrée `bench` au journal. Un run ne modifie jamais `BENCH.md` ;
    une attendue disparue est signalée « banc à mettre à jour » et exclue du
    score. Coût : une vectorisation API par question.
- Action `bench` ajoutée au journal et `BENCH.md` à la structure du template
  (`INSTRUCTIONS-CLAUDE.md`).

## [1.10.0] — 2026-07-27

**Raison de l'update** : le vault ne se déclenche plus seulement à la commande — trois hooks l'amènent dans la session : Claude connaît la carte du vault dès l'ouverture, reçoit des pistes sémantiques sous chaque prompt, et le savoir d'une conversation survit au compactage via le sas `inbox/`.

### Ajouté
- **Hooks plugin** (`hooks/hooks.json` + trois scripts), tous soumis à la même
  garde : projet sans `.claude/vault-path.local` → sortie 0 immédiate et
  silencieuse, le plugin reste invisible tant que `/vault-init` n'a pas tourné.
  - **SessionStart** : injecte `INDEX.md` dans le contexte à l'ouverture de
    session (tronqué à 16 Ko) ; vault configuré mais inaccessible → une ligne
    d'avertissement (Drive pas monté ?).
  - **UserPromptSubmit** : recherche sémantique directe sur le prompt
    (`vault-search.sh`, pas de fork) — top 3 injecté comme pistes (des
    extraits, pas une réponse : `/doc-query` reste la vraie recherche).
    Jamais d'indexation ici ; filtres : commandes slash/`!`/`#` et prompts
    < 12 caractères ignorés ; requiert le clone local d'agentic-toolbox (un
    hook ne peut pas appeler les outils MCP). Chaque prompt éligible est
    vectorisé via l'API Mistral, comme toute question `/doc-query`.
  - **PreCompact** : dépose la partie textuelle de la conversation (tours
    utilisateur/assistant — jamais les sorties d'outils ni les rappels
    système) dans `inbox/session-YYYY-MM-DD-<id>.md` en `type: session` ;
    même session recompactée → même fichier, réécrit plus complet.
  - Sécurité des hooks : payload lu sur stdin uniquement (jamais via argv ni
    l'environnement), champs filtrés avant usage en nom de fichier, écriture
    confinée à `inbox/` (vérifiée), échec quelconque = silence sans effet.
- **Règle d'ingestion des dépôts `type: session`**
  (`INSTRUCTIONS-CLAUDE.md` du template + `/doc-ingest`) : un transcript est
  verbeux et peu dense — n'en extraire que les décisions prises et les faits
  durables, jamais le déroulé ; brut archivé comme toute pièce du sas ; aucun
  enseignement durable → archivage direct, sans note source.
- Migration des vaults existants : reporter la règle `type: session` dans leur
  `INSTRUCTIONS-CLAUDE.md` (le template n'est copié qu'à l'init) ; les hooks
  se chargent au prochain démarrage de session après la mise à jour.

## [1.9.0] — 2026-07-27

**Raison de l'update** : les deux points de contention structurels de la synchro Drive disparaissent — le journal devient un fichier par jour (`LOG/`), et `INDEX.md` devient un dérivé entièrement régénérable depuis le frontmatter : un conflit sur un dérivé ne coûte rien, on régénère.

### Modifié
- **Journal `LOG/`** : append-only, un fichier par jour
  (`LOG/YYYY-MM-DD.md`, créé au besoin), format d'entrée inchangé. Un
  `LOG.md` racine hérité est **gelé** : il se consulte (dates, diagnostics),
  on n'y écrit plus. `vault-init.sh` crée `LOG/` et n'écrit l'entrée `init`
  que dans un vault neuf (jamais dans un vault déjà vivant).
- **`INDEX.md` = dérivé régénérable** : chaque entrée
  (`- [[<slug>]] — <description>`) vient du frontmatter de sa note ;
  `/doc-lint` régénère le fichier en entier au lieu de le rapiécer — trous
  d'INDEX comme conflit Drive sur `INDEX.md` se résolvent par régénération.
- **Modèle de note** : `description` (la note en quelques mots) devient
  obligatoire — c'est elle qui alimente l'INDEX. `/doc-ingest` la renseigne
  (celle du dossier d'ingestion), `/doc-query` aussi pour les synthèses,
  `/doc-lint` la vérifie.
- Migration des vaults existants, sans étape bloquante : le prochain
  `/doc-lint` signale les `description` manquantes et propose de rapatrier
  celle de l'entrée INDEX existante ; reporter les nouvelles conventions dans
  l'`INSTRUCTIONS-CLAUDE.md` du vault (le template n'est copié qu'à l'init).

## [1.8.0] — 2026-07-27

**Raison de l'update** : les doublons de pages vivantes étaient le seul défaut du vault qui empire tout seul (`Docker.md` + `conteneurisation-docker.md` : graphe fragmenté, recherches partielles, échec silencieux) — `/doc-lint` les détecte désormais et guide leur fusion ; et les contradictions tranchées deviennent de l'update-in-place avec historique.

### Ajouté
- `/doc-lint` : 9e vérification — **doublons suspectés de pages vivantes**
  (`concepts/` + `entites/` confondus) : collisions de noms normalisés
  (casse, accents, tirets, pluriel) entre fichiers et alias, plus similarité
  sémantique quand le moteur est disponible (le titre d'une page qui remonte
  une autre page vivante en tête de recherche). Compteur ajouté à la ligne de
  tête. Détection seulement — la **fusion assistée** est validée paire par
  paire : contenu rapatrié dans la survivante, nom absorbé conservé en
  `aliases:` (tout wikilink oublié continue de résoudre), wikilinks entrants
  réécrits, liens pendants re-vérifiés, réindexation incrémentale enchaînée
  (les vecteurs de la page absorbée sont purgés, la survivante enrichie
  revectorisée).
- Frontmatter : propriété optionnelle **`aliases`** (noms alternatifs d'une
  page) — reconnue par la vérification des wikilinks pendants.
- `/doc-ingest` : avant de créer une page vivante, chercher une existante qui
  couvre déjà le sujet (nom normalisé, alias, libellé proche) — en cas de
  doute, enrichir plutôt que dupliquer.

### Modifié
- **Contradictions — convention à deux issues** : tranchée avec l'utilisateur
  → la note porte la valeur courante, l'ancienne descend dans une section
  `## Historique` append-only en fin de note (une seule vérité lisible en
  tête, l'historique conservé) ; non tranchable → callout `> [!warning]`,
  comme avant. Règle de recherche associée : un passage trouvé sous
  `## Historique` est périmé, jamais cité comme état courant.
- Vaults existants : reporter les nouvelles conventions (`aliases`,
  `## Historique`, anti-doublon) dans l'`INSTRUCTIONS-CLAUDE.md` du vault —
  le template n'est copié qu'à l'initialisation, `/vault-init` ne remplace
  jamais un fichier existant.

## [1.7.0] — 2026-07-27

**Raison de l'update** : `/doc-lint` détecte les wikilinks pendants et ouvre son rapport par une ligne de compteurs — l'instrumentation préalable à la future fusion d'entités (qui réécrit des wikilinks : il faut un avant/après). Inclut aussi la synchronisation documentaire avec agentic-toolbox 3.0.0.

### Ajouté
- `/doc-lint` : 8e vérification — **wikilinks pendants** (une cible `[[...]]`,
  extraite avant `|` et `#`, qui ne correspond à aucun fichier du vault ni à
  aucun alias `aliases:` de frontmatter). Miroir de la vérification
  « orphelines » : l'orpheline n'est pas pointée, le lien pendant pointe dans
  le vide. Correction proposée : corriger la cible, créer la page, ou délier —
  jamais de page coquille.
- `/doc-lint` : le rapport s'ouvre sur une **ligne de compteurs** (liens
  pendants, orphelines, trous d'INDEX, conflits Drive, inbox, frontmatters
  incomplets, notes par dossier) — l'état de santé du vault d'un coup d'œil,
  comparable d'un lint à l'autre.

### Modifié
- Synchronisation avec agentic-toolbox 3.0.0 (docs uniquement, aucun
  changement de comportement : les commandes passaient déjà le dossier du
  vault explicitement partout). Les mentions du défaut `VAULT_PATH` disparaissent
  (README, PREREQUIS, `/doc-ingest`, `/doc-query`, `/doc-lint`) ; la règle
  reste « jamais de dossier implicite ». PREREQUIS : l'activation du plugin
  toolbox se réduit à la clé `MISTRAL_API_KEY` (plus de champ « dossier par
  défaut » à laisser vide).

## [1.6.0] — 2026-07-26

**Raison de l'update** : sur un gros volume, l'ingestion saturait le contexte principal (source brute lue en session). `/doc-ingest` lit désormais la source dans des sub-agents lecteurs, dimensionnés au volume mesuré — le contexte principal ne voit que les enseignements.

### Modifié
- `/doc-ingest` : la lecture de la source (fichier, URL, OCR de PDF) se fait
  dans un **sub-agent lecteur** qui ne retourne qu'un « dossier d'ingestion »
  (enseignements, citations ≤ 125 car., concepts/entités candidats,
  description INDEX) — jamais la source brute. Un texte bref passé en
  argument reste ingéré sans sub-agent (déjà en contexte).
- Montage dimensionné au **volume mesuré avant lecture** (`wc -c`, markdown
  OCR pour un PDF) : source ≤ ~150 Ko → un lecteur ; > ~150 Ko → découpe par
  structure en tranches ≤ ~150 Ko, un lecteur par tranche (parallèle, ≤ 4) et
  un **synthétiseur** qui fusionne les dossiers partiels et porte la
  validation ; lot de fichiers → un lecteur par fichier, une note et un
  accord par source. Un lecteur qui déborde retourne un plan de découpe au
  lieu d'un dossier (bascule automatique).
- Validation conversationnelle : les retouches de fond sont relayées au même
  sub-agent via SendMessage (contexte, source comprise, conservé sur tous les
  allers-retours) ; sub-agent perdu → relance avec la source et le cumul des
  retours. L'écriture (wiki, INDEX, LOG, archivage, indexation) reste en
  contexte principal, à partir du seul dossier validé.

### Corrigé
- `/doc-ingest` (validation conversationnelle) : les 2-5 enseignements clés
  doivent être écrits en clair dans le corps de la réponse avant toute demande
  d'accord ; un outil de question (AskUserQuestion ou équivalent) ne peut que
  recueillir l'accord, jamais porter le contenu.

## [1.5.4] — 2026-07-26

**Raison de l'update** : fin du renommage `.md` → `.md.txt` à l'archivage — les archives gardent leurs extensions d'origine. L'exclusion de l'index se fait proprement : seul `wiki/` est indexé, et l'index vit dans `wiki/.index/`.

### Modifié
- Périmètre d'indexation : `$VAULT/wiki` au lieu de `$VAULT` — `archives/`,
  `inbox/` et les fichiers racine (LOG, INDEX, INSTRUCTIONS) sortent de
  l'index par construction ; le filtre « bruit d'indexation » de `/doc-query`
  devient inutile (gardé en tolérance pour un index ≤ 1.5.3 pas encore
  reconstruit). L'index vit dans `wiki/.index/` (voyage toujours avec le
  vault) ; `vault-init.sh`, les wrappers CLI et les trois commandes `/doc-*`
  sont alignés.
- `/doc-ingest` : plus aucun renommage à l'archivage — un fichier archivé
  garde son nom et son extension.
- `/doc-lint` : un `.index/` à la racine du vault est signalé comme reliquat
  ≤ 1.5.3 (suppression proposée — dérivé jetable).

## [1.5.3] — 2026-07-26

**Raison de l'update** : `origine`/`original` pouvaient contenir un chemin absolu de la machine (`/home/...`) — mort avec la machine, vault plus auto-porteur. Toute pièce locale ingérée est désormais copiée dans `archives/` et référencée relativement au vault.

### Corrigé
- `/doc-ingest` (étape 5) : l'archivage vaut pour TOUT fichier local — venu
  d'`inbox/` → déplacé, venu d'ailleurs sur la machine → **copié** (l'original
  de l'utilisateur n'est jamais touché) ; PDF passé par OCR → le markdown OCR
  ET le PDF d'origine sont archivés. `origine:`/`original:` reçoivent ces
  chemins archivés relatifs au vault — jamais un chemin absolu de la machine.
- `vault-template/INSTRUCTIONS-CLAUDE.md` : modèle de note — `original`
  seulement si la pièce diffère de la copie pointée par `origine` (copie dans
  `archives/` ou emplacement durable : URL, dossier partagé) ; interdiction
  explicite des chemins absolus machine dans `origine`/`original`.

## [1.5.2] — 2026-07-25

**Raison de l'update** : le README ne disait pas par où commencer une fois le plugin installé — la section « Usage » ouvre maintenant sur `/vault-init` et le redémarrage de session obligatoire.

### Ajouté
- `README.md` : rappel en tête de « Usage » — première commande
  `/vault-init "/chemin/du/vault"`, puis relance de la session Claude Code
  (chargement de la permission `additionalDirectories`) avant les `/doc-*`.

## [1.5.1] — 2026-07-25

**Raison de l'update** : les synthèses apparaissaient déconnectées dans le graphe Obsidian — leurs références étaient des chemins bruts, qui ne créent pas de liens.

### Corrigé
- `/doc-query` : la section `## Références` des synthèses utilise des
  wikilinks `[[<slug>]]`, plus des chemins bruts.
- `vault-template/INSTRUCTIONS-CLAUDE.md` : règle explicite — toute référence
  inter-notes en wikilink, jamais en chemin brut (exceptions : `origine`/
  `original`, hors graphe voulu).

### Ajouté
- `README.md` : astuce vue graphique — colorer les nœuds par type via un
  groupe par dossier (`path:wiki/concepts`, etc.).

## [1.5.0] — 2026-07-25

**Raison de l'update** : modèle de note à frontmatter obligatoire — `type`, `date`, `auteur`, `origine` (sources), `question` (synthèses) — appliqué par `/doc-ingest`, vérifié par `/doc-lint`.

### Ajouté
- `vault-template/INSTRUCTIONS-CLAUDE.md` : section « Modèle de note » —
  propriétés obligatoires communes (`type`, `date` de création, `auteur`) et
  par type (`origine` + `original` optionnel pour les sources, `question` +
  `perimetre` optionnel pour les synthèses) ; propriétés libres autorisées en
  plus (ex. `image`, `capture_precedente`/`capture_suivante`), jamais en moins.
- `/doc-lint` : 7e vérification — notes de `wiki/` non conformes au modèle,
  avec proposition de valeurs déduites du contenu ou du LOG (jamais inventées
  sans le signaler).

### Modifié
- `/doc-ingest` et `/doc-query` (synthèses) : frontmatter aligné sur le modèle,
  `auteur` repéré dans les notes existantes ou demandé une fois.
- **Vaults existants** : le template ne s'applique qu'aux nouveaux vaults —
  reporter la section « Modèle de note » dans l'`INSTRUCTIONS-CLAUDE.md` de
  votre vault, puis `/doc-lint` mettra les notes en conformité.

## [1.4.3] — 2026-07-25

**Raison de l'update** : le rôle d'`archives/` documenté dans le README — principe « vault auto-porteur ».

### Ajouté
- `README.md`, section Principes : `inbox/` = sas, fichier ingéré déplacé vers
  `archives/` (immuable, hors index sémantique via renommage `.md.txt`, jamais
  supprimé), avertissement données sensibles avant partage.

## [1.4.2] — 2026-07-25

**Raison de l'update** : README aligné sur l'en-tête du changelog — installer une mise à jour = update **puis** `/reload-plugins`, cache invalidé seulement si la version change.

### Corrigé
- `README.md` : « manuelle en une seule étape » → la séquence complète
  (`/plugin marketplace update zairth_store` puis `/reload-plugins`), avec la
  condition d'invalidation du cache.

## [1.4.1] — 2026-07-25

**Raison de l'update** : description du plugin réécrite — l'optimisation agentique (`context: fork`) mise en avant, alignée avec l'About du repo GitHub.

### Modifié
- `plugin.json` : la description mentionne l'exécution de `/doc-query` et
  `/doc-lint` en sub-agent isolé (zéro pollution du contexte principal).

## [1.4.0] — 2026-07-25

**Raison de l'update** : `/doc-query` et `/doc-lint` s'exécutent désormais entièrement dans un sub-agent (`context: fork`) — zéro pollution du contexte principal, préambule et notes compris.

### Modifié
- `/doc-query`, `/doc-lint` : frontmatter `context: fork` + `agent: Explore` +
  `background: false` — toute la commande (vault-check, lecture
  d'`INSTRUCTIONS-CLAUDE.md`, indexation, recherche, vérifications) tourne
  dans un sub-agent isolé ; seul le rapport final remonte. L'instruction
  « lancer un sub-agent » dans le corps des commandes devient inutile et
  disparaît.
- Les étapes interactives (proposer la sauvegarde en synthèse, valider les
  corrections de lint) restent en contexte principal : le rapport du fork se
  termine par un bloc « Pour l'agent principal » avec le chemin du vault
  résolu et les recettes exactes à appliquer après accord de l'utilisateur —
  un fork ne peut pas dialoguer.
- `/doc-ingest` inchangé : sa validation conversationnelle exige le contexte
  principal, un fork ne peut pas dialoguer avec l'utilisateur.
- `README.md` : principes et usage mis à jour (fork isolé).

## [1.3.2] — 2026-07-25

**Raison de l'update** : en-tête du changelog clarifié — il aide à décider d'*installer* une mise à jour, il n'invite pas à modifier le repo.

### Corrigé
- « Mise à jour côté consommateur » → « Installer une mise à jour » (même
  clarification dans le changelog d'agentic-toolbox).

## [1.3.1] — 2026-07-25

**Raison de l'update** : ce CHANGELOG — savoir pourquoi mettre à jour sans lire l'historique git.

### Ajouté
- `CHANGELOG.md` : une entrée par version, avec la raison de l'update.

## [1.3.0] — 2026-07-25

**Raison de l'update** : la stack fonctionne désormais **sans aucun clone** — les `/doc-*` utilisent les outils MCP du plugin agentic-toolbox en priorité.

### Modifié
- `/doc-query`, `/doc-ingest`, `/doc-lint` : cascade moteur — outils MCP
  (`mcp__plugin_agentic-toolbox_toolbox__semantic_index_build`,
  `…semantic_search`, `…semantic_info`, `…ocr_convert`) → wrappers CLI si
  clone local présent → repli grep explicite. Le dossier du vault est
  toujours passé **explicitement** aux outils MCP (celui du projet, via
  `vault-check.sh`) — jamais le `VAULT_PATH` global du plugin toolbox : un
  vault par projet, garanti.
- `PREREQUIS.md` section 5 : voie nominale = plugin agentic-toolbox + `uv`
  (clés saisies à l'installation), clone + venv relégué en alternative.
- `README.md` : « sans clone, sans service qui tourne » ; section recherche
  sémantique réécrite en deux portes d'entrée.

## [1.2.1] — 2026-07-25

**Raison de l'update** : docs d'installation alignées sur le marketplace dédié ; aucune config personnelle versionnée.

### Modifié
- Installation documentée via [Zairth/marketplace](https://github.com/Zairth/marketplace)
  (`/plugin marketplace add` en URL HTTPS — clonable anonymement, sans clé SSH).
- `.claude/settings.json` sorti du versioning (config par machine) ;
  `.claude/` et `CLAUDE.md` locaux gitignorés.

## [1.2.0] — 2026-07-25

**Raison de l'update** : le repo redevient un simple plugin — skill et catalogue vivent chez eux.

### Modifié
- Skill agentic-toolbox déplacé dans le repo
  [agentic-toolbox](https://github.com/Zairth/agentic-toolbox) (il vit avec le
  code qu'il documente) ; distribué via une entrée marketplace externe.
- Catalogue marketplace déménagé dans son propre dépôt Zairth/marketplace —
  plus de `marketplace.json` ici.

## [1.1.0] — 2026-07-25

**Raison de l'update** : le vault devient auto-porteur (`archives/`) et les wrappers acceptent les chemins relatifs.

### Ajouté
- `archives/` : `/doc-ingest` **déplace** le brut d'`inbox/` au lieu de le
  supprimer (`.md` renommé `.md.txt`, hors index sémantique) ; `vault-init.sh`
  crée le dossier.
- `PREREQUIS.md` (de la machine nue au vault), section Objectif du README,
  licence MIT.

### Corrigé
- Chemins relatifs : `vault-check.sh` imprime un chemin absolu, les wrappers
  résolvent leur cible avant le `cd` vers la toolbox.
- Piège WSL documenté : le vault vit côté Windows (`/mnt/...`), jamais dans le
  disque WSL (Obsidian plante en `EISDIR` sur `\\wsl.localhost\...`).

## [1.0.0] — 2026-07-25

**Raison de l'update** : première version distribuée en plugin Claude Code.

### Ajouté
- Conversion en plugin : manifeste `.claude-plugin/plugin.json`, commandes
  `/vault-init`, `/doc-ingest`, `/doc-query`, `/doc-lint`, scripts
  (`vault-check`, `vault-init`, `toolbox-env`, wrappers sémantiques),
  template de vault. Code dans le plugin, config dans chaque projet
  (`.claude/*.local` gitignorés) : un plugin, un vault par projet.
