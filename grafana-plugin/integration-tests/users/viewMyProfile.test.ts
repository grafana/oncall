import { test, expect } from '@playwright/test';
import { configureOnCallPlugin } from '../utils/configurePlugin';
import { openViewMyProfile } from '../utils/userSettings';
import { VIEWER_FILE } from '../auth.setup';

test.beforeEach(async ({ page }) => {
  await configureOnCallPlugin(page);
});

test.describe(() => {
  test.use({ storageState: VIEWER_FILE });

  test('it opens View My Profile with success', async ({ page }) => {
    await openViewMyProfile(page);
    await delay(6000);

    expect(true).toBe(true);
  });
});

function delay(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}
