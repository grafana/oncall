import { scheduleViewToDaysInOneRow } from 'models/schedule/schedule.helpers';
import { ScheduleView } from 'models/schedule/schedule.types';
import { HTML_ID } from 'utils/DOM';

import { expect, test } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createOnCallScheduleWithRotation } from '../utils/schedule';

test.skip('schedule view (week/2 weeks/month) toggler works', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallScheduleWithRotation(page, onCallScheduleName, userName);

  // ScheduleView.OneWeek is selected by default
  expect(await page.getByLabel(ScheduleView.OneWeek, { exact: true }).isChecked()).toBe(true);

  expect(await page.locator(`#${HTML_ID.SCHEDULE_FINAL} .TEST_weekday`).count()).toStrictEqual(
    scheduleViewToDaysInOneRow[ScheduleView.OneWeek]
  );

  await page.getByLabel(ScheduleView.TwoWeeks, { exact: true }).click();
  expect(await page.getByLabel(ScheduleView.TwoWeeks, { exact: true }).isChecked()).toBe(true);
  expect(await page.locator(`#${HTML_ID.SCHEDULE_FINAL} .TEST_weekday`).count()).toStrictEqual(
    scheduleViewToDaysInOneRow[ScheduleView.TwoWeeks]
  );

  await page.getByLabel(ScheduleView.OneMonth, { exact: true }).click();
  expect(await page.getByLabel(ScheduleView.OneMonth, { exact: true }).isChecked()).toBe(true);
  expect(await page.locator(`#${HTML_ID.SCHEDULE_FINAL} .TEST_weekday`).count()).toBeGreaterThanOrEqual(28);
});
