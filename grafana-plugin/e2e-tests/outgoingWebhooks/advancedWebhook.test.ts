import { test } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { createIntegration } from '../utils/integrations';
import { goToOnCallPage } from '../utils/navigation';
import { checkWebhookPresenceInTable } from '../utils/outgoingWebhooks';

test('create advanced webhook and check it is displayed on the list correctly', async ({ adminRolePage: { page } }) => {
  const WEBHOOK_NAME = generateRandomValue();
  const WEBHOOK_INTEGRATION_NAME = generateRandomValue();
  const WEBHOOK_URL = 'https://example.com';

  await createIntegration({ page, integrationSearchText: 'Webhook', integrationName: WEBHOOK_INTEGRATION_NAME });

  await goToOnCallPage(page, 'outgoing_webhooks');

  await clickButton({ page, buttonText: 'New Outgoing Webhook' });
  await page.getByText('Advanced').first().click();
  await page.waitForTimeout(2000);

  const webhooksFormDivs = page.locator('#OutgoingWebhook div');

  // Enter webhook name
  await webhooksFormDivs.locator('[name=name]').fill(WEBHOOK_NAME);

  // Select team
  await page.getByLabel('New Outgoing Webhook').getByRole('img').nth(1).click(); // Open team dropdown
  await page.getByLabel('Select options menu').getByText('No team').click(); // Select "No team"

  // Select trigger type
  await webhooksFormDivs.filter({ hasText: 'Trigger Type' }).getByRole('img').click();
  await page.getByLabel('Select options menu').getByText('Resolved', { exact: true }).click();

  // Select integration
  await webhooksFormDivs.filter({ hasText: 'Integrations' }).getByText('Choose').click();
  await page.keyboard.insertText(WEBHOOK_INTEGRATION_NAME.slice(0, -1));
  await page.waitForTimeout(1000);
  await page.getByText(WEBHOOK_INTEGRATION_NAME).click();

  // Enter webhook URL
  await webhooksFormDivs.locator('.monaco-editor').first().click();
  await page.keyboard.insertText(WEBHOOK_URL);

  await clickButton({ page, buttonText: 'Create' });

  await checkWebhookPresenceInTable({ page, webhookName: WEBHOOK_NAME, expectedTriggerType: 'Resolved' });
});
