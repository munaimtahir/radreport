import { Page } from '@playwright/test';

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
