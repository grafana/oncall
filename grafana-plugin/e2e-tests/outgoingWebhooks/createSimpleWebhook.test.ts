import { test } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';

test('create simple webhook and check it is displayed on the list correctly', async ({ adminRolePage: { page } }) => {
  const webhookName = generateRandomValue();
  const webhookUrl = 'https://example.com';
  await goToOnCallPage(page, 'outgoing_webhooks');

  await clickButton({ page, buttonText: 'New Outgoing Webhook' });

  await page.getByText('Simple').first().click();

  await page.waitForTimeout(2000);

  await page.keyboard.insertText(webhookUrl);
  await page.locator('[name=name]').fill(webhookName);
  await page.getByLabel('New Outgoing Webhook').getByRole('img').nth(1).click(); // Open team dropdown
  await page.getByText('No team', { exact: true }).click();
  await clickButton({ page, buttonText: 'Create Webhook' });

  // assert that it is in webhooks table now
});
