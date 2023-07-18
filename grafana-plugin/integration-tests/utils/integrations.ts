import { Page } from '@playwright/test';
import { clickButton, selectDropdownValue } from './forms';
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

export const assignEscalationChainToIntegration = async (page: Page, escalationChainName: string): Promise<void> => {
  await page.getByTestId('integration-escalation-chain-not-selected').click();

  // assign the escalation chain to the integration
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Select Escalation Chain',
    value: escalationChainName,
    startingLocator: page.getByTestId('integration-block-item'),
  });
};

export const sendDemoAlert = async (page: Page): Promise<void> => {
  await clickButton({ page, buttonText: 'Send demo alert', dataTestId: 'send-demo-alert' });
  await clickButton({ page, buttonText: 'Send Alert', dataTestId: 'submit-send-alert' });
  await page.getByTestId('demo-alert-sent-notification').waitFor({ state: 'visible' });
};

export const createIntegrationAndSendDemoAlert = async (
  page: Page,
  integrationName: string,
  escalationChainName: string
): Promise<void> => {
  await createIntegration(page, integrationName);
  await assignEscalationChainToIntegration(page, escalationChainName);
  await sendDemoAlert(page);
};

export const filterIntegrationsTableAndGoToDetailPage = async (page: Page, integrationName: string): Promise<void> => {
  // filter the integrations page by the integration in question, then go to its detail page
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Search or filter results...',
    value: integrationName,
    pressEnterInsteadOfSelectingOption: true,
  });

  await (
    await page.waitForSelector(
      `div[data-testid="integrations-table"] table > tbody > tr > td:first-child a >> text=${integrationName}`
    )
  ).click();
};
