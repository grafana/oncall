import { AlertReceiveChannel } from './alert_receive_channel.types';

export const getAlertReceiveChannelDisplayName = (
  alertReceiveChannel?: AlertReceiveChannel,
  withDescription = true
) => {
  if (!alertReceiveChannel) {
    return '';
  }

  const { description, verbal_name } = alertReceiveChannel;
  return withDescription && description ? `${verbal_name} (${description})` : verbal_name;
};
