import { AlertReceiveChannel } from './alert_receive_channel.types';

export function getAlertReceiveChannelDisplayName(alertReceiveChannel?: AlertReceiveChannel, withDescription = true) {
  if (!alertReceiveChannel) {
    return '';
  }

  return withDescription && alertReceiveChannel.description
    ? `${alertReceiveChannel.verbal_name} (${alertReceiveChannel.description})`
    : alertReceiveChannel.verbal_name;
}
