import { BrowserContext, chromium, test as setup, expect } from '@playwright/test';
import {
  BASE_URL,
  GRAFANA_ADMIN_USERNAME,
  GRAFANA_ADMIN_PASSWORD,
  GRAFANA_VIEWER_PASSWORD,
  GRAFANA_VIEWER_USERNAME,
} from './utils/constants';
import config from '../playwright.config';
import { configureOnCallPlugin } from './configurePlugin.setup';
import { createGrafanaUserWithRole } from './utils/api';
import { OrgRole } from '@grafana/data';

export const ADMIN_FILE = './.auth/adminState.json';
export const VIEWER_FILE = './.auth/viewerState.json';

setup('authenticate as admin', async ({ page }) => {
  const { headless } = config.projects[0]!.use;
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 100 });
  const browserContext = await browser.newContext();

  const res = await login(browserContext, GRAFANA_ADMIN_USERNAME, GRAFANA_ADMIN_PASSWORD);

  expect(res.ok()).toBeTruthy();

  await page.context().storageState({ path: ADMIN_FILE });
  await browserContext.storageState({ path: ADMIN_FILE });

  await configureOnCallPlugin(page);

  await browserContext.close();
});

setup('authenticate as viewer', async ({ page }) => {
  const { headless } = config.projects[0]!.use;
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 100 });
  const browserContext = await browser.newContext();

  await createGrafanaUserWithRole(browserContext, GRAFANA_VIEWER_USERNAME, GRAFANA_VIEWER_PASSWORD, OrgRole.Viewer);

  const res = await login(browserContext, GRAFANA_VIEWER_USERNAME, GRAFANA_VIEWER_PASSWORD);
  expect(res.ok()).toBeTruthy();

  await page.context().storageState({ path: VIEWER_FILE });
  await browserContext.storageState({ path: VIEWER_FILE });

  await browserContext.close();
});

async function login(browserContext: BrowserContext, user: string, password: string) {
  return browserContext.request.post(`${BASE_URL}/login`, {
    data: {
      user,
      password,
    },
  });
}
