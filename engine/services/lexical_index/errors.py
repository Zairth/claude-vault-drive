# services/lexical_index/errors.py
"""Exception du module lexical_index.

Une seule classe, même contrat que le reste du moteur : échec EXPLICITE (dossier
introuvable, corpus vide, question sans mot cherchable, SQLite sans FTS5) — jamais
de résultat vide qui laisserait croire à une recherche aboutie."""


class LexicalIndexError(Exception):
    """Échec explicite de la recherche lexicale — le message porte la raison humaine."""
