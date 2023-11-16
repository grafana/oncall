import { test, expect } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createIntegration } from '../utils/integrations';

test('Integrations table shows data in Connections and Direct Paging tabs', async ({ adminRolePage: { page } }) => {
  //   // Create 2 integrations that are not Direct Paging
  const ID = generateRandomValue();
  const WEBHOOK_INTEGRATION_NAME = `Webhook-${ID}`;
  const ALERTMANAGER_INTEGRATION_NAME = `Alertmanager-${ID}`;
  const DIRECT_PAGING_INTEGRATION_NAME = `Direct paging`;

  await createIntegration({ page, integrationSearchText: 'Webhook', integrationName: WEBHOOK_INTEGRATION_NAME });
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  await createIntegration({
    page,
    integrationSearchText: 'Alertmanager',
    shouldGoToIntegrationsPage: false,
    integrationName: ALERTMANAGER_INTEGRATION_NAME,
  });
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  // Create 1 Direct Paging integration if it doesn't exist
  const integrationsTable = page.getByTestId('integrations-table');
  await page.getByRole('tab', { name: 'Tab Direct Paging' }).click();
  const isDirectPagingAlreadyCreated = await page.getByText('Direct paging').isVisible();
  if (!isDirectPagingAlreadyCreated) {
    await createIntegration({
      page,
      integrationSearchText: 'Direct paging',
      shouldGoToIntegrationsPage: false,
      integrationName: DIRECT_PAGING_INTEGRATION_NAME,
    });
  }
  await page.getByRole('tab', { name: 'Tab Integrations' }).click();

  // By default Connections tab is opened and newly created integrations are visible except Direct Paging one
  await expect(integrationsTable.getByText(WEBHOOK_INTEGRATION_NAME)).toBeVisible();
  await expect(integrationsTable.getByText(ALERTMANAGER_INTEGRATION_NAME)).toBeVisible();
  await expect(integrationsTable).not.toContainText(DIRECT_PAGING_INTEGRATION_NAME);

  // Then after switching to Direct Paging tab only Direct Paging integration is visible
  await page.getByRole('tab', { name: 'Tab Direct Paging' }).click();
  await expect(integrationsTable.getByText(WEBHOOK_INTEGRATION_NAME)).not.toBeVisible();
  await expect(integrationsTable.getByText(ALERTMANAGER_INTEGRATION_NAME)).not.toBeVisible();
  await expect(integrationsTable).toContainText(DIRECT_PAGING_INTEGRATION_NAME);
});
