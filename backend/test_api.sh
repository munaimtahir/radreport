#!/bin/bash
# API endpoint test script
# Requires: curl, jq (optional but recommended)
# Usage: ./test_api.sh [base_url] [username] [password]

BASE_URL="${1:-http://localhost:8000}"
USERNAME="${2:-admin}"
PASSWORD="${3:-admin}"

echo "=========================================="
echo "RIMS API End-to-End Test"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "[1/10] Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/health/")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed: HTTP $HTTP_CODE${NC}"
    exit 1
fi

# Test 2: Login
echo -e "\n[2/10] Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/token/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Login successful${NC}"
else
    echo -e "${RED}✗ Login failed: $LOGIN_RESPONSE${NC}"
    exit 1
fi

# Test 3: Create Patient
echo -e "\n[3/10] Creating patient..."
PATIENT_DATA='{
    "mrn": "TEST'$(date +%s)'",
    "name": "Test Patient",
    "age": 30,
    "gender": "M",
    "phone": "123-456-7890"
}'

PATIENT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PATIENT_DATA")
PATIENT_HTTP=$(echo "$PATIENT_RESPONSE" | tail -n1)
PATIENT_BODY=$(echo "$PATIENT_RESPONSE" | head -n-1)

if [ "$PATIENT_HTTP" == "201" ]; then
    PATIENT_ID=$(echo "$PATIENT_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    echo -e "${GREEN}✓ Patient created: $PATIENT_ID${NC}"
else
    echo -e "${RED}✗ Patient creation failed: HTTP $PATIENT_HTTP${NC}"
    echo "$PATIENT_BODY"
    exit 1
fi

# Test 4: Create Modality
echo -e "\n[4/10] Creating modality..."
MODALITY_DATA='{
    "code": "USG",
    "name": "Ultrasound"
}'

MODALITY_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/modalities/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$MODALITY_DATA")
MODALITY_HTTP=$(echo "$MODALITY_RESPONSE" | tail -n1)
MODALITY_BODY=$(echo "$MODALITY_RESPONSE" | head -n-1)

if [ "$MODALITY_HTTP" == "201" ] || [ "$MODALITY_HTTP" == "200" ]; then
    MODALITY_ID=$(echo "$MODALITY_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    echo -e "${GREEN}✓ Modality created: $MODALITY_ID${NC}"
else
    echo -e "${YELLOW}⚠ Modality creation: HTTP $MODALITY_HTTP (may already exist)${NC}"
    MODALITY_ID=$(curl -s "$BASE_URL/api/modalities/" \
        -H "Authorization: Bearer $TOKEN" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
fi

# Test 5: Create Service
echo -e "\n[5/10] Creating service..."
SERVICE_DATA="{
    \"modality\": \"$MODALITY_ID\",
    \"name\": \"Abdominal Ultrasound\",
    \"price\": \"150.00\",
    \"tat_minutes\": 30
}"

SERVICE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/services/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$SERVICE_DATA")
SERVICE_HTTP=$(echo "$SERVICE_RESPONSE" | tail -n1)
SERVICE_BODY=$(echo "$SERVICE_RESPONSE" | head -n-1)

if [ "$SERVICE_HTTP" == "201" ] || [ "$SERVICE_HTTP" == "200" ]; then
    SERVICE_ID=$(echo "$SERVICE_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    echo -e "${GREEN}✓ Service created: $SERVICE_ID${NC}"
else
    echo -e "${YELLOW}⚠ Service creation: HTTP $SERVICE_HTTP (may already exist)${NC}"
    SERVICE_ID=$(curl -s "$BASE_URL/api/services/" \
        -H "Authorization: Bearer $TOKEN" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
fi

# Test 6: Create Template
echo -e "\n[6/10] Creating template..."
TEMPLATE_DATA='{
    "name": "Test USG Template",
    "modality_code": "USG",
    "is_active": true,
    "sections": [{
        "title": "Findings",
        "order": 1,
        "fields": [{
            "label": "Liver",
            "key": "liver",
            "field_type": "short_text",
            "required": true,
            "order": 1
        }, {
            "label": "Status",
            "key": "status",
            "field_type": "dropdown",
            "required": true,
            "order": 2,
            "options": [
                {"label": "Normal", "value": "normal", "order": 1},
                {"label": "Abnormal", "value": "abnormal", "order": 2}
            ]
        }]
    }]
}'

TEMPLATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/templates/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$TEMPLATE_DATA")
TEMPLATE_HTTP=$(echo "$TEMPLATE_RESPONSE" | tail -n1)
TEMPLATE_BODY=$(echo "$TEMPLATE_RESPONSE" | head -n-1)

if [ "$TEMPLATE_HTTP" == "201" ]; then
    TEMPLATE_ID=$(echo "$TEMPLATE_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    echo -e "${GREEN}✓ Template created: $TEMPLATE_ID${NC}"
else
    echo -e "${RED}✗ Template creation failed: HTTP $TEMPLATE_HTTP${NC}"
    echo "$TEMPLATE_BODY"
    exit 1
fi

# Test 7: Publish Template Version
echo -e "\n[7/10] Publishing template version..."
PUBLISH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/templates/$TEMPLATE_ID/publish/" \
    -H "Authorization: Bearer $TOKEN")
PUBLISH_HTTP=$(echo "$PUBLISH_RESPONSE" | tail -n1)
PUBLISH_BODY=$(echo "$PUBLISH_RESPONSE" | head -n-1)

if [ "$PUBLISH_HTTP" == "201" ]; then
    VERSION_ID=$(echo "$PUBLISH_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    VERSION=$(echo "$PUBLISH_BODY" | grep -o '"version":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ Template version published: v$VERSION ($VERSION_ID)${NC}"
else
    echo -e "${RED}✗ Template publish failed: HTTP $PUBLISH_HTTP${NC}"
    echo "$PUBLISH_BODY"
    exit 1
fi

# Test 8: Create Study
echo -e "\n[8/10] Creating study..."
STUDY_DATA="{
    \"patient\": \"$PATIENT_ID\",
    \"service\": \"$SERVICE_ID\",
    \"indication\": \"Routine checkup\",
    \"status\": \"registered\"
}"

STUDY_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/studies/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$STUDY_DATA")
STUDY_HTTP=$(echo "$STUDY_RESPONSE" | tail -n1)
STUDY_BODY=$(echo "$STUDY_RESPONSE" | head -n-1)

if [ "$STUDY_HTTP" == "201" ]; then
    STUDY_ID=$(echo "$STUDY_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    ACCESSION=$(echo "$STUDY_BODY" | grep -o '"accession":"[^"]*' | cut -d'"' -f4 | head -1)
    echo -e "${GREEN}✓ Study created: $ACCESSION ($STUDY_ID)${NC}"
else
    echo -e "${RED}✗ Study creation failed: HTTP $STUDY_HTTP${NC}"
    echo "$STUDY_BODY"
    exit 1
fi

# Test 9: Create Report
echo -e "\n[9/10] Creating report..."
REPORT_DATA="{
    \"study_id\": \"$STUDY_ID\",
    \"template_version_id\": \"$VERSION_ID\"
}"

REPORT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/reports/create_for_study/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$REPORT_DATA")
REPORT_HTTP=$(echo "$REPORT_RESPONSE" | tail -n1)
REPORT_BODY=$(echo "$REPORT_RESPONSE" | head -n-1)

if [ "$REPORT_HTTP" == "201" ] || [ "$REPORT_HTTP" == "200" ]; then
    REPORT_ID=$(echo "$REPORT_BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    echo -e "${GREEN}✓ Report created: $REPORT_ID${NC}"
else
    echo -e "${RED}✗ Report creation failed: HTTP $REPORT_HTTP${NC}"
    echo "$REPORT_BODY"
    exit 1
fi

# Test 10: Finalize Report
echo -e "\n[10/10] Finalizing report..."
FINALIZE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/reports/$REPORT_ID/finalize/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"values": {"liver": "Normal", "status": "normal"}, "narrative": "Normal findings", "impression": "No abnormalities"}')
FINALIZE_HTTP=$(echo "$FINALIZE_RESPONSE" | tail -n1)
FINALIZE_BODY=$(echo "$FINALIZE_RESPONSE" | head -n-1)

if [ "$FINALIZE_HTTP" == "200" ]; then
    echo -e "${GREEN}✓ Report finalized${NC}"
    if echo "$FINALIZE_BODY" | grep -q "pdf_file"; then
        echo -e "${GREEN}✓ PDF file generated${NC}"
    fi
else
    echo -e "${RED}✗ Report finalization failed: HTTP $FINALIZE_HTTP${NC}"
    echo "$FINALIZE_BODY"
    exit 1
fi

echo -e "\n=========================================="
echo -e "${GREEN}✅ All tests passed!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Patient: $PATIENT_ID"
echo "  - Study: $ACCESSION ($STUDY_ID)"
echo "  - Report: $REPORT_ID (finalized)"
echo "  - Template: $TEMPLATE_ID (v$VERSION)"
echo ""

