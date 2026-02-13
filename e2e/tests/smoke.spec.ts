import { test, expect } from '@playwright/test';
import { ensureAuth } from '../fixtures/auth';
import { loginAPI, bootstrapV2ReportByTemplateCode } from '../fixtures/api';
import { SELECTORS } from '../fixtures/selectors';
import { waitForIdle } from '../utils/wait';

test.describe('RadReport V2 Smoke Workflow', () => {
  let bootstrapData: any;

  test.beforeAll(async () => {
    // Bootstrap data via API to ensure deterministic starting state
    const session = await loginAPI();
    bootstrapData = await bootstrapV2ReportByTemplateCode(session, 'USG_ABD_V1');
  });

  test('V2 reporting smoke: fill, save, verify, preview', async ({ page }) => {
    // 1. Auth and Navigate
    await ensureAuth(page);
    await page.goto(`/reporting/worklist/${bootstrapData.workItemId}/report`);

    // 2. Assert V2 UI is loaded
    await expect(page.locator(SELECTORS.report.v2Marker)).toBeVisible();
    await expect(page.locator(SELECTORS.report.status)).toBeVisible();

    // 3. Fill Fields
    // Enum
    await page.locator(`${SELECTORS.report.field('liv_visualized')} select`).selectOption('Satisfactory');

    // Number
    await page.locator(`${SELECTORS.report.field('liv_size_cm')} input`).fill('14.5');

    // 4. Save Draft
    await page.locator(SELECTORS.report.save).click();
    await expect(page.locator('[data-testid="report-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="report-success"]')).toContainText(/saved/i);

    // 5. Reload and Verify Persistence
    await page.reload();
    await expect(page.locator(`${SELECTORS.report.field('liv_size_cm')} input`)).toHaveValue('14.5');

    // 6. Submit and Verify
    await page.locator('[data-testid="report-submit"]').click();
    await page.locator('[data-testid="submit-confirm"]').click();

    // Wait for status change
    await expect(page.locator(SELECTORS.report.status)).toContainText(/submitted/i);

    // Verify (if admin/superuser)
    await page.locator('[data-testid="report-verify"]').click();
    await expect(page.locator(SELECTORS.report.status)).toContainText(/verified/i);

    // 7. Publish
    await page.locator('[data-testid="report-publish"]').click();
    await page.locator('[data-testid="publish-confirm"]').fill('PUBLISH');
    await page.locator('[data-testid="publish-confirm-button"]').click();

    await expect(page.locator(SELECTORS.report.status)).toContainText(/verified/i);
    await expect(page.locator(SELECTORS.report.status)).toContainText(/published/i);

    // 8. Open PDF Preview
    const [newPage] = await Promise.all([
      page.context().waitForEvent('page'),
      page.locator(SELECTORS.report.preview).click(),
    ]);

    await newPage.waitForLoadState();
    expect(newPage.url()).toContain('/print/report/');
    // Assuming PDF is served, we check if it didn't crash
    const response = await newPage.reload(); // simple check
    expect(response?.status()).toBe(200);
  });
});
