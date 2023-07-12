import { Page } from '@playwright/test';
import { clickButton } from './forms';
import { goToOnCallPage } from './navigation';

const CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR = 'div[data-testid="create-integration-modal"]';

export const openCreateIntegrationModal = async (page: Page): Promise<void> => {
  // go to the integrations page
  await goToOnCallPage(page, 'integrations');

  // open the create integration modal
  (await page.waitForSelector('text=New integration')).click();

  // wait for it to pop up
  await page.waitForSelector(CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR);
};

export const createIntegration = async (page: Page, integrationName: string): Promise<void> => {
  await openCreateIntegrationModal(page);

  // create a webhook integration
  (await page.waitForSelector(`${CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR} >> text=Webhook`)).click();

  // fill in the required inputs
  (await page.waitForSelector('input[name="verbal_name"]', { state: 'attached' })).fill(integrationName);
  (await page.waitForSelector('textarea[name="description_short"]', { state: 'attached' })).fill(
    'Here goes your integration description'
  );

  const grafanaUpdateBtn = page.getByTestId('update-integration-button');
  await grafanaUpdateBtn.click();
};

export const createIntegrationAndSendDemoAlert = async (
  page: Page,
  integrationName: string,
  _escalationChainName: string
): Promise<void> => {
  await createIntegration(page, integrationName);

  /*
   * TODO: This is slightly more complicated now, change this in next iteration */
  // const integrationSettingsElement = page.getByTestId('integration-settings');

  // // assign the escalation chain to the integration
  // await selectDropdownValue({
  //   page,
  //   selectType: 'grafanaSelect',
  //   placeholderText: 'Select Escalation Chain',
  //   value: escalationChainName,
  //   startingLocator: integrationSettingsElement,
  // });

  // send demo alert
  await clickButton({ page, buttonText: 'Send demo alert', dataTestId: 'send-demo-alert' });
  await clickButton({ page, buttonText: 'Send Alert', dataTestId: 'submit-send-alert' });
};
