#!/usr/bin/env bash
set -euo pipefail

# -----------------------
# Config (override via env)
# -----------------------
E2E_BASE_URL="${E2E_BASE_URL:-http://localhost:8000}"
E2E_API_BASE="${E2E_API_BASE:-$E2E_BASE_URL}"
E2E_USER="${E2E_USER:-admin@example.com}"
E2E_PASS="${E2E_PASS:-admin}"

# Optional: if your e2e suite supports seeding via a command + json output
E2E_SEED_CMD="${E2E_SEED_CMD:-}"
E2E_SEED_JSON="${E2E_SEED_JSON:-e2e/.tmp/seed.json}"

# Where to run docker compose from (repo root by default)
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-radreport}"

# Timeout for stack readiness
WAIT_SECONDS="${WAIT_SECONDS:-120}"

# -----------------------
# Helpers
# -----------------------
log() { printf "\n[%s] %s\n" "$(date +'%Y-%m-%d %H:%M:%S')" "$*"; }

mkdir -p ARTIFACTS REPORTS e2e/.tmp

# -----------------------
# Step 1: Start stack
# -----------------------
if [[ -f "$COMPOSE_FILE" ]]; then
  log "Starting Docker stack using $COMPOSE_FILE ..."
  docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" up -d --build
else
  log "No $COMPOSE_FILE found. Skipping docker compose up."
  log "If your stack is started another way, start it now and re-run this script."
fi

# -----------------------
# Step 2: Wait for base URL
# -----------------------
log "Waiting for server: $E2E_BASE_URL (timeout ${WAIT_SECONDS}s) ..."
end=$((SECONDS + WAIT_SECONDS))
ok="0"
while [[ "$SECONDS" -lt "$end" ]]; do
  if curl -fsS -o /dev/null "$E2E_BASE_URL" || curl -fsS -o /dev/null "$E2E_BASE_URL/health" || curl -fsS -o /dev/null "$E2E_API_BASE/health"; then
    ok="1"
    break
  fi
  sleep 2
done

if [[ "$ok" != "1" ]]; then
  log "Server not reachable at $E2E_BASE_URL within ${WAIT_SECONDS}s"
  log "Docker status:"
  docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" ps || true
  exit 1
fi
log "Server reachable ✅"

# -----------------------
# Step 3: Export env vars for Playwright
# -----------------------
export E2E_BASE_URL
export E2E_API_BASE
export E2E_USER
export E2E_PASS
export E2E_SEED_CMD
export E2E_SEED_JSON

log "E2E vars:"
log "  E2E_BASE_URL=$E2E_BASE_URL"
log "  E2E_API_BASE=$E2E_API_BASE"
log "  E2E_USER=$E2E_USER"
log "  E2E_SEED_JSON=$E2E_SEED_JSON"
if [[ -n "$E2E_SEED_CMD" ]]; then
  log "  E2E_SEED_CMD=$E2E_SEED_CMD"
else
  log "  E2E_SEED_CMD=(not set)"
fi

# -----------------------
# Step 4: Install node deps + Playwright browsers
# -----------------------
if [[ -f "package.json" ]]; then
  log "Installing npm deps..."
  npm install

  log "Installing Playwright browsers + deps..."
  npx playwright install --with-deps
else
  log "package.json not found at repo root."
  log "If your frontend lives in a subfolder (e.g., frontend/), run this script from that folder or modify it."
  exit 1
fi

# -----------------------
# Step 5: Optional seed step (if configured)
# -----------------------
if [[ -n "$E2E_SEED_CMD" ]]; then
  log "Running seed command..."
  # shellcheck disable=SC2086
  bash -lc "$E2E_SEED_CMD"
  if [[ ! -f "$E2E_SEED_JSON" ]]; then
    log "Seed JSON not created at $E2E_SEED_JSON"
    exit 1
  fi
  log "Seed JSON created ✅ ($E2E_SEED_JSON)"
else
  log "Skipping seed command (E2E_SEED_CMD not set)."
fi

# -----------------------
# Step 6: Run Playwright smoke + save logs
# -----------------------
log "Running Playwright smoke..."
set +e
npm run e2e:smoke 2>&1 | tee ARTIFACTS/e2e_run.txt
status=${PIPESTATUS[0]}
set -e

# -----------------------
# Step 7: Save a short report
# -----------------------
log "Writing REPORTS/e2e_smoke_summary.md ..."
cat > REPORTS/e2e_smoke_summary.md <<EOF
# E2E Smoke Summary

- Date: $(date -Iseconds)
- Base URL: $E2E_BASE_URL
- API Base: $E2E_API_BASE
- Seed: ${E2E_SEED_CMD:+YES} ${E2E_SEED_CMD:-(NO)}
- Result: $(if [[ "$status" -eq 0 ]]; then echo PASS; else echo FAIL; fi)

Artifacts:
- ARTIFACTS/e2e_run.txt
- e2e/artifacts/ (Playwright html report, traces, screenshots if configured)
EOF

# -----------------------
# Final status
# -----------------------
if [[ "$status" -eq 0 ]]; then
  log "E2E SMOKE: PASS ✅"
  exit 0
else
  log "E2E SMOKE: FAIL ❌"
  log "See ARTIFACTS/e2e_run.txt and Playwright report under e2e/artifacts/."
  exit "$status"
fi
