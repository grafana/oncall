import { test as base, Browser, Page } from '@playwright/test';

import { VIEWER_USER_STORAGE_STATE, EDITOR_USER_STORAGE_STATE, ADMIN_USER_STORAGE_STATE } from '../playwright.config';

import { GRAFANA_ADMIN_USERNAME, GRAFANA_EDITOR_USERNAME, GRAFANA_VIEWER_USERNAME } from './utils/constants';

export class BaseRolePage {
  page: Page;
  userName: string;

  constructor(page: Page) {
    this.page = page;
  }
}

type BaseRolePageType = new (page: Page) => BaseRolePage;

class ViewerRolePage extends BaseRolePage {
  userName = GRAFANA_VIEWER_USERNAME;
}

class EditorRolePage extends BaseRolePage {
  userName = GRAFANA_EDITOR_USERNAME;
}

class AdminRolePage extends BaseRolePage {
  userName = GRAFANA_ADMIN_USERNAME;
}

type Fixtures = {
  viewerRolePage: ViewerRolePage;
  editorRolePage: EditorRolePage;
  adminRolePage: AdminRolePage;
};

const setContextForPage = async (
  browser: Browser,
  use: (r: BaseRolePage) => Promise<void>,
  storageStateLocation: string,
  RolePage: BaseRolePageType
) => {
  const context = await browser.newContext({
    storageState: storageStateLocation,
  });
  const page = new RolePage(await context.newPage());
  await use(page);
};

export * from '@playwright/test';
export const test = base.extend<Fixtures>({
  viewerRolePage: ({ browser }, use) => setContextForPage(browser, use, VIEWER_USER_STORAGE_STATE, ViewerRolePage),
  editorRolePage: async ({ browser }, use) =>
    setContextForPage(browser, use, EDITOR_USER_STORAGE_STATE, EditorRolePage),
  adminRolePage: async ({ browser }, use) => setContextForPage(browser, use, ADMIN_USER_STORAGE_STATE, AdminRolePage),
});
