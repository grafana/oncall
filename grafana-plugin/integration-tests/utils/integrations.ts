import { Page } from '@playwright/test';
import { clickButton, fillInInput, selectDropdownValue } from './forms';
import { goToOnCallPage } from './navigation';

const CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR = 'div[data-testid="create-integration-modal"]';

export const openCreateIntegrationModal = async (page: Page): Promise<void> => {
  // go to the integrations page
  await goToOnCallPage(page, 'integrations');

  // open the create integration modal
  (await page.waitForSelector('text=New integration to receive alerts')).click();

  // wait for it to pop up
  await page.waitForSelector(CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR);
};

export const createIntegrationAndSendDemoAlert = async (
  page: Page,
  integrationName: string,
  escalationChainName: string
): Promise<void> => {
  await openCreateIntegrationModal(page);

  // create a webhook integration
  (await page.waitForSelector(`${CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR} >> text=Webhook`)).click();

  // wait for the integrations settings modal to open up... and then close it
  await clickButton({ page, buttonText: 'Open Escalations Settings' });

  // update the integration name
  await (await page.waitForSelector('div[data-testid="integration-header"] >> h4 >> button')).click();
  await fillInInput(page, 'div[data-testid="edit-integration-name-modal"] >> input', integrationName);
  await clickButton({ page, buttonText: 'Update' });

  const integrationSettingsElement = page.getByTestId('integration-settings');

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
