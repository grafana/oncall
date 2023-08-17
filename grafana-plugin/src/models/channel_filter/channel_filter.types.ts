import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { TelegramChannel, TelegramChannelDetails } from 'models/telegram_channel/telegram_channel.types';

export enum FilteringTermType {
  regex,
  jinja2,
}

export interface ChannelFilter {
  id: string;
  alert_receive_channel: AlertReceiveChannel['id'];
  slack_channel_id?: SlackChannel['id'];
  slack_channel?: SlackChannel;
  telegram_channel?: TelegramChannel['id'];
  telegram_channel_details?: TelegramChannelDetails;
  created_at: string;
  filtering_term: string;
  filtering_term_as_jinja2: string;
  filtering_term_type: FilteringTermType;
  is_default: boolean;
  notify_in_slack: boolean;
  notify_in_telegram: boolean;
  notification_backends: {
    [key: string]: any;
  } | null;
  escalation_chain: EscalationChain['id'];
}
