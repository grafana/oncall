import { Locator, expect, test } from '../fixtures';
import { createEscalationChain, EscalationStep, selectEscalationStepValue } from '../utils/escalationChain';
import { generateRandomValue, selectDropdownValue } from '../utils/forms';

test('escalation policy does not go back to "Default" after adding users to notify', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;
  const escalationChainName = generateRandomValue();

  // create important escalation step
  await createEscalationChain(page, escalationChainName, EscalationStep.NotifyUsers, null, true);
  // add user to notify
  await selectEscalationStepValue(page, EscalationStep.NotifyUsers, userName);

  // reload and check if important is still selected
  await page.reload();
  await page.waitForLoadState('networkidle');

  expect(await page.locator('text=Important').isVisible()).toBe(true);
});

test.only('from_time and to_time for "Continue escalation if current UTC time is in" escalation step type can be properly updated', async ({
  adminRolePage,
}) => {
  const FROM_TIME = '13:31';
  const TO_TIME = '13:32';

  const { page } = adminRolePage;
  const escalationChainName = generateRandomValue();

  // create escalation step w/ Continue escalation if current UTC time is in policy step
  await createEscalationChain(page, escalationChainName, EscalationStep.ContinueEscalationIfCurrentUTCTimeIsIn);

  const _getFromTimeInput = () => page.locator('[data-testid="time-range-from"] > input');
  const _getToTimeInput = () => page.locator('[data-testid="time-range-to"] > input');

  const clickAndInputValue = async (locator: Locator, value: string) => {
    await locator.click();
    await locator.pressSequentially(value);
  };

  // update from and to time values
  await clickAndInputValue(_getFromTimeInput(), FROM_TIME);
  await clickAndInputValue(_getToTimeInput(), TO_TIME);

  // reload and check that these values have been persisted
  await page.reload();
  await page.waitForLoadState('networkidle');

  expect(await _getFromTimeInput().textContent()).toBe(FROM_TIME);
  expect(await _getToTimeInput().textContent()).toBe(FROM_TIME);
});
