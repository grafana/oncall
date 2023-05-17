import { test, expect } from '@playwright/test';
import { GRAFANA_USERNAME } from '../utils/constants';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { waitForSms } from '../utils/phone';
import { configureUserNotificationSettings, verifyUserPhoneNumber } from '../utils/userSettings';

// TODO: enable once we've signed up for a MailSlurp account to receieve SMSes
test.skip('we can verify our phone number + receive an SMS alert', async ({ page }) => {
  const escalationChainName = generateRandomValue();
  const integrationName = generateRandomValue();

  await verifyUserPhoneNumber(page);
  await configureUserNotificationSettings(page, 'SMS');

  await createEscalationChain(page, escalationChainName, EscalationStep.NotifyUsers, GRAFANA_USERNAME);
  await createIntegrationAndSendDemoAlert(page, integrationName, escalationChainName);

  // wait for the SMS alert notification to arrive
  const smsAlertNotification = await waitForSms();

  expect(smsAlertNotification).toContain('OnCall');
  expect(smsAlertNotification).toContain('alert');
});
