import { test as setup, chromium, expect, Page, BrowserContext, FullConfig, APIRequestContext } from '@playwright/test';

import GrafanaAPIClient from './utils/clients/grafana';
import {
  GRAFANA_ADMIN_PASSWORD,
  GRAFANA_ADMIN_USERNAME,
  GRAFANA_EDITOR_PASSWORD,
  GRAFANA_EDITOR_USERNAME,
  GRAFANA_VIEWER_PASSWORD,
  GRAFANA_VIEWER_USERNAME,
  IS_CLOUD,
  IS_OPEN_SOURCE,
  ONCALL_API_URL,
} from './utils/constants';
import { clickButton, getInputByName } from './utils/forms';
import { goToGrafanaPage } from './utils/navigation';
import { VIEWER_USER_STORAGE_STATE, EDITOR_USER_STORAGE_STATE, ADMIN_USER_STORAGE_STATE } from '../playwright.config';
import { OrgRole } from '@grafana/data';

const grafanaApiClient = new GrafanaAPIClient(GRAFANA_ADMIN_USERNAME, GRAFANA_ADMIN_PASSWORD);

type UserCreationSettings = {
  adminAuthedRequest: APIRequestContext;
  role: OrgRole;
};

const generateLoginStorageStateAndOptionallCreateUser = async (
  config: FullConfig,
  userName: string,
  password: string,
  storageStateFileLocation: string,
  userCreationSettings?: UserCreationSettings,
  closeContext = false
): Promise<BrowserContext> => {
  if (userCreationSettings !== undefined && IS_OPEN_SOURCE) {
    const { adminAuthedRequest, role } = userCreationSettings;
    await grafanaApiClient.idempotentlyCreateUserWithRole(adminAuthedRequest, userName, password, role);
  }

  const { headless } = config.projects[0]!.use;
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 100 });
  const browserContext = await browser.newContext();

  await grafanaApiClient.login(browserContext.request, userName, password);
  await browserContext.storageState({ path: storageStateFileLocation });

  if (closeContext) {
    await browserContext.close();
  }
  return browserContext;
};

/**
 go to config page and wait for plugin icon to be available on left-hand navigation
 */
const configureOnCallPlugin = async (page: Page): Promise<void> => {
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
setup('Configure Grafana OnCall plugin', async ({ request }, { config }) => {
  /**
   * Unconditionally marks the setup as "slow", giving it triple the default timeout.
   * This is mostly useful for the rare case for Cloud Grafana instances where the instance may be down/unavailable
   * and we need to poll it until it is available
   */
  setup.slow();

  if (IS_CLOUD) {
    await grafanaApiClient.pollInstanceUntilItIsHealthy(request);
  }

  const adminBrowserContext = await generateLoginStorageStateAndOptionallCreateUser(
    config,
    GRAFANA_ADMIN_USERNAME,
    GRAFANA_ADMIN_PASSWORD,
    ADMIN_USER_STORAGE_STATE
  );
  const adminPage = await adminBrowserContext.newPage();
  const { request: adminAuthedRequest } = adminBrowserContext;

  await generateLoginStorageStateAndOptionallCreateUser(
    config,
    GRAFANA_EDITOR_USERNAME,
    GRAFANA_EDITOR_PASSWORD,
    EDITOR_USER_STORAGE_STATE,
    {
      adminAuthedRequest,
      role: OrgRole.Editor,
    },
    true
  );

  await generateLoginStorageStateAndOptionallCreateUser(
    config,
    GRAFANA_VIEWER_USERNAME,
    GRAFANA_VIEWER_PASSWORD,
    VIEWER_USER_STORAGE_STATE,
    {
      adminAuthedRequest,
      role: OrgRole.Viewer,
    },
    true
  );

  if (IS_OPEN_SOURCE) {
    // plugin configuration can safely be skipped for cloud environments
    await configureOnCallPlugin(adminPage);
  }

  await adminBrowserContext.close();
});
