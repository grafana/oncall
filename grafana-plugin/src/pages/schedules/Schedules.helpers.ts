import { Moment } from 'moment';
import moment from 'moment-timezone';

import { Schedule } from 'models/schedule/schedule.types';

const DATE_FORMAT = 'HH:mm YYYY-MM-DD';

function isToday(m: Moment, currentMoment: Moment) {
  return m.isSame('day');
}

function isYesterday(m: Moment, currentMoment: Moment) {
  return m.diff(currentMoment, 'days') === -1;
}

function isTomorrow(m: Moment, currentMoment: Moment) {
  return m.diff(currentMoment, 'days') === 1;
}

export function prepareForEdit(schedule: Schedule) {
  return {
    ...schedule,
    slack_channel_id: schedule.slack_channel?.id,
    user_group: schedule.user_group?.id,
  };
}

function humanize(m: Moment, currentMoment: Moment) {
  if (isToday(m, currentMoment)) {
    return 'Today';
  }
  if (isYesterday(m, currentMoment)) {
    return 'Yesterday';
  }

  if (isTomorrow(m, currentMoment)) {
    return 'Tomorrow';
  }

  return m.format(DATE_FORMAT);
}

export function getDatesString(start: string, end: string, allDay: boolean) {
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

  let startString = humanize(startMoment, currentMoment);

  let endString = humanize(endMoment, currentMoment);

  return `${startString} — ${endString}`;
}
