import { test, expect } from '@playwright/test';
import {
  expectFieldHidden,
  expectFieldVisible,
  openOrCreateReport,
  saveDraft,
  setFieldByLabel,
  setSegmentedYesNo,
  tabThroughAndAssertNotFocusable,
} from './helpers/reporting';

test('USG_PELVIS_V1 enhanced ovaries and persistence', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await openOrCreateReport(page, 'USG_PELVIS_V1');
  await expect(page.getByTestId('paired-group-ovaries')).toBeVisible();

  await setSegmentedYesNo(page, 'Adnexal mass present', 'No');
  await expectFieldHidden(page, 'Vascularity');
  await tabThroughAndAssertNotFocusable(page, 'Vascularity');

  await setSegmentedYesNo(page, 'Adnexal mass present', 'Yes');
  await expectFieldVisible(page, 'Vascularity');
  await setFieldByLabel(page, 'Post-void residual (mL)', '45');

  await saveDraft(page);
  await page.reload();
  await expect(page.locator('input[type="number"]').first()).toHaveValue('45');

  await setSegmentedYesNo(page, 'Adnexal mass present', 'No');
  await setSegmentedYesNo(page, 'Adnexal mass present', 'Yes');
  await expect(page.locator('input[type="number"]').first()).toHaveValue('45');

  await page.getByRole('button', { name: /preview pdf/i }).click();
  await expect(errors).toEqual([]);
});
