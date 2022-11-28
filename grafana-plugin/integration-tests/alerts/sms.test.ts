import { test, expect } from '@playwright/test';
import { openOnCallPlugin } from '../utils';
import { createEscalationChain } from '../utils/escalationChain';
import { generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { waitForSms } from '../utils/phone';
import { configureUserNotificationSettings, verifyUserPhoneNumber } from '../utils/userSettings';

test.beforeEach(async ({ page }) => {
  await openOnCallPlugin(page);
});

test('we can verify our phone number + receive an SMS alert', async ({ page }) => {
  test.slow(); // easy way to triple the default timeout

  const escalationChainName = generateRandomValue();

  await verifyUserPhoneNumber(page);
  await configureUserNotificationSettings(page, 'SMS');

  await createEscalationChain(page, escalationChainName);
  await createIntegrationAndSendDemoAlert(page, escalationChainName);

  // wait for the SMS alert notification to arrive
  const smsAlertNotification = await waitForSms();

  // TODO:
  console.log('SMS Alert Notification: ', smsAlertNotification);
  expect(smsAlertNotification).toContain('OnCall');
  expect(smsAlertNotification).toContain('alert');
});
