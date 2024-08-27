import { test, expect } from '../../fixtures';
import { generateRandomValue, selectDropdownValue } from '../../utils/forms';
import { createIntegration } from '../../utils/integrations';

import { HEARTBEAT_SETTINGS_FORM_TEST_ID, openHeartbeatSettingsForm } from './';

test('change heartbeat interval', async ({ adminRolePage: { page } }) => {
  test.slow();

  const integrationName = generateRandomValue();
  await createIntegration({ page, integrationName });

  await openHeartbeatSettingsForm(page);

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

  await openHeartbeatSettingsForm(page);

  const heartbeatIntervalValue = await heartbeatSettingsForm
    .locator('div[class*="grafana-select-value-container"] > div[class*="-singleValue"]')
    .textContent();

  expect(heartbeatIntervalValue).toEqual(value);
});
