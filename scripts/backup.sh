#!/usr/bin/env bash
# ===========================================
# Database backup script
# ===========================================
# Intended for crontab: 0 3 * * * /path/to/scripts/backup.sh
#
# Restore procedure:
#   gunzip < backups/amirb_db_2025-01-01_030000.sql.gz | \
#     docker compose -f docker-compose.prod.yml exec -T db \
#     psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
# ===========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
RETENTION_DAYS=30

# Load env vars
if [ -f "${PROJECT_DIR}/.env.prod" ]; then
    set -a
    # shellcheck source=/dev/null
    source "${PROJECT_DIR}/.env.prod"
    set +a
fi

POSTGRES_USER="${POSTGRES_USER:-amirb}"
POSTGRES_DB="${POSTGRES_DB:-amirb_db}"
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date -Iseconds)] Starting backup of ${POSTGRES_DB}..."

docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl \
    | gzip > "$BACKUP_FILE"

echo "[$(date -Iseconds)] Backup saved: ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"

# Purge backups older than retention period
DELETED=$(find "$BACKUP_DIR" -name "*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date -Iseconds)] Purged ${DELETED} backup(s) older than ${RETENTION_DAYS} days"
fi

echo "[$(date -Iseconds)] Backup complete."
