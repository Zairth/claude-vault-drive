# mcp_server/server.py
"""Les briques métier exposées en outils MCP — LA porte d'entrée du moteur.

Le plugin Claude Code lance ce serveur (via uv, depuis sa copie du dépôt) et les
clés API arrivent en variables d'environnement (userConfig du plugin). Les
erreurs métier remontent telles quelles — leurs messages sont déjà explicites
et actionnables (contrat du projet : échec explicite, jamais de fallback
silencieux).
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from providers import PINNED_PROVIDER, describe_providers
from services.document_ocr import convert_to_markdown
from services.lexical_index import search_lexical
from services.semantic_index import build_index, read_index_metadata, search_indexes

_DEFAULT_TOP_K = 5

server = FastMCP("vault-engine")


@server.tool()
async def semantic_index_build(directory: str, excluded_callouts: list[str] | None = None) -> dict:
    """(Re)construit l'index sémantique d'un dossier de fichiers markdown.

    Incrémental par hash : seuls les chunks nouveaux/modifiés coûtent un appel API.
    L'index vit DANS le dossier (<dossier>/.index/embeddings.jsonl) et épingle son
    fournisseur — contrat incompatible = erreur proposant le rebuild complet.

    `excluded_callouts` : types de bloc de callout (`> [!TYPE]`, insensible à la casse)
    à ne PAS vectoriser — pour les blocs de service qu'un projet écrit dans ses fichiers
    (chemins, numéros de ligne, identifiants, horodatages) et qui diluent le vecteur sans
    rien apporter à une recherche. Le bloc reste ENTIER dans les résultats de recherche :
    seul le texte vectorisé l'ignore. À passer avec la MÊME liste à chaque construction
    d'un même dossier — le hash en dépend, donc la changer revectorise tout le corpus une
    fois (et rend ensuite gratuite toute modification du contenu d'un bloc exclu). La
    liste retenue se relit dans `semantic_info`.
    """
    report = await build_index(Path(directory), PINNED_PROVIDER, excluded_callouts or [])
    return report.model_dump()


@server.tool()
async def semantic_search(
    question: str, directories: list[str], top_k: int = _DEFAULT_TOP_K
) -> list[dict]:
    """Cherche dans l'index sémantique d'UN OU PLUSIEURS dossiers, en un seul appel.

    La question n'est vectorisée qu'UNE fois quel que soit le nombre de dossiers —
    c'est le seul coût API d'une recherche, le reste est du calcul local. Passer
    la liste des dossiers pertinents plutôt que d'appeler l'outil plusieurs fois ;
    n'en passer qu'un pour cibler un périmètre précis.

    Rend un groupe par dossier ({directory, results}), dans l'ordre demandé : deux
    dossiers sont deux corpus disjoints, leurs scores ne se comparent pas et ne
    doivent pas être fusionnés en un classement unique. Chaque résultat :
    relative_path, section, score, excerpt.

    top_k compte des FICHIERS distincts : un fichier n'apparaît qu'une fois, par
    son meilleur extrait. Un top_k de 3 rend donc 3 fichiers à lire, pas trois
    passages du même — lire le fichier entier si l'extrait ne suffit pas.

    Fournisseur d'embedding épinglé à l'index ; indisponible = erreur explicite —
    dégrader alors vers une recherche par mots-clés (grep), jamais vers un autre
    fournisseur (espaces vectoriels incomparables).
    """
    grouped_results = await search_indexes([Path(directory) for directory in directories], question, top_k)
    return [group.model_dump() for group in grouped_results]


@server.tool()
def lexical_search(question: str, directories: list[str], top_k: int = _DEFAULT_TOP_K) -> list[dict]:
    """Cherche les MOTS de la question (BM25) dans un ou plusieurs dossiers markdown.

    NON câblé dans `semantic_search`, et c'est une conclusion mesurée, pas une
    attente : sur 22 questions de banc, zéro où le lexical touche une cible que le
    sémantique rate — une fusion n'ajouterait aucune couverture. C'est un outil à
    part entière, pas un demi-moteur.
    Son rôle propre : dès qu'un TERME RARE ancre la question (un identifiant, une
    référence, une empreinte de commit), il sort la bonne cible en premier rang,
    immédiatement. Son mode d'échec, tout aussi net : la PÉRIPHRASE — une question
    qui ne partage aucun mot avec sa cible (« parapheur numérique » face à des
    fichiers qui disent « yousign ») ne lui rend rien. C'est exactement là que le
    bras sémantique travaille : les deux se complètent au lieu de se doubler.

    Purement local : zéro réseau, zéro quota, rien d'écrit sur disque (l'index est
    construit en mémoire à la requête et jeté). Fonctionne sans `semantic_index_build`
    préalable, et sur un dossier en lecture seule. Rend un groupe par dossier
    ({directory, results}) ; chaque résultat : relative_path, score, excerpt.
    """
    grouped_results = search_lexical([Path(directory) for directory in directories], question, top_k)
    return [group.model_dump() for group in grouped_results]


@server.tool()
def semantic_info(directory: str) -> dict:
    """Contrat épinglé de l'index d'un dossier : fournisseur, modèle, dimension,
    version de format, `chunk_chars` (la granularité de découpe à laquelle l'index a
    été produit) et `excluded_callouts` (les types de bloc soustraits à la vectorisation).

    Ces deux derniers servent à comparer des dossiers entre eux : deux index bâtis à des
    granularités — ou avec des exclusions — différentes restent cherchables ensemble
    (mêmes vecteurs, scores justes) mais n'ont pas vectorisé le même texte ; un dossier
    oublié lors d'un changement se voit ici, au lieu de passer inaperçu. `chunk_chars`
    à `null` = index construit avant que le champ existe ; `excluded_callouts` vide =
    aucune exclusion.

    Purement local : zéro réseau, zéro quota — à utiliser librement pour diagnostiquer.
    """
    metadata = read_index_metadata(Path(directory))
    if metadata is None:
        return {"index": None, "message": f"aucun index sémantique dans {directory}"}
    return metadata.model_dump()


@server.tool()
async def ocr_convert(document: str, output: str | None = None) -> dict:
    """Convertit un document (.pdf, .png, .jpg, .jpeg, .avif) en markdown par OCR.

    Sortie par défaut : <document>.md à côté de la source, écrasée si existante.
    Fournisseur épinglé : mistral — indisponible = erreur, JAMAIS de fallback.
    """
    report = await convert_to_markdown(Path(document), Path(output) if output else None)
    return report.model_dump()


@server.tool()
def llm_check() -> list[dict]:
    """État des fournisseurs LLM : qui est configuré, avec quel modèle d'embedding.

    Purement local (lecture de la config) : zéro réseau, zéro quota.
    """
    return describe_providers()
