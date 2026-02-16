#!/bin/bash
set -e

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
