import semver from 'semver';

import { test, expect } from '../fixtures';
import { resolveFiringAlert } from '../utils/alertGroup';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { clickButton, generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { goToGrafanaPage, goToOnCallPage } from '../utils/navigation';
import { createOnCallScheduleWithRotation } from '../utils/schedule';

/**
 * Insights is dependent on Scenes which were only added in Grafana 10.0.0
 * https://grafana.com/docs/grafana/latest/whatsnew/whats-new-in-v10-0/#scenes
 * TODO: remove the process.env.CURRENT_GRAFANA_VERSION portion
 * and use the currentGrafanaVersion fixture once this bugged is patched in playwright
 * https://github.com/microsoft/playwright/issues/29608
 */
test.skip(
  () => semver.lt(process.env.CURRENT_GRAFANA_VERSION, '10.0.0'),
  'Insights is only available in Grafana 10.0.0 and above'
);

/**
 * skipping as these tests are currently flaky
 * see this Slack conversation for more details:
 * https://raintank-corp.slack.com/archives/C04JCU51NF8/p1712069772861909
 */
test.describe.skip('Insights', () => {
  test.beforeAll(async ({ adminRolePage: { page } }) => {
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
  });

  test('Viewer can see all the panels in OnCall insights', async ({ viewerRolePage: { page } }) => {
    await goToOnCallPage(page, 'insights');
    [
      'New alert groups',
      'Mean time to respond \\(MTTR\\) average',
      'Alert groups by Integration',
      'Mean time to respond \\(MTTR\\) by Integration',
      'Alert groups by Team',
      'Mean time to respond \\(MTTR\\) by Team',
      'New alert groups notifications',
    ].forEach(async (panelTitle) => {
      await expect(page.getByRole('heading', { name: new RegExp(`^${panelTitle}$`) }).first()).toBeVisible();
    });
  });

  test('There is no panel that misses data', async ({ adminRolePage: { page, userName } }) => {
    test.setTimeout(90_000);

    // send alert and resolve to get some values in insights
    const escalationChainName = generateRandomValue();
    const integrationName = generateRandomValue();
    const onCallScheduleName = generateRandomValue();
    await createOnCallScheduleWithRotation(page, onCallScheduleName, userName);
    await createEscalationChain(
      page,
      escalationChainName,
      EscalationStep.NotifyUsersFromOnCallSchedule,
      onCallScheduleName
    );
    await createIntegrationAndSendDemoAlert(page, integrationName, escalationChainName);
    await resolveFiringAlert(page);
    // wait for Prometheus to scrape the data
    await page.waitForTimeout(5000);

    // check that we have data in insights panels
    await goToOnCallPage(page, 'insights');
    await page.getByText('Last 24 hours').click();
    await page.getByText('Last 1 hour').click();
    await page.waitForTimeout(3000);
    await expect(page.getByText('No data')).toBeHidden();
  });
});
