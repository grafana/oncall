import { test, expect } from '../fixtures';
import { isGrafanaVersionLowerThan } from '../utils/constants';
import { goToOnCallPage } from '../utils/navigation';
import { verifyThatUserCanViewOtherUsers, accessProfileTabs } from '../utils/users';

test.describe('Users screen actions', () => {
  test('Viewer is not allowed to view the list of users', async ({ viewerRolePage: { page } }) => {
    await verifyThatUserCanViewOtherUsers(page, false);
  });

  test('Viewer cannot access restricted tabs from View My Profile', async ({ viewerRolePage }) => {
    const { page } = viewerRolePage;
    const tabsToCheck = ['tab-phone-verification', 'tab-slack', 'tab-telegram'];

    // After 10.3 it's been moved to global user profile
    if (isGrafanaVersionLowerThan('10.3.0')) {
      tabsToCheck.unshift('tab-mobile-app');
    }

    await accessProfileTabs(page, tabsToCheck, false);
  });

  test('Editor is allowed to view the list of users', async ({ editorRolePage }) => {
    await verifyThatUserCanViewOtherUsers(editorRolePage.page);
  });

  test("Editor cannot view other users' data", async ({ editorRolePage }) => {
    const { page } = editorRolePage;

    await goToOnCallPage(page, 'users');
    await page.getByTestId('users-email').and(page.getByText('editor')).waitFor();

    await expect(page.getByTestId('users-email').and(page.getByText('editor'))).toHaveCount(1);
    const maskedEmailsCount = await page.getByTestId('users-email').and(page.getByText('******')).count();
    expect(maskedEmailsCount).toBeGreaterThan(1);
    const maskedPhoneNumbersCount = await page.getByTestId('users-phone-number').and(page.getByText('******')).count();
    expect(maskedPhoneNumbersCount).toBeGreaterThan(1);
  });

  test('Editor can access tabs from View My Profile', async ({ editorRolePage }) => {
    const { page } = editorRolePage;

    // the other tabs depend on Cloud, skip for now
    await accessProfileTabs(page, ['tab-slack', 'tab-telegram'], true);
  });

  test("Editor is not allowed to edit other users' profile", async ({ editorRolePage: { page } }) => {
    await goToOnCallPage(page, 'users');
    await expect(page.getByTestId('users-table').getByRole('button', { name: 'Edit', disabled: false })).toHaveCount(1);
    const usersCountWithDisabledEdit = await page
      .getByTestId('users-table')
      .getByRole('button', { name: 'Edit', disabled: true })
      .count();
    expect(usersCountWithDisabledEdit).toBeGreaterThan(1);
  });

  test("Admin is allowed to edit other users' profile", async ({ adminRolePage: { page } }) => {
    await goToOnCallPage(page, 'users');
    const editableUsers = page.getByTestId('users-table').getByRole('button', { name: 'Edit', disabled: false });
    await editableUsers.first().waitFor();
    const editableUsersCount = await editableUsers.count();
    expect(editableUsersCount).toBeGreaterThan(1);
  });

  test('Admin is allowed to view the list of users', async ({ adminRolePage: { page } }) => {
    await verifyThatUserCanViewOtherUsers(page);
  });

  test('Search updates the table view', async ({ adminRolePage }) => {
    const { page, userName } = adminRolePage;
    await goToOnCallPage(page, 'users');

    await page.waitForTimeout(2000);

    await page
      .locator('div')
      .filter({ hasText: /^Search or filter results\.\.\.$/ })
      .nth(1)
      .click();
    await page.keyboard.insertText(userName);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);

    const result = page.locator(`[data-testid="users-username"]`);

    expect(await result.count()).toBe(1);
  });
});
