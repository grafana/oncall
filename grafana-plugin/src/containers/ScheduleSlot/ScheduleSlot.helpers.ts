import { User } from 'models/user/user.types';

export const getTitle = (user: User) => {
  return user ? user.username.split(' ')[0] : null;
};
