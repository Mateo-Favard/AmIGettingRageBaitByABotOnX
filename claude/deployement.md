# Stratégie de Déploiement

## Environnements

| Env | Usage | Backend | Frontend |
|---|---|---|---|
| `local` | Développement | `http://localhost:8000` | `http://localhost:3000` |
| `production` | Public | À définir | À définir |

Pas de staging au démarrage. On itérera si le besoin se fait sentir.

---

## 1. Développement local

### Prérequis

- Python 3.12+
- Node.js 20+ (pour Nuxt)
- Docker & Docker Compose
- Git
- Clé API twitterapi.io

### Setup rapide

```bash
git clone https://github.com/<org>/amigettingragebaitbyabotonx.git
cd amigettingragebaitbyabotonx

# Config
cp .env.example .env
# → Remplir TWITTER_API_KEY et les autres valeurs

# Tout lancer
docker compose up -d
```

### Docker Compose (dev)

Services :
- **api** : FastAPI avec hot reload (volume monté)
- **frontend** : Nuxt dev server avec hot reload
- **db** : PostgreSQL 16
- **redis** : Redis 7

Le frontend et l'API sont exposés sur l'hôte pour le dev. La DB et Redis ne sont accessibles que via le réseau Docker interne.

### Sans Docker (dev backend seulement)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Sans Docker (dev frontend seulement)

```bash
cd frontend
npm install
npm run dev
```

---

## 2. Docker — Production

### Dockerfile backend

Principes :
- Multi-stage build (builder → runtime)
- Image `python:3.12-slim`
- User non-root
- Pas de sources de dev dans l'image finale
- Modèles ML téléchargés au runtime (pas dans l'image)

### Dockerfile frontend

Principes :
- Multi-stage build (node build → nginx/node serve)
- Build Nuxt en mode SSR ou static selon le choix final
- Servir via le reverse proxy

---

## 3. CI/CD — GitHub Actions

### Sur chaque PR vers main

```
├── Backend
│   ├── ruff check (lint)
│   ├── mypy (types)
│   ├── pytest (tests unitaires + intégration)
│   ├── bandit (sécurité)
│   └── pip-audit (dépendances)
├── Frontend
│   ├── eslint
│   ├── nuxt typecheck
│   └── vitest (tests)
└── Docker
    └── docker build (vérifier que ça build)
```

### Sur merge dans main

```
├── Build images Docker (backend + frontend)
├── Tag avec SHA du commit
├── Push vers GitHub Container Registry (GHCR)
├── Scan images avec trivy
└── Deploy production (manuel ou auto selon maturité)
```

---

## 4. Production

### Architecture cible (démarrage simple)

```
Internet
  │
  ▼
┌──────────┐
│ Traefik  │ ← TLS (Let's Encrypt), routing, rate limiting
└────┬─────┘
     │
     ├──► /api/*  → Backend FastAPI (conteneur)
     └──► /*      → Frontend Nuxt (conteneur)
                        │
                  ┌─────┴──────┐
                  │            │
             ┌────▼────┐ ┌────▼────┐
             │ Postgres │ │  Redis  │
             └─────────┘ └─────────┘
```

### Hébergement

Option recommandée au démarrage : **VPS** (Hetzner, Scaleway, OVH)
- Rapport coût/contrôle optimal
- Docker Compose en production (suffisant pour démarrer)
- Traefik comme reverse proxy avec TLS auto

Migration vers services managés si le trafic le justifie.

### Déploiement

Méthode simple pour démarrer :
1. SSH sur le VPS
2. `git pull` ou `docker compose pull`
3. `docker compose up -d`

À automatiser plus tard via GitHub Actions (deploy on merge).

---

## 5. Gestion des modèles ML

Les modèles ne sont PAS dans l'image Docker ni dans le repo git (trop volumineux).

### Stratégie

1. Modèles hébergés sur HuggingFace Hub
2. Script de téléchargement (`python -m app.ml.download_models`)
3. Vérification de checksum SHA256
4. Stockés dans un volume Docker persistant
5. Téléchargés une seule fois, mis à jour manuellement

```yaml
# docker-compose.yml
volumes:
  model-cache:

services:
  api:
    volumes:
      - model-cache:/app/models
```

---

## 6. Base de données

### Migrations

- Alembic pour les migrations de schéma
- Migrations versionnées dans le repo
- Appliquées automatiquement au démarrage du conteneur (ou via script)
- Chaque migration doit être réversible

### Backups

- Backup quotidien automatisé (pg_dump)
- Stocké hors du VPS (object storage ou transfert distant)
- Rétention : 30 jours
- Test de restauration mensuel

---

## 7. Monitoring

### Essentiels

- **Health check** : `GET /health` vérifie DB + Redis + modèles chargés
- **Logs** : stdout structuré JSON, collecté par Docker
- **Métriques basiques** : temps de réponse, taux d'erreur, usage API twitterapi.io

### Nice to have (plus tard)

- Prometheus + Grafana
- Alerting (erreur rate, latence, disk)
- Dashboard d'usage de l'API twitterapi.io (pour surveiller les quotas)

---

## 8. Rollback

- Chaque image est taguée avec le SHA du commit
- Rollback = `docker compose pull` avec le tag du commit précédent
- Migrations DB réversibles via Alembic downgrade
- En cas de migration destructive : déployer en 2 phases

---

## 9. Checklist pré-production

- [ ] `.env` de production configuré
- [ ] HTTPS actif avec certificat valide
- [ ] CORS limité au domaine de production
- [ ] Rate limiting actif et testé
- [ ] Backups DB automatisés et testés
- [ ] Modèles ML téléchargés et vérifiés
- [ ] Logs en mode production (pas de debug)
- [ ] Health check fonctionnel
- [ ] Clé API twitterapi.io sécurisée
- [ ] `SECURITY.md` publié
