import { test } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createIntegration, searchIntegrationAndAssertItsPresence } from '../utils/integrations';

test('Integrations table shows data in Monitoring Systems and Direct Paging tabs', async ({
  adminRolePage: { page },
}) => {
  const ID = generateRandomValue();
  const WEBHOOK_INTEGRATION_NAME = `Webhook-${ID}`;
  const ALERTMANAGER_INTEGRATION_NAME = `Alertmanager-${ID}`;
  const DIRECT_PAGING_INTEGRATION_NAME = `Direct paging integration name`;

  // Create 2 integrations that are not Direct Paging
  await createIntegration({ page, integrationSearchText: 'Webhook', integrationName: WEBHOOK_INTEGRATION_NAME });
  await page.waitForTimeout(1000);
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();
  await createIntegration({
    page,
    integrationSearchText: 'Alertmanager',
    integrationName: ALERTMANAGER_INTEGRATION_NAME,
  });
  await page.waitForTimeout(1000);
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  // Create 1 Direct Paging integration if it doesn't exist
  await page.getByRole('tab', { name: 'Tab Manual Direct Paging' }).click();
  const integrationsTable = page.getByTestId('integrations-table');
  await page.waitForTimeout(2000);
  const isDirectPagingAlreadyCreated = (await integrationsTable.getByText('Direct paging').count()) >= 1;
  if (!isDirectPagingAlreadyCreated) {
    await createIntegration({
      page,
      integrationSearchText: 'Direct paging',
      integrationName: DIRECT_PAGING_INTEGRATION_NAME,
    });
    await page.waitForTimeout(1000);
  }
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  // By default Monitoring Systems tab is opened and newly created integrations are visible except Direct Paging one
  await searchIntegrationAndAssertItsPresence({ page, integrationName: WEBHOOK_INTEGRATION_NAME });
  await searchIntegrationAndAssertItsPresence({
    page,
    integrationName: ALERTMANAGER_INTEGRATION_NAME,
  });
  await searchIntegrationAndAssertItsPresence({
    page,
    integrationName: DIRECT_PAGING_INTEGRATION_NAME,
    visibleExpected: false,
  });

  // Then after switching to Direct Paging tab only Direct Paging integration is visible
  await page.getByRole('tab', { name: 'Tab Manual Direct Paging' }).click();
  await searchIntegrationAndAssertItsPresence({
    page,
    integrationName: WEBHOOK_INTEGRATION_NAME,
    visibleExpected: false,
  });
  await searchIntegrationAndAssertItsPresence({
    page,
    integrationName: ALERTMANAGER_INTEGRATION_NAME,
    visibleExpected: false,
  });
  await searchIntegrationAndAssertItsPresence({
    page,
    integrationName: 'Direct paging',
  });
});
