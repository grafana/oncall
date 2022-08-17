import dayjs from 'dayjs';

import { Event } from './schedule.types';

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
