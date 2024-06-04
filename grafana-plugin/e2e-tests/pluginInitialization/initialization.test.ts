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

import { test } from '../fixtures';
import { goToGrafanaPage } from '../utils/navigation';

test.describe('Plugin initialization', () => {
  test('plugin config page', async ({ adminRolePage: { page } }) => {
    await goToGrafanaPage(page);
    expect(page).toHaveText('plugin config page');
  });
});

test.describe('Plugin configuration', () => {
  test('plugin config page', async ({ adminRolePage: { page } }) => {
    await goToGrafanaPage(page);
    expect(page).toHaveText('plugin config page');
  });
});
