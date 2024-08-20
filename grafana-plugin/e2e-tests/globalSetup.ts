import {
  test as setup,
  chromium,
  type BrowserContext,
  type FullConfig,
  type APIRequestContext,
  Page,
} from '@playwright/test';

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
  OrgRole,
  isGrafanaVersionLowerThan,
} from './utils/constants';
import { goToOnCallPage } from './utils/navigation';

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

const idempotentlyInitializePlugin = async (page: Page) => {
  await goToOnCallPage(page, 'alert-groups');
  await page.waitForTimeout(1000);
  const openPluginConfigurationButton = page.getByRole('button', { name: 'Open configuration' });
  if (await openPluginConfigurationButton.isVisible()) {
    await openPluginConfigurationButton.click();
    // Before 10.3 Admin user needs to create service account manually
    if (isGrafanaVersionLowerThan('10.3.0')) {
      await page.getByTestId('recreate-service-account').click();
    }
    await page.getByTestId('connect-plugin').click();
    await page.waitForLoadState('networkidle');
    await page.getByText('Plugin is connected').waitFor();
  }
};

const determineGrafanaVersion = async (adminAuthedRequest: APIRequestContext) => {
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

  await determineGrafanaVersion(adminAuthedRequest);

  await idempotentlyInitializePlugin(adminPage);

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

  await adminBrowserContext.close();
});
