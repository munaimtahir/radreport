import fs from 'fs';
import path from 'path';
import type { Page } from '@playwright/test';
import { E2E_BASE_URL, E2E_USER, E2E_PASS } from '../utils/env';
import { selectors } from './selectors';

const AUTH_PATH = 'e2e/.auth/state.json';
const TOKEN_KEY = 'token';

function decodeJwtPayload(token: string): { exp?: number } | null {
  const parts = token.split('.');
  if (parts.length < 2) return null;
  try {
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = payload.padEnd(payload.length + ((4 - (payload.length % 4)) % 4), '=');
    const json = Buffer.from(padded, 'base64').toString('utf8');
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function isTokenValid(token: string, leewaySeconds = 60): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload?.exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return payload.exp > now + leewaySeconds;
}

export function readTokenFromStorageState(statePath = AUTH_PATH): string | null {
  if (!fs.existsSync(statePath)) return null;
  const raw = fs.readFileSync(statePath, 'utf-8');
  const data = JSON.parse(raw);
  const origins = Array.isArray(data.origins) ? data.origins : [];
  for (const origin of origins) {
    const items = Array.isArray(origin.localStorage) ? origin.localStorage : [];
    const tokenItem = items.find((entry: any) => entry.name === TOKEN_KEY);
    if (tokenItem?.value) return tokenItem.value;
  }
  return null;
}

export async function ensureAuth(page: Page) {
  const token = readTokenFromStorageState();
  if (token && isTokenValid(token)) return;

  fs.mkdirSync(path.dirname(AUTH_PATH), { recursive: true });

  await page.goto(`${E2E_BASE_URL.replace(/\/$/, '')}/login`);
  await page.getByTestId(selectors.loginUsername).fill(E2E_USER);
  await page.getByTestId(selectors.loginPassword).fill(E2E_PASS);
  await page.getByTestId(selectors.loginSubmit).click();
  await page.waitForURL(/\/$/);

  await page.context().storageState({ path: AUTH_PATH });
}
