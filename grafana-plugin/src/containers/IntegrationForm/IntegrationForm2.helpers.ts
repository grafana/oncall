import { AlertReceiveChannel } from 'models/alert_receive_channel';

export function prepareForEdit(item: AlertReceiveChannel) {
  return {
    verbal_name: item.verbal_name,
    description_short: item.description_short,
    team: item.team,
  };
}
