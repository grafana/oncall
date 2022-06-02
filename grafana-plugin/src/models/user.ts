import { UserAction } from 'state/userAction';

import { UserRole } from './user/user.types';

export interface UserDTO {
  pk: number;
  slack_login: string;
  email: string;
  phone: string;
  avatar: string;
  name: string;
  company: string;
  role_in_company: string;
  username: string;
  slack_id: string;
  verified_phone_number?: string;
  unverified_phone_number?: string;
  phone_verified: boolean;
  role: UserRole;
  telegram_configuration: {
    telegram_nick_name: string;
    telegram_chat_id: number;
  };
  slack_user_identity: any;
  post_onboarding_entry_allowed: any;
  teams: [];
  onboarding_conversation_data: {
    image_link: string | null;
    inviter_name: string | null;
    video_conference_link: string | null;
  };
  permissions: UserAction[];
  trigger_video_call?: boolean;
}
