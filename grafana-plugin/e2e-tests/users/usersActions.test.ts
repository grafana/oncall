import { test, expect } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';
import { viewUsers, accessProfileTabs } from '../utils/users';

test.describe('Users screen actions', () => {
  test("Admin is allowed to edit other users' profile", async ({ adminRolePage: { page } }) => {
    await goToOnCallPage(page, 'users');
    await expect(page.getByTestId('users-table').getByRole('button', { name: 'Edit', disabled: false })).toHaveCount(3);
  });

  test('Admin is allowed to view the list of users', async ({ adminRolePage: { page } }) => {
    await viewUsers(page);
  });

  test('Viewer is not allowed to view the list of users', async ({ viewerRolePage: { page } }) => {
    await viewUsers(page, false);
  });

  test('Viewer cannot access restricted tabs from View My Profile', async ({ viewerRolePage }) => {
    const { page } = viewerRolePage;

    await accessProfileTabs(page, ['tab-mobile-app', 'tab-phone-verification', 'tab-slack', 'tab-telegram'], false);
  });

  test('Editor is allowed to view the list of users', async ({ editorRolePage }) => {
    await viewUsers(editorRolePage.page);
  });

  test("Editor cannot view other users' data", async ({ editorRolePage }) => {
    const { page } = editorRolePage;

    await goToOnCallPage(page, 'users');
    await page.getByTestId('users-email').and(page.getByText('editor')).waitFor();

    await expect(page.getByTestId('users-email').and(page.getByText('editor'))).toHaveCount(1);
    await expect(page.getByTestId('users-email').and(page.getByText('******'))).toHaveCount(2);
    await expect(page.getByTestId('users-phone-number').and(page.getByText('******'))).toHaveCount(2);
  });

  test('Editor can access tabs from View My Profile', async ({ editorRolePage }) => {
    const { page } = editorRolePage;

    // the other tabs depend on Cloud, skip for now
    await accessProfileTabs(page, ['tab-slack', 'tab-telegram'], true);
  });

  test("Editor is not allowed to edit other users' profile", async ({ editorRolePage: { page } }) => {
    await goToOnCallPage(page, 'users');
    await expect(page.getByTestId('users-table').getByRole('button', { name: 'Edit', disabled: false })).toHaveCount(1);
    await expect(page.getByTestId('users-table').getByRole('button', { name: 'Edit', disabled: true })).toHaveCount(2);
  });

  test('Search updates the table view', async ({ adminRolePage }) => {
    const { page, userName } = adminRolePage;
    await goToOnCallPage(page, 'users');

    await page.waitForTimeout(2000);

    const searchInput = page.locator(`[data-testid="search-users"]`);

    await searchInput.fill(userName);
    await page.waitForTimeout(2000);

    const result = page.locator(`[data-testid="users-username"]`);

    expect(await result.count()).toBe(1);
  });
});
