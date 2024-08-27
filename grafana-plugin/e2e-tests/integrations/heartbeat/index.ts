import { Page } from '../../fixtures';

export const HEARTBEAT_SETTINGS_FORM_TEST_ID = 'heartbeat-settings-form';

export const openHeartbeatSettingsForm = async (page: Page) => {
  await page.getByTestId('integration-settings-context-menu-wrapper').click();
  await page.getByTestId('integration-heartbeat-settings').click();
};
