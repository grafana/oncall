import { BrowserContext, chromium, test as setup, expect } from '@playwright/test';
import {
  BASE_URL,
  GRAFANA_PASSWORD,
  GRAFANA_USERNAME,
  GRAFANA_VIEWER_EMAIL,
  GRAFANA_VIEWER_PASSWORD,
  GRAFANA_VIEWER_USERNAME,
} from './utils/constants';
import config from '../playwright.config';

export const ADMIN_FILE = './adminState.json';
export const VIEWER_FILE = './viewerState.json';

setup('authenticate as admin', async ({ page }) => {
  const { headless } = config.projects[0]!.use;
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 100 });
  const browserContext = await browser.newContext();

  const res = await login(browserContext, GRAFANA_USERNAME, GRAFANA_PASSWORD);

  expect(res.ok()).toBeTruthy();

  await page.context().storageState({ path: ADMIN_FILE });
  await browserContext.storageState({ path: ADMIN_FILE });
  await browserContext.close();
});

setup('authenticate as viewer', async ({ page }) => {
  const { headless } = config.projects[0]!.use;
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 100 });
  const browserContext = await browser.newContext();

  try {
    // Create a Viewer user if none exists
    const createUserRes = await browserContext.request.post(`${BASE_URL}/api/admin/users`, {
      data: {
        name: GRAFANA_VIEWER_USERNAME,
        email: GRAFANA_VIEWER_EMAIL,
        login: GRAFANA_VIEWER_USERNAME,
        password: GRAFANA_VIEWER_PASSWORD,
      },
    });

    expect(createUserRes.ok()).toBeTruthy();
  } catch (ex) {}

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
