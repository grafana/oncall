import { test, Page, expect, Locator } from '../fixtures';

import { generateRandomValue, selectDropdownValue } from '../utils/forms';
import { createIntegration } from '../utils/integrations';

test.describe("updating an integration's heartbeat interval works", async () => {
  test.slow();

  const _openIntegrationSettingsPopup = async (page: Page): Promise<Locator> => {
    const integrationSettingsPopupElement = page.getByTestId('integration-settings-context-menu');
    await integrationSettingsPopupElement.click();
    return integrationSettingsPopupElement;
  };

  const _openHeartbeatSettingsForm = async (page: Page) => {
    const integrationSettingsPopupElement = await _openIntegrationSettingsPopup(page);

    await integrationSettingsPopupElement.click();

    await page.getByTestId('integration-heartbeat-settings').click();
  };

  test('"change heartbeat interval', async ({ adminRolePage: { page } }) => {
    const integrationName = generateRandomValue();
    await createIntegration(page, integrationName);

    await _openHeartbeatSettingsForm(page);

    const heartbeatSettingsForm = page.getByTestId('heartbeat-settings-form');

    const value = '30 minutes';

    await selectDropdownValue({
      page,
      startingLocator: heartbeatSettingsForm,
      selectType: 'grafanaSelect',
      value,
      optionExactMatch: false,
    });

    await heartbeatSettingsForm.getByTestId('update-heartbeat').click();

    await _openHeartbeatSettingsForm(page);

    const heartbeatIntervalValue = await heartbeatSettingsForm
      .locator('div[class*="grafana-select-value-container"] > div[class*="-singleValue"]')
      .textContent();

    expect(heartbeatIntervalValue).toEqual(value);
  });

  test('"send heartbeat', async ({ request, adminRolePage: { page } }) => {
    const integrationName = generateRandomValue();
    await createIntegration(page, integrationName);

    await _openHeartbeatSettingsForm(page);

    const heartbeatSettingsForm = page.getByTestId('heartbeat-settings-form');

    const endpoint = await heartbeatSettingsForm
      .getByTestId('input-wrapper')
      .locator('input[class*="input-input"]')
      .inputValue();

    await request.get(endpoint);
    await page.reload({ waitUntil: 'networkidle' });

    const heartbeatBadge = await page.getByTestId('heartbeat-badge');
    await expect(heartbeatBadge).toHaveClass(/--success/);
  });
});
