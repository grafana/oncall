import { SlackChannel } from 'models/slack_channel/slack_channel.types';

export enum SubscriptionStatus {
  OK,
  VIOLATION,
  HARD_VIOLATION,
}

export interface Limit {
  left: number;
  limit_title: string;
  total: number;
}

export interface Team {
  pk: string;
  is_free_version: boolean;
  limits: {
    period_title: string;
    show_limits_popup: boolean;
    limits_to_show: Limit[];
    show_limits_warning: boolean;
    warning_text: string;
  };
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
  name_slug: string;
  slack_team_identity: {
    general_log_channel_id: string;
    general_log_channel_pk: string;
    cached_name: string;
  };

  slack_channel: SlackChannel | null;

  number_of_employees: number;

  subscription_status: SubscriptionStatus;

  stats: {
    alerts_count: number;
    average_response_time: string;
    grouped_percent: number;
    noise_reduction: number;
    verbal_time_saved_by_amixr: string;
  };

  incident_retention_web_report: {
    num_month_available: number;
    incidents_hidden: number;
  } | null;

  // ex team settings
  archive_alerts_from: string;
  is_resolution_note_required: boolean;

  env_status: {
    twilio_configured: boolean;
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
