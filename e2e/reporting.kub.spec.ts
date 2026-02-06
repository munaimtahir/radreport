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

test('USG_KUB_V1 enhanced paired layout and invariants', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await openOrCreateReport(page, 'USG_KUB_V1');
  await expect(page.getByTestId('paired-group-kidneys')).toBeVisible();
  await expect(page.getByTestId('paired-group-ureters')).toBeVisible();

  await setSegmentedYesNo(page, 'Visualized', 'No');
  await expectFieldHidden(page, 'Hydroureter present');
  await tabThroughAndAssertNotFocusable(page, 'Hydroureter present');

  await setSegmentedYesNo(page, 'Visualized', 'Yes');
  await expectFieldVisible(page, 'Hydroureter present');
  await setSegmentedYesNo(page, 'Hydroureter present', 'Yes');
  await setFieldByLabel(page, 'Length', 10.2);

  await saveDraft(page);
  await page.reload();
  await expect(page.locator('input[type="number"]').first()).toHaveValue('10.2');

  await setSegmentedYesNo(page, 'Visualized', 'No');
  await setSegmentedYesNo(page, 'Visualized', 'Yes');
  await expect(page.locator('input[type="number"]').first()).toHaveValue('10.2');

  await page.getByRole('button', { name: /preview pdf/i }).click();
  await expect(errors).toEqual([]);
});
