import { test, expect, Page } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test.describe("edit other user's profiles", () => {
  test.slow();

  const _testButtons = async (page: Page, selector: string) => {
    await goToOnCallPage(page, 'users');

    const usersTableElement = page.getByTestId('users-table');
    await usersTableElement.waitFor({ state: 'visible' });

    const buttonsList = await page.locator(selector);

    expect(buttonsList).toHaveCount(0);
  };

  test('admin is allowed', async ({ adminRolePage }) => {
    await _testButtons(adminRolePage.page, 'button.edit-other-profile-button[disabled]');
  });

  test('editor is not allowed', async ({ editorRolePage }) => {
    await _testButtons(editorRolePage.page, 'button.edit-other-profile-button:not([disabled])');
  });
});
