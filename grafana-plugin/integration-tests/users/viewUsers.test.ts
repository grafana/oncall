import { test, expect, Page } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test.describe('view list of users', () => {
  const testFlow = async (page: Page, isAllowedToView = true): Promise<void> => {
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
  };

  test('admin is allowed to', async ({ adminRolePage }) => {
    await testFlow(adminRolePage.page);
  });

  test('editor is allowed to', async ({ editorRolePage }) => {
    await testFlow(editorRolePage.page);
  });

  test('viewer is not allowed to', async ({ viewerRolePage }) => {
    await testFlow(viewerRolePage.page, false);
  });
});
