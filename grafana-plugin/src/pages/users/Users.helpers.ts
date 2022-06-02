import { User as UserType, UserRole } from 'models/user/user.types';

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

export const getRealFilters = (filters: any) => {
  let realFilters = { ...filters };
  if (!realFilters.roles || !realFilters.roles.length) {
    realFilters = {
      ...filters,
      roles: [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER],
    };
  }

  return realFilters;
};
