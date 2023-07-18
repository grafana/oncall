import { test, Page, Locator } from '../fixtures';

import { generateRandomValue, selectDropdownValue } from '../utils/forms';
import { createIntegration } from '../utils/integrations';

test.describe("updating an integration's heartbeat interval works", () => {
  test.slow();

  const _openIntegrationSettingsPopup = async (page: Page): Promise<Locator> => {
    const integrationSettingsPopupElement = page.getByTestId('integration-settings-context-menu');
    await integrationSettingsPopupElement.click();
    return integrationSettingsPopupElement;
  };

  const changeHeartbeatInterval = async (page: Page, heartbeatIntervalValue: string): Promise<void> => {
    const heartbeatSettingsForm = page.getByTestId('heartbeat-settings-form');

    await selectDropdownValue({
      page,
      startingLocator: heartbeatSettingsForm,
      selectType: 'grafanaSelect',
      placeholderText: 'Heartbeat Timeout',
      value: heartbeatIntervalValue,
      optionExactMatch: false,
    });

    await heartbeatSettingsForm.getByTestId('update-heartbeat').click();
  };

  test('"change heartbeat interval', async ({ adminRolePage: { page } }) => {
    const integrationName = generateRandomValue();
    await createIntegration(page, integrationName);

    const integrationSettingsPopupElement = await _openIntegrationSettingsPopup(page);

    await integrationSettingsPopupElement.click();

    await page.getByTestId('integration-heartbeat-settings').click();

    await changeHeartbeatInterval(page, '1 day');

    const heartbeatSettingsForm = page.getByTestId('heartbeat-settings-form');

    await heartbeatSettingsForm.getByTestId('close-heartbeat-form').click();
  });
});
