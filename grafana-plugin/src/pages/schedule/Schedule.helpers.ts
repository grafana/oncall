import { DateTime, dateTime } from '@grafana/data';
import dayjs from 'dayjs';

import { Timezone } from 'models/timezone/timezone.types';

export const getStartOfWeek = (tz: Timezone) => {
  return dayjs().tz(tz).utcOffset() === 0 ? dayjs().utc().startOf('isoWeek') : dayjs().tz(tz).startOf('isoWeek');
};

export const getUTCString = (moment: dayjs.Dayjs) => {
  return moment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');
};

export const getDateTime = (date: string) => {
  return dayjs(date);
};
