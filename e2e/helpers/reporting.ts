import { expect, Locator, Page } from '@playwright/test';

function escapeRegex(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function findFieldControlByLabel(page: Page, labelText: string): Promise<Locator> {
  const label = page.locator('label', { hasText: new RegExp(`^${escapeRegex(labelText)}\\s*\\*?$`, 'i') }).first();
  await expect(label).toBeVisible();
  const container = label.locator('xpath=..');
  const control = container.locator('input, select, textarea').first();
  await expect(control).toHaveCount(1);
  return control;
}

export async function gotoReporting(page: Page) {
  await page.goto('/reporting/worklist');
  await expect(page.getByRole('heading', { name: /reporting worklist/i })).toBeVisible();
}

export async function openOrCreateReport(page: Page, templateCode: string) {
  await gotoReporting(page);

  const row = page.locator('tr', { hasText: templateCode }).first();
  if (await row.count()) {
    await row.getByRole('button', { name: /enter report|view report/i }).first().click();
    await expect(page).toHaveURL(/\/reporting\/worklist\/\d+\/report/);
    return;
  }

  throw new Error(`No worklist row found for template ${templateCode}. Seed data/work item is required for this template.`);
}

export async function setFieldByLabel(page: Page, labelText: string, value: string | number) {
  const control = await findFieldControlByLabel(page, labelText);
  const tagName = await control.evaluate((el) => el.tagName.toLowerCase());

  if (tagName === 'select') {
    await control.selectOption(String(value));
    return;
  }

  await control.fill(String(value));
}

export async function setSegmentedYesNo(page: Page, fieldLabel: string, yesNo: 'Yes' | 'No') {
  const label = page.locator('label', { hasText: new RegExp(`^${escapeRegex(fieldLabel)}\\s*\\*?$`, 'i') }).first();
  await expect(label).toBeVisible();
  const container = label.locator('xpath=..');
  await container.getByTestId(`segmented-boolean-${yesNo.toLowerCase()}`).click();
}

export async function expectFieldHidden(page: Page, labelText: string) {
  const label = page.locator('label', { hasText: new RegExp(`^${escapeRegex(labelText)}\\s*\\*?$`, 'i') }).first();
  await expect(label).toBeHidden();
}

export async function expectFieldVisible(page: Page, labelText: string) {
  const label = page.locator('label', { hasText: new RegExp(`^${escapeRegex(labelText)}\\s*\\*?$`, 'i') }).first();
  await expect(label).toBeVisible();
}

export async function tabThroughAndAssertNotFocusable(page: Page, labelText: string) {
  for (let i = 0; i < 50; i += 1) {
    await page.keyboard.press('Tab');
    const activeLabel = await page.evaluate(() => {
      const active = document.activeElement as HTMLElement | null;
      if (!active) return '';
      const fieldContainer = active.closest('div');
      const label = fieldContainer?.querySelector('label');
      return label?.textContent?.trim() || '';
    });

    expect(activeLabel.toLowerCase()).not.toContain(labelText.toLowerCase());
  }
}

export async function saveDraft(page: Page) {
  await page.getByRole('button', { name: /save draft/i }).click();
  await expect(page.getByText(/draft saved successfully/i)).toBeVisible();
}
