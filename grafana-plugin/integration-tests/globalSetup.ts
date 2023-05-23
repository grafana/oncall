import { chromium, FullConfig, expect, Page } from '@playwright/test';

import { BASE_URL, GRAFANA_PASSWORD, GRAFANA_USERNAME, IS_OPEN_SOURCE, ONCALL_API_URL } from './utils/constants';
import { clickButton, getInputByName } from './utils/forms';
import { goToGrafanaPage } from './utils/navigation';

/**
 * The plugin configuration can sometimes be flaky on CI. In the rare case that it fails
 * lets retry rather than failing the enter CI job
 * Example failed CI job
 * https://github.com/grafana/oncall/actions/runs/5061747867/jobs/9086615168#step:18:18
 */
const GLOBAL_SETUP_RETRY_ATTEMPTS = 3;

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

  /**
   * wait for the "Connected to OnCall" message to know that everything is properly configured
   *
   * Regarding increasing the timeout for the "plugin configured" assertion:
   * This is because it can sometimes take a bit longer for the backend sync to finish. The default assertion
   * timeout is 5s, which is sometimes not enough if the backend is under load
   */
  await expect(page.getByTestId('status-message-block')).toHaveText(/Connected to OnCall.*/, { timeout: 25_000 });
};

/**
 * Borrowed from our friends on the Incident team
 * https://github.com/grafana/incident/blob/main/plugin/e2e/global-setup.ts
 */
const globalSetup = async (config: FullConfig): Promise<void> => {
  const { headless } = config.projects[0]!.use;
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 100 });
  const browserContext = await browser.newContext();

  const res = await browserContext.request.post(`${BASE_URL}/login`, {
    data: {
      user: GRAFANA_USERNAME,
      password: GRAFANA_PASSWORD,
    },
  });

  expect(res.ok()).toBeTruthy();
  await browserContext.storageState({ path: './storageState.json' });

  // make sure the plugin has been configured
  const page = await browserContext.newPage();

  for (let i = 0; i < GLOBAL_SETUP_RETRY_ATTEMPTS - 1; i++) {
    try {
      await configureOnCallPlugin(page);
    } catch (e) {}
  }
  // One last time, throwing an error if it fails.
  await configureOnCallPlugin(page);

  await browserContext.close();
};

export default globalSetup;
