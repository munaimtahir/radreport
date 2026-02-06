import { test, expect } from '@playwright/test';
import {
  expectFieldHidden,
  expectFieldVisible,
  openOrCreateReport,
  saveDraft,
  setFieldByLabel,
  tabThroughAndAssertNotFocusable,
} from './helpers/reporting';

test('USG_ABD_V1 enhanced behaviors', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await openOrCreateReport(page, 'USG_ABD_V1');
  await expect(page.getByTestId('paired-group-kidneys')).toBeVisible();
  await expect(page.getByTestId('paired-group-right-column')).toBeVisible();
  await expect(page.getByTestId('paired-group-left-column')).toBeVisible();

  await setFieldByLabel(page, 'Visualized', 'No');
  await expectFieldHidden(page, 'Length');
  await tabThroughAndAssertNotFocusable(page, 'Length');

  await setFieldByLabel(page, 'Visualized', 'Satisfactory');
  await expectFieldVisible(page, 'Length');
  await setFieldByLabel(page, 'Length', '9.7');

  await saveDraft(page);
  await page.reload();
  await expect(page.locator('input[type="number"]').first()).toHaveValue('9.7');

  await setFieldByLabel(page, 'Visualized', 'No');
  await setFieldByLabel(page, 'Visualized', 'Satisfactory');
  await expect(page.locator('input[type="number"]').first()).toHaveValue('9.7');

  await page.getByRole('button', { name: /preview pdf/i }).click();
  await expect(errors).toEqual([]);
});
