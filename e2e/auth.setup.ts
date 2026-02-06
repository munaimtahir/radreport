import { test, expect } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config({ path: '.env.e2e' });

const user = process.env.E2E_USER;
const pass = process.env.E2E_PASS;

test('authenticate once and persist storage state', async ({ page }) => {
  if (!user || !pass) {
    throw new Error('E2E_USER and E2E_PASS must be set in .env.e2e or environment.');
  }

  await page.goto('/login');
  await page.getByPlaceholder('Username').fill(user);
  await page.getByPlaceholder('Password').fill(pass);
  await page.getByRole('button', { name: /login/i }).click();

  await expect(page).toHaveURL(/\/$/);
  await page.context().storageState({ path: 'e2e/.auth/state.json' });
});
