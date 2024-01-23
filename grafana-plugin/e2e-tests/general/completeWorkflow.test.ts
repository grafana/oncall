import { test } from '../fixtures';
import {
  filterAlertGroupsTableByIntegrationAndGoToDetailPage,
  verifyThatAlertGroupIsTriggered,
} from '../utils/alertGroup';
import { EscalationStep, createEscalationChain } from '../utils/escalationChain';
import { clickButton, generateRandomValue, selectDropdownValue } from '../utils/forms';
import {
  createIntegration,
  createIntegrationAndSendDemoAlert,
  searchIntegrationAndAssertItsPresence,
} from '../utils/integrations';
import { createOnCallSchedule } from '../utils/schedule';

test('Create integration, schedule and escalation chain, attach schedule to the escalation chain, attach escalation chain to the integraton, send demo alert from the integration, check alert group has been created and schedule was notified', async ({
  adminRolePage: { page, userName },
}) => {
  const ID = generateRandomValue();
  const WEBHOOK_INTEGRATION_NAME = `Webhook-${ID}`;

  const integrationName = WEBHOOK_INTEGRATION_NAME;

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName);

  const escalationChainName = generateRandomValue();
  await createEscalationChain(
    page,
    escalationChainName,
    EscalationStep.NotifyUsersFromOnCallSchedule,
    onCallScheduleName
  );

  await createIntegration({ page, integrationSearchText: 'Webhook', integrationName });

  await page.getByText('Unmatched alerts routed to default route').click();

  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Select escalation chain',
    value: escalationChainName,
    optionExactMatch: false,
  });

  await clickButton({ page, buttonText: 'Send demo alert' });
  await clickButton({ page, buttonText: 'Send Alert' });

  await page.getByTestId('demo-alert-sent-notification').waitFor({ state: 'visible' });

  await page.getByTestId('demo-alert-sent-notification').locator('a').click();

  await filterAlertGroupsTableByIntegrationAndGoToDetailPage(page, integrationName);

  await verifyThatAlertGroupIsTriggered(page, integrationName, `Notify on-call from Schedule'${onCallScheduleName}'`);
});
