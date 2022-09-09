import dayjs from 'dayjs';

import { getColor, getOverrideColor, getRandomUser } from 'components/Rotations/Rotations.helpers';
import { getRandomUsers } from 'pages/schedule/Schedule.helpers';

export const getRandomSchedules = () => {
  const schedules = [];
  for (let i = 0; i < 20; i++) {
    schedules.push({
      id: i + 1,
      name: `Schedule Team ${i + 1}`,
      users: getRandomUsers(2),
      chatOps: '#irm-incidents-primary',
      quality: 20 + Math.floor(Math.random() * 80),
    });
  }

  return schedules;
};

export const getRandomTimeslots = (count = 6) => {
  const slots = [];
  for (let i = 0; i < count; i++) {
    const start = dayjs()
      .startOf('day')
      .add(i * 4, 'hour');
    const end = dayjs()
      .startOf('day')
      .add(i * 4 + 2, 'hour');
    //const inactive = end.isBefore(dayjs());
    const inactive = false;

    slots.push({
      start,
      end,
      inactive,
      users: [getRandomUser()],
      color: getOverrideColor(i),
    });
  }
  return slots;
};
