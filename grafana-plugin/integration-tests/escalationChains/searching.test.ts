import { test, expect, Page } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createEscalationChain } from '../utils/escalationChain';

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

// TODO: add tests for the new filtering. Commented out as this search doesn't exist anymore
test.skip('searching allows case-insensitive partial matches', async ({ adminRolePage }) => {
  const { page } = adminRolePage;

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
