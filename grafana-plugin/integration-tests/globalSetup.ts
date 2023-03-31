import { FullConfig, chromium, expect } from '@playwright/test';
import { BASE_URL, GRAFANA_ADMIN_PASSWORD, GRAFANA_ADMIN_USERNAME } from './utils/constants';
import { configureOnCallPlugin } from './configurePlugin.setup';

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
      user: GRAFANA_ADMIN_USERNAME,
      password: GRAFANA_ADMIN_PASSWORD,
    },
  });

  expect(res.ok()).toBeTruthy();
  await browserContext.storageState({ path: './storageState.json' });

  // make sure the plugin has been configured
  const page = await browserContext.newPage();
  await configureOnCallPlugin(page);

  await browserContext.close();
};

export default globalSetup;
