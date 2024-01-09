import { test, expect } from '../fixtures';
import { resolveFiringAlert } from '../utils/alertGroup';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { clickButton, generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { goToGrafanaPage, goToOnCallPage } from '../utils/navigation';
import { createOnCallSchedule } from '../utils/schedule';

test.describe('Insights', () => {
  test.beforeAll(async ({ adminRolePage: { page, userName } }) => {
    const DATASOURCE_NAME = 'OnCall Prometheus';
    const DATASOURCE_URL = 'http://oncall-dev-prometheus-server.default.svc.cluster.local';

    await goToGrafanaPage(page, '/connections/datasources');
    await page.waitForLoadState('networkidle');

    // setup data source if it's not already connected
    const isDataSourceAlreadyConnected = await page.getByText(DATASOURCE_NAME).isVisible();
    if (!isDataSourceAlreadyConnected) {
      await page.getByRole('link', { name: 'Add data source' }).click();
      await clickButton({ page, buttonText: 'Prometheus' });
      await page.getByRole('textbox', { name: 'Data source settings page name input field' }).fill(DATASOURCE_NAME);
      await page.getByPlaceholder('http://localhost:9090').fill(DATASOURCE_URL);
      await clickButton({ page, buttonText: 'Save & test' });
    }

    // send alert and resolve to get some values in insights
    const escalationChainName = generateRandomValue();
    const integrationName = generateRandomValue();
    const onCallScheduleName = generateRandomValue();
    await createOnCallSchedule(page, onCallScheduleName, userName);
    await createEscalationChain(
      page,
      escalationChainName,
      EscalationStep.NotifyUsersFromOnCallSchedule,
      onCallScheduleName
    );
    await createIntegrationAndSendDemoAlert(page, integrationName, escalationChainName);
    await resolveFiringAlert(page);
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

  test('There is no panel that misses data', async ({ adminRolePage: { page } }) => {
    await goToOnCallPage(page, 'insights');
    await page.getByText('Last 7 days').click();
    await page.getByText('Last 1 hour').click();
    await page.waitForTimeout(2000);
    await expect(page.getByText('No data')).toBeHidden();
  });
});
