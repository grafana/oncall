import { test } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { createIntegration } from '../utils/integrations';
import { goToOnCallPage } from '../utils/navigation';

test('create advanced webhook and check it is displayed on the list correctly', async ({ adminRolePage: { page } }) => {
  const WEBHOOK_NAME = generateRandomValue();
  const WEBHOOK_INTEGRATION_NAME = generateRandomValue();
  const WEBHOOK_URL = 'https://example.com';

  await createIntegration({ page, integrationSearchText: 'Webhook', integrationName: WEBHOOK_INTEGRATION_NAME });

  await goToOnCallPage(page, 'outgoing_webhooks');

  await clickButton({ page, buttonText: 'New Outgoing Webhook' });
  await page.getByText('Advanced').first().click();
  await page.waitForTimeout(2000);

  const webhooksForm = page.locator('#OutgoingWebhook div');

  // Enter webhook name
  await webhooksForm.locator('[name=name]').fill(WEBHOOK_NAME);

  // Select team
  await page.getByLabel('New Outgoing Webhook').getByRole('img').nth(1).click(); // Open team dropdown
  await page.getByLabel('Select options menu').getByText('No team').click(); // Select "No team"

  // Select trigger type
  await webhooksForm.filter({ hasText: 'Trigger Type' }).getByRole('img').click();
  await webhooksForm.getByText('Resolved', { exact: true }).click();

  // Select integration
  await webhooksForm.filter({ hasText: 'Integrations' }).getByText('Choose').click();
  await page.keyboard.insertText(WEBHOOK_INTEGRATION_NAME.slice(0, -1));
  await webhooksForm.getByText(WEBHOOK_INTEGRATION_NAME).click();

  // Enter webhook URL
  await webhooksForm.filter({ hasText: 'Webhook URL' }).getByTestId('monaco-editor').click();
  await page.keyboard.insertText(WEBHOOK_URL);

  await clickButton({ page, buttonText: 'Create Webhook' });

  // filter table to show only created schedule
  await page
    .locator('div')
    .filter({ hasText: /^Search or filter results\.\.\.$/ })
    .nth(1)
    .click();
  await page.keyboard.insertText(WEBHOOK_NAME);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2000);

  // schedules table displays details created schedule
  const webhooksTable = page.getByTestId('outgoing-webhooks-table');
  await expect(webhooksTable.getByRole('cell', { name: WEBHOOK_NAME })).toBeVisible();
  await expect(webhooksTable.getByRole('cell', { name: 'Resolved' })).toBeVisible();
  await expect(webhooksTable.getByRole('cell', { name: WEBHOOK_URL })).toBeVisible();
  await expect(webhooksTable.getByRole('cell', { name: 'No team' })).toBeVisible();
});
