#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE. Copy .env.production.example and fill deployment values first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
umask 077
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
destination="$BACKUP_DIR/postgres_${POSTGRES_DB}_${timestamp}.sql.gz"

APP_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/compose.production.yaml" exec -T db \
  pg_dump --format=plain --no-owner --no-privileges --username "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip -9 > "$destination"

gzip -t "$destination"
echo "Backup created and verified: $destination"
