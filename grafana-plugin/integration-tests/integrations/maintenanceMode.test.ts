import { test, expect, Page } from '../fixtures';
import { generateRandomValue, selectDropdownValue } from '../utils/forms';
import { createIntegration } from '../utils/integrations';

test.describe('maintenance mode works', () => {
  const MAINTENANCE_DURATION = '1 hour';
  const REMAINING_TIME_TEXT = '59m left';

  const enableMaintenanceMode = async (page: Page, mode: string): Promise<void> => {
    const integrationName = generateRandomValue();

    await createIntegration(page, integrationName);

    // open the integration settings popup
    const integrationSettingsDialog = page.getByTestId('integration-settings-context-menu');
    await integrationSettingsDialog.waitFor({ state: 'visible' });
    await integrationSettingsDialog.click();

    // open the maintenance mode settings drawer + fill in the maintenance details
    await page.getByTestId('integration-start-maintenance').click();

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

    const remainingTimeTooltipTestId = 'maintenance-mode-remaining-time-tooltip';

    const maintenanceModeEnabledTooltip = page.getByTestId(remainingTimeTooltipTestId);
    await maintenanceModeEnabledTooltip.waitFor({ state: 'visible' });

    expect(await page.getByTestId(`${remainingTimeTooltipTestId}-text`).innerText()).toContain(REMAINING_TIME_TEXT);
  };

  test('debug mode', async ({ adminRolePage }) => {
    await enableMaintenanceMode(adminRolePage.page, 'Debug');
  });

  test('"maintenance" mode', async ({ adminRolePage }) => {
    await enableMaintenanceMode(adminRolePage.page, 'Maintenance');
  });
});
