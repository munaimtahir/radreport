import { getHealthUrl } from './env';

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function waitForApiReady(timeoutMs = 60_000) {
  const healthUrl = getHealthUrl();
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(healthUrl, { method: 'GET' });
      if (res.ok) return;
    } catch {
      // ignore and retry
    }
    await sleep(1500);
  }

  throw new Error(`API health check timed out after ${timeoutMs}ms at ${healthUrl}`);
}
