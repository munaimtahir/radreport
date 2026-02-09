import { Page } from '@playwright/test';
import { E2E_API_URL } from './env';

/**
 * Wait for a small amount of time for animations or eventual consistency
 */
export async function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Wait for network to be idle
 */
export async function waitForIdle(page: Page) {
  await page.waitForLoadState('networkidle');
}

/**
 * Polls the API health endpoint until it returns 200
 */
export async function waitForApiReady() {
  const maxRetries = 30;
  const delayMs = 1000;

  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await fetch(`${E2E_API_URL}/api/health/`);
      if (res.ok) return;
    } catch (e) {
      // ignore
    }
    await new Promise(r => setTimeout(r, delayMs));
  }
  throw new Error(`API at ${E2E_API_URL} did not become ready in time.`);
}
