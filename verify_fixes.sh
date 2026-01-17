#!/bin/bash
# Receipt PDF Verification Test Script
# Tests all the fixes applied on 2026-01-17

echo "=========================================="
echo "RIMS Receipt PDF Fixes Verification"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Test 1: Logo file exists
echo "✓ Test 1: Verifying logo file..."
if [ -f "frontend/public/brand/Consultants_Place_Clinic_Logo_Transparent.png" ]; then
    echo "  ✅ Logo file exists with correct filename"
    ls -lh frontend/public/brand/Consultants_Place_Clinic_Logo_Transparent.png
else
    echo "  ❌ Logo file NOT found"
fi
echo ""

# Test 2: Receipt format is compact (check code)
echo "✓ Test 2: Verifying receipt format..."
if grep -q "COMPACT_PAGE_HEIGHT = 148 \* mm" backend/apps/reporting/pdf_engine/receipt.py; then
    echo "  ✅ Receipt uses compact format (148mm height, not full A4)"
else
    echo "  ❌ Receipt format not updated"
fi
echo ""

# Test 3: Logging is present
echo "✓ Test 3: Verifying comprehensive logging..."
LOG_COUNT=$(grep -c "\[RECEIPT PDF\]" backend/apps/reporting/pdf_engine/receipt.py)
if [ "$LOG_COUNT" -gt 50 ]; then
    echo "  ✅ Comprehensive logging added ($LOG_COUNT log statements)"
else
    echo "  ❌ Insufficient logging ($LOG_COUNT log statements)"
fi
echo ""

# Test 4: Dashboard API fix
echo "✓ Test 4: Verifying dashboard API fix..."
if ! grep -q "Q(assigned_to=user)" backend/apps/workflow/dashboard_api.py; then
    echo "  ✅ Dashboard API fixed (no invalid assigned_to query)"
else
    echo "  ❌ Dashboard API still has issue"
fi
echo ""

# Test 5: Autocomplete attributes
echo "✓ Test 5: Verifying autocomplete attributes..."
if grep -q 'autoComplete="current-password"' frontend/src/views/Login.tsx; then
    echo "  ✅ Autocomplete attributes added to login form"
else
    echo "  ❌ Autocomplete attributes missing"
fi
echo ""

# Test 6: Backend health
echo "✓ Test 6: Testing backend health..."
BACKEND_STATUS=$(curl -s http://127.0.0.1:8015/api/health/ | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$BACKEND_STATUS" = "ok" ]; then
    echo "  ✅ Backend is healthy"
else
    echo "  ❌ Backend health check failed"
fi
echo ""

# Test 7: Frontend accessibility
echo "✓ Test 7: Testing frontend accessibility..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8081/)
if [ "$FRONTEND_CODE" = "200" ]; then
    echo "  ✅ Frontend is accessible (HTTP $FRONTEND_CODE)"
else
    echo "  ❌ Frontend not accessible (HTTP $FRONTEND_CODE)"
fi
echo ""

# Test 8: Docker services status
echo "✓ Test 8: Checking Docker services..."
SERVICES_UP=$(docker compose ps --format json 2>/dev/null | grep -c '"State":"running"' || docker ps --format "{{.Names}}" | grep -c "rims_")
if [ "$SERVICES_UP" -ge 3 ]; then
    echo "  ✅ All services running ($SERVICES_UP containers)"
else
    echo "  ⚠️  Some services may be down ($SERVICES_UP containers)"
fi
echo ""

echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "📋 Manual Tests Required:"
echo "  1. Login to https://rims.alshifalab.pk"
echo "  2. Check browser console - no 404 or 400 errors"
echo "  3. Navigate to Dashboard - worklist should load"
echo "  4. Generate a receipt from Billing module"
echo "  5. Open receipt PDF - verify it's single compact page"
echo "  6. Check backend logs: docker compose logs backend | grep 'RECEIPT PDF'"
echo ""
echo "📖 Full documentation: FIXES_SUMMARY_2026_01_17.md"
echo ""
