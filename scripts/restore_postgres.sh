#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: RESTORE_CONFIRM=RESTORE-<database> $0 backups/file.sql.gz" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"
BACKUP_FILE="$1"

if [[ ! -f "$ENV_FILE" || ! -f "$BACKUP_FILE" ]]; then
  echo "Environment file or backup file is missing." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ "${RESTORE_CONFIRM:-}" != "RESTORE-${POSTGRES_DB}" ]]; then
  echo "Restore refused. Set RESTORE_CONFIRM=RESTORE-${POSTGRES_DB}." >&2
  exit 1
fi

gzip -t "$BACKUP_FILE"
compose=(env APP_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/compose.production.yaml")
"${compose[@]}" stop web worker beat
"${compose[@]}" exec -T db dropdb --if-exists --force --username "$POSTGRES_USER" "$POSTGRES_DB"
"${compose[@]}" exec -T db createdb --username "$POSTGRES_USER" --owner "$POSTGRES_USER" "$POSTGRES_DB"
gunzip -c "$BACKUP_FILE" | "${compose[@]}" exec -T db psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=on
"${compose[@]}" up -d web worker beat
echo "Restore completed. Check /health/ready/ and run a purchase smoke test."
