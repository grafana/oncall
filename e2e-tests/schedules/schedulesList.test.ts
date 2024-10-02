import { expect, test } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';
import { createOnCallSchedule } from '../utils/schedule';

test('schedule calendar and list of schedules is correctly displayed', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName);

  await goToOnCallPage(page, 'schedules');
  await page.waitForLoadState('networkidle');

  // schedule slots are present in calendar
  const nbOfSlotsInCalendar = await page.getByTestId('schedule-slot').count();
  await expect(nbOfSlotsInCalendar).toBeGreaterThan(0);

  // filter table to show only created schedule
  await page
    .locator('div')
    .filter({ hasText: /^Search or filter results\.\.\.$/ })
    .nth(1)
    .click();
  await page.keyboard.insertText(onCallScheduleName);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2000);

  // schedules table displays details created schedule
  const schedulesTableLastRow = page.getByTestId('schedules-table').getByRole('row').last();
  await expect(schedulesTableLastRow.getByRole('cell', { name: onCallScheduleName })).toBeVisible();
  await expect(schedulesTableLastRow.getByRole('cell', { name: 'Web' })).toBeVisible();
  await expect(schedulesTableLastRow.getByRole('cell', { name: userName })).toBeVisible();
  await expect(schedulesTableLastRow.getByRole('cell', { name: 'No team' })).toBeVisible();
});
