import { test, expect } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test('User can create, copy and revoke ical link', async ({ adminRolePage: { page } }) => {
  await goToOnCallPage(page, 'users/me');
  await page.getByTestId('create-ical-link').click();
  await page.getByTestId('copy-ical-link').click();
  await expect(page.getByText('iCal link is copied')).toBeVisible();
  await page.reload();

  await page.getByTestId('revoke-ical-link').click();
  await page.getByLabel('Are you sure you want to revoke iCal link').getByRole('button', { name: 'Revoke' }).click();
  await page.reload();

  await expect(page.getByTestId('create-ical-link')).toBeVisible();
});
