import dayjs from 'dayjs';

import { findColor } from 'containers/Rotations/Rotations.helpers';
import { getLayersFromStore, getOverridesFromStore, getShiftsFromStore } from 'models/schedule/schedule.helpers';
import { Event, Layer } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';

export const getNow = (tz: Timezone) => {
  const now = dayjs().tz(tz);
  return now.utcOffset() === 0 ? now.utc() : now;
};

export const getStartOfDay = (tz: Timezone) => {
  return getNow(tz).startOf('day');
};

export const getStartOfWeek = (tz: Timezone) => {
  return getNow(tz).startOf('isoWeek');
};

export const getUTCString = (moment: dayjs.Dayjs) => {
  return moment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');
};

export const getDateTime = (date: string) => {
  return dayjs(date);
};

export const getUTCByDay = (dayOptions: SelectOption[], by_day: string[], moment: dayjs.Dayjs) => {
  if (by_day.length && moment.day() !== moment.utc().day()) {
    // when converting to UTC, shift starts on a different day,
    // so we need to update the by_day list
    // depending on the UTC side, move one day before or after
    let offset = moment.utcOffset();
    let UTCDays = [];
    let byDayOptions = [];
    dayOptions.forEach(({ value }) => byDayOptions.push(value));
    by_day.forEach((element) => {
      let index = byDayOptions.indexOf(element);
      if (offset < 0) {
        // move one day after
        UTCDays.push(byDayOptions[(index + 1) % 7]);
      } else {
        // move one day before
        UTCDays.push(byDayOptions[(((index - 1) % 7) + 7) % 7]);
      }
    });
    return UTCDays;
  }
  return by_day;
};

export const getColorSchemeMappingForUsers = (
  store: RootStore,
  scheduleId: string,
  startMoment: dayjs.Dayjs
): { [userId: string]: Set<string> } => {
  const usersColorSchemeHash: { [userId: string]: Set<string> } = {};

  const finalScheduleShifts = getShiftsFromStore(store, scheduleId, startMoment);
  const layers: Layer[] = getLayersFromStore(store, scheduleId, startMoment);
  const overrides = getOverridesFromStore(store, scheduleId, startMoment);

  if (!finalScheduleShifts?.length || !layers?.length) {
    return usersColorSchemeHash;
  }

  const rotationShifts = layers.reduce((prev, current) => {
    prev.push(...current.shifts);
    return prev;
  }, []);

  finalScheduleShifts.forEach(({ shiftId, events }) => populateUserHashSet(events, shiftId));
  rotationShifts.forEach(({ shiftId, events }) => populateUserHashSet(events, shiftId));

  return usersColorSchemeHash;

  function populateUserHashSet(events: Event[], id: string) {
    events.forEach((event) => {
      event.users.forEach((user) => {
        if (!usersColorSchemeHash[user.pk]) {
          usersColorSchemeHash[user.pk] = new Set<string>();
        }

        usersColorSchemeHash[user.pk].add(findColor(id as string, layers, overrides));
      });
    });
  }
};
