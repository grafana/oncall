import { test, expect, Page } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test.describe('view list of users', () => {
  test.slow(); // this test is doing a good amount of work, give it time

  test('admin is allowed to edit other profiles', async ({ adminRolePage }) => {
    const { page } = adminRolePage;

    await goToOnCallPage(page, 'users');

    const usersTableElement = page.getByTestId('users-table');
    await usersTableElement.waitFor({ state: 'visible' });

    const editOtherUserProfileDisabledButtonList = await page.locator('button.edit-other-profile-button[disabled]');

    expect(editOtherUserProfileDisabledButtonList).toHaveCount(0);
  });

  test('editor is not allowed to edit other profiles', async ({ editorRolePage }) => {
    const { page } = editorRolePage;

    await goToOnCallPage(page, 'users');

    const usersTableElement = page.getByTestId('users-table');
    await usersTableElement.waitFor({ state: 'visible' });

    const editOtherUserProfileEnabledButtonList = await page.locator(
      'button.edit-other-profile-button:not([disabled])'
    );

    expect(editOtherUserProfileEnabledButtonList).toHaveCount(0);
  });

  test.skip('viewer is not allowed to', async ({ viewerRolePage }) => {});
});
