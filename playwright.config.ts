import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config({ path: process.env.E2E_ENV_FILE || '.env.e2e' });

const baseURL = process.env.E2E_BASE_URL || 'http://localhost:8000';

export default defineConfig({
  testDir: './e2e/tests',
  testMatch: ['**/*.spec.ts'],
  fullyParallel: false,
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  retries: process.env.CI ? 2 : 1,
  reporter: [
    ['html', { outputFolder: 'e2e/artifacts/playwright-report', open: 'never' }],
    ['line']
  ],
  use: {
    baseURL,
    trace: 'on-first-retry',
    video: 'on-first-retry',
    screenshot: 'on-first-retry',
    headless: true,
    storageState: 'e2e/.auth/state.json',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],
  globalSetup: './e2e/fixtures/global-setup.ts',
  outputDir: 'e2e/artifacts/test-results',
});
