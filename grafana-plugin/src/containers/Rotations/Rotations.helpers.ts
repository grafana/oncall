import dayjs from 'dayjs';

import { getColor, getOverrideColor } from 'models/schedule/schedule.helpers';
import { Layer, Shift } from 'models/schedule/schedule.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { toDateWithTimezoneOffset } from 'pages/schedule/Schedule.helpers';

// DatePickers will convert the date passed to local timezone, instead we want to use the date in the given timezone
export const toDatePickerDate = (value: dayjs.Dayjs, timezoneOffset: number) => {
  const date = toDateWithTimezoneOffset(value, timezoneOffset);

  return dayjs()
    .set('hour', 0)
    .set('minute', 0)
    .set('second', 0)
    .set('millisecond', 0)
    .set('date', 1)
    .set('month', date.month())
    .set('date', date.date())
    .set('year', date.year())
    .toDate();
};

export const getCalendarStartDateInTimezone = (calendarStartDate: dayjs.Dayjs, utcOffset: number) => {
  const offsetedDate = dayjs(calendarStartDate.toDate())
    .utcOffset(utcOffset)
    .set('date', 1)
    .set('months', calendarStartDate.month())
    .set('date', calendarStartDate.date())
    .set('year', calendarStartDate.year())
    .set('hours', 0)
    .set('minutes', 0)
    .set('second', 0)
    .set('milliseconds', 0);

  return offsetedDate;
};

export const findColor = (shiftId: Shift['id'], layers: Layer[], overrides?) => {
  let color = undefined;

  let layerIndex = -1;
  let rotationIndex = -1;
  if (layers) {
    outer: for (let i = 0; i < layers.length; i++) {
      for (let j = 0; j < layers[i].shifts.length; j++) {
        const shift = layers[i].shifts[j];
        if (shift.shiftId === shiftId || (shiftId === 'new' && shift.isPreview)) {
          layerIndex = i;
          rotationIndex = j;
          break outer;
        }
      }
    }
  }

  let overrideIndex = -1;
  if (layerIndex === -1 && rotationIndex === -1 && overrides) {
    for (let k = 0; k < overrides.length; k++) {
      const shift = overrides[k];
      if (shift.shiftId === shiftId || (shiftId === 'new' && shift.isPreview)) {
        overrideIndex = k;
      }
    }
  }

  if (layerIndex > -1 && rotationIndex > -1) {
    color = getColor(layerIndex, rotationIndex);
  } else if (overrideIndex > -1) {
    color = getOverrideColor(overrideIndex);
  }

  return color;
};

export const findClosestUserEvent = (startMoment: dayjs.Dayjs, userPk: ApiSchemas['User']['pk'], layers: Layer[]) => {
  let minDiff;
  let closestEvent;

  if (!layers) {
    return undefined;
  }

  for (let i = 0; i < layers.length; i++) {
    for (let j = 0; j < layers[i].shifts.length; j++) {
      const shift = layers[i].shifts[j];
      const events = shift.events;
      for (let k = 0; k < events.length; k++) {
        const event = events[k];
        const diff = dayjs(event.start).diff(startMoment, 'seconds');

        if (
          event.users.some((user) => user.pk === userPk) &&
          !event.users.some((user) => user.swap_request) &&
          diff > 0 &&
          (minDiff === undefined || diff < minDiff)
        ) {
          minDiff = diff;
          closestEvent = event;
        }
      }
    }
  }

  return closestEvent;
};
