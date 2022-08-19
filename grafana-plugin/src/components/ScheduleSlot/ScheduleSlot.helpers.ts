import dayjs from 'dayjs';

import { Shift } from 'models/schedule/schedule.types';
import { User } from 'models/user/user.types';

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

export const getTitle = (user: User) => {
  return user ? user.username.split(' ')[0] : null;
  return user
    ? user.username
        .split(' ')
        .map((word) => word.charAt(0).toUpperCase())
        .join('')
    : null;
};

export const getOuRanges = (shift: Shift, user: User) => {};
