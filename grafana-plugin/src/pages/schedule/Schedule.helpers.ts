import dayjs from 'dayjs';

import { findColor } from 'containers/Rotations/Rotations.helpers';
import { getLayersFromStore, getOverridesFromStore, getShiftsFromStore } from 'models/schedule/schedule.helpers';
import { Event, Layer } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { RootStore } from 'state';

type UsersColorScheme = {
  [userId: string]: Set<string>;
};

export const getStartOfWeek = (tz: Timezone): dayjs.Dayjs =>
  dayjs().tz(tz).utcOffset() === 0 ? dayjs().utc().startOf('isoWeek') : dayjs().tz(tz).startOf('isoWeek');

export const getUTCString = (moment: dayjs.Dayjs): string => moment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');

export const getDateTime = (date: string) => dayjs(date);

export const getColorSchemeMappingForUsers = (
  store: RootStore,
  scheduleId: string,
  startMoment: dayjs.Dayjs
): UsersColorScheme => {
  const usersColorSchemeHash: UsersColorScheme = {};

  const finalScheduleShifts = getShiftsFromStore(store, scheduleId, startMoment);
  const layers: Layer[] = getLayersFromStore(store, scheduleId, startMoment);
  const overrides = getOverridesFromStore(store, scheduleId, startMoment);

  const populateUserHashSet = (events: Event[], id: string): void => {
    events.forEach((event) => {
      event.users.forEach((user) => {
        if (!usersColorSchemeHash[user.pk]) {
          usersColorSchemeHash[user.pk] = new Set<string>();
        }

        usersColorSchemeHash[user.pk].add(findColor(id as string, layers, overrides));
      });
    });
  };

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
};
