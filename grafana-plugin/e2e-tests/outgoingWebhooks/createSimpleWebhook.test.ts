import { test } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';
import { checkWebhookPresenceInTable } from '../utils/outgoingWebhooks';

test('create simple webhook and check it is displayed on the list correctly', async ({ adminRolePage: { page } }) => {
  const WEBHOOK_NAME = generateRandomValue();
  const WEBHOOK_URL = 'https://example.com';
  await goToOnCallPage(page, 'outgoing_webhooks');

  await clickButton({ page, buttonText: 'New Outgoing Webhook' });

  await page.getByText('Simple').first().click();

  await page.waitForTimeout(2000);

  await page.keyboard.insertText(WEBHOOK_URL);
  await page.locator('[name=name]').fill(WEBHOOK_NAME);
  await page.getByLabel('New Outgoing Webhook').getByRole('img').nth(1).click(); // Open team dropdown
  await page.getByLabel('Select options menu').getByText('No team').click();
  await clickButton({ page, buttonText: 'Create' });

  await checkWebhookPresenceInTable({ page, webhookName: WEBHOOK_NAME, expectedTriggerType: 'Escalation step' });
});
