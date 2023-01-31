import dayjs from 'dayjs';
import hash from 'object-hash';

const workingMomentsCache = {};

const getKey = (startMoment, endMoment, workingHours, timezone) => {
  return `${startMoment}-${endMoment}-${hash(workingHours)}-${timezone}`;
};

export const getWorkingMoments = (startMoment, endMoment, workingHours, timezone) => {
  const weekdays = dayjs.weekdays();

  const key = getKey(startMoment, endMoment, workingHours, timezone);

  if (workingMomentsCache[key]) {
    return workingMomentsCache[key];
  }

  const momentToStartIteration = dayjs().tz(timezone).utcOffset() === 0 ? startMoment : startMoment.tz(timezone);

  const dayOfWeekToStartIteration = momentToStartIteration.format('dddd');

  const weekDaysToIterateChunk = [
    dayOfWeekToStartIteration,
    ...weekdays.slice(weekdays.indexOf(dayOfWeekToStartIteration) + 1),
    ...weekdays.slice(0, weekdays.indexOf(dayOfWeekToStartIteration)),
  ];

  const weeks = endMoment.diff(startMoment, 'weeks');

  const weekDaysToIterate = [...weekDaysToIterateChunk];
  for (let i = 0; i < weeks; i++) {
    weekDaysToIterate.push(...weekDaysToIterateChunk);
  }

  const workingMoments = [];
  for (const [i, weekday] of weekDaysToIterate.entries()) {
    for (const range of workingHours[weekday.toLowerCase()]) {
      const rangeStartData = range.start;
      const rangeEndData = range.end;
      const [start_HH, start_mm, start_ss] = rangeStartData.split(':');
      const [end_HH, end_mm, end_ss] = rangeEndData.split(':');

      const rangeStartMoment = dayjs(momentToStartIteration)
        .add(i, 'day')
        .set('hour', Number(start_HH))
        .set('minute', Number(start_mm))
        .set('second', Number(start_ss));

      const rangeEndMoment = dayjs(momentToStartIteration)
        .add(i, 'day')
        .set('hour', Number(end_HH))
        .set('minute', Number(end_mm))
        .set('second', Number(end_ss));

      if (rangeEndMoment.isSameOrBefore(startMoment)) {
        continue;
      } else if (rangeStartMoment.isSameOrAfter(endMoment)) {
        continue;
      }

      if (
        rangeStartMoment.isSameOrBefore(startMoment) &&
        rangeEndMoment.isSameOrAfter(startMoment) &&
        rangeEndMoment.isSameOrBefore(endMoment)
      ) {
        workingMoments.push({ start: startMoment, end: rangeEndMoment });
      } else if (
        rangeEndMoment.isSameOrAfter(endMoment) &&
        rangeStartMoment.isSameOrBefore(endMoment) &&
        rangeStartMoment.isSameOrAfter(startMoment)
      ) {
        workingMoments.push({ start: rangeStartMoment, end: endMoment });
      } else {
        workingMoments.push({ start: rangeStartMoment, end: rangeEndMoment });
      }
    }
  }

  workingMomentsCache[key] = workingMoments;

  return workingMoments;
};

export const getNonWorkingMoments = (startMoment, endMoment, workingMoments) => {
  const nonWorkingMoments = [{ start: startMoment, end: endMoment }];

  let lastNonWorkingRange = nonWorkingMoments[0];
  for (const [_i, range] of workingMoments.entries()) {
    lastNonWorkingRange.end = range.start;

    lastNonWorkingRange = { start: range.end, end: undefined };
    nonWorkingMoments.push(lastNonWorkingRange);
  }

  lastNonWorkingRange.end = endMoment;

  return nonWorkingMoments;
};

export const isInWorkingHours = (currentMoment: dayjs.Dayjs, workingHours, timezone) => {
  const timeFormat = 'HH:mm:ss';
  const currentDayOfTheWeek = currentMoment.format('dddd').toLowerCase();
  const workingHourStart = workingHours[currentDayOfTheWeek][0]?.start;
  const workingHourEnd = workingHours[currentDayOfTheWeek][0]?.end;

  if (workingHourStart && workingHourEnd) {
    const startTime = dayjs(workingHourStart, timeFormat).tz(timezone).format(timeFormat);
    const endTime = dayjs(workingHourEnd, timeFormat).tz(timezone).format(timeFormat);
    const currentTime = dayjs(currentMoment, timeFormat).format(timeFormat);

    return currentTime < endTime && currentTime >= startTime;
  }

  return false;
};
