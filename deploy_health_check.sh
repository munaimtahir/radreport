#!/bin/bash
# Deployment Health Check Script for RIMS
# Run this after deployment to verify everything is working
# Usage: ./deploy_health_check.sh [base_url]

BASE_URL="${1:-https://rims.alshifalab.pk}"

echo "=========================================="
echo "RIMS Deployment Health Check"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Date: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test 1: Health endpoint (enhanced)
echo "1. Health Check (Enhanced)..."
HEALTH_RESPONSE=$(curl -s "$BASE_URL/api/health/")
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health/")
if [ "$HEALTH_CODE" == "200" ] && echo "$HEALTH_RESPONSE" | grep -q '"status"'; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $HEALTH_CODE)"
    echo "$HEALTH_RESPONSE"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: Static files
echo "2. Static Files..."
STATIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/static/admin/css/base.css")
if [ "$STATIC_CODE" == "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $STATIC_CODE)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $STATIC_CODE)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: Frontend
echo "3. Frontend..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$FRONTEND_CODE" == "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $FRONTEND_CODE)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $FRONTEND_CODE)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: Admin panel
echo "4. Admin Panel..."
ADMIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/")
if [ "$ADMIN_CODE" == "200" ] || [ "$ADMIN_CODE" == "302" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $ADMIN_CODE)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $ADMIN_CODE)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: Service status (if running on VPS)
if [ -f "/etc/systemd/system/rims-backend.service" ]; then
    echo "5. Backend Service Status..."
    if systemctl is-active --quiet rims-backend; then
        echo -e "${GREEN}✓ PASS${NC} (service active)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (service not active)"
        FAILED=$((FAILED + 1))
    fi
    echo ""
fi

# Summary
echo "=========================================="
echo "Health Check Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All health checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some health checks failed. Review output above.${NC}"
    exit 1
fi
