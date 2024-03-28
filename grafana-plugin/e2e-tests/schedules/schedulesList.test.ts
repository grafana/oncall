import { expect, test } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';
import { createOnCallScheduleWithRotation } from '../utils/schedule';

test('schedule calendar and list of schedules is correctly displayed', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallScheduleWithRotation(page, onCallScheduleName, userName);

  await goToOnCallPage(page, 'schedules');

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
  const schedulesTable = page.getByTestId('schedules-table');
  await expect(schedulesTable.getByRole('cell', { name: onCallScheduleName })).toBeVisible();
  await expect(schedulesTable.getByRole('cell', { name: 'Web' })).toBeVisible();
  await expect(schedulesTable.getByRole('cell', { name: userName })).toBeVisible();
  await expect(schedulesTable.getByRole('cell', { name: 'No team' })).toBeVisible();
});
