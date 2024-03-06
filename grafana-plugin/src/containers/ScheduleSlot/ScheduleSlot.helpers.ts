import { ApiSchemas } from 'network/oncall-api/api.types';

export const getTitle = (user: ApiSchemas['User']) => {
  return user ? user.username.split(' ')[0] : null;
};
