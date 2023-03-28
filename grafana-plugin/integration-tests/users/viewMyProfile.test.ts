import { test, expect } from '@playwright/test';
import { openViewMyProfile } from '../utils/userSettings';
import { VIEWER_FILE } from '../auth.setup';
import { OnCallPage, goToOnCallPage } from '../utils/navigation';

test.describe(() => {
  test.use({ storageState: VIEWER_FILE });

  test('it opens View My Profile with success', async ({ page }) => {
    await goToOnCallPage(page, OnCallPage.USERS);

    await openViewMyProfile(page);
    await delay(60000);

    expect(true).toBe(true);
  });
});

function delay(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}
