#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE. Copy .env.production.example and fill every placeholder." >&2
  exit 1
fi

compose=(env APP_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/compose.production.yaml")
"${compose[@]}" config --quiet
"${compose[@]}" build
"${compose[@]}" run --rm web python manage.py production_check
"${compose[@]}" up -d
"${compose[@]}" exec -T web python manage.py migrate --check
"$ROOT_DIR/scripts/smoke_test.sh"

echo "Deployment completed. Run production_check --live only after sandbox payment succeeds."
