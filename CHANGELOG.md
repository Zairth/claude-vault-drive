# Changelog — claude-vault-drive

Ce que contient chaque mise à jour du plugin : la raison en une ligne, puis le
détail des changements — de quoi savoir si elle vaut le coup avant de
l'installer. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/), versions en
[semver](https://semver.org/lang/fr/) (patch = fix/docs, minor = feature).

Installer une mise à jour : `/plugin marketplace update zairth_store` puis
`/reload-plugins` (le cache n'est invalidé que si la version change).

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
