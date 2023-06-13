import { Schedule } from 'models/schedule/schedule.types';
import { User } from 'models/user/user.types';

export interface ManualAlertGroupPayload {
  users: Array<{ id: User['pk']; important: boolean }>;
  schedules: Array<{ id: Schedule['id']; important: boolean }>;
}
