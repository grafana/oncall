import { waitInMs } from 'helpers/async';

import { test, expect, Page } from '../fixtures';
import { OrgRole, isGrafanaVersionLowerThan } from '../utils/constants';
import { goToGrafanaPage, goToOnCallPage } from '../utils/navigation';
import { createGrafanaUser, loginAndWaitTillGrafanaIsLoaded } from '../utils/users';

const assertThatUserCanAccessOnCallWithinMinute = async (page: Page, testIdOfConnectedElem: string) => {
  let isConnected = false;
  let retries = 0;
  while (!isConnected && retries < 12) {
    await waitInMs(5_000);
    await page.reload();
    await page.waitForLoadState('networkidle');
    isConnected = await page.getByTestId(testIdOfConnectedElem).isVisible();
  }
  expect(isConnected).toBe(true);
};

test.describe('Plugin initialization', () => {
  test('Plugin OnCall pages work for new viewer user within 1 minute after creation', async ({
    adminRolePage: { page },
    browser,
  }) => {
    test.slow();

    // Create new viewer user and login as new user
    const USER_NAME = `viewer-${new Date().getTime()}`;
    await createGrafanaUser({ page, username: USER_NAME, role: OrgRole.Viewer });

    // Create new browser context to act as new user
    const viewerUserContext = await browser.newContext();
    const viewerUserPage = await viewerUserContext.newPage();

    await loginAndWaitTillGrafanaIsLoaded({ page: viewerUserPage, username: USER_NAME });

    // Go to OnCall and assert that plugin is connected
    await goToOnCallPage(viewerUserPage, 'alert-groups');

    await assertThatUserCanAccessOnCallWithinMinute(viewerUserPage, 'add-escalation-button');
  });

  test('Extension registered by OnCall plugin works for new editor user within 1 minute after creation', async ({
    adminRolePage: { page },
    browser,
  }) => {
    test.slow();

    test.skip(isGrafanaVersionLowerThan('10.3.0'), 'Extension is only available in Grafana 10.3.0 and above');

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

    await assertThatUserCanAccessOnCallWithinMinute(editorUserPage, 'mobile-app-connection');
  });
});
