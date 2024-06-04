/*
Scenario: User reconfigures plugin successfully
Given user goes to plugin configuration page
When user enters valid URL of OnCall Engine
And OnCall Engine is up and running
And user clicks “Test & Save”
Then user is informed about successful test
And new configuration is saved

Scenario: User reconfigures plugin unsuccessfully
Given user goes to plugin configuration page
When user enters URL of OnCall Engine
And OnCall Engine is down or wrong URL is provided
And user clicks “Test & Save”
Then user is informed about unsuccessful test
And new configuration is not saved

Scenario: New viewer user goes to OnCall
Given OSS viewer user has just been created
When viewer user goes to OnCall page
Then OnCall loads as usual

Scenario: New viewer user goes to OnCall extension
Given OSS viewer user has been just created
When viewer user goes directly to OnCall plugin extension registered in Grafana
Then user sees loading page saying that his/her OnCall data is being synchronized right now
And once sync process is completed user is informed that his/her data has been synced
And OnCall extension is loaded so that user can proceed

Scenario: Existing user goes to OnCall page or extension
Given OSS user that has already used OnCall before
When user goes to OnCall
Then OnCall loads as usual
*/

import { test, expect } from '../fixtures';
import { clickButton } from '../utils/forms';
import { goToGrafanaPage, goToOnCallPage } from '../utils/navigation';
import { createGrafanaUser } from '../utils/users';

test.describe('Plugin initialization', () => {
  test('Plugin OnCall pages work for new viewer user right away', async ({ adminRolePage: { page } }) => {
    // Create new viewer user
    const USER_NAME = `viewer-${new Date().getTime()}`;
    await createGrafanaUser(page, USER_NAME);

    // Login as new user
    await goToGrafanaPage(page, '/logout');
    await page.getByLabel('Email or username').fill(USER_NAME);
    await page.getByLabel(/Password/).fill(USER_NAME);
    await clickButton({ page, buttonText: 'Log in' });

    // Wait till Grafana home page is loaded and start tracking HTTP response codes
    await page.getByText('Welcome to Grafana').waitFor();
    await page.waitForLoadState('networkidle');
    const networkResponseStatuses: number[] = [];
    page.on('requestfinished', async (request) => networkResponseStatuses.push((await request.response()).status()));

    // Go to OnCall and assert that none of the requests failed
    await goToOnCallPage(page, 'alert-groups');
    const allRequestsPassed = networkResponseStatuses.every(
      (status) => `${status}`.startsWith('2') || `${status}`.startsWith('3')
    );
    expect(allRequestsPassed).toBeTruthy();

    // ...and user sees content of alert groups page
    await expect(page.getByText('No alert groups found')).toBeVisible();
  });

  test('Extension registered by OnCall plugin works for new editor user right away', async ({
    adminRolePage: { page },
  }) => {
    // Create new editor user
    const USER_NAME = `editor-${new Date().getTime()}`;
    await createGrafanaUser(page, USER_NAME);
    await clickButton({ page, buttonText: 'Create user' });
    await clickButton({ page, buttonText: 'Change role' });
    await page
      .locator('div')
      .filter({ hasText: /^Viewer$/ })
      .nth(1)
      .click();
    await page.getByText(/Editor/).click();
    await clickButton({ page, buttonText: 'Save' });

    // Login as new user
    await goToGrafanaPage(page, '/logout');
    await page.getByLabel('Email or username').fill(USER_NAME);
    await page.getByLabel(/Password/).fill(USER_NAME);
    await clickButton({ page, buttonText: 'Log in' });

    // Wait till Grafana home page is loaded and start tracking HTTP response codes
    await page.getByText('Welcome to Grafana').waitFor();
    await page.waitForLoadState('networkidle');
    const networkResponseStatuses: number[] = [];
    page.on('requestfinished', async (request) => networkResponseStatuses.push((await request.response()).status()));

    // Go to profile -> IRM tab where OnCall plugin extension is registered
    await goToGrafanaPage(page, '/profile?tab=irm');
    const allRequestsPassed = networkResponseStatuses.every(
      (status) => `${status}`.startsWith('2') || `${status}`.startsWith('3')
    );
    expect(allRequestsPassed).toBeTruthy();

    console.log(networkResponseStatuses);

    // ...and user sees content of alert groups page
    const extensionContentText = page.getByText('Please connect Grafana Cloud OnCall to use the mobile app');
    await extensionContentText.waitFor();
    await expect(extensionContentText).toBeVisible();
  });
});

test.describe('Plugin configuration', () => {
  test('plugin config page', async ({ adminRolePage: { page } }) => {
    await goToGrafanaPage(page);
    expect(page).toBe('plugin config page');
  });
});
