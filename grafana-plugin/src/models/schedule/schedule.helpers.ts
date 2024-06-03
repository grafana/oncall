import dayjs from 'dayjs';

import { ApiSchemas } from 'network/oncall-api/api.types';
import { RootStore } from 'state/rootStore';

import { Event, Layer, Schedule, ScheduleType, ScheduleView, Shift, ShiftEvents, ShiftSwap } from './schedule.types';

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

export const createShiftSwapEventFromShiftSwap = (shiftSwap: Partial<ShiftSwap>) => {
  return {
    shiftSwapId: shiftSwap.id,
    start: shiftSwap.swap_start,
    end: shiftSwap.swap_end,
    is_gap: false,
    users: [],
    all_day: false,
    shift: null,
    missing_users: [],
    is_empty: true,
    is_shift_swap: true,
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

export const scheduleViewToDaysInOneRow = {
  [ScheduleView.OneWeek]: 7,
  [ScheduleView.TwoWeeks]: 14,
  [ScheduleView.OneMonth]: 7,
};

export const getTotalDaysToDisplay = (scheduleView: ScheduleView, calendarStartDate: dayjs.Dayjs) => {
  switch (scheduleView) {
    case ScheduleView.OneWeek:
      return 7;
    case ScheduleView.TwoWeeks:
      return 14;
    case ScheduleView.OneMonth:
      const firstDayOfCurrentMonth =
        calendarStartDate.date() === 1 ? calendarStartDate : calendarStartDate.add(1, 'month').startOf('month');

      const lastDayOfCurrentMonth = firstDayOfCurrentMonth.endOf('month');

      const lastDayOfLastWeek = lastDayOfCurrentMonth.endOf('isoWeek');

      const totalDays = lastDayOfLastWeek.diff(calendarStartDate, 'days') + 1;

      return totalDays;
  }
};

export const splitToShifts = (events: Event[]) => {
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

  return shifts;
};

export const fillGapsInShifts = (shifts: ShiftEvents[]) => {
  return shifts.map((shift) => ({
    ...shift,
    events: fillGaps(shift.events),
  }));
};

export const enrichEventsWithScheduleData = (events: Event[], schedule: Partial<Schedule>) => {
  return events.map((event) => ({ ...event, schedule }));
};

export const getPersonalShiftsFromStore = (
  store: RootStore,
  userPk: ApiSchemas['User']['pk'],
  startMoment: dayjs.Dayjs
): ShiftEvents[] => {
  return store.scheduleStore.personalEvents[userPk]?.[getFromString(startMoment)] as any;
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

export const unFlattenShiftEvents = (shifts: ShiftEvents[]) => {
  for (let i = 0; i < shifts.length; i++) {
    const shift = shifts[i];

    for (let j = 0; j < shift.events.length - 1; j++) {
      for (let k = j + 1; k < shift.events.length; k++) {
        const event1 = shift.events[j];
        const event2 = shift.events[k];

        const event1Start = dayjs(event1.start);
        const event1End = dayjs(event1.end);

        const event2Start = dayjs(event2.start);
        const event2End = dayjs(event2.end);

        if (
          (event1Start.isBefore(event2Start) && event1End.isAfter(event2Start)) ||
          (event1End.isAfter(event2End) && event1Start.isBefore(event2End))
        ) {
          const firstEvent = event1Start.isBefore(event2Start) ? event1 : event2;
          const secondEvent = firstEvent === event1 ? event2 : event1;

          const oldShift = { ...shift, events: shift.events.filter((event) => event !== secondEvent) };

          const newShift = { ...shift, events: [secondEvent] };

          shifts[i] = oldShift;
          shifts.push(newShift);

          return unFlattenShiftEvents(shifts);
        }
      }
    }
  }

  return shifts;
};

export const flattenShiftEvents = (shifts: ShiftEvents[]) => {
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

export const getShiftSwapsFromStore = (
  store: RootStore,
  scheduleId: Schedule['id'],
  startMoment: dayjs.Dayjs
): ShiftEvents[] => {
  return store.scheduleStore.shiftSwapsPreview
    ? store.scheduleStore.shiftSwapsPreview[getFromString(startMoment)]
    : store.scheduleStore.scheduleAndDateToShiftSwaps[scheduleId]?.[getFromString(startMoment)];
};

export const getOverridesFromStore = (
  store: RootStore,
  scheduleId: Schedule['id'],
  startMoment: dayjs.Dayjs
): ShiftEvents[] => {
  return store.scheduleStore.overridePreview
    ? store.scheduleStore.overridePreview[getFromString(startMoment)]
    : (store.scheduleStore.events[scheduleId]?.['override']?.[getFromString(startMoment)] as ShiftEvents[]);
};

export const splitToLayers = (shifts: ShiftEvents[]) => {
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

const L2_COLORS = ['#299C46', '#517A00', '#84362A', '#521913'];

const L3_COLORS = ['#377277', '#638282', '#364E4E', '#423220'];

const OVERRIDE_COLORS = ['#EF9C48'];

export const SHIFT_SWAP_COLOR = '#DC7532';

const COLORS = [L1_COLORS, L2_COLORS, L3_COLORS];

const scheduleToColor = {};

export const getColorForSchedule = (scheduleId: Schedule['id']) => {
  if (scheduleToColor[scheduleId]) {
    return scheduleToColor[scheduleId];
  }

  const colors = [...L1_COLORS, ...L2_COLORS, ...L3_COLORS];

  const index = Object.keys(scheduleToColor).length;
  const normalizedIndex = index % colors.length;

  const color = colors[normalizedIndex];

  scheduleToColor[scheduleId] = color;

  return color;
};

export const getColor = (layerIndex: number, rotationIndex: number) => {
  const normalizedLayerIndex = layerIndex % COLORS.length;
  const normalizedRotationIndex = rotationIndex % COLORS[normalizedLayerIndex]?.length;

  return COLORS[normalizedLayerIndex]?.[normalizedRotationIndex];
};

export const getOverrideColor = (rotationIndex: number) => {
  const normalizedRotationIndex = rotationIndex % OVERRIDE_COLORS.length;
  return OVERRIDE_COLORS[normalizedRotationIndex];
};

export const getShiftName = (shift: Partial<Shift>) => {
  if (!shift) {
    return '';
  }

  if (shift.name) {
    return shift.name;
  }

  if (shift.type === 3) {
    return 'Override';
  }

  return 'Rotation';
};
