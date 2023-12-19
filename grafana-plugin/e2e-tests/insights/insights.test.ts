import { getByRole } from '@testing-library/react';
import { test, expect } from '../fixtures';
import { clickButton } from '../utils/forms';
import { goToGrafanaPage, goToOnCallPage } from '../utils/navigation';
import { viewUsers, accessProfileTabs } from '../utils/users';

test.describe('Insights', () => {
  test.beforeAll(async ({ adminRolePage: { page } }) => {
    const DATASOURCE_NAME = 'OnCall Prometheus';
    const DATASOURCE_URL = 'http://oncall-dev-prometheus-server.default.svc.cluster.local';

    await goToGrafanaPage(page);
    // await page.waitForTimeout(1000);
    // await page.getByLabel('Toggle menu').click();
    await goToGrafanaPage(page, '/connections/datasources');
    // await page.waitForTimeout(1000);
    // http://oncall-dev-prometheus-server.default.svc.cluster.local
    await page.waitForLoadState('networkidle');
    const isDataSourceAlreadyConnected = await page.getByText(DATASOURCE_NAME).isVisible();
    if (!isDataSourceAlreadyConnected) {
      await page.getByRole('link', { name: 'Add data source' }).click();
      await clickButton({ page, buttonText: 'Prometheus' });
      //   await page.waitForTimeout(2000);
      await page.getByRole('textbox', { name: 'Data source settings page name input field' }).fill(DATASOURCE_NAME);
      await page.getByRole('textbox', { name: 'Data source connection URL' }).fill(DATASOURCE_URL);
      //   await page.waitForTimeout(5000);
      await clickButton({ page, buttonText: 'Save & test' });
      await page.getByText('Successfully queried the Prometheus API').waitFor();
    }
  });

  test('Viewer can see all the panels in OnCall insights', async ({ viewerRolePage: { page } }) => {
    await goToOnCallPage(page, 'insights');

    [
      'Total alert groups',
      'Total alert groups by state',
      'New alert groups for selected period',
      'Mean time to respond \\(MTTR\\)',
      'MTTR changed for period',
      'New alert groups during time period',
      'Alert groups by Integration',
      'Mean time to respond \\(MTTR\\) by Integration',
    ].forEach(async (panelTitle) => {
      await expect(page.getByRole('heading', { name: new RegExp(`^${panelTitle}$`) }).first()).toBeVisible();
    });
  });

  test('There is no panel that misses data', async ({ viewerRolePage: { page } }) => {
    await goToOnCallPage(page, 'insights');

    await expect(page.getByText('No data')).toBeHidden();
  });
});
