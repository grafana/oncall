import type { Page } from '@playwright/test';
import { ONCALL_API_URL, ONCALL_LEFT_HAND_NAV_ICON_SELECTOR } from './constants';
import { clickButton, getInputByName } from './forms';
import { goToGrafanaPage } from './navigation';

/**
 * go to config page and wait for plugin icon to be available on left-hand navigation
 */
export const configureOnCallPlugin = async (page: Page): Promise<void> => {
  await goToGrafanaPage(page, '/plugins/grafana-oncall-app');

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

  /**
   * wait for the page to be refreshed and the icon to show up, this means the plugin
   * has been successfully configured
   */
  await page.waitForSelector(ONCALL_LEFT_HAND_NAV_ICON_SELECTOR);
};
