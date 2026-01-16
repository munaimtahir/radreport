# Registration v2 Hardening Sprint - Verification Pack

## Overview
This document provides verification steps and scripts to ensure all Registration v2 features are production-ready.

## Verification Checklist

### ✅ Phase 1: Backend Migration & Settings
- [x] Migration `0004_receiptsettings_footer_text.py` created
- [x] `ReceiptSettings.footer_text` field added to model
- [x] Serializer updated to include `footer_text`
- [x] PDF engine updated to use `footer_text`
- [ ] Migration applied in dev environment
- [ ] Database verification (footer_text persists)

**Verification Script**: See `backend_migrations.md`

---

### ✅ Phase 2: Backend Endpoints
- [x] `/api/services/most-used/` endpoint implemented
- [x] `ServiceSerializer` includes `usage_count` field
- [x] Visit creation payload contract documented
- [ ] Endpoint returns correct JSON structure
- [ ] Usage count calculation verified

**Verification Script**: See `endpoint_verification.sh`

---

### ✅ Phase 3: Frontend E2E Tests
- [ ] Playwright auth setup (token injection)
- [ ] E2E test for full registration flow
- [ ] Keyboard navigation verification
- [ ] Service search dropdown verification
- [ ] Most-used services buttons verification
- [ ] Discount % field verification
- [ ] Receipt generation verification

**Verification Script**: See `e2e_registration_v2.md`

---

### ✅ Phase 4: Keyboard UX Edge Cases
- [ ] Textarea Enter → Tab behavior
- [ ] Dropdown arrow key navigation
- [ ] Focus transitions (patient → services → billing)
- [ ] Remove button focus handling
- [ ] Mobile search debounce

**Verification Script**: Manual testing checklist in `keyboard_ux_verification.md`

---

### ✅ Phase 5: Dual-Copy Receipt
- [x] Dual-copy PDF function implemented
- [x] Patient Copy (top) + Office Copy (bottom)
- [x] Tear line between copies
- [x] Header text from settings
- [x] Footer text from settings
- [ ] PDF output verified (both copies visible)
- [ ] Print layout verified

**Verification Script**: See `receipt_verification.md`

---

## Quick Verification Commands

### Backend Migration
```bash
cd backend
python3 manage.py migrate studies
python3 manage.py shell
# Then run:
# from apps.studies.models import ReceiptSettings
# settings = ReceiptSettings.get_settings()
# assert hasattr(settings, 'footer_text')
# print("✅ PASS: footer_text field exists")
```

### Most-Used Services Endpoint
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/services/most-used/?limit=5" | jq
```

### Receipt Settings
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/receipt-settings/" | jq '.footer_text'
```

### Receipt PDF Generation
```bash
# After creating a visit, test PDF generation
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/pdf/{visit_id}/receipt/" \
  --output receipt_test.pdf
# Verify PDF has Patient Copy and Office Copy
```

---

## Expected Outcomes

### PASS Criteria
1. ✅ Migration applies without errors
2. ✅ `footer_text` persists in database
3. ✅ `/services/most-used/` returns top 5 services with `usage_count`
4. ✅ Receipt PDF shows dual copies with tear line
5. ✅ Frontend can save/update receipt settings (header + footer)
6. ✅ Visit creation accepts discount and generates receipt

### FAIL Criteria
- Migration fails or field missing
- Endpoint returns 500 or incorrect structure
- PDF missing one copy or tear line
- Frontend cannot save footer_text
- Receipt generation fails

---

## Next Steps
1. Apply migration in dev environment
2. Run endpoint verification script
3. Test receipt PDF generation
4. Verify frontend integration
5. Run E2E tests (once v2 RegistrationPage is available)
