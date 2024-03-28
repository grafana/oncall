import { Dayjs } from 'dayjs';

export const calculateTimePassedInDayPercentage = (date: Dayjs) => {
  const midnight = date.startOf('day');
  return (date.diff(midnight, 'minutes') / (60 * 24)) * 100;
};
