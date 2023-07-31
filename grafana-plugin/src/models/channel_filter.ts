import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { TelegramChannel } from 'models/telegram_channel/telegram_channel.types';

export interface ChannelFilter {
  id: string;
  alert_receive_channel: AlertReceiveChannel['id'];
  slack_channel_id?: SlackChannel['id'];
  telegram_channel?: TelegramChannel['id'];
  escalation_chain?: string;
  created_at: string;
  filtering_term: string;
  is_default: boolean;
}
