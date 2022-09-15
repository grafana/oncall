import { DateTime, dateTime } from '@grafana/data';
import dayjs from 'dayjs';

import { Timezone } from 'models/timezone/timezone.types';

export const getStartOfWeek = (tz: Timezone) => {
  return dayjs().tz(tz).utcOffset() === 0 ? dayjs().utc().startOf('isoWeek') : dayjs().tz(tz).startOf('isoWeek');
};

export const getUTCString = (moment: dayjs.Dayjs | DateTime, timezone: Timezone) => {
  const browserTimezone = dayjs.tz.guess();

  const browserTimezoneOffset = dayjs().tz(browserTimezone).utcOffset();
  const timezoneOffset = dayjs().tz(timezone).utcOffset();

  return (moment as dayjs.Dayjs)
    .clone()
    .utc()
    .add(browserTimezoneOffset, 'minutes') // we need these calculations because we can't specify timezone for DateTimePicker directly
    .subtract(timezoneOffset, 'minutes')
    .format('YYYY-MM-DDTHH:mm:ss.000Z');
};

export const getDateTime = (date: string, timezone: Timezone) => {
  const browserTimezone = dayjs.tz.guess();

  const browserTimezoneOffset = dayjs().tz(browserTimezone).utcOffset();
  const timezoneOffset = dayjs().tz(timezone).utcOffset();

  return dateTime(
    dayjs(date)
      .subtract(browserTimezoneOffset, 'minutes')
      .add(timezoneOffset, 'minutes')
      .format('YYYY-MM-DDTHH:mm:ss.000Z')
  );
};
