import moment from 'moment-timezone';

import { Schedule } from 'models/schedule/schedule.types';

const DATE_FORMAT = 'HH:mm YYYY-MM-DD';

const isToday = (m: moment.Moment): boolean => m.isSame('day');
const isYesterday = (m: moment.Moment, currentMoment: moment.Moment): boolean => m.diff(currentMoment, 'days') === -1;
const isTomorrow = (m: moment.Moment, currentMoment: moment.Moment): boolean => m.diff(currentMoment, 'days') === 1;

export const prepareForEdit = (schedule: Schedule) => ({
  ...schedule,
  slack_channel_id: schedule.slack_channel?.id,
  user_group: schedule.user_group?.id,
});

const humanize = (m: moment.Moment, currentMoment: moment.Moment): string => {
  if (isToday(m)) {
    return 'Today';
  }
  if (isYesterday(m, currentMoment)) {
    return 'Yesterday';
  }

  if (isTomorrow(m, currentMoment)) {
    return 'Tomorrow';
  }

  return m.format(DATE_FORMAT);
};

export const getDatesString = (start: string, end: string, allDay: boolean): string => {
  const startMoment = moment(start);
  const endMoment = moment(end);
  const currentMoment = moment();

  if (allDay) {
    if (startMoment.isSame(endMoment, 'day')) {
      return 'All-day';
    }

    return `${startMoment.format(DATE_FORMAT)} — ${endMoment.format(DATE_FORMAT)}`;
  }

  if (startMoment.isSame(endMoment, 'day')) {
    return `${startMoment.format('LT')} — ${endMoment.format('LT')}`;
  }

  const startString = humanize(startMoment, currentMoment);

  const endString = humanize(endMoment, currentMoment);

  return `${startString} — ${endString}`;
};
