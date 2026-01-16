# E2E Test Setup and Execution Guide

## Prerequisites

1. **Playwright Installation**:
   ```bash
   cd frontend
   npm install -D @playwright/test
   npx playwright install
   ```

2. **Environment Variables**:
   Create `.env.test` or set environment variables:
   ```bash
   export E2E_BASE_URL=http://localhost:5173
   export E2E_API_BASE=http://localhost:8000/api
   export E2E_USERNAME=admin
   export E2E_PASSWORD=admin
   ```

3. **Backend Running**: Ensure backend is running on port 8000
4. **Frontend Running**: Ensure frontend is running on port 5173

## Test File Location

`tests/e2e/registration_v2.spec.ts`

## Running Tests

### Run all E2E tests:
```bash
cd frontend
npx playwright test tests/e2e/registration_v2.spec.ts
```

### Run with UI mode (interactive):
```bash
npx playwright test tests/e2e/registration_v2.spec.ts --ui
```

### Run specific test:
```bash
npx playwright test tests/e2e/registration_v2.spec.ts -g "Keyboard navigation"
```

### Run in headed mode (see browser):
```bash
npx playwright test tests/e2e/registration_v2.spec.ts --headed
```

## Test Coverage

### 1. Keyboard Navigation
- ✅ Enter behaves like Tab across patient → services → billing
- ✅ Textarea Enter behaves as Tab (not newline)

### 2. DOB ↔ Age Linkage
- ✅ Entering age auto-calculates DOB
- ✅ Entering DOB auto-calculates age

### 3. Service Search
- ✅ Debounced search (300ms delay)
- ✅ Dropdown with arrow key navigation
- ✅ Enter key selects service from dropdown

### 4. Most-Used Services
- ✅ Quick buttons display (if endpoint available)
- ✅ Local fallback if endpoint fails

### 5. Discount Percentage
- ✅ 0-100 clamp validation
- ✅ Percentage calculation

### 6. Patient Save Flow
- ✅ Patient save locks identity
- ✅ Auto-focuses service search after save

### 7. Full Registration Flow
- ✅ Create patient → Add services → Apply discount → Save & Print
- ✅ Receipt PDF generation

## Authentication Methods

The test supports two authentication methods:

1. **API Login** (preferred, faster):
   - Directly calls `/api/auth/token/` endpoint
   - Stores token in localStorage

2. **UI Login** (fallback):
   - Navigates to login page
   - Fills form and submits
   - Extracts token from localStorage

## Troubleshooting

### Test fails with "Login failed: No token"
- Check backend is running
- Verify credentials in environment variables
- Check network tab for API errors

### Test fails with "Element not found"
- Ensure frontend is running
- Check if RegistrationPage component is loaded
- Verify route is `/registration`

### PDF generation test fails
- Check backend PDF engine is working
- Verify visit was created successfully
- Check browser console for errors

## Expected Test Duration

- Full test suite: ~2-3 minutes
- Individual tests: ~10-30 seconds each

## CI/CD Integration

Add to your CI pipeline:
```yaml
- name: Run E2E tests
  run: |
    cd frontend
    npx playwright test tests/e2e/registration_v2.spec.ts
  env:
    E2E_BASE_URL: ${{ secrets.E2E_BASE_URL }}
    E2E_API_BASE: ${{ secrets.E2E_API_BASE }}
    E2E_USERNAME: ${{ secrets.E2E_USERNAME }}
    E2E_PASSWORD: ${{ secrets.E2E_PASSWORD }}
```
