# services/semantic_index — Index sémantique de fichiers markdown (embeddings)

## Pourquoi ce dossier existe

Donne une recherche sémantique (« voiture » retrouve « automobile ») à n'importe
quel dossier de fichiers markdown : découpe en chunks, vectorisation via un
fournisseur d'embedding, stockage JSONL, recherche top-k. **L'index vit DANS le
dossier indexé** (`<dossier>/.index/embeddings.jsonl`) : il voyage avec lui
(synchro cloud comprise), aucun fichier ailleurs sur la machine.

**Un index par dossier, une seule vectorisation de la question** : la recherche
accepte plusieurs dossiers et n'embarque la question qu'UNE fois — c'est le seul
coût API d'une recherche, le reste n'est que du calcul local sur des vecteurs
déjà stockés. Chercher dans cinq dossiers coûte donc exactement le même appel
réseau que dans un seul. Les classements restent **groupés par dossier** : deux
dossiers indexés séparément sont deux corpus disjoints, leurs scores ne se
comparent pas et ne doivent pas être fusionnés en un classement unique. La liste
sert aussi à **cibler** un périmètre — un dossier, ou trois, selon la question.

**Agnostique** :
le module sait ce qu'est un titre markdown et ce qu'est la FORME d'un bloc de
callout, pas ce qu'est une « note », un « vault » ou un callout de tel type — les
projets appelants (ex : un vault de connaissances piloté par sub-agents) gardent
leurs conventions chez eux et ne consomment que la façade ou les outils MCP. Quand
un appelant veut soustraire ses blocs de service à la vectorisation, il en
**déclare les types** (`excluded_callouts`) : le moteur n'en connaît aucun par
avance et n'en écrit aucun en dur.

**Le contrat central — modèle épinglé, jamais de fallback** : des vecteurs produits
par deux modèles différents ne sont pas comparables. Le fournisseur et le
modèle sont donc épinglés dans les
métadonnées de l'index à la construction, la recherche les relit et réutilise
exactement ceux-là. Fournisseur indisponible → `SemanticIndexError` explicite
— c'est l'appelant qui dégrade vers sa recherche par mots-clés
(grep). Contrat incompatible (modèle, dimension ou version d'index ≠ config
courante) → erreur proposant le **rebuild complet** (supprimer l'index) — jamais
de revectorisation silencieuse, car elle a un coût API.

**DRY / coût** : la vectorisation passe par `provider.embed()`
(`providers/base.py` — même mécanique HTTP que le chat), par lots de 32 ;
la réindexation est incrémentale par **hash de contenu** (jamais les mtime) : un
chunk au texte inchangé garde son vecteur et son `created_at` sans appel API —
une note renommée mais inchangée ne coûte rien.

Points d'entrée : les outils MCP `semantic_index_build` (construire — épingle
mistral/mistral-embed, un dossier à la fois), `semantic_search` (un ou plusieurs
dossiers, un groupe de résultats par dossier : relative_path, section, score,
excerpt) et `semantic_info` (contrat épinglé — zéro réseau). Les dossiers cibles
se passent toujours en argument — aucun défaut : c'est l'appelant qui connaît ses
chemins.

Contenu, brièvement :

- `__init__.py` — la façade publique (`build_index`, `search_indexes`, `SemanticIndexError`, ...)
- `chunker.py` — markdown → chunks (une section par titre, escalier de découpe pour les sections longues)
- `store.py` — persistance JSONL adressée par contenu (métadonnées épinglées + vecteurs base64)
- `service.py` — orchestration : construction incrémentale, recherche cosinus, non-fallback
- `errors.py` — `SemanticIndexError`, l'échec explicite du module

## Documentation détaillée par fichier

### `__init__.py`

La façade : ré-exporte `build_index`, `search_indexes`, `read_index_metadata`, les
types de résultats (`IndexBuildReport`, `SearchResult`, `DirectorySearchResults`)
et `SemanticIndexError`.
Les appelants importent d'ici et de nulle part ailleurs.

### `chunker.py`

`chunk_markdown_directory(root)` : tous les `.md` sous la racine (énumérés ET lus
par `services/markdown_corpus.py` — la même définition de corpus que le bras
lexical, pour que les deux bras ne puissent pas diverger ; c'est là qu'est retiré
le **front matter YAML**, qui sinon atterrirait dans le `(préambule)` de chaque
fichier) → `list[MarkdownChunk]` (`relative_path`, `section`, `content`). Un chunk
par section (titre ATX) ; contenu avant le premier titre → section `(préambule)` ;
section au-delà de `MAX_CHUNK_CHARS` (**2 000**)
re-découpée par un **escalier de séparateurs** récursif
(granularité de recherche, pas limite d'API) : paragraphes (`\n\n`), puis lignes
(`\n`), puis mots — on ne descend d'un cran que pour les morceaux qui dépassent
encore le seuil, et les morceaux consécutifs sont recollés tant qu'ils tiennent.
Escalier épuisé (un « mot » plus long que le seuil : URL géante, blob base64) :
coupe sèche à la longueur, le filet ne peut pas échouer. Le cran des mots — et lui
seul — ajoute un chevauchement de ~10 % du seuil repris du chunk précédent : c'est
le seul qui tranche au milieu d'une idée, les deux autres coupant à des
articulations réelles du texte. Le découpage **ne dépend jamais de la présence de
titres** : un fichier sans aucun titre est une seule section `(préambule)` que
l'escalier découpe normalement. `MarkdownChunk.embedding_text` est LE texte
vectorisé et haché (titre de section inclus — il porte l'intention de la note).

**`excluded_callouts` — les blocs qu'un appelant soustrait au vecteur.** Un projet
qui écrit dans ses fichiers des blocs de service (chemins, numéros de ligne,
identifiants, horodatages) les fait aujourd'hui vectoriser avec la prose : mesuré
sur un corpus réel, section médiane de 221 caractères contre 110 de bloc, soit
**+50 % de texte sans valeur sémantique** dans le vecteur. Un vecteur étant une
moyenne, ce bloc tire tous les chunks d'un fichier vers une même direction et abîme
la discrimination. L'option prend une liste de types (comparaison **insensible à la
casse**, défaut **vide** : sans elle, rien ne change, pas un hash ne bouge) ; un
bloc de callout est reconnu à sa forme seule — une citation dont la première ligne
porte un type entre crochets (`^>\s*\[!type\][-+]?`, convention Obsidian / alertes
GitHub), poursuivie tant que les lignes commencent par `>`, close à la première qui
ne commence pas par `>` (pas à la première ligne vide, qu'il peut ne jamais y
avoir). Une citation ordinaire, sans type, n'est donc jamais exclue.

Deux garde-fous qui décident de la correction :

- l'exclusion porte sur `embedding_text` **seulement** — donc aussi sur le hash,
  qui en dérive. `content`, stocké et rendu par la recherche, reste **entier** :
  un résultat doit continuer à montrer le fichier tel qu'il est, sinon
  l'utilisateur perd l'information qu'il vient de trouver ;
- une section dont le texte vectorisé devient **vide** après exclusion ne produit
  **aucun chunk** : on ne vectorise pas du vide, et l'appel API serait payé pour
  rien.

**Le coût, noir sur blanc** : adopter (ou changer) l'option change **tous** les
hashs — le premier passage revectorise donc l'intégralité du corpus. En
contrepartie, et c'est le vrai gain, modifier ensuite le contenu d'un bloc exclu
(corriger un numéro de ligne, un chemin) ne coûte **plus aucun appel API**,
puisque le hash n'en dépend plus. La liste retenue est inscrite dans les
métadonnées (`excluded_callouts`, forme normalisée et triée) et rendue par
`semantic_info`.

**Le seuil est le seul réglage qui change ce que les vecteurs *représentent***,
et non la façon de les classer : un vecteur est une moyenne, une section longue
dilue chaque idée qu'elle contient au point qu'un passage précis n'en ressort
plus ; trop courte, elle perd le contexte qui la rend interprétable. Aucune
théorie ne tranche entre les deux — **800 a donc été essayé et mesuré**, sur le
même corpus et le même jeu de questions que 2 000. Verdict : un échange, pas un
progrès — une question gagnée, une perdue, rang moyen inchangé (1,18 → 1,19). La
question gagnée l'était par contournement, son défaut réel étant ailleurs que
dans la granularité. **2 000 est donc une valeur mesurée, pas un défaut hérité**,
et le palier intermédiaire n'a plus lieu d'être : ne pas rouvrir ce réglage sans
banc.

Le changer coûte des appels API, mais **pas une revectorisation complète** : le
hash porte sur le texte du chunk, et une section déjà sous le nouveau seuil n'est
pas re-découpée — même texte, même hash, vecteur réutilisé. Mesuré en passant de
2 000 à 800 : 621 chunks réutilisés sur 1 564. Le coût réel dépend donc de la
proportion de sections longues du corpus, pas du nombre total de chunks.

Corollaire de méthode : comparer deux granularités exige que **tous** les
dossiers du banc soient reconstruits, un dossier oublié restant à l'ancien seuil.
Ce n'est plus une consigne à tenir de tête : depuis la 4.5.0 le seuil est inscrit
dans les métadonnées de l'index (`chunk_chars`) et rendu par `semantic_info` —
l'oubli se constate au lieu de se deviner.

### `store.py`

Le fichier JSONL d'UN index (`index_file_path(dossier)` →
`<dossier>/.index/embeddings.jsonl`). Ligne 1 = `IndexMetadata`, le contrat
épinglé (`provider`, `model`, `dimension`, `version` de format, `chunk_chars` la
granularité de découpe, `excluded_callouts` les types de bloc soustraits à la
vectorisation) ; puis une ligne
par chunk (`path`, `section`, `hash` SHA-256 du texte vectorisé, `created_at`,
`excerpt`, `vector_b64` — float32 little-endian encodés base64, endianness fixée
car l'index voyage entre machines). Les modèles pydantic SONT le schéma des
lignes — pas de liste de clés parallèle ; le store parle `list[float]`, l'encodage
est interne. `read_index()` → `LoadedIndex` (ou None si absent/illisible = jamais
construit) ; `LoadedIndex.chunks_by_hash()` alimente la réindexation incrémentale ;
`write_index()` réécrit tout **atomiquement** (fichier temporaire puis rename —
une interruption ne laisse jamais un index tronqué ; l'incrémental se joue en
amont, sur les appels API).

`chunk_chars` est le seul champ **optionnel** des métadonnées : un index bâti
avant la 4.5.0 ne le porte pas, et doit rester lisible — le refuser le ferait
passer pour « jamais construit » et revectoriserait tout un corpus pour un champ
manquant. `None` se lit donc « granularité inconnue », pas « index invalide ». À
l'inverse, il n'est jamais recopié : le build l'écrit depuis `MAX_CHUNK_CHARS`,
définition unique du seuil.

`excluded_callouts` répond au même besoin — savoir sur quel TEXTE un index a été
bâti — mais n'est pas optionnel : une liste vide n'est pas une inconnue, c'est un
fait, et c'est exactement ce qu'était un index antérieur au champ (l'option
n'existait pas). Le build l'écrit sous la forme normalisée qui a réellement servi
(minuscules, triée), pour que `[!Ref]` et `[!ref]` ne produisent pas deux index
qui se disent différents.

### `service.py`

`build_index(notes_dir, provider_name, excluded_callouts=())` : chunke, réutilise vecteur + `created_at`
des chunks inchangés (hash présent dans l'index précédent), vectorise le reste par
lots, réécrit l'index dans le dossier — retourne `IndexBuildReport` (dont
`embedded_chunks` vs `reused_chunks` : le coût API réel). Contrat épinglé
incompatible (modèle, dimension ou version) → erreur « rebuild complet requis :
supprimer l'index » — la revectorisation totale est une décision humaine, jamais
un effet de bord.

`search_indexes(notes_dirs, question, top_k)` : charge les JSONL en mémoire,
vectorise la question **une seule fois** avec LE modèle des métadonnées (pas le
défaut courant du fournisseur), vérifie la dimension, puis classe les chunks de
chaque dossier par similarité cosinus (pure Python — adapté à des
centaines/milliers de chunks ; passer à une lib vectorielle si un index devient
énorme) → un `DirectorySearchResults` par dossier, dans l'ordre demandé. Deux
refus explicites plutôt qu'un résultat trompeur : un dossier non indexé fait
échouer la recherche entière (un résultat partiel silencieux laisserait croire
qu'on a cherché partout), et des dossiers aux contrats épinglés **différents** ne
sont pas cherchables ensemble — une seule vectorisation ne peut servir qu'un seul
modèle, les interroger avec le même vecteur rendrait des scores faux sur tous
sauf un.

`_ONE_RESULT_PER_FILE` (cran interne, **`True` depuis la 4.3.0**) : regroupe les
chunks d'un même fichier et ne garde que le mieux classé — le top-k devient un
top-k de fichiers DISTINCTS, chacun représenté par son meilleur extrait. L'ordre
des opérations fait tout : regrouper d'abord, tronquer à k ENSUITE (dédoublonner
un top-k déjà tronqué rendrait moins de k résultats) ; le regroupement porte sur
la liste entière plutôt que sur un « top-n large » intermédiaire, puisque l'index
est déjà chargé et trié en mémoire — aucun seuil arbitraire à régler. Il est
resté désactivé jusqu'à la baseline du 2026-08-02 parce qu'il CHANGE les
classements : sans point de comparaison, l'écart qu'il introduit n'était pas
lisible. Ce qu'il fait et ce qu'il ne fait pas : il garantit k fichiers distincts
là où un fichier bien découpé pouvait occuper tout le top-k ; il ne corrige aucun
attracteur formé par des fichiers DIFFÉRENTS au gabarit identique — ceux-là
occupent déjà k places. Il reste un cran, pas un paramètre : `False` d'un
caractère si le banc le condamne.

`read_index_metadata(notes_dir)` : l'outil `semantic_info`, zéro réseau. La
résolution du fournisseur épinglé est déléguée à `resolve_embedding_provider`
(`providers/registry.py` — point unique du non-fallback) ; le service traduit
seulement l'échec dans son vocabulaire (`SemanticIndexError` + marche à suivre :
dégrader vers grep).

### `errors.py`

`SemanticIndexError`, unique exception du module : ce module échoue toujours
explicitement, le message porte la raison humaine et la marche à suivre.
