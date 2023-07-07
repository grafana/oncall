import { Choice } from './types';
import { UserDTO as User } from './user';

export interface NotificationPolicyType {
  id: string;
  step: number;
  notify_by: User['pk'] | null;
  wait_delay: string | null;
  important: boolean;
  user: User['pk'];
}

type BaseNotificationChoice = {
  label: string;
  read_only: boolean;
  required: boolean;
};

interface NotificationChoiceNonChoiceType extends BaseNotificationChoice {
  type: 'string' | 'boolean' | 'integer' | 'field';
}

interface NotificationChoiceChoiceType extends BaseNotificationChoice {
  choices: Choice[];
  type: 'choice';
}

type NotificationChoice = NotificationChoiceNonChoiceType | NotificationChoiceChoiceType;

export type NotificationChoices = Record<keyof NotificationPolicyType, NotificationChoice>;

export type NotifyByOption = {
  value: number;
  display_name: string;
  slack_integration_required: boolean;
  telegram_integration_required: boolean;
};

export function prepareNotificationPolicy(value: NotificationPolicyType): NotificationPolicyType {
  return {
    ...value,
    notify_by: null,
    wait_delay: null,
  };
}
