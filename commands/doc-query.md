---
description: Interroger le vault Obsidian — exécution en fork (contexte principal préservé), réponse citée, synthèse optionnelle
argument-hint: <question> [--all-references]
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

## `--all-references` — rendre les entrées, pas les notes

Si `$ARGUMENTS` contient `--all-references` : le retirer de la question, et
répondre par **la liste des entrées elles-mêmes** — datées, attribuées,
citables une par une — au lieu d'une réponse rédigée appuyée sur des notes.
C'est le mode de qui construit un dossier et doit pouvoir produire chaque
pièce, pas une synthèse.

Le mode normal cherche **ce qui répond** ; celui-ci cherche **tout ce qui
concerne**. Les deux ne se conduisent pas pareil.

**1. Nommer le critère de sélection, et le dire.** Une question exhaustive a
presque toujours un terme littéral qui désigne son sujet : une personne, un
module, un produit, un client. C'est lui le critère — et la règle qui écarte
les termes trop répandus **ne s'applique pas** ici, elle s'inverse. Aucun
terme littéral (« tout ce qui montre une satisfaction ») → le dire en tête du
rapport : le périmètre reposera sur le seul jugement, donc l'exhaustivité
n'est **pas** garantie, et c'est une information, pas un détail.

**Une question en porte souvent plusieurs, et elles ne se valent pas.**
« Comment X a géré l'arrivée de Y, combien de fois s'est-il plaint, et
a-t-il été de bonne foi ? » en contient trois : « Y » est littéral, « plainte »
et « bonne foi » ne le sont pas. Trouver un critère littéral pour UNE des
demandes ne dispense pas des autres : découper la question, et déclarer pour
**chacune** si elle repose sur un terme cherchable ou sur un jugement.

**Une demande qui appelle un nombre est la plus dangereuse.** « Combien de
fois » produit un chiffre, et un chiffre se lit comme une mesure même quand
c'est un avis. Y répondre suppose d'avoir défini ce qu'on compte — ce qui est
une plainte, un refus, un manquement. Cette définition n'est pas dans le
corpus, elle vient du lecteur. Alors : **l'écrire**, dire ce qu'elle inclut et
ce qu'elle exclut, et présenter le total comme ce qu'il est — le résultat de
ce découpage-là, pas un décompte. Un chiffre livré sans sa définition est la
seule façon, dans ce mode, de faire passer un jugement pour une preuve.

**2. Le grep d'abord — c'est le plancher.** Sur le critère et ses variantes
(racine, accents repliés, casse ignorée), à travers `wiki/`. Il rend **toutes**
les occurrences, pas un classement : c'est la seule couche qui garantisse
quelque chose. Tout ce qui suit ne fait qu'y ajouter.

**3. Puis des vagues sémantiques, la première non reformulée.** La question
dans les mots de l'utilisateur est le signal le plus fort qui existe : la
reformuler d'emblée reviendrait à chercher la question d'un autre. `top_k`
généreux (20 par dossier plutôt que 3 — on ne cherche plus le meilleur, on
cherche tout).
Vagues suivantes : **une reformulation par vague**, sous un angle différent à
chaque fois — synonymes du critère, formulation inverse, cas concret,
notion abstraite. C'est la reformulation qui fait apparaître de la matière
neuve, en déplaçant le point d'interrogation dans l'espace vectoriel ; retirer
les fichiers déjà collectés ne fait que descendre dans le classement, donc
n'ajoute que du moins pertinent. **Filtrer les `relative_path` déjà retenus**
côté appelant — le moteur n'a pas de paramètre d'exclusion et n'en a pas
besoin.

**4. S'arrêter quand une vague n'apporte aucun fichier nouveau** — jamais à un
nombre fixe de vagues. Un compteur gaspille ou tronque, et une troncature
silencieuse est le pire résultat possible pour ce mode. Dire au rapport combien
de vagues ont tourné.

**5. Lire chaque fichier retenu EN ENTIER**, jamais son seul extrait, et en
extraire les entrées qui répondent — verbatim, avec leur date et leur auteur.
La forme canonique le permet : chaque entrée porte sa date complète et son
auteur sur sa ligne. Trop de fichiers pour un seul lecteur → les répartir entre
plusieurs sub-agents lecteurs, chacun rendant ses entrées ; jamais
d'échantillonnage.

**6. Le rapport rend les entrées sur UNE SEULE ligne de temps**, strictement
croissante, **tous canaux confondus** — et non par canal, par pièce ou par
phase. C'est le point où un rapport se dégrade sans qu'on le voie : regrouper
par canal produit des retours en arrière d'une heure ou d'un jour à chaque
changement de groupe, alors que le rapport annonce l'ordre chronologique.
Et l'entrelacement **est** la matière : ce qui a été dit en privé à la minute
où autre chose se disait en public ne se lit que sur une ligne unique. Les
séparer, c'est détruire l'information qu'on est venu chercher.
Des intertitres restent utiles pour donner du rythme, à condition qu'ils
découpent la **ligne de temps** — une période — et jamais une source.
Chaque entrée porte son **auteur** et de quoi **remonter à la pièce brute** —
pas seulement la note d'où elle vient. Une entrée qui sert de contre-argument doit pouvoir être
rouverte dans la source qui n'a subi aucun traitement, sans quoi elle ne vaut
que ce que vaut sa transcription :
la note de `wiki/sources/` avec sa ligne, **et** l'original — la pièce brute,
qui n'a subi aucun traitement. La ligne s'obtient par `grep -n`, jamais à
l'estime. Sur un PDF, citer l'original suffit : il n'a pas de lignes.
**L'original n'est pas facultatif** : `wiki/sources/…` prouve ce que dit la
NOTE, pas ce que dit la pièce. Sur un dossier destiné à être opposé, c'est
précisément la note qu'on cherchera à contester.
**Et une pièce brute ne se cherche pas comme un markdown.** Un export au
format JSON échappe ses guillemets en `\"` et ses retours à la ligne en `\n`
littéraux : chercher la citation telle qu'elle est écrite dans la note n'y
rend **rien**, et l'échec est silencieux — on croit la citation absente alors
qu'elle est là. Mesuré sur un export réel : 108 guillemets échappés, 248
retours à la ligne. Chercher donc sur un **fragment sans guillemet ni
ponctuation coupante** (`grep -n` sur une dizaine de mots consécutifs), ou
défaire les échappements avant de comparer. Ne jamais conclure « absente de la
pièce » sans avoir essayé ainsi.
Ce rapport n'est pas une note du vault et n'est pas vectorisé : l'attribution
s'y écrit **en clair**, sans bloc `[!source]` — il n'y a rien à soustraire à un
index qui n'existe pas. La forme, à respecter au caractère près pour que le
contrôle mécanique la lise :

```
**<date> — <auteur>** — *<qualification facultative>*
> <texte de l'entrée, verbatim>

`wiki/sources/<slug>.md` Ligne <n> · original `archives/<pièce brute>` Ligne <n>
```

**`Ligne <n>`, pas `l. <n>` ni `L<n>`.** Ce n'est pas une coquetterie : le vault
tient une seule forme, et une abréviation de développeur sur une pièce destinée
à être lue par un tiers lui demande de deviner. Sur un PDF, l'original se cite
sans ligne — il n'en a pas.
**Une série de captures se cite par sa capture**, jamais par son dossier :
`archives/<serie>/<fichier>.png`, avec le rang dans la série. Un dossier ne
désigne aucun endroit, et sur une série de cinquante images c'est un repère qui
ne fait pas gagner une minute à qui doit retrouver le passage.
**Et une transcription n'est jamais l'original** — ni `.ocr.md`, ni
`.transcription.md`, ni la note de `wiki/sources/`. Le cas des captures est le
plus trompeur : leur transcription n'a **aucune autre lecture** qui la
contredise, puisqu'un agent l'a produite à l'œil. C'est exactement pour ça
qu'elle ne peut pas tenir lieu de pièce.
**Contrôler après écriture**, c'est mécanique et c'est le seul garde-fou :
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/verify-citations.py" "$VAULT"`
— il balaie `wiki/enseignements/` **et** `references/`, rouvre chaque pièce, et
distingue un repère faux d'une citation recomposée d'une citation absente.
Puis, obligatoirement, **ce qui n'a pas été couvert** : fichiers non lus, dossiers hors périmètre, `inbox/` non ingéré.
Une couverture partielle se dit ; elle ne se devine pas.
Dans ce mode, le rapport **recopie** donc les entrées, contrairement au mode
normal où recopier serait l'erreur : ici les entrées **sont** le livrable, et
elles n'ont pas d'autre chemin vers l'utilisateur.

**7. La destination de ces entrées n'est pas `syntheses/`.** Une liste
d'extraits n'est pas une réponse : `wiki/syntheses/` est indexé, et y déverser
des entrées déjà présentes dans `wiki/sources/` vectoriserait deux fois le même
texte, ferait remonter le même contenu en double à toute recherche suivante, et
transformerait le dossier des conclusions en le plus gros du vault.
Elles vont dans `references/`, hors de `wiki/` donc hors index sémantique.

**Deux fichiers, jamais un seul.** Le défaut à éviter n'est pas de se tromper
de dossier, c'est de réunir la compilation et la synthèse dans un même
fichier : il n'y a alors plus de bon endroit où le mettre. Dans `syntheses/`,
il traîne les entrées recopiées dans l'index — mesuré sur un cas réel, 48
entrées dont 39 déjà vectorisées par `wiki/sources/`, soit 81 % du fichier
compté deux fois et 14 chunks créés en double. Dans `references/`, c'est la
synthèse qui devient introuvable par la recherche, alors qu'elle est la seule
prose neuve du lot et donc précisément ce qui méritait d'être indexé.
Écrire **deux fichiers**, chacun à sa place, se pointant en wikilink.

**Et les deux livrables se proposent ensemble, dans cet ordre.** La compilation
porte les pièces, la synthèse porte la thèse qu'on en tire ; ni l'une ni
l'autre ne remplace sa voisine, et l'une sans l'autre laisse le travail à
moitié fait — des entrées que personne n'a conclues, ou une conclusion dont on
ne peut plus produire les pièces. Elles **se pointent mutuellement en
wikilink**, exactement comme `sources/` et `enseignements/` le font pour une
pièce : même idiome, même raison — un doute sur la thèse se remonte aux
entrées, une entrée se replace dans ce qu'elle sert à établir.

**Ce que ce mode ne garantit pas, et qu'il doit écrire.** Une entrée qui ne
porte aucun terme du critère et qu'aucune reformulation n'approche reste hors
d'atteinte. Le grep garantit le littéral, les vagues élargissent, le lecteur
juge — mais le jugement n'est pas une preuve. Et rien ne rattrape ce qui n'a
jamais été ingéré, ni ce qu'une lecture d'image a laissé passer.

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

La question à traiter est `$ARGUMENTS`, nettoyée des jetons `dans:`,
`--no-index` et `--all-references`.

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
   **Écarter les termes trop répandus — sauf en énumération.** Sur une
   question thématique, un mot présent dans la plupart des notes ne discrimine
   rien : ce sont les termes rares qui portent le sens, que les touches
   viennent d'eux. Mais dès que la question demande **tout ce qui concerne un
   acteur, un module, un produit, un client**, ce terme fréquent cesse d'être
   du bruit — il **est** le critère de sélection, et l'écarter revient à
   chercher autre chose que ce qui est demandé. Le tri se fait alors à la
   lecture et non au motif : c'est coûteux, c'est normal, c'est le prix de
   l'exhaustivité, et c'est ton contexte qui le paie — jamais celui de
   l'utilisateur.

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

   **Où porte le grep, explicitement.** Par défaut `$VAULT/wiki/` : c'est là
   que vit le texte intégral standardisé, seule couche à la fois complète et
   indexée. `archives/` porte les pièces d'origine et ce qui en a été extrait —
   le même contenu sous une autre forme, donc chaque touche y ferait doublon
   avec celle de `wiki/sources/`. On l'ajoute dans un seul cas, et en
   l'annonçant : quand la question porte sur ce qu'une pièce portait
   **littéralement** et que la couche standardisée ne le rend pas.
   `inbox/` n'est jamais fouillé : ce qui s'y trouve n'est pas ingéré, donc
   ni standardisé ni vérifié — une touche y serait citée comme un fait du
   vault alors qu'elle n'en est pas encore un. Si le périmètre de la question
   laisse penser qu'`inbox/` contient de la matière, le dire dans le rapport
   et appeler un `/doc-ingest` ; ne jamais citer depuis le sas.
5. Ne jamais recopier des notes entières.
6. Si rien de pertinent : le dire explicitement et lister ce qui s'en
   rapproche.

## Rapport final (ton retour à l'agent principal)

**Ton rapport EST ce que l'utilisateur lit.** Cette commande s'exécute en
fork : ta sortie lui est présentée telle quelle. Il n'y a pas d'agent principal
qui trierait ce qui le concerne de ce qui ne le concerne pas — **une consigne
écrite dans ton rapport sera affichée**, quel que soit son titre.

Deux tentatives l'ont établi : interdire l'affichage dans ce fichier (l'agent
principal ne le lit pas), et titrer le bloc « NE PAS AFFICHER » (il a été
affiché avec son titre).
Une troisième voie existe pourtant, et il faut la nommer pour qu'on cesse de
la croire fermée : **tu peux écrire sur disque par `Bash`**. `Edit` et `Write`
te manquent, pas `cat > fichier`. Ce n'est donc pas une impossibilité
technique, c'est un choix — et il tient à ceci : **ton rapport est ce que
l'utilisateur lit**. Le renvoyer vers un fichier lui retirerait la seule chose
qui lui permette de juger ton travail, pour épargner un contexte que la
concision épargne déjà. On écrit sur disque quand le **volume** l'exige, jamais
pour cacher un raisonnement.

La conclusion est simple : **il n'y a pas de consignes à transmettre.** L'agent
principal n'en a pas besoin — les conventions d'écriture sont dans
`$VAULT/INSTRUCTIONS-CLAUDE.md`, qu'il peut lire, et le reste (le corps, les
références) est dans ton rapport, sous les yeux de l'utilisateur.

Ton rapport se termine donc par **deux lignes**, et rien d'autre :

`Vault : <le chemin résolu>`
`<la question, ou le verdict — voir ci-dessous>`

Le chemin, parce que c'est la seule chose que l'agent principal ne peut pas
deviner. La question, parce qu'elle s'adresse à l'utilisateur.

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
4. Les **deux lignes finales** décrites ci-dessus, avec le chemin `$VAULT` résolu écrit en
   clair (l'agent principal ne connaît pas la sortie de vault-check) :
   - **en mode `--all-references`**, la proposition porte sur **les deux
     livrables à la fois** : « Écrire la compilation et sa synthèse dans le
     vault ? » — jamais l'une sans proposer l'autre, sinon le travail reste à
     moitié fait : des entrées que personne n'a conclues, ou une conclusion
     dont on ne peut plus produire les pièces.
     Si oui, **la compilation d'abord**, `$VAULT/references/YYYY-MM-DD-<slug>.md`
     (dossier créé au besoin ; hors de `wiki/`, donc hors index sémantique —
     rien à configurer, l'indexation ne parcourt que `wiki/`). Frontmatter
     `type: references`, `date` (celle de la compilation : c'est un produit de
     travail, pas une pièce), `question`, `couverture` (une phrase : vagues
     jouées, fichiers lus, ce qui reste dehors). Corps : les entrées dans
     l'ordre chronologique, chacune suivie de la note dont elle vient.
     L'agent principal les a déjà sous les yeux dans ton rapport : il recopie,
     il ne relit rien.
     **Deux liens, et deux seulement** : `[[syntheses/<slug>]]` en tête, et un
     renvoi par note citée en fin de fichier. Jamais un lien par entrée — deux
     cents liens vers la même note ne feraient qu'un nœud illisible.
     Ni entrée d'`INDEX.md`, ni indexation : une compilation est
     **régénérable** — relancer la commande la refait, plus complète si le
     vault a grandi entre-temps. Elle n'a pas à être maintenue, seulement
     datée. Une ligne au journal :
     `## [YYYY-MM-DD] references | <slug> — <n> entrées`.
     **Puis la synthèse**, avec le même `<slug>`, selon les règles ci-dessous —
     et un renvoi `[[references/YYYY-MM-DD-<slug>]]` dans sa section
     `## Références`, en tête, présenté comme les pièces qui la fondent. Les
     deux se pointent donc mutuellement, exactement comme `sources/` et
     `enseignements/` le font pour une pièce ;
   - **en mode normal**, présenter la réponse et ses sources à l'utilisateur,
     puis proposer : « Sauvegarder cette réponse en synthèse dans le vault ? » ;
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
