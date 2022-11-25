import { Page } from '@playwright/test';

import { clickButton, fillInInput } from './forms';
import { goToOnCallPageByClickingOnTab } from './navigation';

export const createEscalationChain = async (page: Page, escalationChainName: string): Promise<void> => {
  // go to the escalation chains page
  await goToOnCallPageByClickingOnTab(page, 'Escalation Chains');

  // open the create escalation chain modal
  (await page.waitForSelector('text=New Escalation Chain')).click();

  // fill in the name input
  await fillInInput(page, 'div[class*="EscalationChainForm"] input', escalationChainName);

  // submit the form and wait for it to be created
  await clickButton(page, 'Create');
  await page.waitForSelector(`text=${escalationChainName}`);
};
