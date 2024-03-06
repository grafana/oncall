import { Page, expect } from '@playwright/test';

import { clickButton, generateRandomValue, selectDropdownValue } from './forms';
import { goToOnCallPage } from './navigation';

export const openCreateIntegrationModal = async (page: Page): Promise<void> => {
  // open the create integration modal
  await page.getByRole('button', { name: 'New integration' }).click();

  // wait for it to pop up
  await page.getByTestId('create-integration-modal').waitFor();
};

export const createIntegration = async ({
  page,
  integrationName = `integration-${generateRandomValue()}`,
  integrationSearchText = 'Webhook',
  shouldGoToIntegrationsPage = true,
}: {
  page: Page;
  integrationName?: string;
  integrationSearchText?: string;
  shouldGoToIntegrationsPage?: boolean;
}): Promise<void> => {
  if (shouldGoToIntegrationsPage) {
    // go to the integrations page
    await goToOnCallPage(page, 'integrations');
  }

  await openCreateIntegrationModal(page);

  // create an integration
  await page
    .getByTestId('create-integration-modal')
    .getByTestId('integration-display-name')
    .filter({ hasText: integrationSearchText })
    .first()
    .click();

  // fill in the required inputs
  await page.getByPlaceholder('Integration Name').fill(integrationName);
  await page.getByPlaceholder('Integration Description').fill('Here goes your integration description');
  await page.getByTestId('update-integration-button').focus();
  await page.getByTestId('update-integration-button').click();

  await goToOnCallPage(page, 'integrations');
  await searchIntegrationAndAssertItsPresence({ page, integrationName });

  await page.getByRole('link', { name: integrationName }).click();
};

export const assignEscalationChainToIntegration = async (page: Page, escalationChainName: string): Promise<void> => {
  const notSelected = page.getByTestId('integration-escalation-chain-not-selected');
  if (await notSelected.isHidden()) {
    await clickButton({ page, buttonText: 'Add route' });
    await page.waitForTimeout(500);
  }
  await notSelected.last().click();

  // assign the escalation chain to the integration
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Select Escalation Chain',
    value: escalationChainName,
    startingLocator: page.getByTestId('escalation-chain-select').last(),
  });
};

export const sendDemoAlert = async (page: Page): Promise<void> => {
  await clickButton({ page, buttonText: 'Send demo alert' });
  await clickButton({ page, buttonText: 'Send Alert' });
  await page.getByTestId('demo-alert-sent-notification').waitFor({ state: 'visible' });
};

export const createIntegrationAndSendDemoAlert = async (
  page: Page,
  integrationName: string,
  escalationChainName: string
): Promise<void> => {
  await createIntegration({ page, integrationName });
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

  await page.getByTestId('integrations-table').getByText(`${integrationName}`).click();
};

export const searchIntegrationAndAssertItsPresence = async ({
  page,
  integrationName,
  visibleExpected = true,
}: {
  page: Page;
  integrationName: string;
  visibleExpected?: boolean;
}) => {
  await page
    .locator('div')
    .filter({ hasText: /^Search or filter results\.\.\.$/ })
    .nth(1)
    .click();
  const integrationsTable = page.getByTestId('integrations-table');
  await page.keyboard.insertText(integrationName);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2000);
  const nbOfResults = await integrationsTable.getByText(integrationName).count();
  if (visibleExpected) {
    expect(nbOfResults).toBeGreaterThanOrEqual(1);
  } else {
    expect(nbOfResults).toBe(0);
  }
};
