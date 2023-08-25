import { test, expect } from '../fixtures';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { waitForSms } from '../utils/phone';
import { configureUserNotificationSettings, verifyUserPhoneNumber } from '../utils/userSettings';

// TODO: enable once we've signed up for a MailSlurp account to receieve SMSes
test.skip('we can verify our phone number + receive an SMS alert @expensive', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;
  const escalationChainName = generateRandomValue();
  const integrationName = generateRandomValue();

  await verifyUserPhoneNumber(page);
  await configureUserNotificationSettings(page, 'SMS');

  await createEscalationChain(page, escalationChainName, EscalationStep.NotifyUsers, userName);
  await createIntegrationAndSendDemoAlert(page, integrationName, escalationChainName);

  // wait for the SMS alert notification to arrive
  const smsAlertNotification = await waitForSms();

  expect(smsAlertNotification).toContain('OnCall');
  expect(smsAlertNotification).toContain('alert');
});
