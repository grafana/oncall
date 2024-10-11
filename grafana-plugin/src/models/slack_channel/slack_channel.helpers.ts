import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';

export const getSlackChannelName = (channel?: SlackChannel | null): string | undefined => {
  if (!channel) {
    return undefined;
  }
  if (!channel.display_name) {
    return PRIVATE_CHANNEL_NAME;
  }

  return channel.display_name;
};
