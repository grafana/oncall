import { test } from '@playwright/test';
import { openOnCallPlugin } from '../utils';
import { verifyThatAlertGroupIsTriggered } from '../utils/alertGroup';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { createOnCallSchedule } from '../utils/schedule';

test.beforeEach(async ({ page }) => {
  await openOnCallPlugin(page);
});

test('we can create an oncall schedule + receive an alert', async ({ page }) => {
  const escalationChainName = generateRandomValue();
  const integrationName = generateRandomValue();
  const onCallScheduleName = generateRandomValue();

  await createOnCallSchedule(page, onCallScheduleName);
  await createEscalationChain(
    page,
    escalationChainName,
    EscalationStep.NotifyUsersFromOnCallSchedule,
    onCallScheduleName
  );

  await createIntegrationAndSendDemoAlert(page, integrationName, escalationChainName);

  await verifyThatAlertGroupIsTriggered(page, integrationName, `Notify on-call from Schedule '${onCallScheduleName}'`);
});
