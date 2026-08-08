---
name: vault-engine
description: À utiliser dès qu'une tâche touche au moteur sémantique/OCR embarqué dans claude-vault (celui qu'appellent les commandes /doc-*) — recherche sémantique par embeddings, recherche lexicale BM25, OCR de PDF ou d'images — pour savoir quel outil MCP utiliser et comment lire sa réponse, sans réexplorer le dépôt.
---

# Le moteur du vault — mode d'emploi

## Vue d'ensemble

Le plugin embarque son moteur (`engine/`) : deux briques de recherche
(sémantique, lexicale) plus l'OCR, un seul fournisseur (Mistral, tier gratuit),
zéro service qui tourne, échecs explicites — jamais de fallback silencieux.

Une seule porte d'entrée depuis une session : **les outils MCP du plugin**
(`mcp__plugin_claude-vault_engine__…`) — pas de shell, pas de venv, clé
API déjà fournie par le plugin (`userConfig`).

## Référence rapide

| Besoin | Outil MCP |
|---|---|
| Recherche sémantique d'un ou plusieurs dossiers markdown | `semantic_search` (question, **directories** : liste, top_k) |
| (Re)construire l'index | `semantic_index_build` (directory, excluded_callouts) — un dossier par appel |
| Contrat de l'index + granularité + exclusions (zéro réseau) | `semantic_info` (directory) |
| Trouver un terme rare/exact : identifiant, référence (zéro réseau) | `lexical_search` (question, **directories** : liste, top_k) |
| PDF/image → markdown (OCR) | `ocr_convert` (document, output) — .pdf .png .jpg .jpeg .avif ; sortie écrasée |
| État du fournisseur (zéro réseau, zéro quota) | `llm_check` |

Le dossier cible est **obligatoire** sur les outils de recherche : chaque appel
dit explicitement quel périmètre il vise — le moteur n'a aucun dossier par
défaut, c'est l'appelant qui connaît ses chemins.

**`semantic_search` prend une LISTE de dossiers, et il faut s'en servir** : la
question n'est vectorisée qu'UNE fois quel que soit leur nombre, et c'est le seul
coût API de la recherche. Cinq dossiers en un appel = un embedding ; cinq appels
d'un dossier = cinq embeddings, pour exactement le même résultat. La réponse est
un groupe par dossier (`{directory, results}`) : ne jamais fusionner ces
classements en un seul — ce sont des corpus disjoints, leurs scores ne se
comparent pas. Et n'en passer qu'un (ou deux) quand la question vise clairement
un périmètre précis.

Son `top_k` compte des **fichiers distincts** : un fichier ne remonte qu'une
fois, représenté par son meilleur extrait. `top_k=3` rend donc trois fichiers à
lire, jamais trois passages du même — si l'extrait ne suffit pas, ouvrir le
fichier.

## Sur le vault du projet : passer par les commandes

Pour interroger ou indexer **le vault du projet**, préférer les commandes
`/doc-query`, `/doc-ingest`, `/doc-lint` aux outils bruts : elles résolvent le
chemin du vault (`.claude/vault-path.local`), énumèrent les bons dossiers à
indexer et orchestrent la cascade complète (outils MCP → repli grep explicite).
Les outils MCP directement, c'est pour un périmètre hors vault ou un diagnostic.

## Un appelant qui ne peut pas parler MCP ? le CLI

Les outils MCP restent LA porte d'entrée. Mais un **hook** Claude Code est un
script shell : pas de session, pas de client MCP. Pour lui — et seulement pour
lui — le moteur expose les mêmes briques en ligne de commande. Le plugin les
enveloppe dans `scripts/vault-search.sh`, `vault-lexical.sh`, `vault-index.sh`
et `vault-ocr.sh`, qui résolvent le moteur et l'invoquent :

```
bash "$CLAUDE_PLUGIN_ROOT/scripts/vault-lexical.sh" "ma question" "$corpus" 5
```

Sous ces wrappers, quatre commandes : `search` / `lexical` (question, `--dir`
répétable, `--top-k`), `index --dir [--exclude-callout TYPE …]` (répétable),
`convert <fichier> [--out]`. JSON sur stdout et rien d'autre, échec métier sur
stderr avec le code 1, usage invalide code 2. Depuis une session d'agent, ne PAS
passer par là : les outils MCP font la même chose sans lancer de processus.

## Pièges connus

- **Un seul fournisseur, jamais de fallback** : embeddings et OCR sont
  épinglés sur mistral. Mistral indisponible (clé absente, quota, réseau) =
  échec explicite → pour la recherche, dégrader vers grep ; jamais de plan B
  silencieux.
- **L'index sémantique vit DANS le dossier indexé** (`<dossier>/.index/embeddings.jsonl`)
  et son fournisseur/modèle est épinglé en ligne 1. Contrat incompatible →
  le moteur exige un rebuild complet (supprimer l'index), jamais de
  revectorisation silencieuse.
- **`lexical_search` n'est pas câblé dans `semantic_search`, et ne le sera pas** :
  mesuré au banc, sur 22 questions, le lexical n'atteint AUCUNE cible que le
  sémantique rate — une fusion n'ajouterait pas un résultat. Ce n'est donc pas un
  demi-moteur en attente, c'est un outil à part entière, avec un rôle et un mode
  d'échec connus :
  - **quand le prendre** — la question est ancrée par un TERME RARE : un
    identifiant, une référence, un nom propre, une empreinte de commit. Il rend
    alors la bonne cible en premier rang, immédiatement, et gratuitement (zéro
    réseau, index en mémoire puis jeté, aucun `semantic_index_build` requis) ;
  - **quand il ne rendra rien** — la question est une PÉRIPHRASE qui ne partage
    aucun mot avec sa cible (« pièce jointe signée » face à des fichiers qui ne
    disent que « parapheur »). Aucun token commun, aucun résultat. C'est
    précisément le terrain de `semantic_search` — y basculer plutôt que
    reformuler.

  C'est aussi LE bon outil pour un hook : gratuit et instantané, là où un
  embedding par prompt serait une dépense permanente.
- **Un dossier sans aucun `.md` n'est pas une erreur pour `lexical_search`** : il
  rend `results: []` et les autres dossiers de l'appel sont cherchés quand même
  (un corpus jeune a des couches vides). Un dossier *introuvable*, lui, reste un
  échec — c'est un appel fautif.
- **Le `score` de `lexical_search` ne se lit qu'en relatif** — entre les résultats
  d'un même dossier, dans un même appel. Il n'est comparable ni d'un dossier à
  l'autre (l'IDF se calcule sur le corpus interrogé) ni dans l'absolu (BM25 n'a
  pas d'échelle bornée, contrairement au cosinus de `semantic_search`). Sur un
  petit corpus tous les scores s'écrasent vers `1e-06` : le classement reste
  juste, les valeurs ne veulent rien dire. **Ne jamais filtrer sur un seuil de
  score** — se servir du rang (`top_k`).
- **Le front matter YAML n'est pas indexé** (bloc `---` en tête de fichier,
  retiré dans les deux bras) : ses clés, identiques dans tout un dossier, ne
  discriminaient rien et mangeaient les premiers mots de chaque aperçu. Corollaire
  à connaître : ce qui ne vit QUE dans le front matter n'est pas trouvable — pour
  qu'une information soit cherchable, elle doit être dans le corps du fichier.
- **`semantic_info` rend aussi `chunk_chars`**, la granularité de découpe de
  l'index. Deux dossiers bâtis à des granularités différentes restent cherchables
  ensemble (mêmes vecteurs, scores justes), mais ne décrivent pas le même grain —
  après un changement de granularité, un dossier non reconstruit se repère par ce
  champ au lieu de passer inaperçu. `null` = index antérieur au champ.
- **`excluded_callouts` : des blocs de callout soustraits au vecteur, à la demande
  de l'appelant.** `semantic_index_build(directory, excluded_callouts=["type", …])`
  écarte du texte vectorisé les blocs `> [!TYPE]` (citation dont la première ligne
  porte un type entre crochets ; comparaison insensible à la casse) — c'est fait
  pour les blocs de service qu'un projet écrit dans ses fichiers (chemins, numéros
  de ligne, identifiants, horodatages), qui diluent le vecteur sans répondre à
  aucune question. **Le vault en exclut `source`** : `vault-index.sh` passe
  toujours `--exclude-callout source`, et tout appel MCP `semantic_index_build`
  sur un dossier du vault doit passer `excluded_callouts: ["source"]` — sinon
  l'index change de contrat et tout le corpus est revectorisé au passage suivant.
  Trois choses à savoir :
  - le bloc reste **entier** dans `content` et dans l'extrait rendu par
    `semantic_search` — seul le vecteur (donc le hash) l'ignore ;
  - **la même liste à chaque construction d'un même dossier.** Le hash dérive du
    texte vectorisé : adopter ou changer la liste revectorise TOUT le corpus au
    passage suivant. En échange, modifier ensuite le contenu d'un bloc exclu
    (corriger un chemin, un numéro de ligne) ne coûte plus aucun appel API ;
  - la liste retenue se relit dans `semantic_info` — un dossier reconstruit sans
    elle s'y voit, comme pour `chunk_chars`. Vide = aucune exclusion.
- `llm_check` et `semantic_info` sont purement locaux : à utiliser librement
  pour diagnostiquer sans consommer de quota.
