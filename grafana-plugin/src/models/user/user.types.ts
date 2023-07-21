import { Timezone } from 'models/timezone/timezone.types';

export interface MessagingBackends {
  [key: string]: any;
}

export interface User {
  pk: string;
  slack_login: string;
  email: string;
  phone: string;
  avatar: string;
  name: string;
  company: string;
  hide_phone_number: boolean;
  role_in_company: string;
  username: string;
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
    name: string;
    slack_id: string;
    slack_login: string;
  } | null;
  post_onboarding_entry_allowed: any;
  current_team: string | null;
  onboarding_conversation_data: {
    image_link: string | null;
    inviter_name: string | null;
    video_conference_link: string | null;
  };
  trigger_video_call?: boolean;
  export_url?: string;
  status?: number;
  link?: string;
  cloud_connection_status?: number;
  hidden_fields?: boolean;
  timezone: Timezone;
  working_hours: { [key: string]: [] };
}
