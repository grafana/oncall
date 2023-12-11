import dayjs from 'dayjs';

import { forceCurrentDateToPreventDSTIssues } from './RotationForm.helpers';

describe('forceCurrentDateToPreventDSTIssues()', () => {
  it('should apply DST from current date if it happened between input date and today', () => {
    const todayMock = dayjs('2023-12-01T03:00:00.000Z').tz('America/Toronto');
    const originalDate = dayjs('2023-10-01T03:00:00.000Z').tz('America/Toronto');

    // prove that DST happened between input date and today
    expect(originalDate.hour()).not.toBe(todayMock.hour());

    const result = forceCurrentDateToPreventDSTIssues(originalDate, todayMock.toDate());
    expect(new Date(result).getHours()).toBe(todayMock.toDate().getHours());
  });

  it('should return the same time if DST did not happen', () => {
    const todayMock = dayjs('2023-12-03T17:00:00.000').tz('America/Toronto');
    const originalDate = dayjs('2023-12-01T17:00:00.000').tz('America/Toronto');

    // prove that DST happened between input date and today
    expect(originalDate.hour()).toBe(todayMock.hour());

    const result = forceCurrentDateToPreventDSTIssues(originalDate, todayMock.toDate());
    expect(new Date(result).getHours()).toBe(todayMock.toDate().getHours());
  });
});
