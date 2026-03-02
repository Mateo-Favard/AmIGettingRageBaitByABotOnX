# Découpe Technique — Am I Getting Rage Bait by a Bot on X?

## Récap des choix validés

| Décision | Choix |
|---|---|
| Scope | Planification complète (6 phases), implémentation phase par phase |
| API Twitter | Pas de clé encore → mock des appels |
| Git workflow | Git Flow (main + develop + feature branches) |
| Tests | Unit + Integration dès la Phase 1 |
| Architecture backend | Hexagonale légère (domain / infrastructure / api) |
| Pipeline ML | Interface commune, modules indépendants, tolérant aux pannes |
| DB isolation | Un user applicatif avec droits limités |
| Frontend | Nuxt 3 SSR |
| Docker dev | Tout dans Docker (un seul `docker compose up`) |
| Secrets | .env + gitleaks (déjà configuré en pre-commit) |
| Cache analyse | TTL 7 jours, refresh forcé possible |
| API versioning | /api/v1/ |
| Admin | Pas pour l'instant |
| Hosting | Plus tard (Phase 6) |

---

## User Stories validées

### US ML Pipeline
- **US-ML-01** : En tant que système, je peux exécuter chaque analyseur indépendamment via une interface commune `analyze(data) -> Score`
- **US-ML-02** : En tant que système, je peux ajouter/retirer un analyseur sans toucher aux autres modules
- **US-ML-03** : En tant que système, le pipeline ML a un timeout global et par analyseur
- **US-ML-04** : En tant que système, si un analyseur échoue, les autres continuent et le score s'adapte

### US Frontend
- **US-FE-01** : En tant qu'utilisateur, je colle une URL Twitter et je lance l'analyse en un clic
- **US-FE-02** : En tant qu'utilisateur, je vois un état de chargement clair pendant l'analyse
- **US-FE-03** : En tant qu'utilisateur, je vois le score composite + détail par signal sur la page résultat
- **US-FE-04** : En tant qu'utilisateur, je vois la carte de profil du compte analysé
- **US-FE-05** : En tant qu'utilisateur, je peux partager le lien d'un résultat d'analyse
- **US-FE-06** : En tant qu'utilisateur sur mobile, l'interface est utilisable et lisible

### US Backend / API
- **US-API-01** : En tant qu'utilisateur, je soumets une URL Twitter/X et reçois un score d'analyse
- **US-API-02** : En tant que système, je valide strictement l'URL (pattern twitter.com/x.com)
- **US-API-03** : En tant que système, je cache les résultats d'analyse récents (TTL 7 jours)
- **US-API-04** : En tant que système, je rate-limite les requêtes par IP (10 req/min sur /analyze)
- **US-API-05** : En tant que système, je stocke le profil, les tweets et les scores en base
- **US-API-06** : En tant que système, les appels à twitterapi.io ont un timeout et retry avec backoff
- **US-API-07** : En tant que système, je ne suis jamais de redirection sur les requêtes sortantes (anti-SSRF)

### US Graphe Social
- **US-GR-01** : En tant que système, je stocke les follows niveau 1 d'un compte analysé
- **US-GR-02** : En tant qu'utilisateur, je vois si le compte analysé est lié à d'autres comptes déjà en base
- **US-GR-03** : En tant que système, je détecte les clusters de comptes rage bait interconnectés
- **US-GR-04** : En tant que système, la profondeur du graphe est configurable (défaut: niveau 1)

### US Infra / CI/CD
- **US-INFRA-01** : En tant que dev, je lance tout l'env de dev avec un seul `docker compose up`
- **US-INFRA-02** : En tant que dev, chaque PR déclenche lint + tests + scan sécurité automatiquement
- **US-INFRA-03** : En tant que dev, un merge sur main build et push les images Docker vers GHCR
- **US-INFRA-04** : En tant qu'ops, le rollback se fait en changeant le tag Docker
- **US-INFRA-05** : En tant qu'ops, les backups DB sont automatisés quotidiennement
- **US-INFRA-06** : En tant que système, un endpoint /health vérifie DB + Redis + modèles ML

### US RGPD
- **US-RGPD-01** : En tant que propriétaire d'un compte analysé, je peux demander la suppression de mes données
- **US-RGPD-02** : En tant qu'utilisateur, je vois les mentions légales et la base juridique du traitement
- **US-RGPD-03** : En tant que système, aucun cookie de tracking ou analytics n'est utilisé

---

## Phase 1 — Fondations

### Checklist Phase 1

- [x] **T1.1** — Initialiser le projet Python (backend)
- [x] **T1.2** — Configuration applicative (pydantic-settings)
- [x] **T1.3** — Entrypoint FastAPI + middleware de sécurité
- [x] **T1.4** — Couche exceptions et gestion d'erreurs
- [x] **T1.5** — Setup PostgreSQL + SQLAlchemy async
- [x] **T1.6** — Modèles de base de données
- [x] **T1.7** — Alembic + migration initiale
- [x] **T1.8** — Setup Redis
- [x] **T1.9** — Injection de dépendances
- [x] **T1.10** — Endpoint /health
- [x] **T1.11** — Docker Compose dev
- [x] **T1.12** — CI GitHub Actions (PR)
- [x] **T1.13** — Pre-commit hooks (compléter)
- [x] **T1.14** — Initialiser le projet Nuxt 3
- [x] **T1.15** — Setup tests (backend)

> **Progression** : 15/15 — **Branche** : `feature/phase-1-foundations`

---

### T1.1 — Initialiser le projet Python (backend)

**US** : US-INFRA-01
**Fichiers** : `backend/pyproject.toml`, `backend/app/__init__.py`

**Tâches** :
- Créer `backend/pyproject.toml` avec :
  - Metadata projet (name, version, description, license MIT)
  - Dépendances runtime : `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `redis[hiredis]`, `httpx`, `slowapi`
  - Dépendances dev : `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (pour TestClient), `ruff`, `mypy`, `bandit`, `pip-audit`, `factory-boy`
  - Configuration ruff (line-length=88, target-version="py312", select rules)
  - Configuration mypy (strict mode)
  - Configuration pytest (asyncio_mode="auto", testpaths)
- Créer l'arborescence de dossiers vide avec `__init__.py`
- **NE PAS** inclure de dépendance ML à ce stade

**Clean Code** :
- Versions pinnées avec `>=X.Y,<X+1` (pas de `*`)
- Séparer les dépendances dev dans `[project.optional-dependencies]`

**Sécurité** :
- Pas de dépendance inutile
- `bandit` et `pip-audit` présents dès le jour 1

---

### T1.2 — Configuration applicative (pydantic-settings)

**US** : US-API-02, US-API-07
**Fichiers** : `backend/app/config.py`
**Principe SOLID** : Single Responsibility — un seul endroit pour toute la config

**Tâches** :
- Classe `Settings(BaseSettings)` avec :
  - `environment: Literal["development", "testing", "production"]`
  - `debug: bool = False`
  - `secret_key: SecretStr` (type SecretStr pour ne jamais le logger par accident)
  - `database_url: SecretStr`
  - `redis_url: str`
  - `twitter_api_key: SecretStr`
  - `cors_origins: list[str]`
  - `analysis_cache_ttl_seconds: int = 604800` (7 jours)
  - `twitter_api_timeout_seconds: int = 10`
  - `twitter_api_max_retries: int = 3`
  - `rate_limit_analyze: str = "10/minute"`
  - `rate_limit_global: str = "100/minute"`
  - `ml_inference_timeout_seconds: int = 30`
- `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)`
- Fonction `get_settings()` avec `@lru_cache` pour singleton
- Validation : interdire `debug=True` si `environment="production"`

**Sécurité** :
- `SecretStr` pour tous les secrets (empêche l'affichage dans les logs/repr)
- Validation stricte des valeurs

**Tests** :
- Test unitaire : instanciation avec valeurs valides
- Test unitaire : rejet de config invalide (debug=True en prod)

---

### T1.3 — Entrypoint FastAPI + middleware de sécurité

**US** : US-API-04, US-INFRA-06
**Fichiers** : `backend/app/main.py`, `backend/app/core/middleware.py`, `backend/app/core/security.py`
**Principe SOLID** : Open/Closed — les middlewares sont des plugins, on en ajoute sans modifier main.py

**Tâches** :
- `main.py` :
  - Créer l'app FastAPI avec `title`, `version`, `docs_url=None` en prod, `redoc_url=None` en prod
  - Lifespan handler (startup/shutdown) pour initialiser DB, Redis
  - Inclure le router v1
- `core/middleware.py` :
  - Middleware security headers (X-Content-Type-Options, X-Frame-Options, HSTS en prod)
  - CORS middleware avec origins depuis la config (jamais de wildcard)
  - Middleware request ID (générer un UUID par requête pour le tracing)
- `core/security.py` :
  - Configuration rate limiting avec `slowapi` + backend Redis
  - Limiter factory qui lit la config

**Sécurité** :
- Docs Swagger désactivées en production
- Headers de sécurité sur toutes les réponses
- CORS strictement limité
- Request ID pour traçabilité

**Tests** :
- Test intégration : vérifier que les headers de sécurité sont présents
- Test intégration : vérifier que CORS rejette les origines non autorisées

---

### T1.4 — Couche exceptions et gestion d'erreurs

**US** : US-API-01
**Fichiers** : `backend/app/core/exceptions.py`
**Principe SOLID** : Single Responsibility — chaque exception a un sens métier clair

**Tâches** :
- Hiérarchie d'exceptions métier :
  ```
  AppError (base)
  ├── ValidationError (400)
  ├── NotFoundError (404)
  ├── RateLimitError (429)
  ├── ExternalServiceError (502)
  │   └── TwitterAPIError
  └── AnalysisError (500)
      └── MLPipelineError
  ```
- Exception handlers enregistrés sur l'app FastAPI
- Les réponses d'erreur ne leak JAMAIS de détails internes en prod
- Format de réponse d'erreur uniforme : `{"error": {"code": "...", "message": "..."}}`

**Sécurité** :
- En prod : message générique, pas de stacktrace
- En dev : message détaillé pour le debug
- Logger l'erreur complète côté serveur dans tous les cas

**Tests** :
- Test unitaire : chaque exception produit le bon status code
- Test unitaire : en mode prod, le message est générique

---

### T1.5 — Setup PostgreSQL + SQLAlchemy async

**US** : US-API-05
**Fichiers** : `backend/app/infrastructure/db/session.py`, `backend/app/infrastructure/db/base.py`
**Principe SOLID** : Dependency Inversion — le domain ne dépend jamais de SQLAlchemy

**Tâches** :
- `session.py` :
  - `AsyncEngine` créé via `create_async_engine` avec pool configuré
  - `async_sessionmaker` pour les sessions
  - `get_db_session()` async generator pour l'injection de dépendances
  - Pool : `pool_size=5`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`
- `base.py` :
  - `Base = declarative_base()` avec mixin commun :
    - `id: UUID` (PK, généré côté app avec `uuid4`, jamais auto-increment)
    - `created_at: datetime` (UTC, default=now)
    - `updated_at: datetime` (UTC, onupdate=now)

**Sécurité** :
- UUID au lieu d'auto-increment (pas d'énumération possible)
- Timestamps en UTC systématiquement
- Pool avec timeout pour éviter les connexions pendantes

**Tests** :
- Test intégration : connexion à la DB de test
- Test intégration : création et lecture d'un enregistrement

---

### T1.6 — Modèles de base de données

**US** : US-API-05, US-GR-01
**Fichiers** : `backend/app/infrastructure/db/models.py`

**Tâches** :
- Modèle `TwitterAccount` :
  - `handle: str` (unique, indexed, validé)
  - `display_name: str | None`
  - `bio: str | None`
  - `profile_image_url: str | None`
  - `followers_count: int`
  - `following_count: int`
  - `tweets_count: int`
  - `account_created_at: datetime | None`
  - `last_fetched_at: datetime`
- Modèle `Tweet` :
  - `twitter_id: str` (unique, l'ID Twitter du tweet)
  - `account_id: UUID` (FK → TwitterAccount)
  - `content: str`
  - `posted_at: datetime`
  - `likes_count: int`
  - `retweets_count: int`
  - `replies_count: int`
- Modèle `AnalysisResult` :
  - `account_id: UUID` (FK → TwitterAccount)
  - `composite_score: float` (0-100)
  - `ai_content_score: float | None`
  - `behavioral_score: float | None`
  - `sentiment_score: float | None`
  - `political_shift_score: float | None`
  - `network_score: float | None`
  - `details: dict` (JSONB — détails bruts de chaque analyseur)
  - `model_versions: dict` (JSONB — versions des modèles utilisés pour reproductibilité)
  - `analyzed_at: datetime`
- Modèle `SocialRelation` :
  - `source_account_id: UUID` (FK)
  - `target_account_id: UUID` (FK)
  - `relation_type: str` ("follows")
  - Contrainte unique sur (source, target, relation_type)

**Clean Code** :
- Chaque modèle dans un fichier séparé si ça grossit, sinon un seul `models.py`
- Relations SQLAlchemy explicites avec `back_populates`
- Index sur les colonnes fréquemment requêtées (handle, account_id, analyzed_at)

**Sécurité** :
- Pas de données sensibles utilisateur dans ces modèles
- JSONB pour les détails (pas de colonnes dynamiques)

---

### T1.7 — Alembic + migration initiale

**US** : US-API-05
**Fichiers** : `backend/migrations/`, `backend/alembic.ini`

**Tâches** :
- `alembic init migrations` avec config async
- `alembic.ini` : lire `DATABASE_URL` depuis les variables d'env (pas en dur)
- `migrations/env.py` : configurer pour SQLAlchemy async + importer les modèles
- Générer la migration initiale avec les 4 tables
- Vérifier que la migration est réversible (downgrade)

**Sécurité** :
- `alembic.ini` ne contient PAS de credentials (lecture depuis env)
- Chaque migration doit avoir un downgrade fonctionnel

---

### T1.8 — Setup Redis

**US** : US-API-03, US-API-04
**Fichiers** : `backend/app/infrastructure/redis/client.py`

**Tâches** :
- Client Redis async avec `redis.asyncio`
- `get_redis()` async generator pour injection de dépendances
- Fonctions utilitaires :
  - `cache_get(key) -> str | None`
  - `cache_set(key, value, ttl_seconds)`
  - `cache_delete(key)`
- Health check : `ping()` qui vérifie la connexion

**Clean Code** :
- Interface (ABC) dans `domain/interfaces/` pour le cache → l'implémentation Redis est un adapteur
- Le domain ne sait pas que Redis existe

**Sécurité** :
- Timeout sur les connexions Redis (pas de hang infini)
- Pas de données sensibles en clé Redis (utiliser des hashes)

**Tests** :
- Test intégration : set/get/delete avec Redis de test
- Test unitaire : le service métier fonctionne avec un mock de cache

---

### T1.9 — Injection de dépendances

**US** : Toutes
**Fichiers** : `backend/app/dependencies.py`
**Principe SOLID** : Dependency Inversion — tout est injecté, rien n'est instancié en dur

**Tâches** :
- `get_settings() -> Settings`
- `get_db_session() -> AsyncSession`
- `get_redis() -> Redis`
- `get_twitter_client() -> TwitterClientInterface` (mock par défaut tant qu'on n'a pas de clé)
- `get_analysis_service() -> AnalysisService`
- Chaque dépendance est typée par son interface (ABC), pas par son implémentation

**Clean Code** :
- Un seul fichier pour le wiring
- Les tests peuvent override chaque dépendance individuellement

---

### T1.10 — Endpoint /health

**US** : US-INFRA-06
**Fichiers** : `backend/app/api/v1/endpoints/health.py`

**Tâches** :
- `GET /api/v1/health` retourne :
  ```json
  {
    "status": "healthy",
    "checks": {
      "database": "ok",
      "redis": "ok",
      "ml_models": "not_loaded"
    },
    "version": "0.1.0"
  }
  ```
- Chaque check est indépendant (si Redis est down, on le dit mais DB peut être ok)
- Status code 200 si tout est ok, 503 si un check critique échoue (DB)

**Tests** :
- Test intégration : /health retourne 200 quand tout est up
- Test intégration : /health retourne 503 quand la DB est down

---

### T1.11 — Docker Compose dev

**US** : US-INFRA-01
**Fichiers** : `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`

**Tâches** :
- `docker-compose.yml` avec services :
  - `api` : Python 3.12-slim, hot reload via volume monté, port 8000
  - `frontend` : Node 20-slim, hot reload via volume monté, port 3000
  - `db` : PostgreSQL 16 alpine, volume persistant, port **non exposé** sur l'hôte
  - `redis` : Redis 7 alpine, port **non exposé** sur l'hôte
- `backend/Dockerfile` (dev) :
  - Multi-stage : deps → dev
  - User non-root (`appuser`)
  - `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`
- Réseau Docker interne pour DB et Redis
- Healthcheck sur chaque service
- `.dockerignore` pour backend et frontend

**Sécurité** :
- DB et Redis non exposés sur l'hôte (accessibles uniquement via le réseau Docker)
- User non-root dans tous les conteneurs
- Pas de `privileged: true`
- Healthcheck pour que Docker redémarre les services en échec

---

### T1.12 — CI GitHub Actions (PR)

**US** : US-INFRA-02
**Fichiers** : `.github/workflows/ci.yml`

**Tâches** :
- Trigger : PR vers `develop` ou `main`
- Jobs parallèles :
  - **backend-lint** : `ruff check`, `ruff format --check`
  - **backend-types** : `mypy`
  - **backend-security** : `bandit -r backend/app`, `pip-audit`
  - **backend-tests** : `pytest` avec service containers (PostgreSQL, Redis)
  - **frontend-lint** : `eslint`
  - **frontend-types** : `nuxt typecheck`
  - **frontend-tests** : `vitest`
  - **docker-build** : vérifier que les images buildent
  - **secrets-scan** : `gitleaks detect`
- Matrice Python 3.12 / Node 20
- Cache pip et npm pour la vitesse
- Chaque job a un timeout (10 min max)

**Sécurité** :
- `permissions: contents: read` (principe du moindre privilège)
- Pas de secret exposé dans les logs
- `gitleaks` pour scanner le diff

---

### T1.13 — Pre-commit hooks (compléter)

**US** : US-INFRA-02
**Fichiers** : `.pre-commit-config.yaml`

**Tâches** :
- Déjà en place : trailing-whitespace, end-of-file, check-yaml, check-json, large files, merge conflict, no-commit-to-branch, gitleaks, ruff
- Ajouter :
  - `check-ast` (vérifie que les fichiers Python sont syntaxiquement valides)
  - `detect-private-key` (détecte les clés privées)
  - Hook mypy (optionnel, peut être lent)
- Vérifier que `no-commit-to-branch` bloque aussi `develop` (pas seulement `main`)

---

### T1.14 — Initialiser le projet Nuxt 3

**US** : US-FE-01
**Fichiers** : `frontend/`

**Tâches** :
- `npx nuxi@latest init frontend` avec TypeScript
- Configuration `nuxt.config.ts` :
  - SSR activé
  - Runtime config pour l'URL de l'API backend
  - Désactiver la télémétrie Nuxt
- ESLint + Prettier configurés
- Structure de dossiers :
  ```
  frontend/
  ├── app.vue
  ├── pages/
  │   ├── index.vue
  │   └── analysis/[id].vue
  ├── components/
  ├── composables/
  ├── layouts/
  ├── server/         # API routes Nuxt (si besoin de BFF)
  ├── public/
  ├── nuxt.config.ts
  ├── package.json
  ├── tsconfig.json
  └── Dockerfile
  ```
- `Dockerfile` dev pour le Docker Compose

**Sécurité** :
- Pas de clé API exposée côté client
- Runtime config pour les URLs (pas de valeurs en dur)
- Télémétrie désactivée

---

### T1.15 — Setup tests (backend)

**US** : Toutes
**Fichiers** : `backend/tests/conftest.py`, `backend/tests/unit/`, `backend/tests/integration/`

**Tâches** :
- `conftest.py` :
  - Fixture `app` : instance FastAPI de test avec overrides de dépendances
  - Fixture `client` : `httpx.AsyncClient` pour les tests d'intégration
  - Fixture `db_session` : session SQLAlchemy vers une DB de test (PostgreSQL dans Docker)
  - Fixture `redis_client` : connexion Redis de test (flush entre chaque test)
  - Fixture `settings` : Settings de test (environment="testing", debug=False)
- Base de test isolée : chaque test run dans une transaction qui est rollback à la fin
- Factories (factory-boy) pour les modèles de données

**Clean Code** :
- Les fixtures sont composables et indépendantes
- Pas de side effects entre les tests (isolation totale)
- Tests rapides : pas d'I/O quand c'est évitable (mocks pour les tests unitaires)

---

## Phase 2 — Intégration Twitter

### Checklist Phase 2

- [x] **T2.1** — Interface TwitterClient (port)
- [x] **T2.2** — Mock TwitterClient
- [x] **T2.3** — Client twitterapi.io réel
- [x] **T2.4** — Validation d'URL Twitter
- [x] **T2.5** — Endpoint POST /api/v1/analyze
- [x] **T2.6** — Service d'analyse (use case)
- [x] **T2.7** — Repository pattern pour les comptes
- [x] **T2.8** — Gestion du cache d'analyse
- [x] **T2.9** — Client Twikit (gratuit, login-based)

> **Progression** : 9/9 — **Branche** : `feature/phase-1-foundations`

---

### T2.1 — Interface TwitterClient (port)

**US** : US-API-01, US-ML-02
**Fichiers** : `backend/app/domain/interfaces/twitter.py`
**Principe SOLID** : Interface Segregation — l'interface expose uniquement ce dont le domain a besoin

**Tâches** :
- ABC `TwitterClientInterface` :
  - `async fetch_profile(handle: str) -> TwitterProfile`
  - `async fetch_recent_tweets(handle: str, count: int = 50) -> list[TweetData]`
  - `async fetch_following(handle: str, count: int = 200) -> list[str]`
- Dataclasses domain pour `TwitterProfile` et `TweetData` (dans `domain/models/`)
- Pas de dépendance à httpx ou twitterapi.io dans cette couche

---

### T2.2 — Mock TwitterClient

**US** : US-API-01
**Fichiers** : `backend/app/infrastructure/twitter/mock_client.py`

**Tâches** :
- Implémenter `TwitterClientInterface` avec des données fake réalistes
- Données de test variées : comptes "normaux" et comptes "suspects"
- Utilisé automatiquement quand `TWITTER_API_KEY` n'est pas configuré
- Utile pour les tests et le dev sans clé API

---

### T2.3 — Client twitterapi.io réel

**US** : US-API-06, US-API-07
**Fichiers** : `backend/app/infrastructure/twitter/api_client.py`
**Principe SOLID** : Liskov Substitution — le client réel est interchangeable avec le mock

**Tâches** :
- Implémenter `TwitterClientInterface` avec `httpx.AsyncClient`
- Configuration :
  - `timeout=10s` (depuis config)
  - `max_redirects=0` (anti-SSRF)
  - `follow_redirects=False`
  - Headers : API key dans un header sécurisé
- Retry avec backoff exponentiel (3 tentatives, backoff 1s/2s/4s)
- Gestion des erreurs API : mapper vers `TwitterAPIError` avec contexte
- Logger chaque appel (sans logger la clé API)

**Sécurité** :
- `follow_redirects=False` (SSRF)
- Timeout strict
- Clé API dans un header, jamais dans l'URL
- Pas de log de la clé API (utiliser `SecretStr`)

**Tests** :
- Test unitaire : retry fonctionne sur erreur 5xx
- Test unitaire : timeout est respecté
- Test unitaire : les redirections sont rejetées

---

### T2.4 — Validation d'URL Twitter

**US** : US-API-02
**Fichiers** : `backend/app/api/v1/schemas/analyze.py`

**Tâches** :
- Schema Pydantic `AnalyzeRequest` :
  - `url: str` avec validateur custom
  - Pattern strict : `^https?://(twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})$`
  - Extraction du handle depuis l'URL
  - Rejet de tout ce qui ne match pas (pas de query params, pas de paths supplémentaires)
  - Taille max du body : vérifiée via middleware (1 KB)

**Sécurité** :
- Validation whitelist (on accepte uniquement ce qu'on connaît)
- Pas de regex catastrophique (backtracking)
- Le handle est re-validé après extraction

**Tests** :
- Test unitaire : URLs valides acceptées (twitter.com, x.com, avec/sans https)
- Test unitaire : URLs invalides rejetées (autres domaines, paths bizarres, injection)

---

### T2.5 — Endpoint POST /api/v1/analyze

**US** : US-API-01, US-API-03, US-API-04
**Fichiers** : `backend/app/api/v1/endpoints/analyze.py`

**Tâches** :
- Endpoint `POST /api/v1/analyze` :
  1. Valider l'URL (via schema Pydantic)
  2. Extraire le handle
  3. Vérifier le cache (Redis) → si résultat < 7 jours, retourner directement
  4. Fetcher les données via `TwitterClientInterface`
  5. Stocker/mettre à jour le profil et les tweets en base
  6. Lancer le pipeline ML (Phase 3)
  7. Stocker le résultat d'analyse
  8. Mettre en cache
  9. Retourner le résultat
- Paramètre query optionnel `?force=true` pour bypasser le cache
- Rate limiting : `10/minute` par IP
- Response schema avec score composite et détails

**Clean Code** :
- L'endpoint est mince : il délègue à un service (use case)
- Pas de logique métier dans l'endpoint

---

### T2.6 — Service d'analyse (use case)

**US** : US-API-01, US-API-03
**Fichiers** : `backend/app/domain/services/analysis.py`
**Principe SOLID** : Single Responsibility — orchestration du flux d'analyse uniquement

**Tâches** :
- Classe `AnalysisService` :
  - Injecte : `TwitterClientInterface`, `AccountRepository`, `CacheInterface`, `MLPipeline`
  - Méthode `async analyze(handle: str, force_refresh: bool = False) -> AnalysisResult`
  - Orchestre le flux : cache check → fetch → store → ML → store result → cache set
- Le service ne connaît PAS les détails d'implémentation (pas de Redis, pas de SQLAlchemy)

---

### T2.7 — Repository pattern pour les comptes

**US** : US-API-05
**Fichiers** : `backend/app/domain/interfaces/repositories.py`, `backend/app/infrastructure/db/repositories/account.py`
**Principe SOLID** : Dependency Inversion — le domain définit l'interface, l'infra l'implémente

**Tâches** :
- ABC `AccountRepositoryInterface` :
  - `async get_by_handle(handle: str) -> Account | None`
  - `async upsert(account: Account) -> Account`
  - `async save_tweets(account_id: UUID, tweets: list[Tweet]) -> None`
  - `async save_analysis(result: AnalysisResult) -> None`
  - `async get_latest_analysis(account_id: UUID) -> AnalysisResult | None`
- Implémentation SQLAlchemy dans `infrastructure/db/repositories/`
- Mapping entre modèles domain et modèles ORM explicite (pas de couplage)

---

### T2.8 — Gestion du cache d'analyse

**US** : US-API-03
**Fichiers** : `backend/app/domain/interfaces/cache.py`, intégration dans le service

**Tâches** :
- ABC `CacheInterface` :
  - `async get_analysis(handle: str) -> AnalysisResult | None`
  - `async set_analysis(handle: str, result: AnalysisResult, ttl: int) -> None`
  - `async invalidate(handle: str) -> None`
- Implémentation Redis avec sérialisation JSON
- Clé : `analysis:{handle}` (pas de données sensibles dans la clé)
- TTL 7 jours par défaut (configurable)

---

### T2.9 — Client Twikit (gratuit, login-based)

**US** : US-API-01, US-API-06
**Fichiers** : `backend/app/infrastructure/twitter/twikit_client.py`, `backend/app/config.py`, `backend/app/dependencies.py`
**Principe SOLID** : Liskov Substitution — TwikitClient est interchangeable avec les autres clients

**Tâches** :
- Implémenter `TwitterClientInterface` avec la lib `twikit` (API interne Twitter)
- Login via username/email/password (pas de clé API)
- Persistance des cookies pour éviter le re-login à chaque requête
- Mapping des objets twikit vers les modèles domain (TwitterProfile, TweetData)
- Wrapping des exceptions en `TwitterAPIError`
- Sélection automatique dans `dependencies.py` : API key → Twikit → Mock
- 3 champs `SecretStr` dans Settings : `twitter_username`, `twitter_email`, `twitter_password`

**Limitations** :
- 1 session = 1 compte Twitter (pas de pool)
- ~50-100 req/15min avant rate limit
- Lock de compte possible si surutilisation

**Tests** :
- 12 tests unitaires avec mock de `twikit.Client`
- Mapping, cookies, login, wrapping erreurs

---

## Phase 3 — Pipeline ML

### Checklist Phase 3

- [ ] **T3.1** — Interface Analyzer (port commun)
- [ ] **T3.2** — Pipeline ML (orchestrateur)
- [ ] **T3.3** — Recherche et intégration : détection texte IA
- [ ] **T3.4** — Recherche et intégration : sentiment analysis
- [ ] **T3.5** — Module : patterns comportementaux
- [ ] **T3.6** — Module : virage politique opportuniste
- [ ] **T3.7** — Module : analyse réseau
- [ ] **T3.8** — Script de téléchargement des modèles

> **Progression** : 0/8 — **Branche** : `feature/phase-3-ml-pipeline`

---

### T3.1 — Interface Analyzer (port commun)

**US** : US-ML-01, US-ML-02
**Fichiers** : `backend/app/domain/interfaces/analyzer.py`
**Principe SOLID** : Open/Closed — ajouter un analyseur = ajouter une classe, pas modifier le pipeline

**Tâches** :
- ABC `AnalyzerInterface` :
  ```python
  class AnalyzerInterface(ABC):
      @property
      @abstractmethod
      def name(self) -> str: ...

      @property
      @abstractmethod
      def version(self) -> str: ...

      @abstractmethod
      async def analyze(self, data: AnalysisInput) -> AnalyzerResult: ...

      @abstractmethod
      async def health_check(self) -> bool: ...
  ```
- Dataclass `AnalysisInput` : profil + tweets + follows
- Dataclass `AnalyzerResult` : score (0-100), confidence (0-1), details (dict)

---

### T3.2 — Pipeline ML (orchestrateur)

**US** : US-ML-03, US-ML-04
**Fichiers** : `backend/app/infrastructure/ml/pipeline.py`

**Tâches** :
- Classe `MLPipeline` :
  - Enregistre une liste d'`AnalyzerInterface`
  - `async run(data: AnalysisInput) -> CompositeScore`
  - Exécute tous les analyseurs en parallèle (`asyncio.gather`)
  - Timeout global configurable (30s)
  - Timeout par analyseur (10s)
  - Si un analyseur échoue : log l'erreur, continue avec les autres
  - Score composite = moyenne pondérée des scores disponibles
  - Retourne aussi les versions des modèles utilisés

**Clean Code** :
- Le pipeline ne connaît pas les analyseurs concrets
- Pondération configurable (dict de poids par nom d'analyseur)
- Logging structuré de chaque étape

---

### T3.3 — Recherche et intégration : détection texte IA

**US** : US-ML-01
**Fichiers** : `backend/app/infrastructure/ml/analyzers/ai_content.py`

**Tâches** :
- Rechercher les meilleurs modèles francophones de détection de texte IA sur HuggingFace
- Implémenter `AIContentAnalyzer(AnalyzerInterface)`
- Input : liste de tweets (texte)
- Output : score de probabilité que le contenu soit généré par IA
- Fallback : heuristiques simples (perplexité, diversité vocabulaire) si pas de modèle satisfaisant

---

### T3.4 — Recherche et intégration : sentiment analysis

**US** : US-ML-01
**Fichiers** : `backend/app/infrastructure/ml/analyzers/sentiment.py`

**Tâches** :
- Rechercher modèles de sentiment analysis francophones (CamemBERT-based)
- Implémenter `SentimentAnalyzer(AnalyzerInterface)`
- Analyser le ton des tweets : inflammatoire, neutre, constructif
- Score : proportion de tweets excessivement inflammatoires
- Détection de l'absence de contenu neutre/personnel

---

### T3.5 — Module : patterns comportementaux

**US** : US-ML-01
**Fichiers** : `backend/app/infrastructure/ml/analyzers/behavioral.py`

**Tâches** :
- Implémenter `BehavioralAnalyzer(AnalyzerInterface)` — heuristiques, pas de ML
- Signaux :
  - Ratio followers/following anormal
  - Âge du compte vs volume de posts
  - Régularité suspecte de publication (écart-type des intervalles)
  - Horaires de publication (activité 24/7 = suspect)
  - Taux d'engagement vs followers
- Chaque signal produit un sous-score, agrégé en score global

---

### T3.6 — Module : virage politique opportuniste

**US** : US-ML-01
**Fichiers** : `backend/app/infrastructure/ml/analyzers/political_shift.py`

**Tâches** :
- Implémenter `PoliticalShiftAnalyzer(AnalyzerInterface)`
- Analyse temporelle des thématiques
- Détection de changement brusque de ton/sujet
- Corrélation avec les sujets "trending" au moment du tweet
- Modèle potentiel : topic modeling (LDA ou BERTopic)

---

### T3.7 — Module : analyse réseau

**US** : US-ML-01, US-GR-03
**Fichiers** : `backend/app/infrastructure/ml/analyzers/network.py`

**Tâches** :
- Implémenter `NetworkAnalyzer(AnalyzerInterface)`
- Input : follows + comptes déjà analysés en base
- Signaux :
  - Proportion de follows qui sont des comptes rage bait connus
  - Participation à un cluster détecté
  - Suivre beaucoup de comptes eux-mêmes suspects

---

### T3.8 — Script de téléchargement des modèles

**US** : US-ML-01
**Fichiers** : `backend/app/infrastructure/ml/download.py`

**Tâches** :
- CLI : `python -m app.infrastructure.ml.download`
- Télécharge les modèles depuis HuggingFace Hub
- Vérifie les checksums SHA256
- Stocke dans le volume Docker `/app/models`
- Refuse les formats pickle (seulement safetensors/ONNX)
- Affiche la progression

**Sécurité** :
- Checksum obligatoire
- Format safetensors uniquement (pas de pickle = pas d'exécution de code arbitraire)
- Timeout sur le téléchargement

---

## Phase 4 — Frontend

### Checklist Phase 4

- [ ] **T4.1** — Layout et design system
- [ ] **T4.2** — Page d'accueil (input URL)
- [ ] **T4.3** — Page résultat
- [ ] **T4.4** — Composable API
- [ ] **T4.5** — Tests frontend

> **Progression** : 0/5 — **Branche** : `feature/phase-4-frontend`

---

### T4.1 — Layout et design system

**US** : US-FE-06
**Fichiers** : `frontend/layouts/default.vue`, `frontend/assets/`

**Tâches** :
- Layout principal avec header minimal (titre + lien GitHub)
- Design system basique : couleurs, typo, espacements
- Mobile-first responsive
- Choix CSS : Tailwind CSS ou UnoCSS (à confirmer)

---

### T4.2 — Page d'accueil (input URL)

**US** : US-FE-01
**Fichiers** : `frontend/pages/index.vue`, `frontend/components/AnalyzeForm.vue`

**Tâches** :
- Champ input avec placeholder "Collez un lien Twitter/X..."
- Validation côté client (même regex que le backend)
- Bouton "Analyser"
- Au submit : appel API `POST /api/v1/analyze` → redirect vers page résultat

---

### T4.3 — Page résultat

**US** : US-FE-02, US-FE-03, US-FE-04, US-FE-05
**Fichiers** : `frontend/pages/analysis/[id].vue`

**Tâches** :
- URL : `/analysis/{account_handle}` (SEO-friendly, partageable)
- Composant `ProfileCard.vue` : photo, handle, bio, métriques
- Composant `ScoreGauge.vue` : score composite avec jauge visuelle (0-100)
- Composant `SignalBreakdown.vue` : détail par signal avec barres de progression
- Composant `TweetList.vue` : tweets analysés avec highlight des signaux détectés
- Loading state : skeleton screens pendant le chargement
- Error state : message clair si l'analyse échoue
- Meta tags pour le partage social (Open Graph, titre avec le score)

---

### T4.4 — Composable API

**US** : US-FE-01
**Fichiers** : `frontend/composables/useApi.ts`, `frontend/composables/useAnalysis.ts`

**Tâches** :
- `useApi()` : wrapper fetch avec base URL depuis runtime config, gestion d'erreurs
- `useAnalysis()` : logique d'analyse (submit URL, poll résultat, état)
- Typage strict des réponses API

**Sécurité** :
- Pas de clé API côté client
- Sanitization des données affichées (XSS)

---

### T4.5 — Tests frontend

**US** : US-FE-01 à US-FE-06
**Fichiers** : `frontend/tests/`

**Tâches** :
- Vitest + @vue/test-utils
- Test : le formulaire valide correctement les URLs
- Test : le composant ScoreGauge affiche le bon score
- Test : le loading state s'affiche pendant le fetch
- Test : les erreurs API sont affichées proprement

---

## Phase 5 — Graphe social

### Checklist Phase 5

- [ ] **T5.1** — Stocker les follows niveau 1
- [ ] **T5.2** — Endpoint API graphe social
- [ ] **T5.3** — Détection de clusters
- [ ] **T5.4** — Configuration profondeur du graphe

> **Progression** : 0/4 — **Branche** : `feature/phase-5-social-graph`

---

### T5.1 — Stocker les follows niveau 1

**US** : US-GR-01
**Fichiers** : `backend/app/infrastructure/db/repositories/social.py`

**Tâches** :
- Repo `SocialRelationRepository` :
  - `async save_following(source_handle: str, following_handles: list[str]) -> None`
  - `async get_analyzed_connections(handle: str) -> list[AnalyzedConnection]`
- Lors de chaque analyse : stocker les follows dans `SocialRelation`
- Ne stocker que si le follow est aussi un compte analysé (ou le stocker pour futur cross-ref)

---

### T5.2 — Endpoint API graphe social

**US** : US-GR-02
**Fichiers** : `backend/app/api/v1/endpoints/graph.py`

**Tâches** :
- `GET /api/v1/graph/{handle}` : retourne les connexions connues
- Rate limiting : 20 req/min par IP
- Response : liste de comptes liés avec leur score (si analysé)

---

### T5.3 — Détection de clusters

**US** : US-GR-03
**Fichiers** : `backend/app/domain/services/cluster_detection.py`

**Tâches** :
- Algorithme de détection de communautés (composantes connexes ou Louvain simplifié)
- Identifier les groupes de comptes rage bait interconnectés
- Ajouter le résultat cluster au score réseau

---

### T5.4 — Configuration profondeur du graphe

**US** : US-GR-04
**Fichiers** : config + service

**Tâches** :
- Setting `graph_depth: int = 1` dans la config
- Le service de fetch des follows respecte cette profondeur
- Architecture modulaire pour supporter profondeur > 1 plus tard

---

## Phase 6 — Production

### Checklist Phase 6

- [ ] **T6.1** — Dockerfile production (backend)
- [ ] **T6.2** — Dockerfile production (frontend)
- [ ] **T6.3** — Docker Compose production
- [ ] **T6.4** — CI/CD : build + push images
- [ ] **T6.5** — Backups DB automatisés
- [ ] **T6.6** — Monitoring et health check
- [ ] **T6.7** — Mentions légales et RGPD

> **Progression** : 0/7 — **Branche** : `feature/phase-6-production`

---

### T6.1 — Dockerfile production (backend)

**US** : US-INFRA-03, US-INFRA-04
**Fichiers** : `backend/Dockerfile.prod`

**Tâches** :
- Multi-stage : deps → build → runtime
- Image finale : `python:3.12-slim`
- User non-root
- Pas de sources de dev
- Modèles ML téléchargés au runtime (pas dans l'image)
- Healthcheck intégré

---

### T6.2 — Dockerfile production (frontend)

**US** : US-INFRA-03
**Fichiers** : `frontend/Dockerfile.prod`

**Tâches** :
- Multi-stage : deps → build → serve
- Build Nuxt SSR
- Image finale légère (Node slim ou Alpine)

---

### T6.3 — Docker Compose production

**US** : US-INFRA-01
**Fichiers** : `docker-compose.prod.yml`

**Tâches** :
- Services : api, frontend, db, redis, traefik
- Traefik :
  - TLS auto (Let's Encrypt)
  - Routing : `/api/*` → backend, `/*` → frontend
  - Rate limiting au niveau reverse proxy aussi
- Volumes persistants pour DB et modèles ML
- Restart policy : `unless-stopped`
- Logging configuré (JSON, rotation)

---

### T6.4 — CI/CD : build + push images

**US** : US-INFRA-03
**Fichiers** : `.github/workflows/cd.yml`

**Tâches** :
- Trigger : merge sur `main`
- Build images Docker (backend + frontend)
- Tag avec SHA du commit + `latest`
- Push vers GHCR
- Scan avec `trivy`
- Notification en cas d'échec

---

### T6.5 — Backups DB automatisés

**US** : US-INFRA-05
**Fichiers** : `scripts/backup.sh`, cron ou service Docker

**Tâches** :
- Script `pg_dump` quotidien
- Compression gzip
- Transfert vers stockage distant (object storage)
- Rétention 30 jours
- Test de restauration documenté

---

### T6.6 — Monitoring et health check

**US** : US-INFRA-06
**Fichiers** : configuration Traefik + logs

**Tâches** :
- Health check Traefik sur `/api/v1/health`
- Logs structurés JSON
- Métriques basiques : latence, taux d'erreur
- Alerte si le service est down (script simple ou uptime monitoring externe)

---

### T6.7 — Mentions légales et RGPD

**US** : US-RGPD-01, US-RGPD-02, US-RGPD-03
**Fichiers** : `frontend/pages/legal.vue`, endpoint API suppression

**Tâches** :
- Page mentions légales avec :
  - Base juridique du traitement (intérêt légitime)
  - Nature des données collectées (données publiques Twitter uniquement)
  - Contact pour exercer ses droits
- Endpoint `DELETE /api/v1/account/{handle}` pour demande de suppression
  - Supprime profil, tweets, scores, relations
  - Rate limité (éviter l'abus)
  - Log de la demande
- Pas de cookies, pas de tracking, pas d'analytics

---

## Ordre d'implémentation recommandé

```
Phase 1 : T1.1 → T1.2 → T1.3 → T1.4 → T1.5 → T1.6 → T1.7 → T1.8 → T1.9 → T1.10 → T1.11 → T1.12 → T1.13 → T1.14 → T1.15
Phase 2 : T2.1 → T2.2 → T2.4 → T2.7 → T2.8 → T2.6 → T2.5 → T2.3
Phase 3 : T3.1 → T3.2 → T3.5 → T3.3 → T3.4 → T3.6 → T3.7 → T3.8
Phase 4 : T4.1 → T4.4 → T4.2 → T4.3 → T4.5
Phase 5 : T5.1 → T5.2 → T5.4 → T5.3
Phase 6 : T6.1 → T6.2 → T6.3 → T6.4 → T6.5 → T6.6 → T6.7
```

---

## Principes transversaux

### Clean Code
- Fonctions courtes (< 20 lignes idéalement)
- Nommage explicite (pas d'abréviations cryptiques)
- Pas de magic numbers (constantes nommées ou config)
- Type hints partout (mypy strict)
- Docstrings uniquement sur les interfaces publiques

### SOLID
- **S** : Chaque classe a une seule raison de changer
- **O** : Le pipeline ML est extensible sans modification (plugin pattern)
- **L** : Mock et implémentation réelle sont interchangeables
- **I** : Interfaces fines (TwitterClient ne fait pas de ML)
- **D** : Le domain ne dépend que d'abstractions

### Sécurité
- Jamais de secret dans le code ou les logs
- Validation à toutes les frontières (API input, données externes)
- Principe du moindre privilège (DB user, Docker user, CI permissions)
- Isolation réseau (DB/Redis non exposés)
- Pas de pickle, pas de eval, pas de exec
- Timeouts sur tout ce qui est externe
- Rate limiting sur tous les endpoints publics

---

## Journal de bord

> Remplir à chaque session de travail pour garder le fil.

| Date | Tâche(s) | Statut | Notes / Blockers |
|---|---|---|---|
| 2026-03-02 | Planification complète | Terminé | US validées, découpe technique faite, CLAUDE.md créé |
| 2026-03-02 | T1.1 → T1.15 (Phase 1 complète) | Terminé | 15/15. 17 tests passent. Stack Docker complet (API+Frontend+DB+Redis). /health OK. Frontend Nuxt SSR up sur :3000. |
| 2026-03-03 | T2.1 → T2.8 (Phase 2 complète) | Terminé | 8/8. 96 tests passent. Flux d'analyse complet : validation URL → fetch Twitter → scoring → cache → BDD. 3 clients : API payante, Mock. |
| 2026-03-03 | T2.9 — Client Twikit | Terminé | Alternative gratuite via login Twitter. Cookies persistés. Sélection auto : API key → Twikit → Mock. 12 tests dédiés. |
| | | | |

### Décisions prises en cours de route

> Documenter ici les décisions d'implémentation qui divergent du plan initial.

| Date | Décision | Raison |
|---|---|---|
| 2026-03-02 | `extra="ignore"` dans Settings | Le `.env` contient des vars Docker (POSTGRES_USER etc.) que pydantic ne connaît pas |
| 2026-03-02 | Lazy init pour engine/redis (lru_cache) | Éviter le chargement config au module load time, casse les tests |
| 2026-03-02 | CORS_ORIGINS en JSON dans .env | pydantic-settings v2 parse les list comme JSON, pas CSV |
| 2026-03-03 | Ajout Twikit comme client Twitter gratuit | Alternative sans clé API payante. Sélection 3 niveaux : API → Twikit → Mock. Limite : ~15-30 analyses/h (rate limit Twitter interne) |
| | | |

### Questions ouvertes

> Points à trancher plus tard.

- [ ] Choix CSS frontend : Tailwind CSS ou UnoCSS ?
- [ ] Modèle exact pour la détection de texte IA francophone
- [ ] Modèle exact pour le sentiment analysis francophone
- [ ] Nom de domaine final
- [ ] Provider VPS final (Hetzner / Scaleway / OVH)
