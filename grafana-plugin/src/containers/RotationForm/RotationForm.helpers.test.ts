import dayjs from 'dayjs';

import { forceCurrentDateToPreventDSTIssues } from './RotationForm.helpers';

describe('forceCurrentDateToPreventDSTIssues()', () => {
  it('should apply DST from current date if it happened between input date and today', () => {
    const todayMock = dayjs('2023-12-01T03:00:00.000Z').tz('Europe/Berlin');
    const originalDate = dayjs('2023-10-01T03:00:00.000Z').tz('Europe/Berlin');

    // prove that DST happened between input date and today
    expect(originalDate.hour()).not.toBe(todayMock.hour());

    const result = forceCurrentDateToPreventDSTIssues(originalDate, todayMock);
    expect(result.getHours()).toBe(todayMock.hour());
  });

  it('should return the same time if DST did not happen', () => {
    const todayMock = dayjs('2023-12-01T03:00:00.000Z').tz('Europe/Berlin');
    const originalDate = dayjs('2023-12-01T03:00:00.000Z').tz('Europe/Berlin');

    // prove that DST didn't happen between input date and today
    expect(originalDate.hour()).toBe(todayMock.hour());

    const result = forceCurrentDateToPreventDSTIssues(originalDate, todayMock);
    expect(result.getHours()).toBe(todayMock.hour());
  });
});
