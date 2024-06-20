import { test, expect, Locator } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { createOnCallSchedule } from '../utils/schedule';

test('Fills in Rotation time and  reacts to timezone change', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName, false);

  await clickButton({ page, buttonText: 'Add rotation' });
  // enable Rotation End
  await page.getByTestId('rotation-end').getByLabel('Toggle switch').click();

  const startEl = page.getByTestId('rotation-start');
  await changeDatePickerTime(startEl, '02');
  await expect(startEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('02:00');

  const endEl = page.getByTestId('rotation-end');
  await changeDatePickerTime(endEl, '12');
  await expect(endEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('12:00');

  await page.getByRole('dialog').click(); // clear focus

  await page.getByTestId('timezone-select').locator('svg').click();
  await page.getByTestId('timezone-select').getByText('GMT', { exact: true }).click();

  // expect times to go back by -3
  await expect(startEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('23:00');
  await expect(endEl.getByTestId('date-time-picker').getByRole('textbox')).toHaveValue('09:00');

  async function changeDatePickerTime(element: Locator, value: string) {
    await element.getByRole('img').click();
    // set minutes to {value}
    await page.locator('.rc-time-picker-panel').getByRole('button', { name: value }).first().click();
    // set seconds to 00
    await page.getByRole('button', { name: '00' }).nth(1).click();
  }
});
