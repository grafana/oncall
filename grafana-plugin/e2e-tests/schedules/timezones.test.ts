import { expect } from '@playwright/test';
import dayjs from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import utc from 'dayjs/plugin/utc';

import { test } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { setTimezoneInProfile } from '../utils/grafanaProfile';
import { createOnCallScheduleWithRotation } from '../utils/schedule';

dayjs.extend(utc);
dayjs.extend(isoWeek);

const MOSCOW_TIMEZONE = 'Europe/Moscow';

test.use({ timezoneId: MOSCOW_TIMEZONE }); // GMT+3 the whole year
const currentUtcTimeHour = dayjs().utc().format('HH');
const currentUtcDate = dayjs().utc().format('DD MMM');
const currentMoscowTimeHour = dayjs().utcOffset(180).format('HH');
const currentMoscowDate = dayjs().utcOffset(180).format('DD MMM');

test('dates in schedule are correct according to selected current timezone', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  await setTimezoneInProfile(page, MOSCOW_TIMEZONE);

  const onCallScheduleName = generateRandomValue();
  await createOnCallScheduleWithRotation(page, onCallScheduleName, userName);

  // Current timezone is selected by default to currently logged in user timezone
  await expect(page.getByTestId('timezone-select')).toHaveText('GMT+3');

  // Change timezone to GMT
  await page.getByTestId('timezone-select').getByRole('img').click();
  await page.getByText('GMT', { exact: true }).click();

  // Selected timezone and local time is correctly displayed
  await expect(page.getByText(`Current timezone: GMT, local time: ${currentUtcTimeHour}`)).toBeVisible();

  // // User avatar tooltip shows correct time and timezones
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
