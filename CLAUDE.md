# CLAUDE.md — Am I Getting Rage Bait by a Bot on X?

## Projet

App web publique qui analyse un compte Twitter/X et calcule un score de probabilité de rage bait opportuniste (0-100).

## Documentation

| Fichier | Contenu |
|---|---|
| `claude/project-pitch.md` | Vision produit, concept, signaux de détection |
| `claude/technical-tasks.md` | **Découpe technique complète** — US validées + tâches par phase avec cases à cocher |
| `claude/taskfollowing.md` | Suivi macro par phase (vue d'ensemble) |
| `claude/security.md` | Pratiques de sécurité détaillées |
| `claude/deployement.md` | Stratégie de déploiement |

## Avancement

> Mettre à jour cette section à chaque fin de tâche.

| Phase | Statut | Progression |
|---|---|---|
| Phase 1 — Fondations | ✅ Terminé | 15/15 |
| Phase 2 — Intégration Twitter | ✅ Terminé | 8/8 + Twikit |
| Phase 3 — Pipeline ML | ⬜ À faire | 0/8 |
| Phase 4 — Frontend | ⬜ À faire | 0/5 |
| Phase 5 — Graphe social | ⬜ À faire | 0/4 |
| Phase 6 — Production | ⬜ À faire | 0/7 |

## Stack

- **Backend** : Python 3.12+ / FastAPI / SQLAlchemy async / Alembic
- **Frontend** : Vue 3 / Nuxt 3 (SSR)
- **DB** : PostgreSQL 16 / Redis 7
- **ML** : HuggingFace Transformers (modèles pré-entraînés francophones)
- **Infra** : Docker Compose / GitHub Actions / Traefik

## Conventions

### Git
- **Git Flow** : `main` (prod) + `develop` + `feature/*` branches
- PR obligatoire vers `develop`, jamais de commit direct sur `main` ou `develop`
- Pre-commit hooks actifs (ruff, gitleaks, trailing-whitespace, no-commit-to-branch)

### Code
- Architecture hexagonale : `domain/` (logique pure) → `interfaces/` (ABC) → `infrastructure/` (implémentations)
- Type hints partout, mypy strict
- Tests : unit + integration (pytest-asyncio)
- Nommage : snake_case Python, PascalCase classes, UPPER_CASE constantes

### Sécurité
- Secrets : `SecretStr` partout, jamais dans le code ou les logs
- Entrées : validation Pydantic stricte à toutes les frontières
- Docker : user non-root, DB/Redis non exposés sur l'hôte
- API externe : `follow_redirects=False`, timeout 10s
- Pas de pickle, pas de eval, pas de exec

## Commandes utiles

```bash
# Dev — tout lancer
docker compose up -d

# Backend seulement
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload

# Tests
cd backend && pytest
cd frontend && npm run test

# Lint
cd backend && ruff check . && ruff format --check .
cd frontend && npm run lint

# Migrations
cd backend && alembic upgrade head
```
