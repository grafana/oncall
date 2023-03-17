import { Page } from '@playwright/test';

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
  escalationStep: EscalationStep | null,
  escalationStepValue: string | null
): Promise<void> => {
  // go to the escalation chains page
  await goToOnCallPage(page, 'escalations');

  // open the create escalation chain modal
  (await page.waitForSelector('text=New Escalation Chain')).click();

  // fill in the name input
  await fillInInput(page, 'div[class*="EscalationChainForm"] input', escalationChainName);

  // submit the form and wait for it to be created
  await clickButton({ page, buttonText: 'Create' });
  await page.waitForSelector(`text=${escalationChainName}`);

  if (!escalationStep) {
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
