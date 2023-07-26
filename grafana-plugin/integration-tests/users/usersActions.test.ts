import { test, expect, Page } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test.describe('Users screen actions', () => {
  test("Admin is allowed to edit other users' profile", async ({ adminRolePage }) => {
    await _testButtons(adminRolePage.page, 'button.edit-other-profile-button[disabled]');
  });

  test("Editor is not allowed to edit other users' profile", async ({ editorRolePage }) => {
    await _testButtons(editorRolePage.page, 'button.edit-other-profile-button:not([disabled])');
  });

  test('Viewer is not allowed to view the list of users', async ({ viewerRolePage }) => {
    const { page } = viewerRolePage;

    await goToOnCallPage(page, 'users');

    await expect(page.getByTestId('users-missing-permissions')).toBeVisible();
    await expect(page.getByTestId('users-filters')).not.toBeVisible();
    await expect(page.getByTestId('users-table')).not.toBeVisible();
  });

  test('Viewer cannot access restricted tabs from View My Profile', async ({ viewerRolePage }) => {
    const { page } = viewerRolePage;

    await goToOnCallPage(page, 'users');

    await page.getByTestId('users-view-my-profile').click();

    // the next queries could or could not resolve
    // therefore we wait a generic 1000ms duration and assert based on visibility
    await page.waitForTimeout(1000);

    const tabs = ['tab-phone-verification', 'tab-mobile-app', 'tab-slack', 'tab-telegram'];

    for (let i = 0; i < tabs.length - 1; ++i) {
      const tab = page.getByTestId(tabs[i]);
      if (tab.isVisible()) {
        await tab.click();
        await expect(
          page.getByText('You do not have permission to perform this action. Ask an admin to upgrade your permissions.')
        ).toBeVisible();
      }
    }
  });

  const _testButtons = async (page: Page, selector: string) => {
    await goToOnCallPage(page, 'users');

    const usersTableElement = page.getByTestId('users-table');
    await usersTableElement.waitFor({ state: 'visible' });

    const buttonsList = await page.locator(selector);

    expect(buttonsList).toHaveCount(0);
  };
});
