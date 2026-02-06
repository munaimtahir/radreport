import { test, expect } from '@playwright/test';
import { gotoReporting, saveDraft } from './helpers/reporting';

const ENHANCED = new Set(['USG_ABD_V1', 'USG_KUB_V1', 'USG_PELVIS_V1']);

test('non-enhanced template uses fallback renderer', async ({ page }) => {
  await gotoReporting(page);

  const rows = page.locator('tbody tr');
  const count = await rows.count();
  let fallbackRow = null as any;

  for (let i = 0; i < count; i += 1) {
    const row = rows.nth(i);
    const txt = await row.textContent();
    const match = txt?.match(/[A-Z]{2,}_[A-Z0-9_]+_V\d+/);
    if (match && !ENHANCED.has(match[0])) {
      fallbackRow = row;
      break;
    }
  }

  test.skip(!fallbackRow, 'No fallback template row available in seeded worklist data.');

  await fallbackRow.getByRole('button', { name: /enter report|view report/i }).click();
  await expect(page).toHaveURL(/\/reporting\/worklist\/\d+\/report/);

  await expect(page.getByTestId('paired-group-kidneys')).toHaveCount(0);
  await expect(page.getByTestId('paired-group-ureters')).toHaveCount(0);
  await expect(page.getByTestId('paired-group-ovaries')).toHaveCount(0);
  await expect(page.getByTestId('measurement-unit-badge')).toHaveCount(0);
  await expect(page.getByTestId('segmented-boolean')).toHaveCount(0);

  await saveDraft(page);
  await page.reload();
  await expect(page.getByRole('button', { name: /save draft/i })).toBeVisible();
});
