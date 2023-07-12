import { SlackChannel } from 'models/slack_channel/slack_channel.types';

export interface Team {
  pk: string;
  banner: {
    title: string;
    body: string;
  };
  telegram_configuration: {
    channel_chat_id: number;
    channel_name: string;
    discussion_group_chat_id: number; // TODO check if string
    discussion_group_name: string;
  };
  name: string;
  slack_team_identity: {
    general_log_channel_id: string;
    general_log_channel_pk: string;
    cached_name: string;
  };

  slack_channel: SlackChannel | null;

  // ex team settings
  is_resolution_note_required: boolean;

  env_status: {
    telegram_configured: boolean;
    phone_provider: {
      configured: boolean;
      test_call: boolean;
      test_sms: boolean;
      verification_call: boolean;
      verification_sms: boolean;
    };
  };
}
