import { test, expect } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test(`tab query param is used to show proper page tab`, async ({ adminRolePage }) => {
  const { page } = adminRolePage;
  goToOnCallPage(page, `settings`, { tab: 'ChatOps' });

  const tab = page.getByRole('tab', { name: 'Chat Ops' });
  const isSelected = await tab.getAttribute('aria-selected');

  expect(isSelected).toBe('true');
});
