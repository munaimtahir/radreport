import { chromium } from '@playwright/test';
import { ensureAuth } from './auth';
import { seedTestData } from './api';
import { waitForApiReady } from '../utils/wait';

export default async function globalSetup() {
  await waitForApiReady();
  seedTestData();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await ensureAuth(page);
  await browser.close();
}
