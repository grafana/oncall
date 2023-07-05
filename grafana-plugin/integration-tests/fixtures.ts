import { test as base, Page } from '@playwright/test';

import { GRAFANA_ADMIN_USERNAME, GRAFANA_EDITOR_USERNAME, GRAFANA_VIEWER_USERNAME } from './utils/constants';
import { VIEWER_USER_STORAGE_STATE, EDITOR_USER_STORAGE_STATE, ADMIN_USER_STORAGE_STATE } from '../playwright.config';

export class BaseRolePage {
  page: Page;
  userName: string;

  constructor(page: Page) {
    this.page = page;
  }
}

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

export * from '@playwright/test';
export const test = base.extend<Fixtures>({
  viewerRolePage: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: VIEWER_USER_STORAGE_STATE });
    const page = new ViewerRolePage(await context.newPage());
    await use(page);
    await context.close();
  },
  editorRolePage: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: EDITOR_USER_STORAGE_STATE });
    const page = new EditorRolePage(await context.newPage());
    await use(page);
    await context.close();
  },
  adminRolePage: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: ADMIN_USER_STORAGE_STATE });
    const page = new AdminRolePage(await context.newPage());
    await use(page);
    await context.close();
  },
});
