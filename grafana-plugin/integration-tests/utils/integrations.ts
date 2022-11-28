import { Page } from '@playwright/test';
import { GRAFANA_USERNAME } from './constants';
import { clickButton, selectDropdownValue } from './forms';
import { goToOnCallPageByClickingOnTab } from './navigation';

export const createIntegrationAndSendDemoAlert = async (page: Page, escalationChainName: string): Promise<void> => {
  // go to the integrations page
  await goToOnCallPageByClickingOnTab(page, 'Integrations');

  // open the create integration modal
  (await page.waitForSelector('text=New integration for receiving alerts')).click();

  // create a webhook integration
  (await page.waitForSelector('div[class*="CreateAlertReceiveChannelContainer"] >> text=Webhook')).click();

  // wait for the integrations settings modal to open up... and then close it
  await page.waitForTimeout(2000);
  await clickButton({ page, buttonText: 'Open Escalations Settings' });

  // get the surrounding element for the integration settings
  const integrationSettingsElement = page.locator(
    'div[class*="components-Collapse-Collapse-module__root containers-AlertRules-AlertRules-module__route"]'
  );

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
    selectType: 'grafanaSelect',
    placeholderText: 'Add escalation step...',
    value: 'Notify users',
    startingLocator: integrationSettingsElement,
  });

  // select our current user..
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Select Users',
    value: GRAFANA_USERNAME,
    startingLocator: integrationSettingsElement,
  });

  // send demo alert
  await clickButton({ page, buttonText: 'Send demo alert', startingLocator: integrationSettingsElement });
};
