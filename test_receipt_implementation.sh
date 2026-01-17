#!/bin/bash
# Receipt PDF Implementation Verification Script
# Tests all aspects of the receipt PDF as per verification guide

cd "$(dirname "$0")"

echo "=========================================="
echo "Receipt PDF Implementation Test"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $2"
        ((FAILED++))
    fi
}

echo ""
echo "1. Testing Migration Status..."
MIGRATION_STATUS=$(docker compose exec -T backend python manage.py showmigrations studies | grep "0005_backfill_receipt_settings" || echo "")
if echo "$MIGRATION_STATUS" | grep -q "\[X\]"; then
    test_result 0 "Migration 0005_backfill_receipt_settings is applied"
else
    test_result 1 "Migration 0005_backfill_receipt_settings NOT applied"
fi

echo ""
echo "2. Testing Receipt Settings..."
docker compose exec -T backend python manage.py shell << 'EOF' > /tmp/settings_test.txt 2>&1
from apps.studies.models import ReceiptSettings
settings = ReceiptSettings.get_settings()
print(f"HEADER:{settings.header_text}")
print(f"FOOTER_START:{settings.footer_text[:50]}")
EOF

if grep -q "HEADER:Consultant Place Clinic" /tmp/settings_test.txt; then
    test_result 0 "Header text is correct"
else
    test_result 1 "Header text is incorrect"
fi

if grep -q "FOOTER_START:Adjacent Excel Labs" /tmp/settings_test.txt; then
    test_result 0 "Footer text is correct"
else
    test_result 1 "Footer text is incorrect"
fi

echo ""
echo "3. Testing PDF Generation..."
docker compose exec -T backend python manage.py shell << 'EOF' > /tmp/pdf_test.txt 2>&1
from apps.workflow.models import ServiceVisit, Invoice
from apps.workflow.pdf import build_service_visit_receipt_pdf

service_visit = ServiceVisit.objects.first()
if not service_visit:
    print("ERROR:No service visits found")
    exit(1)

invoice = Invoice.objects.filter(service_visit=service_visit).first()
if not invoice:
    print("ERROR:No invoice found")
    exit(1)

try:
    pdf_file = build_service_visit_receipt_pdf(service_visit, invoice)
    print(f"PDF_NAME:{pdf_file.name}")
    print(f"PDF_SIZE:{pdf_file.size}")
    print(f"VISIT_ID:{service_visit.visit_id}")
    print(f"RECEIPT_NO:{invoice.receipt_number}")
    
    # Save for verification
    with open('/tmp/final_receipt_test.pdf', 'wb') as f:
        f.write(pdf_file.read())
    print("PDF_SAVED:SUCCESS")
except Exception as e:
    print(f"ERROR:{e}")
EOF

if grep -q "PDF_SAVED:SUCCESS" /tmp/pdf_test.txt; then
    test_result 0 "PDF generation successful"
else
    test_result 1 "PDF generation failed"
    cat /tmp/pdf_test.txt
fi

# Extract visit_id and receipt_no from test output
VISIT_ID=$(grep "VISIT_ID:" /tmp/pdf_test.txt | cut -d: -f2)
RECEIPT_NO=$(grep "RECEIPT_NO:" /tmp/pdf_test.txt | cut -d: -f2)
PDF_NAME=$(grep "PDF_NAME:" /tmp/pdf_test.txt | cut -d: -f2)

echo ""
echo "4. Testing Filename Format..."
EXPECTED_FILENAME="receipt_${VISIT_ID}_${RECEIPT_NO}.pdf"
if [ "$PDF_NAME" = "$EXPECTED_FILENAME" ]; then
    test_result 0 "Filename format correct: $PDF_NAME"
else
    test_result 1 "Filename format incorrect. Expected: $EXPECTED_FILENAME, Got: $PDF_NAME"
fi

echo ""
echo "5. Testing PDF Structure..."
# Copy PDF from container for inspection
docker compose cp backend:/tmp/final_receipt_test.pdf /tmp/final_receipt_test.pdf 2>/dev/null

if [ -f /tmp/final_receipt_test.pdf ]; then
    # Check if it's a valid PDF
    if file /tmp/final_receipt_test.pdf | grep -q "PDF document"; then
        test_result 0 "PDF file is valid"
        
        # Check PDF version and page count
        FILE_OUTPUT=$(file /tmp/final_receipt_test.pdf)
        if echo "$FILE_OUTPUT" | grep -q "2 page"; then
            test_result 0 "PDF has 2 pages (dual copy format)"
        else
            test_result 1 "PDF does not have expected 2 pages"
        fi
    else
        test_result 1 "PDF file is not valid"
    fi
    
    # Check file size is reasonable (should be a few KB)
    FILE_SIZE=$(stat -f%z /tmp/final_receipt_test.pdf 2>/dev/null || stat -c%s /tmp/final_receipt_test.pdf 2>/dev/null)
    if [ $FILE_SIZE -gt 1000 ] && [ $FILE_SIZE -lt 100000 ]; then
        test_result 0 "PDF file size is reasonable ($FILE_SIZE bytes)"
    else
        test_result 1 "PDF file size is unusual ($FILE_SIZE bytes)"
    fi
else
    test_result 1 "PDF file not found"
fi

echo ""
echo "6. Testing API Endpoint..."
# Get service visit ID for API test
VISIT_UUID=$(docker compose exec -T backend python manage.py shell -c "from apps.workflow.models import ServiceVisit; print(ServiceVisit.objects.first().id)" 2>/dev/null | tail -1 | tr -d '\r')

# Test endpoint (should require authentication)
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8015/api/pdf/${VISIT_UUID}/receipt/")

if [ "$HTTP_STATUS" = "401" ]; then
    test_result 0 "API endpoint requires authentication (HTTP 401)"
else
    test_result 1 "API endpoint authentication check failed (HTTP $HTTP_STATUS)"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "Failed: $FAILED"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Receipt PDF Implementation Status: COMPLETE"
    echo ""
    echo "Key Features Verified:"
    echo "  ✓ Migration applied and settings configured"
    echo "  ✓ PDF generation working with dual-copy format"
    echo "  ✓ Filename includes Visit ID and Receipt Number"
    echo "  ✓ API endpoint secured with authentication"
    echo "  ✓ Clinic branding (header/footer) configured"
    echo ""
    echo "Sample filename: $PDF_NAME"
    echo "Sample PDF saved: /tmp/final_receipt_test.pdf"
    echo ""
    echo "API Endpoint: GET /api/pdf/{service_visit_id}/receipt/"
    echo "Authentication: Required (Bearer token)"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo "Please review the errors above."
    exit 1
fi
