import { config } from '@grafana/runtime';
import dayjs from 'dayjs';

import { findColor } from 'containers/Rotations/Rotations.helpers';
import { getLayersFromStore, getOverridesFromStore, getShiftsFromStore } from 'models/schedule/schedule.helpers';
import { Event, Layer } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';

const mondayDayOffset = {
  saturday: -2,
  sunday: -1,
  monday: 0,
  browser: 0,
};

export const getWeekStartString = () => {
  if (!config.bootData.user.weekStart || config.bootData.user.weekStart === 'browser') {
    return 'monday';
  }
  return config.bootData.user.weekStart;
};

export const getNow = (tz: Timezone) => {
  const now = dayjs().tz(tz);
  return now.utcOffset() === 0 ? now.utc() : now;
};

export const getStartOfDay = (tz: Timezone) => {
  return getNow(tz).startOf('day');
};

export const getStartOfWeek = (tz: Timezone) => {
  return getNow(tz)
    .startOf('isoWeek') // it's Monday always
    .add(mondayDayOffset[getWeekStartString()], 'day');
};

export const getUTCString = (moment: dayjs.Dayjs) => {
  return moment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');
};

export const getDateTime = (date: string) => {
  return dayjs(date);
};

const getUTCDayIndex = (index: number, moment: dayjs.Dayjs, reverse: boolean) => {
  let utc_index = index;
  if (moment.day() !== moment.utc().day()) {
    let offset = moment.utcOffset();
    if ((offset < 0 && !reverse) || (reverse && offset > 0)) {
      // move one day after
      utc_index = (utc_index + 1) % 7;
    } else {
      // move one day before
      utc_index = utc_index - 1;
    }
  }
  if (utc_index < 0) {
    utc_index = ((utc_index % 7) + 7) % 7;
  }
  return utc_index;
};

export const getUTCByDay = (dayOptions: SelectOption[], by_day: string[], moment: dayjs.Dayjs) => {
  if (moment.day() === moment.utc().day()) {
    return by_day;
  }
  // when converting to UTC, shift starts on a different day,
  // so we need to update the by_day list
  // depending on the UTC side, move one day before or after
  let UTCDays = [];
  let byDayOptions = [];
  dayOptions.forEach(({ value }) => byDayOptions.push(value));
  by_day.forEach((element) => {
    let index = byDayOptions.indexOf(element);
    index = getUTCDayIndex(index, moment, false);
    UTCDays.push(byDayOptions[index]);
  });

  return UTCDays;
};

export const getSelectedDays = (dayOptions: SelectOption[], by_day: string[], moment: dayjs.Dayjs) => {
  if (moment.day() === moment.utc().day()) {
    return by_day;
  }

  const byDayOptions = dayOptions.map(({ value }) => value);

  let selectedTimezoneDays = [];
  by_day.forEach((element) => {
    let index = byDayOptions.indexOf(element);
    index = getUTCDayIndex(index, moment, true);
    selectedTimezoneDays.push(byDayOptions[index]);
  });

  return selectedTimezoneDays;
};

export const getUTCWeekStart = (dayOptions: SelectOption[], moment: dayjs.Dayjs) => {
  let week_start_index = 0;
  let byDayOptions = [];
  dayOptions.forEach(({ value }) => byDayOptions.push(value));
  if (moment.day() !== moment.utc().day()) {
    // when converting to UTC, shift starts on a different day,
    // so we may need to change when week starts based on the UTC start time
    // depending on the UTC side, move one day before or after
    let offset = moment.utcOffset();
    if (offset < 0) {
      // move one day after
      week_start_index = (week_start_index + 1) % 7;
    } else {
      // move one day before
      week_start_index = (((week_start_index - 1) % 7) + 7) % 7;
    }
  }
  return byDayOptions[week_start_index];
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
