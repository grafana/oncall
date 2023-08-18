import { test, Page, expect } from '../fixtures';

import { generateRandomValue, selectDropdownValue } from '../utils/forms';
import { createIntegration } from '../utils/integrations';

const HEARTBEAT_SETTINGS_FORM_TEST_ID = 'heartbeat-settings-form';

test.describe("updating an integration's heartbeat interval works", async () => {
  const _openHeartbeatSettingsForm = async (page: Page) => {
    const integrationSettingsPopupElement = page.getByTestId('integration-settings-context-menu');
    await integrationSettingsPopupElement.waitFor({ state: 'visible' });
    await integrationSettingsPopupElement.click();

    await page.getByTestId('integration-heartbeat-settings').click();
  };

  test('change heartbeat interval', async ({ adminRolePage: { page } }) => {
    await createIntegration(page, generateRandomValue());

    await _openHeartbeatSettingsForm(page);

    const heartbeatSettingsForm = page.getByTestId(HEARTBEAT_SETTINGS_FORM_TEST_ID);

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

  test('send heartbeat', async ({ adminRolePage: { page } }) => {
    await createIntegration(page, generateRandomValue());

    await _openHeartbeatSettingsForm(page);

    const heartbeatSettingsForm = page.getByTestId(HEARTBEAT_SETTINGS_FORM_TEST_ID);

    const endpoint = await heartbeatSettingsForm
      .getByTestId('input-wrapper')
      .locator('input[class*="input-input"]')
      .inputValue();

    /**
     * make an HTTP call to the integration's hearbeat URL and assert that it was called
     * (ie. the greenheart badge is shown)
     */
    await page.request.get(endpoint);
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByTestId('heartbeat-badge').waitFor({ state: 'visible' });
  });
});
