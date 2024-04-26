import { TimeOption, TimeRange, rangeUtil } from '@grafana/data';
import { TimeZone } from '@grafana/schema';

export const mapOptionToTimeRange = (option: TimeOption, timeZone?: TimeZone): TimeRange => {
  return rangeUtil.convertRawToRange({ from: option.from, to: option.to }, timeZone);
};

export function convertRelativeToAbsoluteDate(dateRangeString: string) {
  if (!dateRangeString) {
    return undefined;
  }

  const [from, to] = dateRangeString?.split('/') || [];
  if (rangeUtil.isRelativeTimeRange({ from, to })) {
    const { from: startDate, to: endDate } = rangeUtil.convertRawToRange({ from, to });
    return `${startDate.utc().format('YYYY-MM-DDTHH:mm:ss')}/${endDate.utc().format('YYYY-MM-DDTHH:mm:ss')}`;
  }
  return dateRangeString;
}
