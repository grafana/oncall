import { Page } from '@playwright/test';
import { clickButton, fillInInput, selectDropdownValue } from './forms';
import { goToOnCallPageByClickingOnTab } from './navigation';

export const createIntegrationAndSendDemoAlert = async (
  page: Page,
  integrationName: string,
  escalationChainName: string
): Promise<void> => {
  // go to the integrations page
  await goToOnCallPageByClickingOnTab(page, 'Integrations');

  // open the create integration modal
  (await page.waitForSelector('text=New integration for receiving alerts')).click();

  // create a webhook integration
  (await page.waitForSelector('div[data-testid="create-integration-modal"] >> text=Webhook')).click();

  // wait for the integrations settings modal to open up... and then close it
  await clickButton({ page, buttonText: 'Open Escalations Settings' });

  // update the integration name
  await (await page.waitForSelector('div[data-testid="integration-header"] >> h4 >> button')).click();
  await fillInInput(page, 'div[data-testid="edit-integration-name-modal"] >> input', integrationName);
  await clickButton({ page, buttonText: 'Update' });

  const integrationSettingsElement = page.locator('div[data-testid="integration-settings"]');

  // assign the escalation chain to the integration
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Select Escalation Chain',
    value: escalationChainName,
    startingLocator: integrationSettingsElement,
  });

  // send demo alert
  await clickButton({ page, buttonText: 'Send demo alert', dataTestId: 'send-demo-alert' });
};
