import dotenv from 'dotenv';

dotenv.config({ path: '.env.e2e' });

export const E2E_BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';
export const E2E_API_URL = process.env.E2E_API_URL || 'http://localhost:8000';
export const E2E_USER = process.env.E2E_USER || 'admin';
export const E2E_PASS = process.env.E2E_PASS || 'admin';
