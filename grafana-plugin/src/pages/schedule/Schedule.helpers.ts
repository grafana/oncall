import dayjs from 'dayjs';

import { findColor } from 'containers/Rotations/Rotations.helpers';
import { getLayersFromStore, getOverridesFromStore, getShiftsFromStore } from 'models/schedule/schedule.helpers';
import { Event, Layer } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { RootStore } from 'state';

export const getStartOfWeek = (tz: Timezone) => {
  return dayjs().tz(tz).utcOffset() === 0 ? dayjs().utc().startOf('isoWeek') : dayjs().tz(tz).startOf('isoWeek');
};

export const getUTCString = (moment: dayjs.Dayjs) => {
  return moment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');
};

export const getDateTime = (date: string) => {
  return dayjs(date);
};

export const getColorSchemeMappingForUsers = (
  store: RootStore,
  scheduleId: string,
  startMoment: dayjs.Dayjs
): { [userId: string]: Set<string> } => {
  const usersColorSchemeHash: { [userId: string]: Set<string> } = {};

  const layers: Layer[] = getLayersFromStore(store, scheduleId, startMoment);
  const overrides = getOverridesFromStore(store, scheduleId, startMoment);

  if (!layers?.length) {
    return usersColorSchemeHash;
  }

  const shiftsFromLayers = layers.reduce((prev, current) => {
    prev.push(...current.shifts);
    return prev;
  }, []);

  shiftsFromLayers.forEach(({ shiftId, events }) => populateUserHashSet(events, shiftId));

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
