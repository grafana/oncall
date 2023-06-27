import { test as setup, chromium, FullConfig, expect, Page, BrowserContext, APIResponse } from '@playwright/test';

import { BASE_URL, GRAFANA_PASSWORD, GRAFANA_USERNAME, IS_OPEN_SOURCE, ONCALL_API_URL } from './utils/constants';
import { clickButton, getInputByName } from './utils/forms';
import { goToGrafanaPage } from './utils/navigation';

const IS_CLOUD = !IS_OPEN_SOURCE;
const GLOBAL_SETUP_RETRIES = 3;

const makeGrafanaLoginRequest = async (browserContext: BrowserContext): Promise<APIResponse> =>
  browserContext.request.post(`${BASE_URL}/login`, {
    data: {
      user: GRAFANA_USERNAME,
      password: GRAFANA_PASSWORD,
    },
  });

const pollGrafanaInstanceUntilItIsHealthy = async (browserContext: BrowserContext): Promise<boolean> => {
  const res = await makeGrafanaLoginRequest(browserContext);

  if (!res.ok()) {
    return pollGrafanaInstanceUntilItIsHealthy(browserContext);
  }
  return true;
};

/**
 * go to config page and wait for plugin icon to be available on left-hand navigation
 */
const configureOnCallPlugin = async (page: Page): Promise<void> => {
  // plugin configuration can safely be skipped for non open-source environments
  if (IS_CLOUD) {
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

  if (IS_CLOUD) {
    /**
     * check that the grafana instance is available. If HTTP 503 is returned it means the
     * instance is currently unavailable. Poll until it is available
     */
    await pollGrafanaInstanceUntilItIsHealthy(browserContext);
  }

  const res = await makeGrafanaLoginRequest(browserContext);

  expect(res.ok()).toBeTruthy();
  await browserContext.storageState({ path: './storageState.json' });

  // make sure the plugin has been configured
  const page = await browserContext.newPage();
  await configureOnCallPlugin(page);

  await browserContext.close();
};

/**
 * Let's retry global setup, in the event that it fails due to an oncall-engine/oncall-celery backend error.
 * Sometimes the sync endpoint will randomly return HTTP 500.
 * See here for an example CI job which failed global setup
 * https://github.com/grafana/oncall/actions/runs/5062712137/jobs/9088529416#step:19:2536
 *
 * References on retrying playwright global setup
 * https://github.com/microsoft/playwright/discussions/11371
 */
const globalSetupWithRetries = async (config: FullConfig): Promise<void> => {
  for (let i = 0; i < GLOBAL_SETUP_RETRIES - 1; i++) {
    try {
      return await globalSetup(config);
    } catch (e) {}
  }
  // One last time, throwing an error if it fails.
  await globalSetup(config);
};

setup('Configure Grafana OnCall plugin', async ({}, { config }) => {
  /**
   * Unconditionally marks the setup as "slow", giving it triple the default timeout.
   * This is mostly useful for the rare case for Cloud Grafana instances where the instance may be down/unavailable
   * and we need to poll it until it is available
   */
  setup.slow();

  await globalSetupWithRetries(config);
});
