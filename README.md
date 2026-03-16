# Am I Getting Rage Bait by a Bot on X?

Outil open source qui analyse un compte Twitter/X et calcule un score de probabilité qu'il s'agisse d'un compte opportuniste de rage bait (0-100).

## Le problème

Les réseaux sociaux sont envahis par des comptes — bots, fermes à contenus, influenceurs opportunistes — qui exploitent la colère, la peur et l'indignation pour générer de l'engagement. Ce rage bait industrialisé est un enjeu de désinformation, de manipulation de l'opinion et de santé mentale.

Cet outil vous aide à prendre du recul en analysant objectivement les signaux d'un compte.

## Comment ça marche

L'analyse repose sur 4 signaux indépendants combinés en un score composite :

| Signal | Description |
|---|---|
| **Contenu IA** | Détection multi-stratégie : ensemble de modèles HuggingFace (CamemBERTa + RoBERTa), analyse statistique linguistique (TTR, entropie, burstiness), et analyse de similarité inter-tweets via sentence-transformers |
| **Comportement** | Ratio followers/following suspect, volume de tweets excessif, compte récent avec forte activité |
| **Sentiment** | Proportion de tweets négatifs ou alarmistes, ton catastrophiste, vocabulaire émotionnel intense |
| **Opportunisme** | Surreprésentation de tweets "problème", sauts thématiques fréquents, surf systématique sur les tendances |

## Stack technique

- **Backend** : Python 3.12 / FastAPI / SQLAlchemy async / Alembic
- **Frontend** : Vue 3 / Nuxt 3 (SSR) / Tailwind CSS
- **ML** : HuggingFace Transformers + sentence-transformers
- **DB** : PostgreSQL 16 / Redis 7
- **Infra** : Docker Compose / GitHub Actions / Traefik
- **API Externe** : Twitterapi.io

## Lancer le projet

```bash
# Cloner le repo
git clone https://github.com/Mateo-Favard/AmIGettingRageBaitByABotOnX.git
cd AmIGettingRageBaitByABotOnX

# Copier le fichier d'environnement
cp .env.example .env

# Lancer tout via Docker
docker compose up -d

# L'app est accessible sur http://localhost:3000
```

Au premier lancement, les modèles ML sont téléchargés automatiquement (~2 Go). L'analyse initiale peut prendre un peu de temps sur CPU.

## Commandes utiles

```bash
# Tests backend
docker compose exec api pytest

# Lint backend
docker compose exec api ruff check .

# Lint frontend
docker compose exec frontend npm run lint

# Logs
docker compose logs -f api
```

## Contribuer

Les contributions sont les bienvenues. Le projet suit une architecture hexagonale (`domain/` -> `interfaces/` -> `infrastructure/`) avec pre-commit hooks (ruff, gitleaks).

## Licence

MIT
