import { chromium, FullConfig, expect } from '@playwright/test';

import { BASE_URL, GRAFANA_PASSWORD, GRAFANA_USERNAME } from './utils/constants';

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
  await browserContext.close();
};

export default globalSetup;
