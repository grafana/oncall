import { TimeOption, TimeRange, rangeUtil } from '@grafana/data';
import { TimeZone } from '@grafana/schema';
import moment from 'moment-timezone';

export const DATE_RANGE_DELIMITER = '_';

export const mapOptionToTimeRange = (option: TimeOption, timeZone?: TimeZone): TimeRange => {
  return rangeUtil.convertRawToRange({ from: option.from, to: option.to }, timeZone);
};

export function convertRelativeToAbsoluteDate(dateRangeString: string) {
  if (!dateRangeString) {
    return undefined;
  }

  const [from, to] = dateRangeString?.split(DATE_RANGE_DELIMITER) || [];
  if (rangeUtil.isRelativeTimeRange({ from, to })) {
    const { from: startDate, to: endDate } = rangeUtil.convertRawToRange({ from, to });

    return `${startDate.utc().format('YYYY-MM-DDTHH:mm:ss')}${DATE_RANGE_DELIMITER}${endDate
      .utc()
      .format('YYYY-MM-DDTHH:mm:ss')}`;
  }
  return dateRangeString;
}

export const convertTimerangeToFilterValue = (timeRange: TimeRange) => {
  const isRelative = rangeUtil.isRelativeTimeRange(timeRange.raw);

  if (isRelative) {
    return timeRange.raw.from + DATE_RANGE_DELIMITER + timeRange.raw.to;
  } else if (timeRange.from.isValid() && timeRange.to.isValid()) {
    return (
      timeRange.from.utc().format('YYYY-MM-DDTHH:mm:ss') +
      DATE_RANGE_DELIMITER +
      timeRange.to.utc().format('YYYY-MM-DDTHH:mm:ss')
    );
  }
  return '';
};

export const getValueForDateRangeFilterType = (rawInput: string) => {
  let value = { from: undefined, to: undefined, raw: { from: '', to: '' } };
  if (rawInput) {
    const [fromString, toString] = rawInput.split(DATE_RANGE_DELIMITER);
    const isRelative = rangeUtil.isRelativeTimeRange({ from: fromString, to: toString });

    const raw = {
      from: fromString,
      to: toString,
    };

    if (isRelative) {
      const absolute = convertRelativeToAbsoluteDate(rawInput);
      const [absoluteFrom, absoluteTo] = absolute.split(DATE_RANGE_DELIMITER);
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
