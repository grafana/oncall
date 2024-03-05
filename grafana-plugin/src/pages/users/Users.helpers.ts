import { ApiSchemas } from 'network/oncall-api/api.types';

export const getUserRowClassNameFn = (
  userPkToEdit?: ApiSchemas['User']['pk'],
  currentUserPk?: ApiSchemas['User']['pk']
) => {
  return (user: ApiSchemas['User']) => {
    if (user.pk === currentUserPk) {
      return 'highlighted-row';
    }

    if (user.pk === userPkToEdit) {
      return 'highlighted-row';
    }

    return '';
  };
};
