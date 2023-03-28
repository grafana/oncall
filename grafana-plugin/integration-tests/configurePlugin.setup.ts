import { expect, Page } from '@playwright/test';

import { IS_OPEN_SOURCE, ONCALL_API_URL } from './utils/constants';
import { clickButton, getInputByName } from './utils/forms';
import { goToGrafanaPage } from './utils/navigation';

/**
 * go to config page and wait for plugin icon to be available on left-hand navigation
 */
export const configureOnCallPlugin = async (page: Page): Promise<void> => {
  // plugin configuration can safely be skipped for non open-source environments
  if (!IS_OPEN_SOURCE) {
    return;
  }

  /**
   * go to the oncall plugin configuration page and wait for the page to be loaded
   */
  await goToGrafanaPage(page, '/plugins/grafana-oncall-app');
  await page.waitForSelector('text=Configure Grafana OnCall');

  /**
   * we may need to fill in the OnCall API URL if it is not set in the process.env
   * of the frontend build
   */
  const onCallApiUrlInput = getInputByName(page, 'onCallApiUrl');
  const pluginIsAutoConfigured = (await onCallApiUrlInput.count()) === 0;

  if (!pluginIsAutoConfigured) {
    await onCallApiUrlInput.fill(ONCALL_API_URL);
    await clickButton({ page, buttonText: 'Connect' });
  }

  // wait for the "Connected to OnCall" message to know that everything is properly configured
  await expect(page.getByTestId('status-message-block')).toHaveText(/Connected to OnCall.*/);
};
