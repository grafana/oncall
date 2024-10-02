export interface TelegramChannel {
  id: string;
  channel_chat_id: string;
  channel_name: string;
  discussion_group_chat_id: string;
  discussion_group_name: string;
  is_default_channel: false;
}

export interface TelegramChannelDetails {
  display_name: string;
  id: string;
}
