import { User } from './user/user.types';

export interface NotificationPolicyType {
  id: string;
  step: number;
  notify_by: number | null;
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
