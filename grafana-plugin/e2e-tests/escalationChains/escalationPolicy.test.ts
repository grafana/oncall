import {expect, test} from "../fixtures";
import {createEscalationChain, EscalationStep, selectEscalationStepValue} from "../utils/escalationChain";
import {generateRandomValue} from "../utils/forms";

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
