#!/bin/bash
set -e
#!/usr/bin/env bash

set -euo pipefail



# Production Smoke Test Script (STRICT)

# Usage:

#   BASE_URL=https://rims.example.com ADMIN_USER=admin ADMIN_PASS=pass ./scripts/smoke_prod.sh

#

# Optional:

#   MEDIA_TEST_URL=https://rims.example.com/media/printing/receipt/logo.png

#   STRICT_PROD=1

#   RCLONE_REMOTE=gdrive  (or "gdrive:" depending on your convention)

#   RCLONE_PATH=/usr/bin/rclone  (optional)



BASE_URL="${BASE_URL:-http://localhost:8000}"

ADMIN_USER="${ADMIN_USER:-admin}"

ADMIN_PASS="${ADMIN_PASS:-admin}"

MEDIA_TEST_URL="${MEDIA_TEST_URL:-}"

STRICT_PROD="${STRICT_PROD:-0}"

RCLONE_REMOTE="${RCLONE_REMOTE:-}"

RCLONE_PATH="${RCLONE_PATH:-rclone}"



# curl defaults: fail on non-2xx, no redirects, short timeout

CURL_BASE=(curl -fsS --max-time 12 --connect-timeout 5)



fail() {

  echo "✗ FAIL: $1"

  [ -n "${2:-}" ] && echo "  $2"

  exit 1

}



pass() {

  echo "✓ PASS: $1"

  [ -n "${2:-}" ] && echo "  $2"

}



json_get() {

  # Reads JSON from stdin, prints value for a key (top-level), or empty

  # Usage: echo "$json" | json_get access

  local key="$1"

  python3 -c "
import sys, json
try:
  obj = json.load(sys.stdin)
except Exception:
  print('')
  sys.exit(0)
v = obj.get('$key', '')
if v is None: v = ''
print(v if isinstance(v, str) else v)
"

}



json_has_keys() {

  # Validate JSON has all required top-level keys

  # Usage: echo "$json" | json_has_keys key1 key2 ...

  python3 -c "
import sys, json
keys = sys.argv[1:]
try:
  obj = json.load(sys.stdin)
except Exception:
  sys.exit(2)
missing = [k for k in keys if k not in obj]
if missing:
  print('Missing keys:', ', '.join(missing))
  sys.exit(1)
sys.exit(0)
" "$@"

}



echo "=========================================="

echo "Production Smoke Test (STRICT)"

echo "=========================================="

echo "Base URL:      $BASE_URL"

echo "Admin User:    $ADMIN_USER"

echo "STRICT_PROD:   $STRICT_PROD"

echo "MEDIA_TEST_URL ${MEDIA_TEST_URL:-<not set>}"

echo "RCLONE_REMOTE  ${RCLONE_REMOTE:-<not set>}"

echo ""



# 1) Health

echo "[1/6] Health..."

"${CURL_BASE[@]}" "$BASE_URL/api/health/" >/dev/null

pass "Health endpoint" "200 OK"



# 2) Auth token (strict JSON parsing)

echo ""

echo "[2/6] Auth..."

TOKEN_JSON=$("${CURL_BASE[@]}" -X POST "$BASE_URL/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}")



ACCESS_TOKEN=$(echo "$TOKEN_JSON" | json_get access)

[ -n "$ACCESS_TOKEN" ] || fail "Authentication" "No access token returned. Response: $TOKEN_JSON"

pass "Authentication" "Token obtained"



AUTH_HEADER=("Authorization: Bearer $ACCESS_TOKEN")



# 3) Printing config (validate required keys)

echo ""

echo "[3/6] Printing config..."

CONFIG_JSON=$("${CURL_BASE[@]}" -H "${AUTH_HEADER[@]}" "$BASE_URL/api/printing/config/")



# Adjust keys below to what your merged response guarantees.

# Keep them minimal but meaningful.

REQ_KEYS=("org_name" "disclaimer_text" "receipt_header_text" "receipt_footer_text")

KEY_CHECK=$(echo "$CONFIG_JSON" | json_has_keys "${REQ_KEYS[@]}" 2>&1) || fail "Printing config endpoint" "$KEY_CHECK"

pass "Printing config endpoint" "200 OK + required keys present"



# 4) Sequence preview (no redirects; validate regex)

echo ""

echo "[4/6] Printing sequence (dry run)..."

SEQ_JSON=$("${CURL_BASE[@]}" -H "${AUTH_HEADER[@]}" "$BASE_URL/api/printing/sequence/next/?type=receipt&dry_run=1")

NEXT_VAL=$(echo "$SEQ_JSON" | json_get next)

[ -n "$NEXT_VAL" ] || fail "Sequence next endpoint" "Missing 'next'. Response: $SEQ_JSON"

echo "$NEXT_VAL" | grep -qE '^[0-9]{4}-[0-9]{4}$' || fail "Sequence next endpoint" "Invalid next format: $NEXT_VAL (expected YYMM-NNNN)"

pass "Sequence next endpoint" "next=$NEXT_VAL"



# 5) Backups list endpoint (strict JSON parse sanity)

echo ""

echo "[5/6] Backups list..."

BACKUPS_JSON=$("${CURL_BASE[@]}" -H "${AUTH_HEADER[@]}" "$BASE_URL/api/backups/")

# We accept either list or dict response, but must be valid JSON.

echo "$BACKUPS_JSON" | python3 -c "
import sys, json
s = sys.stdin.read()
json.loads(s)
print('OK')
" >/dev/null || fail "Backups endpoint" "Invalid JSON response"

pass "Backups endpoint" "200 OK + valid JSON"



# 6) Optional checks (STRICT_PROD may require them)

echo ""

echo "[6/6] Optional checks..."



# Media check

if [ -n "$MEDIA_TEST_URL" ]; then

  "${CURL_BASE[@]}" -I "$MEDIA_TEST_URL" >/dev/null

  pass "Media URL" "200 OK ($MEDIA_TEST_URL)"

else

  if [ "$STRICT_PROD" = "1" ]; then

    fail "Media URL" "STRICT_PROD=1 requires MEDIA_TEST_URL to be set and return 200."

  else

    echo "• Skipping Media URL check (MEDIA_TEST_URL not set)"

  fi

fi



# rclone check (only if configured)

if [ -n "$RCLONE_REMOTE" ]; then

  command -v "$RCLONE_PATH" >/dev/null 2>&1 || fail "rclone availability" "rclone not found at '$RCLONE_PATH'"

  "$RCLONE_PATH" version >/dev/null 2>&1 || fail "rclone" "rclone exists but failed to run 'rclone version'"

  # Lightweight remote listing (won't download anything)

  "$RCLONE_PATH" lsd "${RCLONE_REMOTE}:" >/dev/null 2>&1 || fail "rclone remote" "Failed to list remote '${RCLONE_REMOTE}:' (check config mount + credentials)"

  pass "rclone remote" "lsd ${RCLONE_REMOTE}: OK"

else

  if [ "$STRICT_PROD" = "1" ]; then

    echo "• Skipping rclone remote check (RCLONE_REMOTE not set) — allowed in STRICT_PROD unless you mandate it."

  else

    echo "• Skipping rclone remote check (RCLONE_REMOTE not set)"

  fi

fi



echo ""

echo "=========================================="

echo "✓ All smoke tests PASSED"

echo "=========================================="

exit 0


# Production Smoke Test Script
# Tests critical endpoints to verify production deployment
# Usage: BASE_URL=https://rims.alshifalab.pk ADMIN_USER=admin ADMIN_PASS=password ./scripts/smoke_prod.sh

BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-admin}"

echo "=========================================="
echo "Production Smoke Test"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Admin User: $ADMIN_USER"
echo ""

FAILED=0

# Helper function to print test results
print_test() {
    local name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "PASS" ]; then
        echo "✓ PASS: $name"
        if [ -n "$details" ]; then
            echo "  $details"
        fi
    else
        echo "✗ FAIL: $name"
        if [ -n "$details" ]; then
            echo "  $details"
        fi
        FAILED=1
    fi
}

# Test 1: Health endpoint
echo "[1/5] Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health/" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    print_test "Health endpoint" "PASS" "HTTP $HTTP_CODE"
else
    print_test "Health endpoint" "FAIL" "Expected 200, got $HTTP_CODE"
    exit 1
fi

# Test 2: Auth token
echo ""
echo "[2/5] Testing authentication..."
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/token/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" || echo "")
    
if echo "$TOKEN_RESPONSE" | grep -q "access"; then
    TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
    if [ -n "$TOKEN" ]; then
        print_test "Authentication" "PASS" "Token obtained"
    else
        print_test "Authentication" "FAIL" "Token response missing access field"
        exit 1
    fi
else
    print_test "Authentication" "FAIL" "Login failed: $TOKEN_RESPONSE"
    exit 1
fi

# Test 3: Printing config endpoint
echo ""
echo "[3/5] Testing printing config endpoint..."
CONFIG_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/printing/config/" \
    -H "Authorization: Bearer $TOKEN" || echo "")
HTTP_CODE=$(echo "$CONFIG_RESPONSE" | tail -n1)
BODY=$(echo "$CONFIG_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    # Check if response is valid JSON
    if echo "$BODY" | grep -q "{"; then
        print_test "Printing config endpoint" "PASS" "HTTP $HTTP_CODE + JSON"
    else
        print_test "Printing config endpoint" "FAIL" "HTTP $HTTP_CODE but invalid JSON"
        exit 1
    fi
else
    print_test "Printing config endpoint" "FAIL" "Expected 200, got $HTTP_CODE"
    exit 1
fi

# Test 4: Sequence next endpoint
echo ""
echo "[4/5] Testing sequence next endpoint..."
SEQUENCE_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/printing/sequence/next/?type=receipt&dry_run=1" \
    -H "Authorization: Bearer $TOKEN" || echo "")
HTTP_CODE=$(echo "$SEQUENCE_RESPONSE" | tail -n1)
BODY=$(echo "$SEQUENCE_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    # Extract next value and validate format (YYYY-NNNN)
    NEXT_VAL=$(echo "$BODY" | grep -o '"next":"[^"]*' | cut -d'"' -f4)
    if [ -n "$NEXT_VAL" ]; then
        # Validate format: YYMM-NNNN (e.g., 2602-0001)
        if echo "$NEXT_VAL" | grep -qE '^[0-9]{4}-[0-9]{4}$'; then
            print_test "Sequence next endpoint" "PASS" "HTTP $HTTP_CODE + next=$NEXT_VAL"
        else
            print_test "Sequence next endpoint" "FAIL" "HTTP $HTTP_CODE but invalid format: $NEXT_VAL (expected YYYY-NNNN)"
            exit 1
        fi
    else
        print_test "Sequence next endpoint" "FAIL" "HTTP $HTTP_CODE but missing 'next' field"
        exit 1
    fi
else
    print_test "Sequence next endpoint" "FAIL" "Expected 200, got $HTTP_CODE"
    exit 1
fi

# Test 5: Backups endpoint
echo ""
echo "[5/5] Testing backups endpoint..."
BACKUPS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/backups/" \
    -H "Authorization: Bearer $TOKEN" || echo "")
HTTP_CODE=$(echo "$BACKUPS_RESPONSE" | tail -n1)
BODY=$(echo "$BACKUPS_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    # Check if response is valid JSON
    if echo "$BODY" | grep -q "{"; then
        print_test "Backups endpoint" "PASS" "HTTP $HTTP_CODE + JSON"
    else
        print_test "Backups endpoint" "FAIL" "HTTP $HTTP_CODE but invalid JSON"
        exit 1
    fi
else
    print_test "Backups endpoint" "FAIL" "Expected 200, got $HTTP_CODE"
    exit 1
fi

# Optional: Media test if MEDIA_TEST_URL is provided
if [ -n "$MEDIA_TEST_URL" ]; then
    echo ""
    echo "[Optional] Testing media URL..."
    MEDIA_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$MEDIA_TEST_URL" || echo "000")
    if [ "$MEDIA_HTTP_CODE" = "200" ]; then
        print_test "Media URL" "PASS" "HTTP $MEDIA_HTTP_CODE"
    else
        print_test "Media URL" "FAIL" "Expected 200, got $MEDIA_HTTP_CODE"
        # Don't exit on media test failure as it's optional
    fi
fi

echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✓ All smoke tests PASSED"
    echo "=========================================="
    exit 0
else
    echo "✗ Smoke tests FAILED"
    echo "=========================================="
    exit 1
fi
