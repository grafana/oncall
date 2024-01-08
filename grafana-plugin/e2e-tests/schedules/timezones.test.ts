import { expect } from '@playwright/test';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';

import { test } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { createOnCallSchedule } from '../utils/schedule';

dayjs.extend(utc);

test.use({ timezoneId: 'Europe/Moscow' }); // GMT+3 the whole year
const currentUtcTime = dayjs().utc().format('HH:mm');
const currentUtcDate = dayjs().utc().format('DD MMM');
const currentMoscowTime = dayjs().utcOffset(180).format('HH:mm');
const currentMoscowDate = dayjs().utcOffset(180).format('DD MMM');

test('default dates in override creation modal are correct', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName);

  // Current timezone is selected by default to currently logged in user timezone
  await expect(page.getByTestId('timezone-select')).toHaveText('GMT+3');

  // Change timezone to GMT
  await page.getByTestId('timezone-select').getByRole('img').click();
  await page.getByText('GMT', { exact: true }).click();

  // Selected timezone and local time is correctly displayed
  await expect(page.getByText(`Current timezone: GMT, local time: ${currentUtcTime}`)).toBeVisible();

  // // User avatar tooltip shows correct time and timezones
  await page.getByTestId('user-avatar-in-schedule').hover();
  await expect(page.getByTestId('schedule-user-details_your-current-time')).toHaveText(/GMT\+3/);
  await expect(page.getByTestId('schedule-user-details_your-current-time')).toHaveText(new RegExp(currentMoscowTime));
  await expect(page.getByTestId('schedule-user-details_user-local-time')).toHaveText(/GMT\+3/);
  await expect(page.getByTestId('schedule-user-details_user-local-time')).toHaveText(new RegExp(currentMoscowTime));

  // Schedule slot shows correct times and timezones
  await page.getByTestId('schedule-slot').first().hover();
  await expect(page.getByText(`User's local time${currentMoscowDate}, ${currentMoscowTime}(GMT+3)`)).toBeVisible();
  await expect(page.getByText(`Current timezone${currentUtcDate}, ${currentUtcTime}(GMT)`)).toBeVisible();

  // Rotation form has correct start date and current timezone information
  await clickButton({ page, buttonText: 'Add rotation' });
  await page.getByText('Layer 1 rotation').click();
  await expect(page.getByTestId('rotation-form').getByText('Current timezone: GMT')).toBeVisible();
  await expect(page.getByTestId('rotation-form').getByPlaceholder('Date')).toHaveValue(
    dayjs().utcOffset(0).format('MM/DD/YYYY')
  );
  await expect(page.getByTestId('rotation-form').getByTestId('date-time-picker').getByRole('textbox')).toHaveValue(
    '00:00'
  );
});
