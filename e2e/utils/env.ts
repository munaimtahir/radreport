import dotenv from 'dotenv';

dotenv.config({ path: process.env.E2E_ENV_FILE || '.env.e2e' });

export const E2E_BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:8000';
export const E2E_API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api';
export const E2E_USER = process.env.E2E_USER || 'e2e_reporter';
export const E2E_PASS = process.env.E2E_PASS || 'e2e_password';
export const E2E_SEED_JSON = process.env.E2E_SEED_JSON || 'e2e/artifacts/seed.json';
export const E2E_SEED_CMD = process.env.E2E_SEED_CMD || '';
export const E2E_SEED_ALWAYS = process.env.E2E_SEED_ALWAYS !== 'false';

export function getHealthUrl() {
  const base = E2E_API_BASE.replace(/\/$/, '');
  return `${base}/health/`;
}

export function getAuthUrl() {
  const base = E2E_API_BASE.replace(/\/$/, '');
  return `${base}/auth/token/`;
}
