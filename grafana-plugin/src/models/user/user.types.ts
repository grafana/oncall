import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Timezone } from 'models/timezone/timezone.types';

export interface MessagingBackends {
  [key: string]: any;
}

interface BaseUser {
  pk: string;
  name: string;
  username: string;
  avatar: string;
  avatar_full: string;
}

export interface User extends BaseUser {
  slack_login: string;
  email: string;
  phone: string;
  display_name: string;
  hide_phone_number: boolean;
  slack_id: string;
  phone_verified: boolean;
  telegram_configuration: {
    telegram_nick_name: string;
    telegram_chat_id: number; // TODO check if string
  };
  messaging_backends: MessagingBackends;
  notification_chain_verbal: {
    default: string;
    important: string;
  };
  verified_phone_number?: string;
  unverified_phone_number?: string;
  slack_user_identity: {
    avatar: string;
    display_name: string;
    name: string;
    slack_id: string;
    slack_login: string;
  } | null;
  current_team: string | null;
  export_url?: string;
  status?: number;
  link?: string;
  cloud_connection_status?: number;
  hidden_fields?: boolean;
  timezone: Timezone;
  working_hours: { [key: string]: [] };
}

export interface PagedUser extends BaseUser {
  important: boolean;
}

export interface UserCurrentlyOnCall extends BaseUser {
  timezone: Timezone;
  is_currently_oncall: boolean;
  teams: GrafanaTeam[];
}
