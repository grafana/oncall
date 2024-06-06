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
import { OrgRole } from '../utils/constants';
import { goToGrafanaPage, goToOnCallPage } from '../utils/navigation';
import { createGrafanaUser, loginAndWaitTillGrafanaIsLoaded } from '../utils/users';

test.describe('Plugin initialization', () => {
  test('Plugin OnCall pages work for new viewer user right away', async ({ adminRolePage: { page }, browser }) => {
    // Create new viewer user and login as new user
    const USER_NAME = `viewer-${new Date().getTime()}`;
    await createGrafanaUser({ page, username: USER_NAME, role: OrgRole.Viewer });

    // Create new browser context to act as new user
    const viewerUserContext = await browser.newContext();
    const viewerUserPage = await viewerUserContext.newPage();

    await loginAndWaitTillGrafanaIsLoaded({ page: viewerUserPage, username: USER_NAME });

    // Start watching for HTTP responses
    const networkResponseStatuses: number[] = [];
    viewerUserPage.on('requestfinished', async (request) =>
      networkResponseStatuses.push((await request.response()).status())
    );

    // Go to OnCall and assert that none of the requests failed
    await goToOnCallPage(viewerUserPage, 'alert-groups');
    await viewerUserPage.waitForLoadState('networkidle');
    const numberOfFailedRequests = networkResponseStatuses.filter(
      (status) => !(`${status}`.startsWith('2') || `${status}`.startsWith('3'))
    ).length;
    expect(numberOfFailedRequests).toBeLessThanOrEqual(1); // we allow /status request to fail once so plugin is reinstalled

    // ...as well as that user sees content of alert groups page
    await expect(viewerUserPage.getByText('No Alert Groups selected')).toBeVisible();
  });

  test('Extension registered by OnCall plugin works for new editor user right away', async ({
    adminRolePage: { page },
    browser,
  }) => {
    // Create new editor user
    const USER_NAME = `editor-${new Date().getTime()}`;
    await createGrafanaUser({ page, username: USER_NAME, role: OrgRole.Editor });
    await page.waitForLoadState('networkidle');

    // Create new browser context to act as new user
    const editorUserContext = await browser.newContext();
    const editorUserPage = await editorUserContext.newPage();

    await loginAndWaitTillGrafanaIsLoaded({ page: editorUserPage, username: USER_NAME });

    // Start watching for HTTP responses
    const networkResponseStatuses: number[] = [];
    editorUserPage.on('requestfinished', async (request) =>
      networkResponseStatuses.push((await request.response()).status())
    );

    // Go to profile -> IRM tab where OnCall plugin extension is registered and assert that none of the requests failed
    await goToGrafanaPage(editorUserPage, '/profile?tab=irm');
    await editorUserPage.waitForLoadState('networkidle');
    const numberOfFailedRequests = networkResponseStatuses.filter(
      (status) => !(`${status}`.startsWith('2') || `${status}`.startsWith('3'))
    ).length;
    expect(numberOfFailedRequests).toBeLessThanOrEqual(1); // we allow /status request to fail once so plugin is reinstalled

    // ...as well as that user sees content of the extension
    const extensionContentText = editorUserPage.getByText('Please connect Grafana Cloud OnCall to use the mobile app');
    await extensionContentText.waitFor();
    await expect(extensionContentText).toBeVisible();
  });
});
