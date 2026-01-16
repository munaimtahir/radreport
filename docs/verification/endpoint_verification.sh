#!/bin/bash
# Endpoint Verification Script for Registration v2
# Tests all backend endpoints with PASS/FAIL outputs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE="${API_BASE:-http://localhost:8000/api}"
USERNAME="${E2E_USERNAME:-admin}"
PASSWORD="${E2E_PASSWORD:-admin}"

# Counters
PASSED=0
FAILED=0

# Helper functions
print_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ INFO:${NC} $1"
}

# Get auth token
print_info "Authenticating..."
TOKEN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/token/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    print_fail "Failed to get auth token"
    echo "$TOKEN_RESPONSE"
    exit 1
fi

print_pass "Authentication successful"
echo ""

# Test 1: GET /api/services/most-used/
print_info "Testing GET /api/services/most-used/"
MOST_USED_RESPONSE=$(curl -s -X GET "${API_BASE}/services/most-used/?limit=5" \
    -H "Authorization: Bearer ${TOKEN}")

if echo "$MOST_USED_RESPONSE" | grep -q '"id"'; then
    COUNT=$(echo "$MOST_USED_RESPONSE" | grep -o '"id"' | wc -l)
    if [ "$COUNT" -le 5 ]; then
        print_pass "/services/most-used/ returns valid JSON with services (count: $COUNT)"
    else
        print_fail "/services/most-used/ returns more than 5 services"
    fi
else
    print_fail "/services/most-used/ does not return valid service data"
    echo "Response: $MOST_USED_RESPONSE"
fi

# Check for usage_count field
if echo "$MOST_USED_RESPONSE" | grep -q '"usage_count"'; then
    print_pass "/services/most-used/ includes usage_count field"
else
    print_fail "/services/most-used/ missing usage_count field"
fi
echo ""

# Test 2: GET /api/receipt-settings/ (footer_text)
print_info "Testing GET /api/receipt-settings/"
SETTINGS_RESPONSE=$(curl -s -X GET "${API_BASE}/receipt-settings/" \
    -H "Authorization: Bearer ${TOKEN}")

if echo "$SETTINGS_RESPONSE" | grep -q '"footer_text"'; then
    print_pass "/receipt-settings/ includes footer_text field"
else
    print_fail "/receipt-settings/ missing footer_text field"
    echo "Response: $SETTINGS_RESPONSE"
fi

if echo "$SETTINGS_RESPONSE" | grep -q '"header_text"'; then
    print_pass "/receipt-settings/ includes header_text field"
else
    print_fail "/receipt-settings/ missing header_text field"
fi
echo ""

# Test 3: PATCH /api/receipt-settings/ (update footer_text)
print_info "Testing PATCH /api/receipt-settings/ (update footer_text)"
UPDATE_RESPONSE=$(curl -s -X PATCH "${API_BASE}/receipt-settings/1/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"footer_text":"Test footer text from verification script"}')

if echo "$UPDATE_RESPONSE" | grep -q '"footer_text"'; then
    UPDATED_TEXT=$(echo "$UPDATE_RESPONSE" | grep -o '"footer_text":"[^"]*' | cut -d'"' -f4)
    if [ "$UPDATED_TEXT" = "Test footer text from verification script" ]; then
        print_pass "PATCH /receipt-settings/ successfully updates footer_text"
    else
        print_fail "PATCH /receipt-settings/ did not update footer_text correctly"
    fi
else
    print_fail "PATCH /receipt-settings/ failed to update footer_text"
    echo "Response: $UPDATE_RESPONSE"
fi
echo ""

# Test 4: POST /api/workflow/visits/create_visit/ (payload validation)
print_info "Testing POST /api/workflow/visits/create_visit/ payload structure"

# First, get a patient ID
PATIENTS_RESPONSE=$(curl -s -X GET "${API_BASE}/patients/?limit=1" \
    -H "Authorization: Bearer ${TOKEN}")

PATIENT_ID=$(echo "$PATIENTS_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$PATIENT_ID" ]; then
    print_info "No existing patients found, creating test patient..."
    PATIENT_CREATE=$(curl -s -X POST "${API_BASE}/patients/" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"name":"Test Patient","phone":"1234567890","gender":"Male"}')
    PATIENT_ID=$(echo "$PATIENT_CREATE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
fi

if [ -z "$PATIENT_ID" ]; then
    print_fail "Could not get or create patient for visit test"
else
    print_pass "Patient ID obtained: ${PATIENT_ID:0:8}..."
    
    # Get a service ID
    SERVICES_RESPONSE=$(curl -s -X GET "${API_BASE}/services/?limit=1" \
        -H "Authorization: Bearer ${TOKEN}")
    SERVICE_ID=$(echo "$SERVICES_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
    
    if [ -z "$SERVICE_ID" ]; then
        print_fail "No services found for visit test"
    else
        print_pass "Service ID obtained: ${SERVICE_ID:0:8}..."
        
        # Create visit with discount_percentage
        VISIT_PAYLOAD=$(cat <<EOF
{
  "patient_id": "${PATIENT_ID}",
  "service_ids": ["${SERVICE_ID}"],
  "subtotal": 100.00,
  "discount_percentage": 20.00,
  "total_amount": 100.00,
  "net_amount": 80.00,
  "amount_paid": 80.00,
  "payment_method": "cash"
}
EOF
)
        
        VISIT_RESPONSE=$(curl -s -X POST "${API_BASE}/workflow/visits/create_visit/" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Content-Type: application/json" \
            -d "$VISIT_PAYLOAD")
        
        if echo "$VISIT_RESPONSE" | grep -q '"visit_id"'; then
            VISIT_ID=$(echo "$VISIT_RESPONSE" | grep -o '"visit_id":"[^"]*' | cut -d'"' -f4)
            print_pass "POST /workflow/visits/create_visit/ successfully created visit: $VISIT_ID"
            
            # Test receipt PDF generation
            print_info "Testing GET /api/pdf/{visit_id}/receipt/"
            PDF_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/receipt_test.pdf \
                -X GET "${API_BASE}/pdf/${PATIENT_ID}/receipt/" \
                -H "Authorization: Bearer ${TOKEN}")
            
            HTTP_CODE="${PDF_RESPONSE: -3}"
            if [ "$HTTP_CODE" = "200" ]; then
                if [ -f /tmp/receipt_test.pdf ] && file /tmp/receipt_test.pdf | grep -q "PDF"; then
                    print_pass "GET /api/pdf/{id}/receipt/ returns valid PDF"
                    rm -f /tmp/receipt_test.pdf
                else
                    print_fail "GET /api/pdf/{id}/receipt/ does not return valid PDF"
                fi
            else
                print_fail "GET /api/pdf/{id}/receipt/ returned HTTP $HTTP_CODE"
            fi
        else
            print_fail "POST /workflow/visits/create_visit/ failed to create visit"
            echo "Response: $VISIT_RESPONSE"
        fi
    fi
fi
echo ""

# Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
