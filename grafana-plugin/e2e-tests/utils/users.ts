import { Page, expect } from '@playwright/test';

import { OrgRole } from './constants';
import { clickButton } from './forms';
import { goToGrafanaPage, goToOnCallPage } from './navigation';

export async function accessProfileTabs(page: Page, tabs: string[], hasAccess: boolean) {
  await goToOnCallPage(page, 'users');

  await page.getByTestId('users-view-my-profile').click();

  // the next queries could or could not resolve
  // therefore we wait a generic 1000ms duration and assert based on visibility
  await page.waitForTimeout(1000);

  for (let i = 0; i < tabs.length - 1; ++i) {
    const tab = page.getByTestId(tabs[i]);

    if (await tab.isVisible()) {
      await tab.click();

      const query = page.getByText(
        'You do not have permission to perform this action. Ask an admin to upgrade your permissions.'
      );

      if (hasAccess) {
        await expect(query).toBeHidden();
      } else {
        await expect(query).toBeVisible();
      }
    }
  }
}

export async function viewUsers(page: Page, isAllowedToView = true): Promise<void> {
  await goToOnCallPage(page, 'users');

  if (isAllowedToView) {
    const usersTable = page.getByTestId('users-table');
    await usersTable.getByRole('row').nth(1).waitFor();
    await expect(usersTable.getByRole('row')).toHaveCount(4);
  } else {
    await expect(page.getByTestId('view-users-missing-permission-message')).toHaveText(
      /You are missing the .* to be able to view OnCall users/
    );
  }
}

export const createGrafanaUser = async ({
  page,
  username,
  role = OrgRole.Viewer,
}: {
  page: Page;
  username: string;
  role?: OrgRole;
}): Promise<void> => {
  await goToGrafanaPage(page, '/admin/users');
  await page.getByRole('link', { name: 'New user' }).click();
  await page.getByLabel('Name *').fill(username);
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password *').fill(username);
  await clickButton({ page, buttonText: 'Create user' });

  if (role !== OrgRole.Viewer) {
    await clickButton({ page, buttonText: 'Change role' });
    await page
      .locator('div')
      .filter({ hasText: /^Viewer$/ })
      .nth(1)
      .click();
    await page.getByText(new RegExp(role)).click();
    await clickButton({ page, buttonText: 'Save' });
  }
};

export const reloginAndWaitTillGrafanaIsLoaded = async ({ page, username }: { page: Page; username: string }) => {
  await goToGrafanaPage(page, '/logout');
  await page.getByLabel('Email or username').fill(username);
  await page.getByLabel(/Password/).fill(username);
  await clickButton({ page, buttonText: 'Log in' });

  await page.getByText('Welcome to Grafana').waitFor();
  await page.waitForLoadState('networkidle');
};
