import { expect } from '@playwright/test';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';

import { test } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createOnCallSchedule } from '../utils/schedule';

dayjs.extend(utc);

test.use({ timezoneId: 'Europe/Moscow' }); // GMT+3 the whole year

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
  const currentTime = dayjs().utc().format('HH:mm');
  await expect(page.getByText(`Current timezone: GMT, local time: ${currentTime}`)).toBeVisible();
});
