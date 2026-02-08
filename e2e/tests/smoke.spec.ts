import { test, expect, Page } from '@playwright/test';
import { loadSeedData, apiLogin } from '../fixtures/api';
import { selectors, fieldTestId, workitemRowTestId, openReportTestId } from '../fixtures/selectors';
import { E2E_API_BASE } from '../utils/env';

const apiBase = E2E_API_BASE.replace(/\/$/, '');

async function fillSelect(page: Page, field: string, value: string) {
  const fieldLoc = page.getByTestId(fieldTestId(field));
  await expect(fieldLoc).toBeVisible();
  await fieldLoc.locator('select').selectOption(value);
}

async function fillNumber(page: Page, field: string, value: number) {
  const fieldLoc = page.getByTestId(fieldTestId(field));
  await expect(fieldLoc).toBeVisible();
  await fieldLoc.locator('input').fill(String(value));
}

async function setSegmented(page: Page, field: string, yesNo: 'yes' | 'no') {
  const fieldLoc = page.getByTestId(fieldTestId(field));
  await expect(fieldLoc).toBeVisible();
  await fieldLoc.getByTestId(`segmented-boolean-${yesNo}`).click();
}

function reportPdfUrl(workitemId: string) {
  return `${apiBase}/reporting/workitems/${workitemId}/report-pdf/`;
}

function publishedPdfUrl(workitemId: string, version = 1) {
  return `${apiBase}/reporting/workitems/${workitemId}/published-pdf/?version=${version}`;
}

test('V2 reporting smoke', async ({ page, request }) => {
  const seed = loadSeedData();

  await page.goto('/reporting/worklist');
  await expect(page.getByTestId(selectors.reportingWorklist)).toBeVisible();
  await expect(page.getByTestId(selectors.worklistTable)).toBeVisible();

  const row = page.getByTestId(workitemRowTestId(seed.workitemId));
  await expect(row).toBeVisible();
  await row.getByTestId(openReportTestId(seed.workitemId)).click();

  await expect(page).toHaveURL(new RegExp(`/reporting/worklist/${seed.workitemId}/report`));
  await expect(page.getByTestId(selectors.reportingRoot)).toBeVisible();
  await expect(page.getByTestId(selectors.reportTemplateCode)).toHaveText(seed.reportTemplateCode);

  await fillSelect(page, 'liv_visualized', 'Satisfactory');
  await fillNumber(page, 'liv_size_cm', 15.2);
  await fillSelect(page, 'liv_echogenicity', 'Normal');
  await fillSelect(page, 'gb_visualized', 'Satisfactory');
  await setSegmented(page, 'gb_stones_present', 'yes');
  await fillSelect(page, 'kid_r_visualized', 'Satisfactory');
  await fillSelect(page, 'kid_l_visualized', 'Satisfactory');
  await fillNumber(page, 'kid_r_length_cm', 9.8);
  await fillNumber(page, 'kid_l_length_cm', 10.1);
  await setSegmented(page, 'kid_r_calculus_present', 'yes');
  await setSegmented(page, 'kid_l_calculus_present', 'no');

  await page.getByTestId(selectors.reportSave).click();
  await expect(page.getByTestId(selectors.reportSuccess)).toBeVisible();

  await page.reload();
  await expect(page.getByTestId(fieldTestId('liv_visualized')).locator('select')).toHaveValue('Satisfactory');
  await expect(page.getByTestId(fieldTestId('liv_size_cm')).locator('input')).toHaveValue('15.2');
  await expect(page.getByTestId(fieldTestId('kid_r_length_cm')).locator('input')).toHaveValue('9.8');
  await expect(page.getByTestId(fieldTestId('kid_l_length_cm')).locator('input')).toHaveValue('10.1');

  await page.getByTestId(selectors.reportSubmit).click();
  await page.getByTestId(selectors.reportSubmitConfirm).click();
  await expect(page.getByTestId(selectors.reportStatus)).toContainText('submitted');

  await page.getByTestId(selectors.reportVerify).click();
  await expect(page.getByTestId(selectors.reportStatus)).toContainText('verified');

  const [pdfResponse] = await Promise.all([
    page.waitForResponse((resp) => resp.url().includes('/report-pdf/') && resp.status() === 200),
    page.getByTestId(selectors.reportPreview).click(),
  ]);
  expect(pdfResponse.headers()['content-type']).toContain('application/pdf');

  await page.getByTestId(selectors.reportPublish).click();
  await page.getByTestId(selectors.reportPublishNotes).fill('e2e smoke');
  await page.getByTestId(selectors.reportPublishConfirm).fill('PUBLISH');
  await page.getByTestId(selectors.reportPublishConfirmButton).click();
  await expect(page.getByTestId(selectors.publishHistory)).toBeVisible();

  const token = await apiLogin(seed.username, seed.password);
  const preview = await request.get(reportPdfUrl(seed.workitemId), {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(preview.status()).toBe(200);
  expect(preview.headers()['content-type']).toContain('application/pdf');
  expect((await preview.body()).length).toBeGreaterThan(1000);

  const published = await request.get(publishedPdfUrl(seed.workitemId, 1), {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(published.status()).toBe(200);
  expect(published.headers()['content-type']).toContain('application/pdf');
  expect((await published.body()).length).toBeGreaterThan(1000);
});
