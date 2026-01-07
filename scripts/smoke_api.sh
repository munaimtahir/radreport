#!/usr/bin/env bash
set -euo pipefail

# Simple API smoke test for RIMS production deployment
# Usage:
#   RIMS_HOST=rims.alshifalab.pk ./scripts/smoke_api.sh
# or:
#   BASE_URL=https://rims.alshifalab.pk ./scripts/smoke_api.sh

RIMS_HOST="${RIMS_HOST:-rims.alshifalab.pk}"
BASE_URL="${BASE_URL:-https://${RIMS_HOST}}"
TIMEOUT="${TIMEOUT:-8}"

echo "==> API Smoke Test against ${BASE_URL}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

curl_s() {
  curl -fsSL --max-time "${TIMEOUT}" "$@"
}

echo "-> Checking homepage..."
curl_s -I "${BASE_URL}/" | grep -i "200" >/dev/null || fail "Homepage not 200"

echo "-> Checking /api/health/ ..."
curl_s "${BASE_URL}/api/health/" | grep -q '"status": "ok"' || fail "/api/health/ did not return {status: ok}"

echo "-> Checking /api/schema/ ..."
curl_s -I "${BASE_URL}/api/schema/" | grep -i "200" >/dev/null || fail "/api/schema/ not 200"

echo "-> Checking /api/auth/token/ (should be reachable)..."
curl_s -I "${BASE_URL}/api/auth/token/" | grep -Ei "Allow:.*POST" >/dev/null || echo "WARN: /api/auth/token/ did not advertise POST (still reachable?)"

echo "-> Checking static (may be empty index) ..."
curl -fsSIL --max-time "${TIMEOUT}" "${BASE_URL}/static/" | grep -Ei "200|301|403|404" >/dev/null || echo "WARN: /static/ HEAD unexpected"

echo "-> Checking media (may be 404 if not present)..."
curl -fsSIL --max-time "${TIMEOUT}" "${BASE_URL}/media/" | grep -Ei "200|301|403|404" >/dev/null || echo "WARN: /media/ HEAD unexpected"

echo "OK: API smoke test passed."
