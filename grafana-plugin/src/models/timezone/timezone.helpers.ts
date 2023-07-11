import dayjs from 'dayjs';

export const allTimezones = Intl.supportedValuesOf('timeZone');

export const getTzOffsetString = (moment: dayjs.Dayjs) => {
  const userOffset = moment.utcOffset();
  const userOffsetHours = userOffset / 60;
  const userOffsetHoursStr =
    userOffsetHours > 0 ? `+${userOffsetHours} GMT` : userOffset < 0 ? `${userOffsetHours} GMT` : `GMT`;

  return userOffsetHoursStr;
};
