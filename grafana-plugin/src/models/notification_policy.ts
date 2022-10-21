import { UserDTO as User } from './user';

export interface NotificationPolicyType {
  id: string;
  order: number;
  step: number;
  notify_by: User['pk'] | null;
  wait_delay: string | null;
  important: boolean;
  user: User['pk'];
}

export const prepareNotificationPolicy = (value: NotificationPolicyType): NotificationPolicyType => ({
  ...value,
  notify_by: null,
  wait_delay: null,
});
