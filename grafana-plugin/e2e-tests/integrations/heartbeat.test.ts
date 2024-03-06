import { test, Page, expect } from '../fixtures';
import { generateRandomValue, selectDropdownValue } from '../utils/forms';
import { createIntegration, searchIntegrationAndAssertItsPresence } from '../utils/integrations';
import { goToOnCallPage } from '../utils/navigation';

const HEARTBEAT_SETTINGS_FORM_TEST_ID = 'heartbeat-settings-form';

test.describe("updating an integration's heartbeat interval works", async () => {
  const _openHeartbeatSettingsForm = async (page: Page) => {
    await page.getByTestId('integration-settings-context-menu-wrapper').click();
    await page.getByTestId('integration-heartbeat-settings').click();
  };

  test('change heartbeat interval', async ({ adminRolePage: { page } }) => {
    const integrationName = generateRandomValue();
    await createIntegration({ page, integrationName });

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

    await page.waitForTimeout(1000);

    await _openHeartbeatSettingsForm(page);

    const heartbeatIntervalValue = await heartbeatSettingsForm
      .locator('div[class*="grafana-select-value-container"] > div[class*="-singleValue"]')
      .textContent();

    expect(heartbeatIntervalValue).toEqual(value);
  });

  test('send heartbeat', async ({ adminRolePage: { page } }) => {
    const integrationName = generateRandomValue();
    await createIntegration({ page, integrationName });

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

    await goToOnCallPage(page, 'integrations');
    await searchIntegrationAndAssertItsPresence({ page, integrationName });
    await page.getByTestId('heartbeat-badge').waitFor();
  });
});
