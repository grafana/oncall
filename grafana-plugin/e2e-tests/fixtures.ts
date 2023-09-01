import * as fs from 'fs';
import * as path from 'path';
import { test as base, Browser, Page, TestInfo } from '@playwright/test';

import { GRAFANA_ADMIN_USERNAME, GRAFANA_EDITOR_USERNAME, GRAFANA_VIEWER_USERNAME } from './utils/constants';
import { VIEWER_USER_STORAGE_STATE, EDITOR_USER_STORAGE_STATE, ADMIN_USER_STORAGE_STATE } from '../playwright.config';

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

/**
 * NOTE: currently videos are not generated automatically because of how we generate a browserContext within our
 * auth fixtures (which is how Playwright suggested setting up multi-role authnz tests..). There's a GitHub
 * Issue here that tracks this issue https://github.com/microsoft/playwright/issues/14813
 *
 * Here's a temporary workaround on this, which is what this function does
 * https://github.com/microsoft/playwright/issues/14813#issuecomment-1582499142
 */
const _recordTestVideo = async (
  browser: Browser,
  use: (r: BaseRolePage) => Promise<void>,
  testInfo: TestInfo,
  storageStateLocation: string,
  RolePage: BaseRolePageType
) => {
  const videoDir = path.join(testInfo.outputPath(), 'videos');

  const context = await browser.newContext({
    storageState: storageStateLocation,
    recordVideo: { dir: videoDir },
  });
  const page = new RolePage(await context.newPage());

  try {
    await use(page);
  } finally {
    await context.close();
    const videoFiles = fs.readdirSync(videoDir);

    if (videoFiles.length > 0) {
      for (let i = videoFiles.length; i > 0; i--) {
        let videoFile = path.join(videoDir, videoFiles[i - 1]);
        await testInfo.attach('video', { path: videoFile });
      }
    }
  }
};

export * from '@playwright/test';
export const test = base.extend<Fixtures>({
  viewerRolePage: ({ browser }, use, testInfo) =>
    _recordTestVideo(browser, use, testInfo, VIEWER_USER_STORAGE_STATE, ViewerRolePage),
  editorRolePage: async ({ browser }, use, testInfo) =>
    _recordTestVideo(browser, use, testInfo, EDITOR_USER_STORAGE_STATE, EditorRolePage),
  adminRolePage: async ({ browser }, use, testInfo) =>
    _recordTestVideo(browser, use, testInfo, ADMIN_USER_STORAGE_STATE, AdminRolePage),
});
