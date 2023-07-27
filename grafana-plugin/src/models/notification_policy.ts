import { UserDTO as User } from './user';

export interface NotificationPolicyType {
  id: string;
  step: number;
  notify_by: User['pk'] | null;
  wait_delay: string | null;
  important: boolean;
  user: User['pk'];
}

export function prepareNotificationPolicy(value: NotificationPolicyType): NotificationPolicyType {
  return {
    ...value,
    notify_by: null,
    wait_delay: null,
  };
}
