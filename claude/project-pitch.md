# Am I Getting Rage Bait by a Bot on X? — Project Pitch

## Concept

App web publique permettant d'analyser un compte Twitter/X et d'évaluer la probabilité qu'il s'agisse d'un compte opportuniste de rage bait — un compte qui ne poste pas par conviction mais surfe sur l'engagement et l'indignation pour faire des stats.

Le nom du projet est un parti pris éditorial assumé. L'outil en lui-même analyse des signaux objectifs.

## Flux utilisateur

1. L'utilisateur colle un lien de compte Twitter/X dans l'interface
2. Le backend fetch les données du compte via [twitterapi.io](https://twitterapi.io) : bio, photo de profil, tweets récents, liste de follows
3. Les données passent dans un pipeline de modèles ML pré-entraînés
4. Un **score composite** (0-100) est retourné avec le détail de chaque signal
5. Le compte et son graphe social (niveau 1) sont stockés en base pour cross-référencement

## Signaux de détection

Le score composite agrège plusieurs analyses indépendantes :

### 1. Détection de contenu généré par IA
- Les tweets sont-ils écrits par un LLM (ChatGPT, Claude, etc.) puis postés à la main ?
- Modèle(s) pré-entraîné(s) de détection de texte synthétique
- À rechercher : modèles francophones de AI text detection

### 2. Patterns comportementaux
- Âge du compte vs volume de posts
- Fréquence de publication (régularité anormale, horaires suspects)
- Ratio followers/following
- Taux d'engagement vs nombre de followers

### 3. Analyse de sentiment
- Ton excessivement inflammatoire de manière constante
- Indignation permanente sans nuance
- Absence de contenu neutre ou personnel
- Modèle(s) de sentiment analysis francophone

### 4. Virage politique opportuniste
- Détection de changement de positionnement politique
- Le compte suit-il systématiquement la vague de ce qui fait le plus réagir ?
- Analyse temporelle des thématiques abordées

### 5. Analyse du réseau social
- Mise en relation avec d'autres comptes déjà analysés en base
- Détection de clusters de comptes rage bait interconnectés
- Analyse des follows directs (niveau 1, architecture modulaire pour aller plus profond)

## Stack technique

| Composant | Choix |
|---|---|
| Backend | Python 3.12+ / FastAPI |
| Frontend | Vue 3 / Nuxt 3 |
| Base de données | PostgreSQL (comptes, scores, graphe social) |
| Cache / Rate limiting | Redis |
| Source de données Twitter | [twitterapi.io](https://twitterapi.io) |
| Modèles ML | HuggingFace Transformers (modèles pré-entraînés — à identifier) |
| Conteneurisation | Docker / Docker Compose |
| CI/CD | GitHub Actions |

## Données stockées

- **Comptes analysés** : handle, bio, pp, date de création, métriques (followers, following, tweets count)
- **Scores** : score composite + scores individuels par signal + date d'analyse
- **Graphe social** : relations follow/following de niveau 1 entre comptes analysés
- **Tweets fetchés** : derniers tweets utilisés pour l'analyse (liés au compte)

## Accès et authentification

- **Pas d'inscription requise** : l'outil est en libre accès
- **Rate limiting par IP** pour éviter les abus
- Pas de données utilisateur collectées

## Licence

MIT — Open source, contributions bienvenues.

## Principes

1. **Transparence** : code, modèles et méthodologie ouverts
2. **Pas de censure** : l'outil informe avec un score, il ne bloque rien
3. **Modularité** : chaque signal de détection est un module indépendant, facile à ajouter/retirer
4. **Privacy** : pas de collecte de données utilisateur, seules les données publiques Twitter sont analysées

## Modèles ML — À rechercher

Les modèles suivants sont à identifier et benchmarker :

- [ ] Détection de texte généré par IA (francophone)
- [ ] Sentiment analysis (francophone, adapté au registre Twitter)
- [ ] Classification de contenu politique / rage bait
- [ ] Détection de bots / comportement automatisé

Piste : CamemBERT et ses dérivés pour la base francophone, fine-tuning potentiel sur un dataset annoté manuellement.
