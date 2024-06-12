import dayjs from 'dayjs';

import { getTotalDaysToDisplay } from './schedule.helpers';
import { ScheduleView } from './schedule.types';

describe('getTotalDaysToDisplay', () => {
  const date = dayjs('2024-05-27T00:00:00Z').utc();

  it(`should return correct total days to display in final schedule  if scheduleView=Week`, () => {
    const result = getTotalDaysToDisplay(ScheduleView.OneWeek, date);

    expect(result).toBe(7);
  });

  it(`should return correcnt total days to display in final schedule  if scheduleView=2 weeks`, () => {
    const result = getTotalDaysToDisplay(ScheduleView.TwoWeeks, date);

    expect(result).toBe(14);
  });

  it(`should return correcnt total days to display in final schedule  if scheduleView=Month`, () => {
    const result = getTotalDaysToDisplay(ScheduleView.OneMonth, date);

    expect(result).toBe(35);
  });
});
