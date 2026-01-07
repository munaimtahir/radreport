#!/bin/bash
# Production Smoke Test Script for RIMS
# Tests all workflows end-to-end via HTTP
# Usage: ./smoke_test_production.sh [base_url] [username] [password]

BASE_URL="${1:-https://rims.alshifalab.pk}"
USERNAME="${2:-admin}"
PASSWORD="${3:-admin123}"

echo "=========================================="
echo "RIMS Production Smoke Test"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Username: $USERNAME"
echo "Date: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
WARNINGS=0
FAILED_TESTS=()

# Helper function to test endpoint
test_endpoint() {
    local test_name="$1"
    local method="${2:-GET}"
    local endpoint="$3"
    local data="${4:-}"
    local expected_code="${5:-200}"
    local auth_header="${6:-}"
    
    echo -n "[TEST] $test_name... "
    
    local curl_cmd="curl -s -w \"\n%{http_code}\" -X $method \"$BASE_URL$endpoint\""
    
    if [ -n "$auth_header" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $auth_header\""
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi
    
    local response=$(eval $curl_cmd 2>&1)
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        echo "$body" | head -c 200
        echo ""
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code, expected $expected_code)"
        FAILED=$((FAILED + 1))
        FAILED_TESTS+=("$test_name")
        echo "Response: $body" | head -c 500
        echo ""
        return 1
    fi
}

# Test 1: Health Check
echo "=========================================="
echo "1. HEALTH CHECK"
echo "=========================================="
test_endpoint "Health endpoint" "GET" "/api/health/" "" "200"
echo ""

# Test 2: Authentication
echo "=========================================="
echo "2. AUTHENTICATION"
echo "=========================================="
echo -n "[TEST] Login... "
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/token/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
    REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ PASS${NC}"
    echo "Token obtained (length: ${#TOKEN})"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $LOGIN_RESPONSE"
    FAILED=$((FAILED + 1))
    FAILED_TESTS+=("Login")
    echo ""
    echo "Cannot continue without authentication. Exiting."
    exit 1
fi
echo ""

# Test 3: Patient Management
echo "=========================================="
echo "3. PATIENT REGISTRATION"
echo "=========================================="
TIMESTAMP=$(date +%s)
PATIENT_MRN="SMOKE${TIMESTAMP}"

# List patients
test_endpoint "List patients" "GET" "/api/patients/" "" "200" "$TOKEN"

# Create patient
PATIENT_DATA="{\"mrn\":\"$PATIENT_MRN\",\"name\":\"Smoke Test Patient\",\"age\":30,\"gender\":\"M\",\"phone\":\"123-456-7890\"}"
echo -n "[TEST] Create patient... "
PATIENT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PATIENT_DATA")
PATIENT_HTTP=$(echo "$PATIENT_RESPONSE" | tail -n1)
PATIENT_BODY=$(echo "$PATIENT_RESPONSE" | head -n-1)

if [ "$PATIENT_HTTP" == "201" ]; then
    PATIENT_ID=$(echo "$PATIENT_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    echo -e "${GREEN}✓ PASS${NC} (HTTP $PATIENT_HTTP)"
    echo "Patient ID: $PATIENT_ID"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $PATIENT_HTTP)"
    echo "$PATIENT_BODY"
    FAILED=$((FAILED + 1))
    FAILED_TESTS+=("Create Patient")
    PATIENT_ID=""
fi
echo ""

# Test 4: Catalog (Modalities & Services)
echo "=========================================="
echo "4. CATALOG MANAGEMENT"
echo "=========================================="
test_endpoint "List modalities" "GET" "/api/modalities/" "" "200" "$TOKEN"
test_endpoint "List services" "GET" "/api/services/" "" "200" "$TOKEN"

# Get first service
SERVICE_RESPONSE=$(curl -s "$BASE_URL/api/services/" \
    -H "Authorization: Bearer $TOKEN")
SERVICE_ID=$(echo "$SERVICE_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)

if [ -n "$SERVICE_ID" ]; then
    echo -e "${GREEN}✓ Found service: $SERVICE_ID${NC}"
else
    echo -e "${YELLOW}⚠ No services found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Test 5: Templates
echo "=========================================="
echo "5. TEMPLATE MANAGEMENT"
echo "=========================================="
test_endpoint "List templates" "GET" "/api/templates/" "" "200" "$TOKEN"

# Get first template
TEMPLATE_RESPONSE=$(curl -s "$BASE_URL/api/templates/" \
    -H "Authorization: Bearer $TOKEN")
TEMPLATE_ID=$(echo "$TEMPLATE_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)

if [ -n "$TEMPLATE_ID" ]; then
    echo -e "${GREEN}✓ Found template: $TEMPLATE_ID${NC}"
    test_endpoint "Get template details" "GET" "/api/templates/$TEMPLATE_ID/" "" "200" "$TOKEN"
else
    echo -e "${YELLOW}⚠ No templates found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Test 6: Study Registration
echo "=========================================="
echo "6. STUDY/EXAM REGISTRATION"
echo "=========================================="
if [ -n "$PATIENT_ID" ] && [ -n "$SERVICE_ID" ]; then
    STUDY_DATA="{\"patient\":\"$PATIENT_ID\",\"service\":\"$SERVICE_ID\",\"indication\":\"Smoke test\",\"status\":\"registered\"}"
    echo -n "[TEST] Create study... "
    STUDY_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/studies/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$STUDY_DATA")
    STUDY_HTTP=$(echo "$STUDY_RESPONSE" | tail -n1)
    STUDY_BODY=$(echo "$STUDY_RESPONSE" | head -n-1)
    
    if [ "$STUDY_HTTP" == "201" ]; then
        STUDY_ID=$(echo "$STUDY_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
        ACCESSION=$(echo "$STUDY_BODY" | grep -o '"accession":"[^"]*' | cut -d'"' -f4 | head -1)
        echo -e "${GREEN}✓ PASS${NC} (HTTP $STUDY_HTTP)"
        echo "Study ID: $STUDY_ID, Accession: $ACCESSION"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $STUDY_HTTP)"
        echo "$STUDY_BODY"
        FAILED=$((FAILED + 1))
        FAILED_TESTS+=("Create Study")
        STUDY_ID=""
    fi
else
    echo -e "${YELLOW}⚠ Skipping study creation (missing patient or service)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Test 7: Receipt Generation
echo "=========================================="
echo "7. RECEIPT GENERATION"
echo "=========================================="
test_endpoint "Receipt settings" "GET" "/api/receipt-settings/" "" "200" "$TOKEN"

if [ -n "$STUDY_ID" ]; then
    # Try to get visit/receipt for study
    VISIT_RESPONSE=$(curl -s "$BASE_URL/api/visits/?study=$STUDY_ID" \
        -H "Authorization: Bearer $TOKEN")
    echo "Visit response: $VISIT_RESPONSE" | head -c 200
    echo ""
fi
echo ""

# Test 8: Report Generation
echo "=========================================="
echo "8. REPORT GENERATION"
echo "=========================================="
test_endpoint "List reports" "GET" "/api/reports/" "" "200" "$TOKEN"

if [ -n "$STUDY_ID" ] && [ -n "$TEMPLATE_ID" ]; then
    # Get template version from template-versions endpoint
    echo -n "[TEST] Get template versions... "
    VERSIONS_RESPONSE=$(curl -s "$BASE_URL/api/template-versions/?template=$TEMPLATE_ID&is_published=true" \
        -H "Authorization: Bearer $TOKEN")
    VERSION_ID=$(echo "$VERSIONS_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    
    if [ -n "$VERSION_ID" ]; then
        echo -e "${GREEN}✓ Found version: $VERSION_ID${NC}"
        REPORT_DATA="{\"study_id\":\"$STUDY_ID\",\"template_version_id\":\"$VERSION_ID\"}"
        echo -n "[TEST] Create report... "
        REPORT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/reports/create_for_study/" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$REPORT_DATA")
        REPORT_HTTP=$(echo "$REPORT_RESPONSE" | tail -n1)
        REPORT_BODY=$(echo "$REPORT_RESPONSE" | head -n-1)
        
        if [ "$REPORT_HTTP" == "201" ] || [ "$REPORT_HTTP" == "200" ]; then
            REPORT_ID=$(echo "$REPORT_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
            echo -e "${GREEN}✓ PASS${NC} (HTTP $REPORT_HTTP)"
            echo "Report ID: $REPORT_ID"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ FAIL${NC} (HTTP $REPORT_HTTP)"
            echo "$REPORT_BODY"
            FAILED=$((FAILED + 1))
            FAILED_TESTS+=("Create Report")
        fi
    else
        echo -e "${YELLOW}⚠ No published template version found${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi
echo ""

# Test 9: Static Files
echo "=========================================="
echo "9. STATIC FILES & MEDIA"
echo "=========================================="
test_endpoint "Static files check" "GET" "/static/" "" "200" "" || echo -e "${YELLOW}⚠ Static files may be proxied${NC}"
echo ""

# Test 10: Admin Panel
echo "=========================================="
echo "10. ADMIN PANEL"
echo "=========================================="
ADMIN_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/admin/" 2>&1)
ADMIN_HTTP=$(echo "$ADMIN_RESPONSE" | tail -n1)
if [ "$ADMIN_HTTP" == "200" ] || [ "$ADMIN_HTTP" == "302" ]; then
    echo -e "${GREEN}✓ Admin panel accessible${NC} (HTTP $ADMIN_HTTP)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠ Admin panel: HTTP $ADMIN_HTTP${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Summary
echo "=========================================="
echo "SMOKE TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "Failed Tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    exit 1
else
    echo -e "${GREEN}✅ All critical tests passed!${NC}"
    exit 0
fi
