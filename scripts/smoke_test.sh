#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

check() {
  local label="$1"
  local url="$2"
  local code
  code="$(curl --silent --show-error --location --output /dev/null --write-out '%{http_code}' "$url")"
  if [[ "$code" != "200" ]]; then
    echo "$label failed with HTTP $code: $url" >&2
    exit 1
  fi
  echo "$label OK"
}

check "Frontend" "$FRONTEND_URL/"
check "Products" "$FRONTEND_URL/products"
check "Robots" "$FRONTEND_URL/robots.txt"
check "Sitemap" "$FRONTEND_URL/sitemap.xml"
check "Backend readiness" "$PUBLIC_BASE_URL/health/ready/"
check "Torob feed" "$PUBLIC_BASE_URL/api/v1/integrations/torob/products/?key=$TOROB_FEED_KEY&page_size=1"

echo "Smoke tests passed. Complete OTP and sandbox payment manually."
