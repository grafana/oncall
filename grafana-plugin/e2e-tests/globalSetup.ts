import {
  test as setup,
  chromium,
  expect,
  type Page,
  type BrowserContext,
  type FullConfig,
  type APIRequestContext,
} from '@playwright/test';

import { getOnCallApiUrl } from 'utils/consts';

import { VIEWER_USER_STORAGE_STATE, EDITOR_USER_STORAGE_STATE, ADMIN_USER_STORAGE_STATE } from '../playwright.config';

import grafanaApiClient from './utils/clients/grafana';
import {
  GRAFANA_ADMIN_PASSWORD,
  GRAFANA_ADMIN_USERNAME,
  GRAFANA_EDITOR_PASSWORD,
  GRAFANA_EDITOR_USERNAME,
  GRAFANA_VIEWER_PASSWORD,
  GRAFANA_VIEWER_USERNAME,
  IS_CLOUD,
  IS_OPEN_SOURCE,
} from './utils/constants';
import { clickButton, getInputByName } from './utils/forms';
import { goToGrafanaPage } from './utils/navigation';

enum OrgRole {
  None = 'None',
  Viewer = 'Viewer',
  Editor = 'Editor',
  Admin = 'Admin',
}

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
  await page.waitForTimeout(3000);

  // if plugin is configured, go to OnCall
  const isConfigured = (await page.getByText('Connected to OnCall').count()) >= 1;
  if (isConfigured) {
    await page.getByRole('link', { name: 'Open Grafana OnCall' }).click();
    return;
  }

  // otherwise we may need to reconfigure the plugin
  const needToReconfigure = (await page.getByText('try removing your plugin configuration').count()) >= 1;
  if (needToReconfigure) {
    await clickButton({ page, buttonText: 'Remove current configuration' });
    await clickButton({ page, buttonText: /^Remove$/ });
  }
  await page.waitForTimeout(2000);

  const needToEnterOnCallApiUrl = await page.getByText(/Connected to OnCall/).isHidden();
  if (needToEnterOnCallApiUrl) {
    await getInputByName(page, 'onCallApiUrl').fill(getOnCallApiUrl() || 'http://oncall-dev-engine:8080');
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

  /**
   * determine the current Grafana version of the stack in question and set it such that it can be used in the tests
   * to conditionally skip certain tests.
   *
   * According to the Playwright docs, the best way to set config like this on the fly, is to set values
   * on process.env https://playwright.dev/docs/test-global-setup-teardown#example
   *
   * TODO: when this bug is fixed in playwright https://github.com/microsoft/playwright/issues/29608
   * move this to the currentGrafanaVersion fixture
   */
  const currentGrafanaVersion = await grafanaApiClient.getGrafanaVersion(adminAuthedRequest);
  process.env.CURRENT_GRAFANA_VERSION = currentGrafanaVersion;

  await adminBrowserContext.close();
});
