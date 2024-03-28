import { test } from '../fixtures';
import { verifyThatAlertGroupIsTriggered } from '../utils/alertGroup';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { createOnCallScheduleWithRotation } from '../utils/schedule';

test('we can create an oncall schedule + receive an alert', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;
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

  await verifyThatAlertGroupIsTriggered(page, integrationName, `Notify on-call from Schedule '${onCallScheduleName}'`);
});
