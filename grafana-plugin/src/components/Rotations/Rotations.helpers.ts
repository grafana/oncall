import dayjs from 'dayjs';

export const getRandomTimeslots = (count: number = 6) => {
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
      users: [getRandomUser(), getRandomUser()],
    });
  }
  return slots;
};

const L1_COLORS = [
  '#3D71D9',
  '#1A6BE8',
  '#6D609C',
  '#50639C',
  '#8214A0',
  '#44449F',
  '#4D3B72',
  '#273C6C',
];

const L2_COLORS = [
  '#3CB979',
  '#A49E7C',
  '#188343',
  '#746D46',
  '#84362A',
  '#464121',
  '#521913',
  '#414130',
];

const L3_COLORS = [
  '#377277',
  '#797B83',
  '#638282',
  '#626779',
  '#364E4E',
  '#47494F',
  '#423220',
  '#44321D',
];

const OVERRIDE_COLORS = ['#C69B06', '#797B83', '#638282', '#626779'];

const COLORS = [L1_COLORS, L2_COLORS, L3_COLORS, OVERRIDE_COLORS];

export const getColor = (layerIndex: number, rotationIndex) => {
  return COLORS[layerIndex][rotationIndex];
};

const USERS = [
  'Innokentii Konstantinov',
  'Ildar Iskhakov',
  'Matias Bordese',
  'Michael Derynck',
  'Vadim Stepanov',
  'Matvey Kukuy',
  'Yulya Artyukhina',
  'Raphael Batyrbaev',
];

export const getRandomUser = () => {
  return USERS[Math.floor(Math.random() * USERS.length)];
};

export const getLabel = (layerIndex: number, rotationIndex) => {
  return `L ${layerIndex + 1}-${rotationIndex + 1}`;
};
