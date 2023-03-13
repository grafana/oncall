import { expect, test } from '@playwright/test';
import { configureOnCallPlugin } from '../utils/configurePlugin';
import { createEscalationChain } from '../utils/escalationChain';
import { generateRandomValue, selectDropdownValue, selectValuePickerValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { goToOnCallPage } from "../utils/navigation";

test.beforeEach(async ({ page }) => {
  await configureOnCallPlugin(page);
});

test('escalation chain filter returns correct alert groups', async ({ page }) => {
  const escalationChainNames = [generateRandomValue(), generateRandomValue()];
  const integrationNames = [generateRandomValue(), generateRandomValue()];

  // create two escalation chains
  await createEscalationChain(
    page,
    escalationChainNames[0],
    null,
    null
  );
  await createEscalationChain(
    page,
    escalationChainNames[1],
    null,
    null
  );

  // create two alert groups, one for each escalation chain
  await createIntegrationAndSendDemoAlert(page, integrationNames[0], escalationChainNames[0]);
  await createIntegrationAndSendDemoAlert(page, integrationNames[1], escalationChainNames[1]);

  // filter by the first escalation chain
  await goToOnCallPage(page, 'incidents');
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Search or filter results...',
    value: 'Escalation Chain',
  });
  await selectValuePickerValue(page, escalationChainNames[0], true);

  // verify that only one alert group is shown
  await expect(page.locator('table > tbody > tr')).toHaveCount(1);

  // verify that the alert group is the one we expect
  const integrationName = await (await page.waitForSelector('table > tbody > tr > td:nth-child(6) span')).textContent();
  expect(integrationName).toBe(integrationNames[0]);
});
