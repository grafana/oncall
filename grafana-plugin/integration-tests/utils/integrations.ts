import { Page } from '@playwright/test';
// import { clickButton, fillInInput, selectDropdownValue } from './forms';
import { goToOnCallPage } from './navigation';
// import { click } from '@testing-library/user-event/dist/types/convenience';

const CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR = 'div[data-testid="create-integration-modal"]';

export const openCreateIntegrationModal = async (page: Page): Promise<void> => {
  // go to the integrations page
  await goToOnCallPage(page, 'integrations');

  // open the create integration modal
  (await page.waitForSelector('text=New integration')).click();

  // wait for it to pop up
  await page.waitForSelector(CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR);
};

export const createIntegrationAndSendDemoAlert = async (
  _page: Page,
  _integrationName: string,
  _escalationChainName: string
): Promise<void> => {
  // await openCreateIntegrationModal(page);

  // // create a webhook integration
  // (await page.waitForSelector(`${CREATE_INTEGRATION_MODAL_TEST_ID_SELECTOR} >> text=Webhook`)).click();

  // // wait for the integrations settings modal to open up... and then close it
  // await clickButton({ page, buttonText: 'Open Escalations Settings' });

  // // update the integration name
  // await (await page.waitForSelector('div[data-testid="integration-header"] >> h4 >> button')).click();

  // const grafanaAlertingIntegration = page.getByTestId('integration-display-name');
  // await grafanaAlertingIntegration.click();

  // await fillInInput(page, 'input[name="verbal_name"]', integrationName);
  // await fillInInput(page, 'textarea[name="description_short"]', "Here goes your integration description");
  // await clickButton({ page, buttonText: "Create Integration" })

  // /*
  //  * TODO: This is slightly more complicated now, change this in next iteration */
  // // const integrationSettingsElement = page.getByTestId('integration-settings');

  // // // assign the escalation chain to the integration
  // // await selectDropdownValue({
  // //   page,
  // //   selectType: 'grafanaSelect',
  // //   placeholderText: 'Select Escalation Chain',
  // //   value: escalationChainName,
  // //   startingLocator: integrationSettingsElement,
  // // });

  // // send demo alert
  // await clickButton({ page, buttonText: 'Send demo alert', dataTestId: 'send-demo-alert' });
  // await clickButton({ page, buttonText: 'Send Alert', dataTestId: "submit-send-alert" })
};
