import { scheduleViewToDaysInOneRow } from 'models/schedule/schedule.helpers';
import { ScheduleView } from 'models/schedule/schedule.types';
import { HTML_ID } from 'utils/DOM';

import { expect, test } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createOnCallScheduleWithRotation } from '../utils/schedule';

test('schedule view (week/2 weeks/month) toggler works', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallScheduleWithRotation(page, onCallScheduleName, userName);

  // ScheduleView.OneWeek is selected by default
  expect(await page.getByLabel(ScheduleView.OneWeek, { exact: true }).isChecked()).toBe(true);

  const count = await page.locator(`#${HTML_ID.SCHEDULE_FINAL} .TEST_weekday`).count();
  expect(count).toStrictEqual(scheduleViewToDaysInOneRow[ScheduleView.OneWeek]);

  /* 
    for some reason loop isn't working
  [ScheduleView.TwoWeeks, ScheduleView.OneMonth, ScheduleView.OneWeek].forEach(async (scheduleView) => {
    await page.locator('.scheduleViewToogler').getByLabel(scheduleView, { exact: true }).click();
    expect(await page.getByLabel(scheduleView, { exact: true }).isChecked()).toBe(true);
  }); */

  await page.locator('.scheduleViewToogler').getByLabel(ScheduleView.TwoWeeks, { exact: true }).click();
  expect(await page.getByLabel(ScheduleView.TwoWeeks, { exact: true }).isChecked()).toBe(true);
  expect(await page.locator(`#${HTML_ID.SCHEDULE_FINAL} .TEST_weekday`).count()).toStrictEqual(
    scheduleViewToDaysInOneRow[ScheduleView.TwoWeeks]
  );

  await page.locator('.scheduleViewToogler').getByLabel(ScheduleView.OneMonth, { exact: true }).click();
  expect(await page.getByLabel(ScheduleView.OneMonth, { exact: true }).isChecked()).toBe(true);
  expect(await page.locator(`#${HTML_ID.SCHEDULE_FINAL} .TEST_weekday`).count()).toBeGreaterThanOrEqual(28);
});
