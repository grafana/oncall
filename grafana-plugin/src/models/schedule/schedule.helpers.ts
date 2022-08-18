import dayjs from 'dayjs';

import { Event, Shift } from './schedule.types';

export const getFromString = (moment: dayjs.Dayjs) => {
  return moment.format('YYYY-MM-DD');
};

export const fillGaps = (events: Event[]) => {
  const newEvents = [];

  for (const [i, event] of events.entries()) {
    newEvents.push(event);

    const nextEvent = events[i + 1];

    if (nextEvent) {
      if (nextEvent.start !== event.end) {
        newEvents.push({ start: event.end, end: nextEvent.start, is_gap: true });
      }
    }
  }

  return newEvents;
};

export const splitToShiftsAndFillGaps = (events: Event[]) => {
  const shifts: Array<{ shiftId: Shift['id']; events: Event[] }> = [];

  for (const [i, event] of events.entries()) {
    if (event.shift?.pk) {
      let shift = shifts.find((shift) => shift.shiftId === event.shift?.pk);
      if (!shift) {
        shift = { shiftId: event.shift.pk, events: [] };
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
