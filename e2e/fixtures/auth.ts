import { Page, expect } from '@playwright/test';
import { E2E_BASE_URL, E2E_USER, E2E_PASS } from '../utils/env';
import fs from 'fs';
import path from 'path';

export const AUTH_STATE_PATH = path.join(__dirname, '../.auth/state.json');

export async function ensureAuth(page: Page) {
  await page.goto(`${E2E_BASE_URL}/login`);

  // Use explicit selectors from current Login view with a fallback.
  const usernameInput = page.locator('[data-testid="login-username"]').or(page.getByPlaceholder(/username/i));
  const passwordInput = page.locator('[data-testid="login-password"]').or(page.getByPlaceholder(/password/i));
  const submitBtn = page.locator('[data-testid="login-submit"]').or(page.getByRole('button', { name: /login/i }));

  await usernameInput.fill(E2E_USER);
  await passwordInput.fill(E2E_PASS);
  await submitBtn.click();

  // Auth success gate: logout button is rendered in shell when token/user load succeeds.
  await expect(page.getByRole('button', { name: /logout/i })).toBeVisible();

  // Ensure .auth directory exists
  const authDir = path.dirname(AUTH_STATE_PATH);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  await page.context().storageState({ path: AUTH_STATE_PATH });
}
