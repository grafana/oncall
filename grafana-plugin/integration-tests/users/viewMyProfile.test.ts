import { test, expect } from '@playwright/test';
import { openViewMyProfile } from '../utils/userSettings';
import { VIEWER_FILE } from '../auth.setup';
import { OnCallPage, goToOnCallPage } from '../utils/navigation';
import { GRAFANA_VIEWER_EMAIL, GRAFANA_VIEWER_USERNAME } from '../utils/constants';

test.describe(() => {
  test.use({ storageState: VIEWER_FILE });

  test('it opens View My Profile with success', async ({ page }) => {
    await goToOnCallPage(page, OnCallPage.USERS);

    await openViewMyProfile(page);

    const addMobileApp = await page.getByTestId('add-mobile-app');
    expect(addMobileApp.isDisabled).toBeTruthy();

    const createICalLink = await page.getByTestId('create-ical-link');
    expect(createICalLink.isDisabled).toBeTruthy();

    expect((await page.getByTestId('user-username').innerText()).valueOf()).toBe(GRAFANA_VIEWER_USERNAME);
    expect((await page.getByTestId('user-email').innerText()).valueOf()).toBe(GRAFANA_VIEWER_EMAIL);
  });
});
