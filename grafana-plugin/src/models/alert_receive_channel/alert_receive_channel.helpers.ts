import { ApiSchemas } from 'network/oncall-api/api.types';

export function getAlertReceiveChannelDisplayName(
  alertReceiveChannel?: ApiSchemas['AlertReceiveChannel'],
  withDescription = true
) {
  if (!alertReceiveChannel) {
    return '';
  }

  return withDescription && alertReceiveChannel.description
    ? `${alertReceiveChannel.verbal_name} (${alertReceiveChannel.description})`
    : alertReceiveChannel.verbal_name;
}
