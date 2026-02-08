import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { E2E_SEED_CMD, E2E_SEED_JSON, E2E_SEED_ALWAYS, E2E_USER, E2E_PASS, getAuthUrl } from '../utils/env';

export type SeedData = {
  username: string;
  password: string;
  workitemId: string;
  reportTemplateCode: string;
  reportInstanceId?: string | null;
  patientName?: string;
  patientMrn?: string;
  serviceCode?: string;
  visitId?: string;
};

function ensureSeedDir() {
  const dir = path.dirname(E2E_SEED_JSON);
  if (!dir || dir === '.') return;
  fs.mkdirSync(dir, { recursive: true });
}

function runSeedCommand() {
  ensureSeedDir();
  const command =
    E2E_SEED_CMD ||
    `python3 backend/manage.py e2e_seed --json-out ${E2E_SEED_JSON} --username ${E2E_USER} --password ${E2E_PASS}`;
  execSync(command, { stdio: 'inherit', env: process.env, shell: true });
}

function readSeedFile(): SeedData {
  if (!fs.existsSync(E2E_SEED_JSON)) {
    throw new Error(`Seed file not found at ${E2E_SEED_JSON}`);
  }
  const raw = fs.readFileSync(E2E_SEED_JSON, 'utf-8');
  const data = JSON.parse(raw) as SeedData;
  if (!data.workitemId || !data.reportTemplateCode || !data.username || !data.password) {
    throw new Error(`Seed file missing required fields: ${E2E_SEED_JSON}`);
  }
  return data;
}

export function seedTestData(): SeedData {
  if (E2E_SEED_ALWAYS || !fs.existsSync(E2E_SEED_JSON)) {
    runSeedCommand();
  }
  return readSeedFile();
}

export function loadSeedData(): SeedData {
  if (!fs.existsSync(E2E_SEED_JSON)) {
    return seedTestData();
  }
  return readSeedFile();
}

export async function apiLogin(username = E2E_USER, password = E2E_PASS): Promise<string> {
  if (!globalThis.fetch) {
    throw new Error('Global fetch is not available in this Node runtime.');
  }
  const res = await fetch(getAuthUrl(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Login failed (${res.status}): ${text}`);
  }
  const data = await res.json();
  return data.access;
}
