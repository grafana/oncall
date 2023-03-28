import { expect, Page } from '@playwright/test';

import { clickButton, fillInInput, selectDropdownValue } from './forms';
import { goToOnCallPage } from './navigation';

export enum EscalationStep {
  NotifyUsers = 'Notify users',
  NotifyUsersFromOnCallSchedule = 'Notify users from on-call schedule',
}

const escalationStepValuePlaceholder: Record<EscalationStep, string> = {
  [EscalationStep.NotifyUsers]: 'Select User',
  [EscalationStep.NotifyUsersFromOnCallSchedule]: 'Select Schedule',
};

export const createEscalationChain = async (
  page: Page,
  escalationChainName: string,
  escalationStep?: EscalationStep,
  escalationStepValue?: string
): Promise<void> => {
  // go to the escalation chains page
  await goToOnCallPage(page, 'escalations');

  /**
   * wait for Esclation Chains page to fully load. this is because this can change which "New Escalation Chain"
   * button is present
   * ie. the one on the left hand side in the list vs the one in the center when no escalation chains exist
   */
  await page.getByTestId('page-title').locator('text=Escalation Chains').waitFor({ state: 'visible' });
  await page.locator('text=Loading...').waitFor({ state: 'detached' });

  // open the create escalation chain modal
  (await page.waitForSelector('text=New Escalation Chain')).click();

  // fill in the name input
  await fillInInput(page, 'div[data-testid="create-escalation-chain-name-input-modal"] >> input', escalationChainName);

  // submit the form and wait for it to be created
  await clickButton({ page, buttonText: 'Create' });
  await expect(page.getByTestId('escalation-chain-name')).toHaveText(escalationChainName);

  if (!escalationStep || !escalationStepValue) {
    return;
  }

  // add an escalation step
  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Add escalation step...',
    value: escalationStep,
  });

  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: escalationStepValuePlaceholder[escalationStep],
    value: escalationStepValue,
  });
};
