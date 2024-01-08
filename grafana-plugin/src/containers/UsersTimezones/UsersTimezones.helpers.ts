import { Dayjs } from 'dayjs';

export const calculateTimePassedInDayPercentage = (date: Dayjs) => {
  const midnight = date.startOf('day');
  return (date.diff(midnight, 'minutes') / 1_440) * 100;
};
