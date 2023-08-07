import dayjs from 'dayjs';

import { getColor, getOverrideColor } from 'models/schedule/schedule.helpers';
import { Layer, Shift } from 'models/schedule/schedule.types';
import { User } from 'models/user/user.types';

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

export const findClosestUserEvent = (startMoment: dayjs.Dayjs, userPk: User['pk'], layers: Layer[]) => {
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
