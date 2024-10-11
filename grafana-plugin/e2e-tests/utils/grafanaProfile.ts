import { Page, expect } from '@playwright/test';

import { goToGrafanaPage } from './navigation';

export const setTimezoneInProfile = async (page: Page, timezone: string) => {
  await goToGrafanaPage(page, '/profile');
  await expect(page.getByLabel('Time zone picker')).toBeVisible();

  await page.getByLabel('Time zone picker').click();
  await page.getByLabel('Select options menu').getByText(timezone).click();
  await page.getByTestId('data-testid-shared-prefs-save').click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000); // wait for reload
};
