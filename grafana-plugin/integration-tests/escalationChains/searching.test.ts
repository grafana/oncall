import { test, expect, Page } from '@playwright/test';
import { configureOnCallPlugin } from '../utils/configurePlugin';
import { generateRandomValue } from '../utils/forms';
import { createEscalationChain } from '../utils/escalationChain';

test.beforeEach(async ({ page }) => {
  await configureOnCallPlugin(page);
});

const assertEscalationChainSearchWorks = async (
  page: Page,
  searchTerm: string,
  escalationChainFullName: string
): Promise<void> => {
  await page.getByTestId('escalation-chain-search-input').fill(searchTerm);

  // wait for the API call(s) to finish
  await page.waitForLoadState('networkidle');

  await expect(page.getByTestId('escalation-chains-list')).toHaveText(escalationChainFullName);
};

test('searching allows case-insensitive partial matches', async ({ page }) => {
  const escalationChainName = `${generateRandomValue()} ${generateRandomValue()}`;
  const [firstHalf, secondHalf] = escalationChainName.split(' ');

  await createEscalationChain(page, escalationChainName);

  await assertEscalationChainSearchWorks(page, firstHalf, escalationChainName);
  await assertEscalationChainSearchWorks(page, firstHalf.toUpperCase(), escalationChainName);
  await assertEscalationChainSearchWorks(page, firstHalf.toLowerCase(), escalationChainName);

  await assertEscalationChainSearchWorks(page, secondHalf, escalationChainName);
  await assertEscalationChainSearchWorks(page, secondHalf.toUpperCase(), escalationChainName);
  await assertEscalationChainSearchWorks(page, secondHalf.toLowerCase(), escalationChainName);
});
