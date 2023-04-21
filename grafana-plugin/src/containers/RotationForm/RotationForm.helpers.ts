import dayjs from 'dayjs';

import { Timezone } from 'models/timezone/timezone.types';

export const toDate = (moment: dayjs.Dayjs, timezone: Timezone) => {
  const localMoment = moment.tz(timezone);

  return new Date(
    localMoment.get('year'),
    localMoment.get('month'),
    localMoment.get('date'),
    localMoment.get('hour'),
    localMoment.get('minute'),
    localMoment.get('second')
  );
};
