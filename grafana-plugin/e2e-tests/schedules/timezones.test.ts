import { expect } from '@playwright/test';
import dayjs from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import utc from 'dayjs/plugin/utc';

import { test } from '../fixtures';
import { MOSCOW_TIMEZONE } from '../utils/constants';
import { clickButton, generateRandomValue } from '../utils/forms';
import { setTimezoneInProfile } from '../utils/grafanaProfile';
import { createOnCallSchedule } from '../utils/schedule';

dayjs.extend(utc);
dayjs.extend(isoWeek);

test.use({ timezoneId: MOSCOW_TIMEZONE }); // GMT+3 the whole year

// The test is skipped because using Clock API breaks several other tests that run in parallel
test.skip('dates in schedule are correct according to selected current timezone', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  /**
   * Always set a fixed time of today's date but at 12:00:00 (noon)
   *
   * This solves the issue here https://github.com/grafana/oncall/issues/4991
   * where we would occasionally see this test flake if it started and finished at a different hour
   *
   * See playwright docs for more details
   * https://playwright.dev/docs/clock
   */
  const fixedDateAtNoon = new Date().setHours(12, 0, 0, 0);
  await page.clock.setFixedTime(fixedDateAtNoon);

  /**
   * Use the fixed time for all time calculations + use the same fixed time for both UTC and Moscow time
   */
  const fixedDayjs = dayjs(fixedDateAtNoon).utc();

  // Calculate time and date based on the fixed time
  const currentUtcTimeHour = fixedDayjs.format('HH'); // 12 in this case
  const currentUtcDate = fixedDayjs.format('DD MMM');
  const currentMoscowTimeHour = fixedDayjs.utcOffset(180).format('HH'); // Adjust for Moscow time (UTC+3)
  const currentMoscowDate = fixedDayjs.utcOffset(180).format('DD MMM');

  await setTimezoneInProfile(page, MOSCOW_TIMEZONE);

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName);

  // Current timezone is selected by default to currently logged in user timezone
  await expect(page.getByTestId('timezone-select')).toHaveText('GMT+3');

  // Change timezone to GMT
  await page.getByTestId('timezone-select').locator('div').filter({ hasText: 'GMT+' }).nth(1).click();
  await page.getByText('GMT', { exact: true }).click();

  // Selected timezone and local time is correctly displayed
  await expect(page.getByText(`Current timezone: GMT, local time: ${currentUtcTimeHour}`)).toBeVisible();

  // User avatar tooltip shows correct time and timezones
  await page.getByTestId('user-avatar-in-schedule').hover();
  await expect(page.getByTestId('schedule-user-details_your-current-time')).toHaveText(/GMT\+3/);
  await expect(page.getByTestId('schedule-user-details_your-current-time')).toHaveText(
    new RegExp(currentMoscowTimeHour)
  );
  await expect(page.getByTestId('schedule-user-details_user-local-time')).toHaveText(new RegExp(MOSCOW_TIMEZONE));
  await expect(page.getByTestId('schedule-user-details_user-local-time')).toHaveText(new RegExp(currentMoscowTimeHour));

  // Schedule slot shows correct times and timezones
  await page.getByTestId('schedule-slot').first().hover();
  await page.waitForTimeout(500);
  await expect(page.getByTestId('schedule-slot-user-local-time')).toHaveText(
    new RegExp(`${currentMoscowDate}, ${currentMoscowTimeHour}`)
  );
  await expect(page.getByTestId('schedule-slot-user-local-time')).toHaveText(new RegExp(MOSCOW_TIMEZONE));
  await expect(page.getByTestId('schedule-slot-current-timezone')).toHaveText(
    new RegExp(`${currentUtcDate}, ${currentUtcTimeHour}`)
  );
  await expect(page.getByTestId('schedule-slot-current-timezone')).toHaveText(/\(GMT\)/);

  const firstDayOfTheWeek = dayjs().utc().startOf('isoWeek');

  // Rotation form has correct start date and current timezone information
  await clickButton({ page, buttonText: 'Add rotation' });
  await page.getByText('Layer 1 rotation').click();
  await expect(page.getByTestId('rotation-form').getByText('Current timezone: GMT')).toBeVisible();
  await expect(page.getByTestId('rotation-form').getByPlaceholder('Date')).toHaveValue(
    firstDayOfTheWeek.format('MM/DD/YYYY')
  );
  await expect(page.getByTestId('rotation-form').getByTestId('date-time-picker').getByRole('textbox')).toHaveValue(
    '00:00'
  );
});
