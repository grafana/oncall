import { UserRole } from 'models/user/user.types';

export const DEFAULT_USER_ROLES = [
  { display_name: 'Admin', value: UserRole.ADMIN },
  { display_name: 'Editor', value: UserRole.EDITOR },
  {
    display_name: 'Viewer',
    value: UserRole.VIEWER,
  },
];
