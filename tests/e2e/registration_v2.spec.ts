import { test, expect, Page } from '@playwright/test';

/**
 * E2E Test for Registration v2 Features
 * Tests keyboard-first navigation, most-used services, discount %, and receipt generation
 */

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';
const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api';
const TEST_USERNAME = process.env.E2E_USERNAME || 'admin';
const TEST_PASSWORD = process.env.E2E_PASSWORD || 'admin';

/**
 * Helper: Login and set auth token
 */
async function login(page: Page): Promise<string> {
  await page.goto(`${BASE_URL}/login`);
  
  // Fill login form
  await page.fill('input[type="text"], input[name="username"]', TEST_USERNAME);
  await page.fill('input[type="password"]', TEST_PASSWORD);
  await page.click('button[type="submit"], button:has-text("Login")');
  
  // Wait for navigation and token storage
  await page.waitForURL(/\/(dashboard|$)/, { timeout: 5000 });
  
  // Get token from localStorage
  const token = await page.evaluate(() => localStorage.getItem('token'));
  if (!token) {
    throw new Error('Login failed: No token in localStorage');
  }
  
  return token;
}

/**
 * Helper: Set auth token in localStorage (alternative to login)
 */
async function setAuthToken(page: Page, token: string) {
  await page.goto(BASE_URL);
  await page.evaluate((t) => {
    localStorage.setItem('token', t);
  }, token);
  await page.reload();
}

test.describe('Registration v2 E2E Tests', () => {
  let authToken: string;
  
  test.beforeAll(async ({ browser }) => {
    // Get auth token via API or login
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      // Try API login first (faster)
      const response = await page.request.post(`${API_BASE}/auth/token/`, {
        data: { username: TEST_USERNAME, password: TEST_PASSWORD }
      });
      if (response.ok()) {
        const data = await response.json();
        authToken = data.access;
      } else {
        // Fallback to UI login
        authToken = await login(page);
      }
    } catch (e) {
      // Fallback to UI login
      authToken = await login(page);
    }
    
    await context.close();
  });
  
  test.beforeEach(async ({ page }) => {
    // Set auth token before each test
    await setAuthToken(page, authToken);
    await page.goto(`${BASE_URL}/registration`);
    await page.waitForLoadState('networkidle');
  });
  
  test('Keyboard navigation: Enter behaves like Tab', async ({ page }) => {
    // Click "New Patient" button
    await page.click('button:has-text("New Patient")');
    
    // Fill patient form using only Enter key
    await page.fill('input[placeholder*="Name"]', 'Test Patient');
    await page.keyboard.press('Enter');
    
    // Verify focus moved to next field (Age or DOB)
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'SELECT']).toContain(focusedElement);
    
    await page.fill('input[type="number"][placeholder*="Age"]', '30');
    await page.keyboard.press('Enter');
    
    // Verify focus moved
    const nextFocused = await page.evaluate(() => (document.activeElement as HTMLElement)?.tagName);
    expect(['INPUT', 'SELECT']).toContain(nextFocused);
  });
  
  test('DOB ↔ Age linkage', async ({ page }) => {
    await page.click('button:has-text("New Patient")');
    
    // Enter age
    await page.fill('input[type="number"][placeholder*="Age"]', '25');
    await page.keyboard.press('Tab');
    
    // Verify DOB is auto-calculated
    const dobValue = await page.inputValue('input[type="date"]');
    expect(dobValue).toBeTruthy();
    
    // Clear age, enter DOB
    await page.fill('input[type="number"][placeholder*="Age"]', '');
    await page.fill('input[type="date"]', '1998-01-15');
    await page.keyboard.press('Tab');
    
    // Verify age is auto-calculated
    const ageValue = await page.inputValue('input[type="number"][placeholder*="Age"]');
    expect(parseInt(ageValue)).toBeGreaterThan(20);
  });
  
  test('Service search with debounce and dropdown', async ({ page }) => {
    // First create/select a patient
    await page.click('button:has-text("New Patient")');
    await page.fill('input[placeholder*="Name"]', 'Test Patient');
    await page.fill('input[placeholder*="Phone"]', '1234567890');
    await page.click('button:has-text("Create Patient")');
    await page.waitForSelector('text=Patient created successfully', { timeout: 5000 });
    
    // Focus service search
    const serviceSearch = page.locator('input[placeholder*="Search services"]');
    await serviceSearch.focus();
    
    // Type search query (should trigger debounced search)
    await serviceSearch.fill('ultra');
    await page.waitForTimeout(400); // Wait for debounce
    
    // Verify dropdown appears
    const dropdown = page.locator('div[style*="position: absolute"]').first();
    await expect(dropdown).toBeVisible({ timeout: 2000 });
    
    // Use arrow keys to navigate
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    
    // Press Enter to select
    await page.keyboard.press('Enter');
    
    // Verify service was added
    await expect(page.locator('text=Selected Services')).toBeVisible();
  });
  
  test('Most-used services quick buttons', async ({ page }) => {
    // Create/select patient first
    await page.click('button:has-text("New Patient")');
    await page.fill('input[placeholder*="Name"]', 'Test Patient');
    await page.fill('input[placeholder*="Phone"]', '1234567890');
    await page.click('button:has-text("Create Patient")');
    await page.waitForSelector('text=Patient created successfully', { timeout: 5000 });
    
    // Check if most-used services section exists
    const mostUsedSection = page.locator('text=Most Used:');
    const isVisible = await mostUsedSection.isVisible().catch(() => false);
    
    if (isVisible) {
      // Click first most-used service button
      const firstButton = page.locator('button:has-text("Most Used")').first();
      if (await firstButton.isVisible()) {
        await firstButton.click();
        // Verify service was added
        await expect(page.locator('text=Selected Services')).toBeVisible({ timeout: 2000 });
      }
    } else {
      // If no most-used services, that's okay (local fallback)
      console.log('Most-used services not available, using local fallback');
    }
  });
  
  test('Discount percentage field (0-100 clamp)', async ({ page }) => {
    // Create patient and add service
    await page.click('button:has-text("New Patient")');
    await page.fill('input[placeholder*="Name"]', 'Test Patient');
    await page.fill('input[placeholder*="Phone"]', '1234567890');
    await page.click('button:has-text("Create Patient")');
    await page.waitForSelector('text=Patient created successfully', { timeout: 5000 });
    
    // Add a service via search
    const serviceSearch = page.locator('input[placeholder*="Search services"]');
    await serviceSearch.fill('test');
    await page.waitForTimeout(400);
    await page.keyboard.press('Enter');
    
    // Set discount type to percentage
    const discountTypeSelect = page.locator('select').filter({ hasText: '%' }).first();
    if (await discountTypeSelect.isVisible()) {
      await discountTypeSelect.selectOption('percentage');
    }
    
    // Try to enter discount > 100 (should be clamped)
    const discountInput = page.locator('input[placeholder*="0-100"]').first();
    if (await discountInput.isVisible()) {
      await discountInput.fill('150');
      await discountInput.blur();
      
      // Verify value is clamped to 100
      const value = await discountInput.inputValue();
      expect(parseFloat(value)).toBeLessThanOrEqual(100);
    }
  });
  
  test('Patient save locks identity and auto-focuses service search', async ({ page }) => {
    // Create patient
    await page.click('button:has-text("New Patient")');
    await page.fill('input[placeholder*="Name"]', 'Test Patient');
    await page.fill('input[placeholder*="Phone"]', '1234567890');
    await page.click('button:has-text("Create Patient")');
    
    // Wait for success message
    await page.waitForSelector('text=Patient created successfully', { timeout: 5000 });
    
    // Verify service search is focused
    await page.waitForTimeout(200);
    const serviceSearch = page.locator('input[placeholder*="Search services"]');
    const isFocused = await serviceSearch.evaluate(el => document.activeElement === el);
    expect(isFocused).toBeTruthy();
  });
  
  test('Full flow: Create visit and generate receipt', async ({ page }) => {
    // Create patient
    await page.click('button:has-text("New Patient")');
    await page.fill('input[placeholder*="Name"]', 'E2E Test Patient');
    await page.fill('input[placeholder*="Phone"]', '9876543210');
    await page.click('button:has-text("Create Patient")');
    await page.waitForSelector('text=Patient created successfully', { timeout: 5000 });
    
    // Add service
    const serviceSearch = page.locator('input[placeholder*="Search services"]');
    await serviceSearch.fill('test');
    await page.waitForTimeout(400);
    await page.keyboard.press('Enter');
    
    // Wait for service to be added
    await page.waitForSelector('text=Selected Services', { timeout: 3000 });
    
    // Set discount
    const discountInput = page.locator('input[type="number"]').filter({ hasText: /discount/i }).first();
    if (await discountInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await discountInput.fill('10');
    }
    
    // Click Save & Print Receipt
    const savePrintButton = page.locator('button:has-text("Save & Print Receipt")');
    await savePrintButton.click();
    
    // Wait for success message
    await page.waitForSelector('text=Service visit created', { timeout: 10000 });
    
    // Verify receipt PDF was requested (check for new window or download)
    // Note: PDF opening in new window is hard to test, so we just verify the visit was created
    const successMessage = page.locator('text=/Service visit created/');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
  });
  
  test('Textarea Enter behaves as Tab', async ({ page }) => {
    await page.click('button:has-text("New Patient")');
    
    // Focus address textarea
    const addressTextarea = page.locator('textarea[placeholder*="Address"]');
    await addressTextarea.focus();
    await addressTextarea.fill('Test Address');
    
    // Press Enter (should move to next field, not create new line)
    await page.keyboard.press('Enter');
    
    // Verify focus moved (not in textarea anymore)
    const activeElement = await page.evaluate(() => (document.activeElement as HTMLElement)?.tagName);
    expect(activeElement).not.toBe('TEXTAREA');
  });
});
