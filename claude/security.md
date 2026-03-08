# Security Practices

## Contexte

Projet open source, app web publique sans authentification utilisateur.
Les risques principaux : abus de l'API, SSRF via les URLs Twitter, fuite de clés API, et exposition de données tierces.

---

## 1. Gestion des secrets

### Règles

- **Aucun secret dans le code source ou l'historique git**
- Variables d'environnement pour toute configuration sensible
- `.env` dans `.gitignore`, `.env.example` fourni avec des placeholders

### Secrets du projet

| Secret | Rôle |
|---|---|
| `TWITTER_API_KEY` | Clé d'accès twitterapi.io |
| `DATABASE_URL` | Connexion PostgreSQL |
| `REDIS_URL` | Connexion Redis |
| `SECRET_KEY` | Signature interne (CSRF, etc.) |

### Outillage

- Pre-commit hook avec `detect-secrets` ou `gitleaks` pour bloquer les commits contenant des secrets
- `python-dotenv` pour le chargement en dev
- En production : secrets injectés via l'environnement du provider (Docker secrets, variables d'env du VPS)

---

## 2. Sécurité API

### Rate limiting (critique)

L'app est publique sans auth, le rate limiting est la première ligne de défense.

| Endpoint | Limite | Par |
|---|---|---|
| `/api/analyze` | 10 req/min | IP |
| `/api/account/{id}` | 30 req/min | IP |
| `/api/graph/*` | 20 req/min | IP |
| Global | 100 req/min | IP |

Implémentation : `slowapi` (basé sur `limits`) avec backend Redis.

### Validation des entrées

- Validation stricte des URLs Twitter soumises via Pydantic :
  - Doit matcher le pattern `https://(twitter.com|x.com)/[a-zA-Z0-9_]+`
  - Rejet de tout autre format
- Taille max du body : 1 KB (on ne reçoit qu'une URL)
- Pas d'injection SQL possible : ORM SQLAlchemy avec requêtes paramétrées exclusivement

### SSRF (Server-Side Request Forgery)

L'app fait des requêtes sortantes vers twitterapi.io. Risques :
- L'URL soumise est validée côté serveur (pattern matching strict) avant toute requête
- Les requêtes sortantes ne ciblent QUE l'API twitterapi.io, jamais l'URL soumise directement
- Timeout de 10s sur les requêtes sortantes
- Pas de redirection automatique suivie

### Headers de sécurité

Middleware FastAPI appliquant sur toutes les réponses :
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (prod)
- `Content-Security-Policy` adapté au frontend

### CORS

- Dev : `localhost:3000` (Nuxt dev server)
- Prod : domaine de production uniquement
- Jamais de wildcard `*`

---

## 3. Sécurité des données

### Données manipulées

L'app ne collecte **aucune donnée utilisateur**. Les seules données stockées sont :
- Données publiques de comptes Twitter (bio, tweets publics, follows publics)
- Scores d'analyse calculés par l'app
- Graphe social reconstitué à partir de données publiques

### Conformité RGPD

- Les données Twitter sont publiques mais restent des données personnelles au sens RGPD
- Prévoir un mécanisme de suppression sur demande (si le propriétaire d'un compte demande le retrait)
- Pas de tracking, pas de cookies analytics, pas de fingerprinting
- Mentions légales avec base légale du traitement (intérêt légitime / recherche)

### Rétention

- Données de profil : mises à jour à chaque nouvelle analyse, pas de versionning historique
- Scores : conservés (historique des analyses)
- Logs serveur : rétention 30 jours max

---

## 4. Sécurité du pipeline ML

- Modèles chargés depuis HuggingFace Hub uniquement
- Vérification des checksums SHA256 au téléchargement
- Format `safetensors` préféré (pas de pickle qui permet l'exécution de code arbitraire)
- Input sanitization avant passage au modèle : longueur max, encoding UTF-8 validé
- Timeout sur les inférences (30s max par analyse complète)

---

## 5. Dépendances

- Versions pinnées dans `pyproject.toml` (ou `requirements.txt`)
- `pip-audit` dans la CI pour détecter les vulnérabilités connues
- Dependabot activé sur le repo GitHub
- Revue mensuelle des mises à jour de sécurité

---

## 6. Infrastructure

### Docker

- Images basées sur `python:3.12-slim` (pas de `latest`, pas de full image)
- User non-root dans les conteneurs
- Multi-stage builds
- Scan d'images avec `trivy` dans la CI

### Base de données

- Credentials dédiés (pas le superuser postgres par défaut)
- Accessible uniquement via le réseau Docker interne (pas d'exposition sur l'hôte en prod)
- Backups réguliers

### Réseau (production)

- Reverse proxy (Traefik ou nginx) devant l'app
- TLS avec Let's Encrypt
- Seuls les ports 80/443 exposés

---

## 7. CI — Checks de sécurité

```
PR ouverte
  ├── gitleaks (secrets dans le code)
  ├── bandit (analyse statique sécurité Python)
  ├── pip-audit (vulnérabilités dépendances)
  ├── trivy (scan image Docker)
  └── ruff (qualité de code, inclut certains checks sécu)
```

---

## 8. Clé API twitterapi.io

Point d'attention spécifique :
- La clé API est le secret le plus sensible du projet (accès payant, quota limité)
- Ne jamais l'exposer côté client (toutes les requêtes passent par le backend)
- Monitoring de l'usage pour détecter les abus
- Avoir un mécanisme de rotation de clé sans downtime

---

## 9. Responsible Disclosure

Ajouter un `SECURITY.md` à la racine du repo :
- Email de contact pour signaler des vulnérabilités
- Délai de réponse : 72h
- Politique de disclosure : 90 jours
- Scope : application web + API + infrastructure
