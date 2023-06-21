import { User } from 'models/user/user.types';

export interface ScheduleFiltersType {
  users: Array<User['pk']>;
}
