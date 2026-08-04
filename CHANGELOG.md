# Changelog — claude-vault-drive

Ce que contient chaque mise à jour du plugin : la raison en une ligne, puis le
détail des changements — de quoi savoir si elle vaut le coup avant de
l'installer. Format inspiré de
[Keep a Changelog](https://keepachangelog.com/fr/), versions en
[semver](https://semver.org/lang/fr/) (patch = fix/docs, minor = feature).

Installer une mise à jour : `/plugin marketplace update zairth_store` puis
`/reload-plugins` (le cache n'est invalidé que si la version change).

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
