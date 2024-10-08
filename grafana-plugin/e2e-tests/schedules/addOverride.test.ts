import dayjs from 'dayjs';

import { test, expect, Locator } from '../fixtures';
import { isGrafanaVersionGreaterThan, MOSCOW_TIMEZONE } from '../utils/constants';
import { clickButton, generateRandomValue } from '../utils/forms';
import { setTimezoneInProfile } from '../utils/grafanaProfile';
import { createOnCallSchedule, getOverrideFormDateInputs } from '../utils/schedule';

test('Default dates in override creation modal are set to today', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName);

  await page.clock.setFixedTime(new Date().setHours(12, 0, 0, 0));
  await page.getByTestId('timezone-select').locator('svg').click();
  await (isGrafanaVersionGreaterThan('11.0.0') ? page.getByRole('option') : page.getByLabel('Select option'))
    .getByText(/^GMT$/)
    .click();

  await clickButton({ page, buttonText: 'Add override' });

  const overrideFormDateInputs = await getOverrideFormDateInputs(page);

  const expectedStart = dayjs().startOf('day'); // start of today
  const expectedEnd = expectedStart.add(1, 'day'); // end of today

  expect(overrideFormDateInputs.start.isSame(expectedStart)).toBe(true);
  expect(overrideFormDateInputs.end.isSame(expectedEnd)).toBe(true);
});

test('Fills in override time and reacts to timezone change', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  await setTimezoneInProfile(page, MOSCOW_TIMEZONE); // UTC+3

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName, false);

  await clickButton({ page, buttonText: 'Add override' });

  const overrideStartEl = page.getByTestId('override-start');
  await changeDatePickerTime(overrideStartEl, '02');
  await expect(overrideStartEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('02:00');

  const overrideEndEl = page.getByTestId('override-end');
  await changeDatePickerTime(overrideEndEl, '12');
  await expect(overrideEndEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('12:00');

  await page.getByRole('dialog').click(); // clear focus

  await page.getByTestId('timezone-select').locator('svg').click();
  await page.getByText('GMT', { exact: true }).click();

  // expect times to go back by -3
  await expect(overrideStartEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('23:00');
  await expect(overrideEndEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('09:00');

  async function changeDatePickerTime(element: Locator, value: string) {
    await element.getByTestId('date-time-picker').getByRole('textbox').click();

    // set minutes to {value}
    await page.getByRole('button', { name: value }).first().click();

    // Old way
    // await page.locator('.rc-time-picker-panel').getByRole('button', { name: value }).first().click();
    // set seconds to 00
    await page.getByRole('button', { name: '00' }).nth(1).click();
  }
});
