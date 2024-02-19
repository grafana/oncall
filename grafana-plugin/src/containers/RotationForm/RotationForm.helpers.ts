import dayjs, { Dayjs, ManipulateType } from 'dayjs';

import { Timezone } from 'models/timezone/timezone.types';

import { RepeatEveryPeriod } from './RotationForm.types';

export const getRepeatShiftsEveryOptions = (repeatEveryPeriod: number) => {
  const count = repeatEveryPeriod === RepeatEveryPeriod.HOURS ? 24 : 30;
  return Array.from(Array(count + 1).keys())
    .slice(1)
    .map((i) => ({ label: String(i), value: i }));
};

export const toDate = (moment: dayjs.Dayjs, timezone: Timezone) => {
  const localMoment = moment.tz(timezone);

  return new Date(
    localMoment.get('year'),
    localMoment.get('month'),
    localMoment.get('date'),
    localMoment.get('hour'),
    localMoment.get('minute'),
    localMoment.get('second')
  );
};

export interface TimeUnit {
  unit: RepeatEveryPeriod;
  value: number;
  maxValue: number;
}

export const repeatEveryPeriodMultiplier = {
  [RepeatEveryPeriod.MONTHS]: 60 * 60 * 24 * 30,
  [RepeatEveryPeriod.WEEKS]: 60 * 60 * 24 * 7,
  [RepeatEveryPeriod.DAYS]: 60 * 60 * 24,
  [RepeatEveryPeriod.HOURS]: 60 * 60,
  [RepeatEveryPeriod.MINUTES]: 60,
};

export const repeatEveryPeriodToNextPeriodCount = {
  [RepeatEveryPeriod.WEEKS]: Number.MAX_SAFE_INTEGER,
  [RepeatEveryPeriod.DAYS]: 7,
  [RepeatEveryPeriod.HOURS]: 24,
  [RepeatEveryPeriod.MINUTES]: 60,
};

export const TIME_UNITS_ORDER = [
  RepeatEveryPeriod.WEEKS,
  RepeatEveryPeriod.DAYS,
  RepeatEveryPeriod.HOURS,
  RepeatEveryPeriod.MINUTES,
];

export const repeatEveryPeriodToUnitName: { [key: number]: ManipulateType } = {
  [RepeatEveryPeriod.DAYS]: 'days',
  [RepeatEveryPeriod.HOURS]: 'hours',
  [RepeatEveryPeriod.WEEKS]: 'weeks',
  [RepeatEveryPeriod.MONTHS]: 'months',
  [RepeatEveryPeriod.MINUTES]: 'minutes',
};

export const repeatEveryPeriodToUnitNameShortened = {
  [RepeatEveryPeriod.DAYS]: 'd',
  [RepeatEveryPeriod.HOURS]: 'h',
  [RepeatEveryPeriod.WEEKS]: 'w',
  [RepeatEveryPeriod.MONTHS]: 'mo',
  [RepeatEveryPeriod.MINUTES]: 'm',
};

export const repeatEveryToTimeUnits = (repeatEveryPeriod: RepeatEveryPeriod, repetEveryValue: number) => {
  const seconds = repeatEveryInSeconds(repeatEveryPeriod, repetEveryValue);

  return secondsToTimeUnits(seconds, repeatEveryPeriod);
};

export const secondsToTimeUnits = (seconds: number, repeatEveryPeriod: RepeatEveryPeriod) => {
  const currentIndex = TIME_UNITS_ORDER.indexOf(repeatEveryPeriod);

  const timeUnits = [];
  for (let i = currentIndex; i < TIME_UNITS_ORDER.length; i++) {
    const unit = TIME_UNITS_ORDER[i];
    const value = Math.floor(seconds / repeatEveryPeriodMultiplier[unit]);
    timeUnits.push({ unit, value, maxValue: value });
    seconds -= value * repeatEveryPeriodMultiplier[unit];
  }

  function cropStart(timeUnits: TimeUnit[]) {
    const newTimeUnits = [];

    let fillStarted = false;
    for (let i = 0; i < timeUnits.length; i++) {
      const timeUnit = timeUnits[i];
      if (timeUnit.value === 0 && !fillStarted) {
        continue;
      }
      fillStarted = true;
      newTimeUnits.push(timeUnit);
    }

    return newTimeUnits;
  }

  function cropEnd(timeUnits: TimeUnit[]) {
    const newTimeUnits = [];

    let fillStarted = false;
    for (let i = timeUnits.length - 1; i >= 0; i--) {
      const timeUnit = timeUnits[i];
      if (timeUnit.value === 0 && !fillStarted) {
        continue;
      }
      fillStarted = true;
      newTimeUnits.unshift(timeUnit);
    }

    return newTimeUnits;
  }

  return cropEnd(cropStart(timeUnits));
};

export const putDownMaxValues = (
  timeUnits: TimeUnit[],
  repeatEveryPeriod: RepeatEveryPeriod,
  repeatEveryValue: number
) => {
  for (let i = 0; i < timeUnits.length; i++) {
    const timeUnit = timeUnits[i];
    if (repeatEveryPeriod === timeUnit.unit) {
      timeUnit.maxValue = repeatEveryValue - 1;
    } else {
      timeUnit.maxValue = repeatEveryPeriodToNextPeriodCount[timeUnit.unit] - 1;
    }
  }
  return timeUnits;
};

export const shiftToLower = (timeUnits: TimeUnit[]) => {
  if (timeUnits.length === 1 && timeUnits[0].value === 1) {
    const timeUnit = timeUnits[0];
    const currentIndex = TIME_UNITS_ORDER.indexOf(timeUnit.unit);
    const nextIndex = currentIndex + 1;

    if (TIME_UNITS_ORDER[nextIndex] !== undefined) {
      timeUnit.unit = TIME_UNITS_ORDER[nextIndex];
      timeUnit.value = repeatEveryPeriodToNextPeriodCount[timeUnit.unit];
      timeUnit.maxValue = timeUnit.value;
    }
  }
  return timeUnits;
};

export const reduceTheLastUnitValue = (timeUnits: TimeUnit[]) => {
  if (timeUnits.length) {
    timeUnits[timeUnits.length - 1].value = Math.floor(timeUnits[timeUnits.length - 1].maxValue / 2);
    timeUnits[timeUnits.length - 1].maxValue--;
  }

  return timeUnits;
};

export const timeUnitsToSeconds = (units: TimeUnit[]) =>
  units.reduce((memo, unit) => {
    memo += repeatEveryPeriodMultiplier[unit.unit] * unit.value;

    return memo;
  }, 0);

export const repeatEveryInSeconds = (repeatEveryPeriod: RepeatEveryPeriod, repeatEveryValue: number) => {
  return repeatEveryPeriodMultiplier[repeatEveryPeriod] * repeatEveryValue;
};

export const getDateForDatePicker = (dayJsDate: Dayjs) => {
  const date = new Date();
  // Day of the month needs to be set to 1st day at first to prevent incorrect month increment
  // when selected day of month doesn't exist in current month
  // E.g. selected date is 30th March and current month is Feb, so in this case date.setMonth(2) results in April

  date.setDate(1); // temporary selection to prevent incorrect month increment

  date.setFullYear(dayJsDate.year());
  date.setMonth(dayJsDate.month());
  date.setDate(dayJsDate.date());
  date.setHours(dayJsDate.hour());
  date.setMinutes(dayJsDate.minute());
  date.setSeconds(dayJsDate.second());
  return date;
};
