# claude-vault

[![plugin Claude Code](https://img.shields.io/badge/plugin-Claude%20Code-d97757)](https://code.claude.com/docs/en/plugins)
[![version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FZairth%2Fclaude-vault%2Fmain%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version&color=blue)](CHANGELOG.md)
[![licence MIT](https://img.shields.io/github/license/Zairth/claude-vault?color=green)](LICENSE)
[![sans service ni clone](https://img.shields.io/badge/install-sans%20clone%2C%20sans%20service-lightgrey)](#démarrer)

**Donnez à Claude Code une mémoire qui survit à vos sessions.**

Vous lui déposez des documents — un PDF, une capture d'écran, un export, un
compte rendu. Le plugin en fait des notes markdown rangées et reliées entre
elles, dans un dossier bien à vous. À la session suivante, Claude les relit et
répond en citant ses sources. Ouvrez ce dossier dans Obsidian si vous voulez le
voir en graphe — rien ne vous y oblige, ce ne sont que des fichiers.

## Démarrer

Une fois, valable pour tous vos projets :

```
/plugin marketplace add https://github.com/Zairth/marketplace
/plugin install claude-vault@zairth_store
```

**Donnez-lui sa clé.** À l'installation, le plugin demande une clé d'API
Mistral (gratuite) : c'est elle qui change tout ce qui compte. Sans elle, la
recherche se fait par mots-clés — elle trouve ce que vous avez su nommer, et
rate la reformulation. Avec elle, elle cherche **par le sens** : « qui a validé
le budget ? » remonte une note qui parle d'accord donné sur une enveloppe, sans
partager un seul mot avec la question. Elle ouvre aussi la lecture des
documents scannés, sans quoi un PDF photographié n'est qu'une image.
Le moteur demande en retour [uv](https://docs.astral.sh/uv/) —
[PREREQUIS.md](PREREQUIS.md) détaille les deux, y compris comment couper
l'utilisation de vos données pour l'entraînement. Clé laissée vide, rien ne
casse : les commandes annoncent leur repli au lieu de faire semblant.

> **Comment taper les commandes de ce plugin.** Elles s'appellent par leur nom
> complet, préfixé du plugin :
>
> ```
> /claude-vault:vault-init …    /claude-vault:doc-ingest …
> /claude-vault:doc-query …     /claude-vault:doc-lint …
> ```
>
> La forme courte `/doc-query` échoue avec `Unknown command` : c'est le
> fonctionnement de Claude Code, pas un défaut d'installation. **La suite de ce
> document les écrit en abrégé** pour rester lisible ; à la saisie, préfixez
> toujours.

Puis dans le projet qui doit avoir sa mémoire :

```
/claude-vault:vault-init "/chemin/vers/mon-vault"
```

Relancez la session : le vault existe, il est vide.

Reste à lui donner de quoi lire. **Deux façons**, au choix :

```
/doc-ingest inbox/                    ← tout ce que vous avez déposé dans le sas
/doc-ingest /chemin/vers/mes-docs     ← un dossier, un fichier, ou un lien
```

- **Le sas.** `/vault-init` crée un dossier `inbox/` à la racine du vault :
  déposez-y vos fichiers, puis lancez `/doc-ingest inbox/` pour ingérer le lot,
  ou `/doc-ingest <nom-du-fichier>` pour n'en prendre qu'un. Sans argument, la
  commande liste ce qui s'y trouve et vous demande — elle n'avale jamais un lot
  entier sans qu'on le lui dise.
- **Un chemin quelconque**, sans rien déplacer. Une seule condition : il doit
  être **autorisé**. Un dossier situé hors du vault et hors du projet sera
  refusé tant qu'il ne figure pas dans `additionalDirectories`
  (`.claude/settings.local.json`) — c'est le cas le plus courant quand les
  sources sont rangées à côté du vault plutôt que dedans.

Puis interrogez : `/doc-query <votre question>`. Aucun clone, aucun service à
faire tourner. Le vault peut être n'importe où — Google Drive, Dropbox, ou un
disque local. Options, montage Drive et cas particuliers :
[PREREQUIS.md](PREREQUIS.md).

## Les cinq commandes

| commande | ce qu'elle fait |
|---|---|
| `/vault-init` | crée le vault et branche le projet dessus |
| `/doc-ingest` | range une source dans le vault — un fichier, un dossier, un lien |
| `/doc-query` | pose une question, obtient une réponse qui cite ses notes — `--all-references` rend toutes les entrées d'un sujet |
| `/doc-lint` | vérifie la cohérence de l'ensemble |
| `/doc-repair` | corrige une information et la répercute partout où elle apparaît |

Au quotidien, deux suffisent : **`/doc-ingest` pour nourrir, `/doc-query` pour
consulter.** Le reste s'enchaîne tout seul — une ingestion lance sa
vérification sans qu'on le lui demande.

## Ce que devient un document que vous déposez

Le vault n'est qu'un dossier de fichiers markdown. Une pièce ingérée y prend
trois formes, et vous pouvez toujours redescendre de l'une à l'autre :

- **ce qu'on en retient** — une note courte, lisible, reliée aux autres par des
  liens ;
- **le texte intégral**, mis au propre mais sans rien trier : ce qu'aucune note
  n'a retenu reste retrouvable ;
- **la pièce elle-même**, archivée telle quelle et jamais modifiée. C'est elle
  qui fait foi, et c'est pour ça qu'une réponse peut citer sa source.

Rien n'est supprimé, rien n'est enfermé dans un format à part : vous pouvez
partir avec le dossier, l'ouvrir dans Obsidian, ou le lire à la main.

> **Avant d'indexer, un point à décider.** La recherche par le sens envoie le
> texte de vos notes à un fournisseur externe, et l'OCR y envoie les documents
> convertis. Les paliers gratuits autorisent souvent l'entraînement **par
> défaut**, et le réglage inverse ne vaut que pour la suite. Si votre vault
> contient des données personnelles ou confidentielles, lisez
> [PREREQUIS.md](PREREQUIS.md) avant la première indexation.

## Pour aller plus loin

- Prérequis pas à pas, montage Drive, clé API : [PREREQUIS.md](PREREQUIS.md)
- Ce que change chaque version : [CHANGELOG.md](CHANGELOG.md)

