import { Locator, expect, test } from '../fixtures';
import { createEscalationChain, EscalationStep } from '../utils/escalationChain';
import { generateRandomValue } from '../utils/forms';

test('escalation policy does not go back to "Default" after adding users to notify', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;
  const escalationChainName = generateRandomValue();

  // create important escalation step + add user to notif
  await createEscalationChain(page, escalationChainName, EscalationStep.NotifyUsers, userName, true);

  // reload and check if important is still selected
  await page.reload();
  await expect(page.getByText('Important')).toBeVisible();
});

test('from_time and to_time for "Continue escalation if current UTC time is in range" escalation step type can be properly updated', async ({
  adminRolePage,
}) => {
  const FROM_TIME = '10:30';
  const TO_TIME = '10:35';

  const { page } = adminRolePage;
  const escalationChainName = generateRandomValue();

  // create escalation step w/ Continue escalation if current UTC time is in policy step
  await createEscalationChain(page, escalationChainName, EscalationStep.ContinueEscalationIfCurrentUTCTimeIsIn);

  const _getFromTimeInput = () => page.locator('[data-testid="time-range-from"] >> input');
  const _getToTimeInput = () => page.locator('[data-testid="time-range-to"] >> input');

  const clickAndInputValue = async (locator: Locator, value: string) => {
    // the first click opens up dropdown which contains the time selector scrollable lists
    await locator.click();

    // the second click focuses on the input where we can actually type the time instead, much easier
    const actualInput = page.locator('input[class="rc-time-picker-panel-input"]');
    await actualInput.click();
    await actualInput.selectText();
    await actualInput.fill(value);

    // click anywhere to close the dropdown
    await page.click('body');
  };

  // update from and to time values
  await clickAndInputValue(_getFromTimeInput(), FROM_TIME);
  await clickAndInputValue(_getToTimeInput(), TO_TIME);

  // reload and check that these values have been persisted
  await page.reload();
  await page.waitForLoadState('networkidle');

  await expect(_getFromTimeInput()).toHaveValue(FROM_TIME);
  await expect(_getToTimeInput()).toHaveValue(TO_TIME);
});
