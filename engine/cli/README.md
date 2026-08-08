# cli — la porte d'entrée shell, pour les appelants qui ne peuvent pas parler MCP

## Pourquoi ce dossier existe

Le moteur a deux portes, et une seule raison à cela : **un hook Claude Code est
un script shell**. Il n'a pas de session, pas de client MCP, pas de boucle
d'agent — juste un processus qui lit stdin et écrit stdout. Cette catégorie
d'appelants ne peut structurellement pas passer par `mcp_server/`. Le CLI avait
été retiré en 2.0.0 au recentrage MCP-only : le recentrage était juste, c'est
cette catégorie-là qui manquait à l'inventaire.

Les deux portes servent **les mêmes briques** et rendent **les mêmes
structures** : le CLI n'a aucune logique métier à lui, il traduit une ligne de
commande en appel de façade et un objet en JSON.

Le contrat shell, identique pour les quatre commandes :

- **stdout = JSON**, et rien d'autre — un script appelant peut le passer à `jq`
  sans filtrer quoi que ce soit ;
- **échec métier = message sur stderr + code de sortie 1**. Le message n'est ni
  reformulé ni préfixé : il porte déjà la raison humaine et la marche à suivre,
  et c'est lui que le script relaiera ;
- **usage invalide = code de sortie 2** (argparse), avec l'usage sur stderr.

```
uv run --directory "$CLAUDE_PLUGIN_ROOT" \
       --with-requirements "$CLAUDE_PLUGIN_ROOT/requirements.txt" \
       python -m cli lexical "ma question" --dir "$corpus" --top-k 5
```

`uv` télécharge les dépendances à la volée en cache partagé — il n'y a pas de
`.venv` dans le dépôt et il n'y en aura pas : c'est la même invocation que celle
qui lance le serveur MCP et que celle qui exécute les tests.

**`lexical` est la commande pensée pour un hook déclenché à chaque prompt.** Elle
ne coûte aucun appel API, ne demande aucune clé, n'exige aucun index préalable,
et rend la main en ~220 ms de bout en bout (uv + démarrage Python compris). Un
hook qui se déclenche à chaque prompt ne peut pas coûter un embedding à chaque
fois — c'est un poste de dépense permanent. Le bras lexical trouve là son
premier usage réel, avant même d'être câblé dans la recherche par défaut.

Contenu, brièvement :

- `__main__.py` — les quatre commandes, leur aiguillage et le contrat de sortie
- `__init__.py` — marqueur de package (le point d'entrée est `python -m cli`)

## Documentation détaillée par fichier

### `__main__.py`

Quatre commandes, toutes en sortie JSON :

| Commande | Brique appelée | Réseau |
|---|---|---|
| `search "<question>" --dir A [--dir B …] [--top-k N]` | `search_indexes` | 1 embedding, quel que soit le nombre de dossiers |
| `lexical "<question>" --dir A [--dir B …] [--top-k N]` | `search_lexical` | aucun |
| `index --dir A [--exclude-callout TYPE …]` | `build_index` | les chunks nouveaux/modifiés |
| `convert <fichier> [--out <chemin>]` | `convert_to_markdown` | 1 appel OCR |

`--dir` est **répétable** sur les deux recherches — c'est la forme plurielle de
la 4.0.0 : les résultats reviennent groupés par dossier, dans l'ordre donné, et
ne doivent jamais être fusionnés en un classement unique (corpus disjoints).
`index` n'en prend qu'un seul : un index vit DANS le dossier qu'il décrit.

`--exclude-callout TYPE` (sur `index`) est **répétable** lui aussi — même forme que
`--dir`, une seule à retenir : chaque occurrence déclare un type de bloc de callout
(`> [!TYPE]`, insensible à la casse) que l'appelant ne veut pas voir vectorisé. Le
bloc reste ENTIER dans les résultats de recherche ; seul le vecteur — donc le hash —
l'ignore. À passer avec la MÊME liste à chaque construction d'un dossier : le hash
en dépend, la changer revectorise tout le corpus une fois (et rend ensuite gratuite
toute modification du contenu d'un bloc exclu).

Chaque sous-commande porte SA fonction (`set_defaults(run=…)`) : la table
d'aiguillage EST le parser, il n'y a pas de chaîne de `if` à tenir en parallèle
de la liste des sous-commandes.

**Chaque commande importe sa brique dans son corps, pas en tête de module.**
C'est délibéré et mesuré : tout importer coûte 280 ms au démarrage (pydantic,
httpx, les fournisseurs), n'importer que le bras lexical en coûte 170. Sur une
porte MCP lancée une fois par session ce serait du zèle ; sur un hook qui se
déclenche à chaque prompt, ces 110 ms sont un poste de dépense permanent. Ne pas
« nettoyer » ces imports en les remontant en tête de fichier.

### `__init__.py`

Marqueur de package. Le point d'entrée est `python -m cli`, c'est-à-dire
`__main__.py` — rien n'est exposé ici, le CLI n'est pas une bibliothèque.
