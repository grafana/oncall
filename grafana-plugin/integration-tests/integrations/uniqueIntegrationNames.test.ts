import { test, expect } from '../fixtures';
import { openCreateIntegrationModal } from '../utils/integrations';

test('integrations have unique names', async ({ adminRolePage }) => {
  const { page } = adminRolePage;
  await openCreateIntegrationModal(page);

  const integrationNames = await page.getByTestId('integration-display-name').allInnerTexts();
  const uniqueLowercasedIntegrationNames = new Set(integrationNames.map((elem) => elem.toLowerCase()));

  expect(uniqueLowercasedIntegrationNames.size).toEqual(integrationNames.length);
});
