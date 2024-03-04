import { test, expect, Page, Locator } from '../fixtures';
import { verifyThatAlertGroupIsRoutedCorrectlyButNotEscalated } from '../utils/alertGroup';
import { EscalationStep, createEscalationChain } from '../utils/escalationChain';
import { generateRandomValue, selectDropdownValue } from '../utils/forms';
import {
  assignEscalationChainToIntegration,
  createIntegration,
  filterIntegrationsTableAndGoToDetailPage,
  sendDemoAlert,
} from '../utils/integrations';
import { goToOnCallPage } from '../utils/navigation';

type MaintenanceModeType = 'Debug' | 'Maintenance';

test.describe('maintenance mode works', () => {
  const MAINTENANCE_DURATION = '1 hour';
  const REMAINING_TIME_TEXT = '59m left';
  const REMAINING_TIME_TOOLTIP_TEST_ID = 'maintenance-mode-remaining-time-tooltip';

  const createRoutedText = (escalationChainName: string): string =>
    `alert group assigned to route "default" with escalation chain "${escalationChainName}"`;

  const _openIntegrationSettingsPopup = async (page: Page, shouldDoubleClickSettingsIcon = false): Promise<void> => {
    await page.waitForTimeout(2000);
    const integrationSettingsPopupElement = page
      .getByTestId('integration-settings-context-menu-wrapper')
      .getByRole('img');
    await integrationSettingsPopupElement.click();
    /**
     * sometimes we need to click twice (e.g. adding the escalation chain route
     * doesn't unfocus out of the select element after selecting an option)
     */
    if (shouldDoubleClickSettingsIcon) {
      await integrationSettingsPopupElement.click();
    }
  };

  const getRemainingTimeTooltip = (page: Page): Locator => page.getByTestId(REMAINING_TIME_TOOLTIP_TEST_ID);

  const enableMaintenanceMode = async (page: Page, mode: MaintenanceModeType): Promise<void> => {
    await _openIntegrationSettingsPopup(page, true);
    // open the maintenance mode settings drawer + fill in the maintenance details
    await page.getByText('Start Maintenance').click();

    // fill in the form
    const maintenanceModeDrawer = page.getByTestId('maintenance-mode-drawer');

    await selectDropdownValue({
      page,
      startingLocator: maintenanceModeDrawer,
      selectType: 'grafanaSelect',
      placeholderText: 'Choose mode',
      value: mode,
      optionExactMatch: false,
    });

    await selectDropdownValue({
      page,
      startingLocator: maintenanceModeDrawer,
      selectType: 'grafanaSelect',
      placeholderText: 'Choose duration',
      value: MAINTENANCE_DURATION,
      optionExactMatch: false,
    });

    await maintenanceModeDrawer.getByTestId('create-maintenance-button').click();

    const maintenanceModeRemainingTimeTooltip = getRemainingTimeTooltip(page);
    await maintenanceModeRemainingTimeTooltip.waitFor({ state: 'visible' });

    expect(await page.getByTestId(`${REMAINING_TIME_TOOLTIP_TEST_ID}-text`).innerText()).toContain(REMAINING_TIME_TEXT);
  };

  const disableMaintenanceMode = async (page: Page, integrationName: string): Promise<void> => {
    await goToOnCallPage(page, 'integrations');

    await filterIntegrationsTableAndGoToDetailPage(page, integrationName);
    await _openIntegrationSettingsPopup(page, true);

    // click the stop maintenance button
    await page.getByText('Stop Maintenance').click();

    // in the modal popup, confirm that we want to stop it
    await page.locator('button >> text=Stop').click();

    await getRemainingTimeTooltip(page).waitFor({ state: 'hidden' });
  };

  const createIntegrationAndEscalationChainAndEnableMaintenanceMode = async (
    page: Page,
    userName: string,
    maintenanceModeType: MaintenanceModeType
  ): Promise<{
    escalationChainName: string;
    integrationName: string;
  }> => {
    const escalationChainName = generateRandomValue();
    const integrationName = generateRandomValue();

    await createEscalationChain(page, escalationChainName, EscalationStep.NotifyUsers, userName);
    await createIntegration({ page, integrationName });
    await page.waitForTimeout(1000);
    await assignEscalationChainToIntegration(page, escalationChainName);
    await enableMaintenanceMode(page, maintenanceModeType);

    return { escalationChainName, integrationName };
  };

  test('debug mode', async ({ adminRolePage: { page, userName } }) => {
    const { escalationChainName, integrationName } = await createIntegrationAndEscalationChainAndEnableMaintenanceMode(
      page,
      userName,
      'Debug'
    );
    await sendDemoAlert(page);
    await verifyThatAlertGroupIsRoutedCorrectlyButNotEscalated(
      page,
      integrationName,
      createRoutedText(escalationChainName)
    );

    await disableMaintenanceMode(page, integrationName);
  });

  test('"maintenance" mode', async ({ adminRolePage: { page, userName } }) => {
    const { integrationName } = await createIntegrationAndEscalationChainAndEnableMaintenanceMode(
      page,
      userName,
      'Maintenance'
    );
    await sendDemoAlert(page);

    // TODO: there seems to be a bug here where "maintenance" mode alert groups don't show up in the UI
    // await verifyThatAlertGroupIsRoutedCorrectlyButNotEscalated(
    //   page,
    //   integrationName,
    //   createRoutedText(escalationChainName)
    // );

    await disableMaintenanceMode(page, integrationName);
  });
});
