# Suivi des tâches

> Détail complet avec cases à cocher : voir [`technical-tasks.md`](./technical-tasks.md)

## Phase 1 — Fondations

Setup du projet, structure de code, infrastructure de base.

| # | Tâche | Statut | Notes |
|---|---|---|---|
| 1.1 | Initialiser le repo (pyproject.toml, structure dossiers) | ✅ Terminé | |
| 1.2 | Configuration applicative (pydantic-settings) | ✅ Terminé | |
| 1.3 | Entrypoint FastAPI + middleware de sécurité | ✅ Terminé | |
| 1.4 | Couche exceptions et gestion d'erreurs | ✅ Terminé | |
| 1.5 | Setup PostgreSQL + SQLAlchemy async | ✅ Terminé | |
| 1.6 | Modèles de base de données | ✅ Terminé | |
| 1.7 | Alembic + migration initiale | ✅ Terminé | |
| 1.8 | Setup Redis | ✅ Terminé | |
| 1.9 | Injection de dépendances | ✅ Terminé | |
| 1.10 | Endpoint /health | ✅ Terminé | |
| 1.11 | Docker Compose dev | ✅ Terminé | |
| 1.12 | CI GitHub Actions (PR) | ✅ Terminé | |
| 1.13 | Pre-commit hooks (compléter) | ✅ Terminé | |
| 1.14 | Initialiser le projet Nuxt 3 (frontend/) | ✅ Terminé | |
| 1.15 | Setup tests (backend) | ✅ Terminé | |

## Phase 2 — Intégration Twitter

Connexion à twitterapi.io et fetch des données.

| # | Tâche | Statut | Notes |
|---|---|---|---|
| 2.1 | Interface TwitterClient (port ABC) | ✅ Terminé | |
| 2.2 | Mock TwitterClient | ✅ Terminé | Fallback quand aucune config |
| 2.3 | Client twitterapi.io réel | ✅ Terminé | Priorité 1 si API key configurée |
| 2.4 | Validation d'URL Twitter (schema Pydantic) | ✅ Terminé | |
| 2.5 | Endpoint POST /api/v1/analyze | ✅ Terminé | |
| 2.6 | Service d'analyse (use case) | ✅ Terminé | |
| 2.7 | Repository pattern pour les comptes | ✅ Terminé | |
| 2.8 | Gestion du cache d'analyse (Redis, TTL 7j) | ✅ Terminé | |
| 2.9 | Client Twikit (gratuit, login-based) | ✅ Terminé | Priorité 2, alternative gratuite |

## Phase 3 — Pipeline ML

Recherche, intégration et scoring des modèles.

| # | Tâche | Statut | Notes |
|---|---|---|---|
| 3.1 | Interface Analyzer (port commun ABC) | ✅ Terminé | `AnalysisInput`, `AnalyzerResult`, `AnalyzerInterface` |
| 3.2 | Pipeline ML (orchestrateur) | ✅ Terminé | Parallel + timeouts + fault tolerance |
| 3.3 | Recherche + intégration : détection texte IA | ✅ Terminé | opus-mt-fr-en + roberta-ai-detection |
| 3.4 | Recherche + intégration : sentiment analysis | ✅ Terminé | camembert-base-tweet-sentiment-fr |
| 3.5 | Module : patterns comportementaux (heuristiques) | ✅ Terminé | 5 signaux heuristiques |
| 3.6 | Module : virage politique opportuniste | ✅ Terminé | politics-sentence-classifier + rolling window |
| 3.7 | Module : analyse réseau | ✅ Terminé | DB lookup + suspect detection |
| 3.8 | Script de téléchargement des modèles | ✅ Terminé | safetensors only, CLI idempotent |

## Phase 4 — Frontend

Interface utilisateur avec Vue/Nuxt SSR.

| # | Tâche | Statut | Notes |
|---|---|---|---|
| 4.1 | Layout et design system | ⬜ À faire | CSS framework à choisir |
| 4.2 | Page d'accueil (input URL) | ⬜ À faire | |
| 4.3 | Page résultat (score + détails) | ⬜ À faire | |
| 4.4 | Composable API (useApi, useAnalysis) | ⬜ À faire | |
| 4.5 | Tests frontend (vitest) | ⬜ À faire | |

## Phase 5 — Graphe social

Analyse réseau et cross-référencement.

| # | Tâche | Statut | Notes |
|---|---|---|---|
| 5.1 | Stocker les follows niveau 1 | ⬜ À faire | |
| 5.2 | Endpoint API graphe social | ⬜ À faire | |
| 5.3 | Détection de clusters | ⬜ À faire | |
| 5.4 | Configuration profondeur du graphe | ⬜ À faire | |

## Phase 6 — Production

Déploiement et hardening.

| # | Tâche | Statut | Notes |
|---|---|---|---|
| 6.1 | Dockerfile production (backend multi-stage) | ⬜ À faire | |
| 6.2 | Dockerfile production (frontend) | ⬜ À faire | |
| 6.3 | Docker Compose production (avec Traefik) | ⬜ À faire | |
| 6.4 | CI/CD : build + push images (GHCR) | ⬜ À faire | |
| 6.5 | Backups DB automatisés | ⬜ À faire | |
| 6.6 | Monitoring et health check | ⬜ À faire | |
| 6.7 | Mentions légales et RGPD | ⬜ À faire | |

---

## Légende

- ⬜ À faire
- 🔄 En cours
- ✅ Terminé
- ❌ Abandonné
- ⏸️ En pause
