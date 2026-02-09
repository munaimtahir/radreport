import { Page, expect } from '@playwright/test';
import { E2E_USER, E2E_PASS, E2E_BASE_URL } from '../utils/env';
import fs from 'fs';
import path from 'path';

export const AUTH_STATE_PATH = path.join(__dirname, '../../.auth/state.json');

export async function ensureAuth(page: Page) {
  if (fs.existsSync(AUTH_STATE_PATH)) {
    const stats = fs.statSync(AUTH_STATE_PATH);
    const mtime = stats.mtimeMs;
    const now = Date.now();
    // If state is less than 1 hour old, reuse it
    if (now - mtime < 3600000) {
      return;
    }
  }

  await page.goto(`${E2E_BASE_URL}/login`);

  // Try to use data-testid if available, fallback to placeholder
  const emailInput = page.locator('[data-testid="login-email"]').or(page.getByPlaceholder(/email|username/i));
  const passwordInput = page.locator('[data-testid="login-password"]').or(page.getByPlaceholder(/password/i));
  const submitBtn = page.locator('[data-testid="login-submit"]').or(page.getByRole('button', { name: /login/i }));

  await emailInput.fill(E2E_USER);
  await passwordInput.fill(E2E_PASS);
  await submitBtn.click();

  // Wait for navigation to dashboard or home
  await expect(page).toHaveURL(/\/(dashboard)?$/);

  // Ensure .auth directory exists
  const authDir = path.dirname(AUTH_STATE_PATH);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  await page.context().storageState({ path: AUTH_STATE_PATH });
}
