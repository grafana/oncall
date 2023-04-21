import { test, expect } from '@playwright/test';
import { openCreateIntegrationModal } from '../utils/integrations';

test('integrations have unique names', async ({ page }) => {
  await openCreateIntegrationModal(page);

  const integrationNames = await page.getByTestId('integration-display-name').allInnerTexts();
  const uniqueLowercasedIntegrationNames = new Set(integrationNames.map((elem) => elem.toLowerCase()));

  expect(uniqueLowercasedIntegrationNames.size).toEqual(integrationNames.length);
});
