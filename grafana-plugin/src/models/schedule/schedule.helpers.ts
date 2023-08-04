import dayjs from 'dayjs';

import { RootStore } from 'state';

import { Event, Layer, Schedule, ScheduleType, Shift, ShiftEvents } from './schedule.types';

export const getFromString = (moment: dayjs.Dayjs) => {
  return moment.format('YYYY-MM-DD');
};

const createGap = (start, end) => {
  return {
    start,
    end,
    is_gap: true,
    users: [],
    all_day: false,
    shift: null,
    missing_users: [],
    is_empty: true,
    calendar_type: ScheduleType.API,
    priority_level: null,
    source: 'web',
    is_override: false,
  };
};

export const fillGaps = (events: Event[]) => {
  const newEvents = [];

  for (const [i, event] of events.entries()) {
    newEvents.push(event);

    const nextEvent = events[i + 1];

    if (nextEvent) {
      if (nextEvent.start !== event.end) {
        newEvents.push(createGap(event.end, nextEvent.start));
      }
    }
  }

  return newEvents;
};

export const splitToShiftsAndFillGaps = (events: Event[]) => {
  const shifts: Array<{ shiftId: Shift['id']; priority: Shift['priority_level']; events: Event[] }> = [];

  for (const [_i, event] of events.entries()) {
    if (event.shift?.pk) {
      let shift = shifts.find((shift) => shift.shiftId === event.shift?.pk);
      if (!shift) {
        shift = { shiftId: event.shift.pk, priority: event.priority_level, events: [] };
        shifts.push(shift);
      }
      shift.events.push(event);
    }
  }

  shifts.forEach((shift) => {
    shift.events = fillGaps(shift.events);
  });

  return shifts;
};

export const getShiftsFromStore = (
  store: RootStore,
  scheduleId: Schedule['id'],
  startMoment: dayjs.Dayjs
): ShiftEvents[] => {
  return store.scheduleStore.finalPreview
    ? store.scheduleStore.finalPreview[getFromString(startMoment)]
    : (store.scheduleStore.events[scheduleId]?.['final']?.[getFromString(startMoment)] as any);
};

export const flattenFinalShifs = (shifts: ShiftEvents[]) => {
  if (!shifts) {
    return undefined;
  }

  function splitToPairs(shifts: ShiftEvents[]) {
    const pairs = [];
    for (let i = 0; i < shifts.length - 1; i++) {
      for (let j = i + 1; j < shifts.length; j++) {
        pairs.push([
          { ...shifts[i], events: [...shifts[i].events] },
          { ...shifts[j], events: [...shifts[j].events] },
        ]);
      }
    }

    return pairs;
  }

  let pairs = splitToPairs(shifts);

  while (pairs.length > 0) {
    const currentPair = pairs.shift();

    const merged = mergePair(currentPair);

    if (merged !== currentPair) {
      // means pair was fully merged

      shifts = shifts.filter((shift) => !currentPair.some((pairShift) => pairShift.shiftId === shift.shiftId));
      shifts.unshift(merged[0]);
      pairs = splitToPairs(shifts);
    }
  }

  function mergePair(pair: ShiftEvents[]): ShiftEvents[] {
    const recipient = { ...pair[0], events: [...pair[0].events] };
    const donor = pair[1];

    const donorEvents = donor.events.filter((event) => !event.is_gap);

    for (let i = 0; i < donorEvents.length; i++) {
      const donorEvent = donorEvents[i];

      const eventStartMoment = dayjs(donorEvent.start);
      const eventEndMoment = dayjs(donorEvent.end);

      const suitablerRecepientGapIndex = recipient.events.findIndex((event) => {
        if (!event.is_gap) {
          return false;
        }

        const gap = event;

        const gapStartMoment = dayjs(gap.start);
        const gapEndMoment = dayjs(gap.end);

        return gapStartMoment.isSameOrBefore(eventStartMoment) && gapEndMoment.isSameOrAfter(eventEndMoment);
      });

      if (suitablerRecepientGapIndex > -1) {
        const suitablerRecepientGap = recipient.events[suitablerRecepientGapIndex];

        const itemsToAdd = [];
        const leftGap = createGap(suitablerRecepientGap.start, donorEvent.start);
        if (leftGap.start !== leftGap.end) {
          itemsToAdd.push(leftGap);
        }
        itemsToAdd.push(donorEvent);

        const rightGap = createGap(donorEvent.end, suitablerRecepientGap.end);
        if (rightGap.start !== rightGap.end) {
          itemsToAdd.push(rightGap);
        }

        recipient.events = [
          ...recipient.events.slice(0, suitablerRecepientGapIndex),
          ...itemsToAdd,
          ...recipient.events.slice(suitablerRecepientGapIndex + 1),
        ];
      } else {
        const firstRecepientEvent = recipient.events[0];
        const firstRecepientEventStartMoment = dayjs(firstRecepientEvent.start);

        const lastRecepientEvent = recipient.events[recipient.events.length - 1];
        const lastRecepientEventEndMoment = dayjs(lastRecepientEvent.end);

        if (eventEndMoment.isSameOrBefore(firstRecepientEventStartMoment)) {
          const itemsToAdd = [donorEvent];
          if (donorEvent.end !== firstRecepientEvent.start) {
            itemsToAdd.push(createGap(donorEvent.end, firstRecepientEvent.start));
          }
          recipient.events = [...itemsToAdd, ...recipient.events];
        } else if (eventStartMoment.isSameOrAfter(lastRecepientEventEndMoment)) {
          const itemsToAdd = [donorEvent];
          if (lastRecepientEvent.end !== donorEvent.start) {
            itemsToAdd.unshift(createGap(lastRecepientEvent.end, donorEvent.start));
          }
          recipient.events = [...recipient.events, ...itemsToAdd];
        } else {
          // the pair can't be fully merged

          return pair;
        }
      }
    }

    return [recipient];
  }

  return shifts;
};

export const getLayersFromStore = (store: RootStore, scheduleId: Schedule['id'], startMoment: dayjs.Dayjs): Layer[] => {
  return store.scheduleStore.rotationPreview
    ? store.scheduleStore.rotationPreview[getFromString(startMoment)]
    : (store.scheduleStore.events[scheduleId]?.['rotation']?.[getFromString(startMoment)] as Layer[]);
};

export const getOverridesFromStore = (
  store: RootStore,
  scheduleId: Schedule['id'],
  startMoment: dayjs.Dayjs
): ShiftEvents[] => {
  return store.scheduleStore.overridePreview
    ? store.scheduleStore.overridePreview[getFromString(startMoment)]
    : (store.scheduleStore.events[scheduleId]?.['override']?.[getFromString(startMoment)] as Layer[]);
};

export const splitToLayers = (
  shifts: Array<{ shiftId: Shift['id']; priority: Shift['priority_level']; events: Event[] }>
) => {
  return shifts
    .reduce((memo, shift) => {
      let layer = memo.find((level) => level.priority === shift.priority);
      if (!layer) {
        layer = { priority: shift.priority, shifts: [] };
        memo.push(layer);
      }
      layer.shifts.push(shift);

      return memo;
    }, [])
    .sort((a, b) => {
      if (a.priority > b.priority) {
        return 1;
      }
      if (a.priority < b.priority) {
        return -1;
      }

      return 0;
    });
};

export const enrichLayers = (
  layers: Layer[],
  newEvents: Event[],
  shiftId: Shift['id'] | 'new',
  priority: Shift['priority_level']
) => {
  let shiftIdFromEvent = shiftId;
  if (shiftId === 'new') {
    const event = newEvents.find((event) => !event.is_gap);
    if (event) {
      shiftIdFromEvent = event.shift.pk;
    }
  }

  const updatingLayer = {
    priority,
    shifts: [
      {
        shiftId: shiftIdFromEvent,
        isPreview: true,
        events: fillGaps(newEvents.filter((event: Event) => !event.is_gap)),
      },
    ],
  };

  let added = false;
  layers = layers.reduce((memo, layer, index) => {
    if (shiftId === 'new') {
      if (layer.priority === priority) {
        const newLayer = { ...layer };
        newLayer.shifts = [...layer.shifts, ...updatingLayer.shifts];

        memo[index] = newLayer;

        added = true;
      }
    } else {
      const oldShiftIndex = layer.shifts.findIndex((shift) => shift.shiftId === updatingLayer.shifts[0].shiftId);
      if (oldShiftIndex > -1) {
        const newLayer = { ...layer };
        newLayer.shifts = [...layer.shifts];
        newLayer.shifts[oldShiftIndex] = updatingLayer.shifts[0];

        memo[index] = newLayer;

        added = true;
      }
    }

    return layers;
  }, layers);

  if (!added) {
    layers.push(updatingLayer);
  }

  return layers;
};

export const enrichOverrides = (
  overrides: Array<{ shiftId: Shift['id']; events: Event[] }>,
  newEvents: Event[],
  shiftId: Shift['id']
) => {
  let shiftIdFromEvent = shiftId;
  if (shiftId === 'new') {
    const event = newEvents.find((event) => !event.is_gap);
    if (event) {
      shiftIdFromEvent = event.shift.pk;
    }
  }

  const newShift = { shiftId: shiftIdFromEvent, isPreview: true, events: fillGaps(newEvents) };

  const index = overrides.findIndex((shift) => shift.shiftId === shiftId);

  if (index > -1) {
    overrides[index] = newShift;
  } else {
    overrides.push(newShift);
  }

  return overrides;
};

const L1_COLORS = ['#3D71D9', '#6D609C', '#4D3B72', '#8214A0'];

const L2_COLORS = ['#3CB979', '#188343', '#84362A', '#521913'];

const L3_COLORS = ['#377277', '#638282', '#364E4E', '#423220'];

const OVERRIDE_COLORS = ['#C69B06', '#C2C837'];

export const SHIFT_SWAP_COLOR = '#C69B06';

const COLORS = [L1_COLORS, L2_COLORS, L3_COLORS];

export const getColor = (layerIndex: number, rotationIndex: number) => {
  const normalizedLayerIndex = layerIndex % COLORS.length;
  const normalizedRotationIndex = rotationIndex % COLORS[normalizedLayerIndex]?.length;

  return COLORS[normalizedLayerIndex]?.[normalizedRotationIndex];
};

export const getOverrideColor = (rotationIndex: number) => {
  const normalizedRotationIndex = rotationIndex % OVERRIDE_COLORS.length;
  return OVERRIDE_COLORS[normalizedRotationIndex];
};

export const getShiftName = (shift: Shift) => {
  if (!shift) {
    return '';
  }

  if (shift.name) {
    return shift.name;
  }

  if (shift.type === 3) {
    return 'Override';
  }

  return `[L${shift.priority_level}] Rotation`;
};
