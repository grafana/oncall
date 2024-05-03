import moment from 'moment-timezone';

import { convertRelativeToAbsoluteDate, getValueForDateRangeFilterType } from './datetime';

const DATE_FORMAT = 'YYYY-MM-DDTHH:mm:ss';

describe('convertRelativeToAbsoluteDate', () => {
  it(`should convert relative date to absolute dates pair separated by an underscore`, () => {
    const result = convertRelativeToAbsoluteDate('now-24h_now');

    const now = moment().utc();
    const nowString = now.format(DATE_FORMAT);
    const dayBefore = now.subtract('1', 'day');
    const dayBeforeString = dayBefore.format(DATE_FORMAT);

    expect(result).toBe(`${dayBeforeString}_${nowString}`);
  });
});

describe('getValueForDateRangeFilterType', () => {
  it(`should convert relative date range string to a suitable format for TimeRangeInput component`, () => {
    const input = 'now-2d_now';
    const [from, to] = input.split('_');
    const result = getValueForDateRangeFilterType(input);

    const now = moment();
    const twoDaysBefore = now.subtract('2', 'day');

    expect(result.from.diff(twoDaysBefore, 'seconds') < 1).toBe(true);
    expect(result.raw.from).toBe(from);
    expect(result.from.diff(twoDaysBefore, 'seconds') < 1).toBe(true);
    expect(result.raw.to).toBe(to);
  });

  it(`should convert absolute date range string to a suitable format for TimeRangeInput component`, () => {
    const input = '2024-03-31T23:00:00_2024-04-15T22:59:59';
    const [from, to] = input.split('_');
    const result = getValueForDateRangeFilterType(input);

    const fromMoment = moment(from + 'Z');
    const toMoment = moment(to + 'Z');

    expect(result.from.diff(fromMoment, 'seconds') < 1).toBe(true);
    expect(result.raw.from).toBe(from);
    expect(result.from.diff(toMoment, 'seconds') < 1).toBe(true);
    expect(result.raw.to).toBe(to);
  });
});
