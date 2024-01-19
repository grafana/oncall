import { Page, expect } from '@playwright/test';

export const checkWebhookPresenceInTable = async ({
  page,
  webhookName,
  expectedTriggerType,
}: {
  page: Page;
  webhookName: string;
  expectedTriggerType: string;
}) => {
  // filter table to show only created schedule
  await page
    .locator('div')
    .filter({ hasText: /^Search or filter results\.\.\.$/ })
    .nth(1)
    .click();
  await page.keyboard.insertText(webhookName);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2000);

  // webhooks table displays details created webhook
  const webhooksTable = page.getByTestId('outgoing-webhooks-table');
  await expect(webhooksTable.getByRole('cell', { name: webhookName })).toBeVisible();
  await expect(webhooksTable.getByRole('cell', { name: expectedTriggerType })).toBeVisible();
  await expect(webhooksTable.getByRole('cell', { name: webhookName })).toBeVisible();
  await expect(webhooksTable.getByRole('cell', { name: 'No team' })).toBeVisible();
};
