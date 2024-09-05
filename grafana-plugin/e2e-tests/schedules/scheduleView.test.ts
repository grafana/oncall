import { HTML_ID } from 'helpers/DOM';

import { scheduleViewToDaysInOneRow } from 'models/schedule/schedule.helpers';
import { ScheduleView } from 'models/schedule/schedule.types';

import { expect, Page, test } from '../fixtures';
import { isGrafanaVersionLowerThan } from '../utils/constants';
import { generateRandomValue } from '../utils/forms';
import { createOnCallSchedule } from '../utils/schedule';

const getNumberOfWeekdaysInFinalSchedule = async (page: Page) =>
  await page.locator(`#${HTML_ID.SCHEDULE_FINAL}`).getByTestId('schedule-weekday').count();
const getScheduleViewRadioButtonLocator = (page: Page, view: ScheduleView) =>
  page
    .getByTestId('schedule-view-picker')
    [isGrafanaVersionLowerThan('10.2.0') ? 'getByText' : 'getByLabel'](view, { exact: true });

test('schedule view (week/2 weeks/month) toggler works', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName);

  // ScheduleView.OneWeek is selected by default
  expect(await getScheduleViewRadioButtonLocator(page, ScheduleView.OneWeek).isChecked()).toBe(true);

  expect(await getNumberOfWeekdaysInFinalSchedule(page)).toStrictEqual(
    scheduleViewToDaysInOneRow[ScheduleView.OneWeek]
  );

  await getScheduleViewRadioButtonLocator(page, ScheduleView.TwoWeeks).click();
  await page.waitForTimeout(1000);
  expect(await getScheduleViewRadioButtonLocator(page, ScheduleView.TwoWeeks).isChecked()).toBe(true);
  expect(await getNumberOfWeekdaysInFinalSchedule(page)).toStrictEqual(
    scheduleViewToDaysInOneRow[ScheduleView.TwoWeeks]
  );

  await getScheduleViewRadioButtonLocator(page, ScheduleView.OneMonth).click();
  await page.waitForTimeout(1000);
  expect(await getScheduleViewRadioButtonLocator(page, ScheduleView.OneMonth).isChecked()).toBe(true);
  expect(await getNumberOfWeekdaysInFinalSchedule(page)).toBeGreaterThanOrEqual(28);
});
