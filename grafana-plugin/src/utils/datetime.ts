import { TimeOption, TimeRange, rangeUtil } from '@grafana/data';
import { TimeZone } from '@grafana/schema';
import moment from 'moment-timezone';

export const mapOptionToTimeRange = (option: TimeOption, timeZone?: TimeZone): TimeRange => {
  return rangeUtil.convertRawToRange({ from: option.from, to: option.to }, timeZone);
};

export function convertRelativeToAbsoluteDate(dateRangeString: string) {
  if (!dateRangeString) {
    return undefined;
  }

  const [from, to] = dateRangeString?.split('_') || [];
  if (rangeUtil.isRelativeTimeRange({ from, to })) {
    const { from: startDate, to: endDate } = rangeUtil.convertRawToRange({ from, to });

    return `${startDate.utc().format('YYYY-MM-DDTHH:mm:ss')}_${endDate.utc().format('YYYY-MM-DDTHH:mm:ss')}`;
  }
  return dateRangeString;
}

export const getValueForDateRangeFilterType = (rawInput: string) => {
  let value = { from: undefined, to: undefined, raw: { from: '', to: '' } };
  if (rawInput) {
    const [fromString, toString] = rawInput.split('_');
    const isRelative = rangeUtil.isRelativeTimeRange({ from: fromString, to: toString });

    const raw = {
      from: fromString,
      to: toString,
    };

    if (isRelative) {
      const absolute = convertRelativeToAbsoluteDate(rawInput);
      const [absoluteFrom, absoluteTo] = absolute.split('_');
      value = {
        from: moment(absoluteFrom + 'Z'),
        to: moment(absoluteTo + 'Z'),
        raw,
      };
    } else {
      value = {
        from: moment(fromString + 'Z'),
        to: moment(toString + 'Z'),
        raw,
      };
    }
  }
  return value;
};
