import { test } from '../../fixtures';
import { generateRandomValue } from '../../utils/forms';
import { createIntegration, searchIntegrationAndAssertItsPresence } from '../../utils/integrations';
import { goToOnCallPage } from '../../utils/navigation';

import { HEARTBEAT_SETTINGS_FORM_TEST_ID, openHeartbeatSettingsForm } from './';

test('send heartbeat', async ({ adminRolePage: { page } }) => {
  const integrationName = generateRandomValue();
  await createIntegration({ page, integrationName });

  await openHeartbeatSettingsForm(page);

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
