import { chromium } from '@playwright/test';
import { ensureAuth } from './auth';
import { waitForApiReady } from '../utils/wait';

export default async function globalSetup() {
  await waitForApiReady();
  // We rely on per-spec bootstrapping or existing data, so no global seed here.
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await ensureAuth(page);
  await browser.close();
}
