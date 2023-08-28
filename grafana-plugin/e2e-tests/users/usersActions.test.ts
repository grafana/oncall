import { test, expect, Page } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test.describe('Users screen actions', () => {
  test("Admin is allowed to edit other users' profile", async ({ adminRolePage }) => {
    await _testButtons(adminRolePage.page, 'button.edit-other-profile-button[disabled]');
  });

  test('Admin is allowed to view the list of users', async ({ adminRolePage }) => {
    await _viewUsers(adminRolePage.page);
  });

  test('Viewer is not allowed to view the list of users', async ({ viewerRolePage }) => {
    await _viewUsers(viewerRolePage.page, false);
  });

  test('Viewer cannot access restricted tabs from View My Profile', async ({ viewerRolePage }) => {
    const { page } = viewerRolePage;

    await _accessProfileTabs(page, ['tab-mobile-app', 'tab-phone-verification', 'tab-slack', 'tab-telegram'], false);
  });

  test('Editor is allowed to view the list of users', async ({ editorRolePage }) => {
    await _viewUsers(editorRolePage.page);
  });

  test("Editor cannot view other users' data", async ({ editorRolePage }) => {
    const { page } = editorRolePage;

    await goToOnCallPage(page, 'users');
    await page.waitForSelector('.current-user');

    // check if these fields are Masked or Not (******)
    const fieldIds = ['users-email', 'users-phone-number'];

    for (let i = 0; i < fieldIds.length - 1; ++i) {
      const currentUsername = page.locator(`.current-user [data-testid="${fieldIds[i]}"]`);

      expect((await currentUsername.all()).length).toBe(1); // match for current user
      (await currentUsername.all()).forEach((val) => expect(val).not.toHaveText('******'));

      const otherUsername = page.locator(`.other-user [data-testid="${fieldIds[i]}"]`);

      expect((await otherUsername.all()).length).toBeGreaterThan(1); // match for other users (>= 1)
      (await otherUsername.all()).forEach((val) => expect(val).toHaveText('******'));
    }
  });

  test('Editor can access tabs from View My Profile', async ({ editorRolePage }) => {
    const { page } = editorRolePage;

    // the other tabs depend on Cloud, skip for now
    await _accessProfileTabs(page, ['tab-slack', 'tab-telegram'], true);
  });

  test("Editor is not allowed to edit other users' profile", async ({ editorRolePage }) => {
    await _testButtons(editorRolePage.page, 'button.edit-other-profile-button:not([disabled])');
  });

  test('Search updates the table view', async ({ adminRolePage }) => {
    const { page } = adminRolePage;
    await goToOnCallPage(page, 'users');

    const searchInput = page.locator(`[data-testid="search-users"]`);

    await searchInput.fill('oncall');
    await page.waitForTimeout(5000);

    const result = page.locator(`[data-testid="users-username"]`);

    expect(await result.count()).toBe(1);
  });

  /*
   * Helper methods
   */

  async function _testButtons(page: Page, selector: string) {
    await goToOnCallPage(page, 'users');

    const usersTableElement = page.getByTestId('users-table');
    await usersTableElement.waitFor({ state: 'visible' });

    const buttonsList = await page.locator(selector);

    expect(buttonsList).toHaveCount(0);
  }

  async function _accessProfileTabs(page: Page, tabs: string[], hasAccess: boolean) {
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

  async function _viewUsers(page: Page, isAllowedToView = true): Promise<void> {
    await goToOnCallPage(page, 'users');

    if (isAllowedToView) {
      const usersTableElement = page.getByTestId('users-table');
      await usersTableElement.waitFor({ state: 'visible' });

      const userRowsContext = await usersTableElement.locator('tbody > tr').allTextContents();
      expect(userRowsContext.length).toBeGreaterThan(0);
    } else {
      const missingPermissionsMessageElement = page.getByTestId('view-users-missing-permission-message');
      await missingPermissionsMessageElement.waitFor({ state: 'visible' });

      const missingPermissionMessage = await missingPermissionsMessageElement.textContent();
      expect(missingPermissionMessage).toMatch(/You are missing the .* to be able to view OnCall users/);
    }
  }
});
