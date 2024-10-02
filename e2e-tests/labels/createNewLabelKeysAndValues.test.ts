import { test, expect } from '../fixtures';
import { isGrafanaVersionGreaterThan } from '../utils/constants';
import { clickButton, generateRandomValidLabel, openDropdown } from '../utils/forms';
import { openCreateIntegrationModal } from '../utils/integrations';
import { goToOnCallPage } from '../utils/navigation';

test.skip(
  () => isGrafanaVersionGreaterThan('10.3.0'),
  'Above 10.3 labels need enterprise version to validate permissions'
);

// TODO: This test is flaky on CI. Undo skipping once we can test labels locally
test.skip('New label keys and labels can be created @expensive', async ({ adminRolePage }) => {
  const { page } = adminRolePage;
  await goToOnCallPage(page, 'integrations');
  await openCreateIntegrationModal(page);
  const NEW_LABEL_KEY = generateRandomValidLabel();
  const NEW_LABEL_VALUE = generateRandomValidLabel();

  await page
    .getByTestId('create-integration-modal')
    .getByTestId('integration-display-name')
    .filter({ hasText: 'Webhook' })
    .first()
    .click();
  await clickButton({ page, buttonText: /^Add Labels$/ });

  await openDropdown({ page, text: /^Select key$/ });
  await page.keyboard.insertText(NEW_LABEL_KEY);
  await page.getByText('Hit enter to add').waitFor();
  await page.keyboard.press('Enter');

  await page.waitForTimeout(1000);

  await openDropdown({ page, text: /^Select value$/ });
  await page.keyboard.insertText(NEW_LABEL_VALUE);
  await page.getByText('Hit enter to add').waitFor();
  await page.keyboard.press('Enter');

  await expect(page.getByText(NEW_LABEL_KEY)).toBeVisible();
  await expect(page.getByText(NEW_LABEL_VALUE)).toBeVisible();
});
