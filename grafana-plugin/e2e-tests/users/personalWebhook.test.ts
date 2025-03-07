import { test, expect } from '../fixtures';
import grafanaApiClient from '../utils/clients/grafana';
import { clickButton, generateRandomValue } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';
import { checkWebhookPresenceInTable } from '../utils/outgoingWebhooks';

const WEBHOOK_NAME = generateRandomValue();
const TRIGGER_TYPE = 'Personal Notification';

let webhookID: string;

test.afterAll(async ({ request }) => {
  // Delete the created webhook
  if (webhookID) {
    await grafanaApiClient.makeRequest(
      request,
      `resources/webhooks/${webhookID}/`,
      'delete',
    )
  }
});

test('Connects a personal notification webhook', async ({ adminRolePage: { page } }) => {
  // Create a new webhook
  await goToOnCallPage(page, 'outgoing_webhooks');
  await page.getByRole('button', { name: 'New Outgoing Webhook' }).click();

  // Choose Advanced webhook
  await page.getByTestId('create-outgoing-webhook-modal').locator('div').filter({ hasText: 'AdvancedAn advanced webhook' }).first().click();

  // Give it a name
  await page.locator('input[name="name"]').fill(WEBHOOK_NAME);

  // Choose a trigger type
  await page.getByTestId('triggerType-selector').locator('div').nth(1).click();
  await page.getByLabel('Select options menu').getByText(TRIGGER_TYPE).click();

  // Set a URL
  await page.locator('#OutgoingWebhook div').locator('.monaco-editor').first().click();
  await page.keyboard.insertText('https://example.com');

  // Create and check it has been created
  const responsePromise = page.waitForResponse('**/resources/webhooks/');
  await clickButton({ page, buttonText: 'Create' });
  await checkWebhookPresenceInTable({ page, webhookName: WEBHOOK_NAME, expectedTriggerType: TRIGGER_TYPE });

  // save the ID so we can delete the webhook after the tests have run
  const response = await responsePromise;
  const wh = await response.json();
  webhookID = wh?.id;

  await goToOnCallPage(page, 'users/me');
  await page.getByRole('tab', { name: 'Webhook connection' }).click();

  // Select webhook
  await page.getByRole('dialog').locator('svg').nth(2).click();
  await page.getByLabel('Select options menu').getByText(WEBHOOK_NAME).click();

  // Add some context
  await page.getByRole('textbox').fill('{ "test": true }');

  // Connect
  await page.getByRole('button', { name: 'Connect' }).click();
  await page.waitForSelector('text=Disconnect');

  // Check connection on User Info tab
  await page.getByRole('tab', { name: 'User info' }).click();
  expect(page.getByText(WEBHOOK_NAME)).toBeVisible();

  // Disconnect 
  await page.getByRole('tab', { name: 'Webhook connection' }).click();
  await page.getByRole('button', { name: 'Disconnect' }).click();
  await page.getByTestId('data-testid Confirm Modal Danger Button').click();

  // Check connection is no longer shown
  await page.getByRole('tab', { name: 'User info' }).click();
  expect(page.getByText(WEBHOOK_NAME)).not.toBeVisible();
})
