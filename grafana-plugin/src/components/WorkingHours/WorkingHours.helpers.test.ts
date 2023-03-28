import dayjs from 'dayjs';
import isBetween from 'dayjs/plugin/isBetween';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';

dayjs.extend(timezone);
dayjs.extend(utc);
dayjs.extend(isBetween);

import { isInWorkingHours } from './WorkingHours.helpers';

describe('Is in working hours', () => {
  const currentMoment = dayjs('2023-03-27 14:57');

  test('Returns true when it is in working hours', () => {
    const workingHours = {
      monday: [{ end: '17:00:00', start: '09:00:00' }],
      tuesday: [{ end: '17:00:00', start: '09:00:00' }],
      wednesday: [{ end: '17:00:00', start: '09:00:00' }],
      thursday: [{ end: '17:00:00', start: '09:00:00' }],
      friday: [{ end: '17:00:00', start: '09:00:00' }],
      saturday: [{ end: '17:00:00', start: '09:00:00' }],
      sunday: [{ end: '17:00:00', start: '09:00:00' }],
    };
    expect(isInWorkingHours(currentMoment, workingHours, dayjs.tz.guess())).toBeTruthy();
  });

  test('Returns false when it is NOT in working hours', () => {
    const workingHours = {
      monday: [{ end: '14:00:00', start: '09:00:00' }],
      tuesday: [{ end: '14:00:00', start: '09:00:00' }],
      wednesday: [{ end: '14:00:00', start: '09:00:00' }],
      thursday: [{ end: '14:00:00', start: '09:00:00' }],
      friday: [{ end: '14:00:00', start: '09:00:00' }],
      saturday: [{ end: '14:00:00', start: '09:00:00' }],
      sunday: [{ end: '14:00:00', start: '09:00:00' }],
    };
    expect(isInWorkingHours(currentMoment, workingHours, dayjs.tz.guess())).toBeFalsy();
  });

  test('Returns false when it is complex Working hours schedule', () => {
    const workingHours = {
      monday: [
        { start: '09:00:00', end: '11:00:00' },
        { start: '15:00:00', end: '18:00:00' },
      ],
      tuesday: [
        { start: '09:00:00', end: '11:00:00' },
        { start: '15:00:00', end: '18:00:00' },
      ],
      wednesday: [
        { start: '09:00:00', end: '11:00:00' },
        { start: '15:00:00', end: '18:00:00' },
      ],
      thursday: [
        { start: '09:00:00', end: '11:00:00' },
        { start: '15:00:00', end: '18:00:00' },
      ],
      friday: [
        { start: '09:00:00', end: '11:00:00' },
        { start: '15:00:00', end: '18:00:00' },
      ],
      saturday: [
        { start: '09:00:00', end: '11:00:00' },
        { start: '15:00:00', end: '18:00:00' },
      ],
      sunday: [
        { start: '09:00:00', end: '11:00:00' },
        { start: '15:00:00', end: '18:00:00' },
      ],
    };

    expect(isInWorkingHours(currentMoment, workingHours, dayjs.tz.guess())).toBeFalsy();
  });

  test('Returns true when it is complex Working hours schedule', () => {
    const workingHours = {
      monday: [
        { start: '09:00:00', end: '13:00:00' },
        { start: '14:00:00', end: '18:00:00' },
      ],
      tuesday: [
        { start: '09:00:00', end: '13:00:00' },
        { start: '14:00:00', end: '18:00:00' },
      ],
      wednesday: [
        { start: '09:00:00', end: '13:00:00' },
        { start: '14:00:00', end: '18:00:00' },
      ],
      thursday: [
        { start: '09:00:00', end: '13:00:00' },
        { start: '14:00:00', end: '18:00:00' },
      ],
      friday: [
        { start: '09:00:00', end: '13:00:00' },
        { start: '14:00:00', end: '18:00:00' },
      ],
      saturday: [
        { start: '09:00:00', end: '13:00:00' },
        { start: '14:00:00', end: '18:00:00' },
      ],
      sunday: [
        { start: '09:00:00', end: '13:00:00' },
        { start: '14:00:00', end: '18:00:00' },
      ],
    };

    expect(isInWorkingHours(currentMoment, workingHours, dayjs.tz.guess())).toBeTruthy();
  });
});
