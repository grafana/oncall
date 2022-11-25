import { Page } from '@playwright/test';
import { GRAFANA_USERNAME } from './constants';
import { clickButton, selectDropdownValue } from './forms';
import { goToOnCallPageByClickingOnTab } from './navigation';

const closeIntegrationSettingsModal = async (page: Page): Promise<void> => {
  const integrationSettingsModal = page.locator('div[class="drawer-mask"]');
  await integrationSettingsModal.waitFor({ state: 'attached' });
  await integrationSettingsModal.click({ position: { x: 0, y: 0 } });
  await integrationSettingsModal.waitFor({ state: 'detached' });
};

export const createIntegrationAndSendDemoAlert = async (page: Page, escalationChainName: string): Promise<void> => {
  // go to the integrations page
  await goToOnCallPageByClickingOnTab(page, 'Integrations');

  // open the create integration modal
  (await page.waitForSelector('text=New integration for receiving alerts')).click();

  // create a webhook integration
  (await page.waitForSelector('div[class*="CreateAlertReceiveChannelContainer"] >> text=Webhook')).click();

  // wait for the integrations settings modal to open up... and then close it
  await closeIntegrationSettingsModal(page);

  // // wait for the escalation chains to be loaded...
  // await page.locator('text=Select Escalation Chain first please ↑').waitFor({ state: 'visible' });

  // get the surrounding element for the integration settings
  const integrationSettingsElement = page.locator(
    'div[class*="components-Collapse-Collapse-module__root containers-AlertRules-AlertRules-module__route"]'
  );

  /**
   * TODO: this is a bit of a hack but for some reason the integrations settings modal
   * pops up twice.. and we have to close it twice
   */
  await closeIntegrationSettingsModal(page);

  // assign the escalation chain to the integration
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Select Escalation Chain',
    value: escalationChainName,
    startingLocator: integrationSettingsElement,
  });

  // add an escalation step to notify user
  await selectDropdownValue({
    page,
    selectType: 'reactSelect',
    placeholderText: 'Add escalation step...',
    value: 'Notify users',
    startingLocator: integrationSettingsElement,
  });

  // select our current user..
  await selectDropdownValue({
    page,
    selectType: 'reactSelect',
    placeholderText: 'Select Users',
    value: GRAFANA_USERNAME,
    startingLocator: integrationSettingsElement,
  });

  // send demo alert
  await clickButton(page, 'Send demo alert');
};
