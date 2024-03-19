import { test, expect } from '../fixtures';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { generateRandomValue } from '../utils/forms';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';
import { goToOnCallPage } from '../utils/navigation';
import { waitForSms } from '../utils/phone';
import { configureUserNotificationSettings, verifyUserPhoneNumber } from '../utils/userSettings';

test('we can verify our phone number + receive an SMS alert @expensive', async ({ adminRolePage }) => {
  test.setTimeout(90_000);
  const { page, userName } = adminRolePage;
  const escalationChainName = generateRandomValue();
  const integrationName = generateRandomValue();

  await goToOnCallPage(page, 'settings');
  await page.getByText('Env Variables').click();
  await page.waitForTimeout(5_000);

  await verifyUserPhoneNumber(page);

  await page.waitForTimeout(5_000);
  await configureUserNotificationSettings(page, 'SMS');

  await createEscalationChain(page, escalationChainName, EscalationStep.NotifyUsers, userName);
  await createIntegrationAndSendDemoAlert(page, integrationName, escalationChainName);

  // wait for the SMS alert notification to arrive
  const smsAlertNotification = await waitForSms();

  expect(smsAlertNotification).toContain('OnCall');
  expect(smsAlertNotification).toContain('alert');
});
