import { User as UserType } from 'models/user/user.types';

export const getUserRowClassNameFn = (userPkToEdit?: UserType['pk'], currentUserPk?: UserType['pk']) => {
  return (user: UserType) => {
    if (user.pk === currentUserPk) {
      return 'highlighted-row';
    }

    if (user.pk === userPkToEdit) {
      return 'highlighted-row';
    }

    return '';
  };
};
