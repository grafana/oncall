import dayjs from 'dayjs';

import { ScheduleView } from 'models/schedule/schedule.types';

import { getNewCalendarStartDate } from './Schedule.helpers';

describe('getNewCalendarStartDate', () => {
  const date = dayjs('2024-05-27T00:00:00Z').utc();

  it(`should return correct next calendar date if scheduleView=Week`, () => {
    const result = getNewCalendarStartDate(date, ScheduleView.OneWeek, 'next');

    expect(result.toString()).toBe('Mon, 03 Jun 2024 00:00:00 GMT');
  });

  it(`should return correct previous calendar date if scheduleView=Week`, () => {
    const result = getNewCalendarStartDate(date, ScheduleView.OneWeek, 'prev');

    expect(result.toString()).toBe('Mon, 20 May 2024 00:00:00 GMT');
  });

  it(`should return correct next calendar date if scheduleView=2 weeks`, () => {
    const result = getNewCalendarStartDate(date, ScheduleView.TwoWeeks, 'next');

    expect(result.toString()).toBe('Mon, 10 Jun 2024 00:00:00 GMT');
  });

  it(`should return correct previous calendar date if scheduleView=2 weeks`, () => {
    const result = getNewCalendarStartDate(date, ScheduleView.TwoWeeks, 'prev');

    expect(result.toString()).toBe('Mon, 13 May 2024 00:00:00 GMT');
  });

  it(`should return correct next calendar date if scheduleView=Month`, () => {
    const result = getNewCalendarStartDate(date, ScheduleView.OneMonth, 'next');

    expect(result.toString()).toBe('Mon, 01 Jul 2024 00:00:00 GMT');
  });

  it(`should return correct previous calendar date if scheduleView=Month`, () => {
    const result = getNewCalendarStartDate(date, ScheduleView.OneMonth, 'prev');

    expect(result.toString()).toBe('Mon, 29 Apr 2024 00:00:00 GMT');
  });
});
