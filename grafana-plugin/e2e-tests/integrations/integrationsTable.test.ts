import { test, expect } from '../fixtures';
import { createIntegration } from '../utils/integrations';

test('Integrations table shows data in Connections and Direct Paging tabs', async ({ adminRolePage: { page } }) => {
  //   // Create 1 direct paging integration and 2 other connections
  const WEBHOOK_INTEGRATION_NAME = 'Webhook-1';
  const ALERTMANAGER_INTEGRATION_NAME = 'Alertmanager-1';
  const DIRECT_PAGING_INTEGRATION_NAME = 'Direct paging-1';

  await createIntegration({ page, integrationSearchText: 'Webhook', integrationName: WEBHOOK_INTEGRATION_NAME });
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  await createIntegration({
    page,
    integrationSearchText: 'Alertmanager',
    shouldGoToIntegrationsPage: false,
    integrationName: ALERTMANAGER_INTEGRATION_NAME,
  });
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  await createIntegration({
    page,
    integrationSearchText: 'Direct paging',
    shouldGoToIntegrationsPage: false,
    integrationName: DIRECT_PAGING_INTEGRATION_NAME,
  });
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  // By default Connections tab is opened and newly created integrations are visible except Direct Paging one
  const integrationsTable = page.getByTestId('integrations-table');
  await expect(integrationsTable.getByText(WEBHOOK_INTEGRATION_NAME)).toBeVisible();
  await expect(integrationsTable.getByText(ALERTMANAGER_INTEGRATION_NAME)).toBeVisible();
  await expect(integrationsTable.getByText(DIRECT_PAGING_INTEGRATION_NAME)).not.toBeVisible();

  // Then after switching to Direct Paging tab only Direct Paging integration is visible
  await page.getByRole('tab', { name: 'Tab Direct Paging' }).click();
  await expect(integrationsTable.getByText(WEBHOOK_INTEGRATION_NAME)).not.toBeVisible();
  await expect(integrationsTable.getByText(ALERTMANAGER_INTEGRATION_NAME)).not.toBeVisible();
  await expect(integrationsTable.getByText(DIRECT_PAGING_INTEGRATION_NAME)).toBeVisible();
});
