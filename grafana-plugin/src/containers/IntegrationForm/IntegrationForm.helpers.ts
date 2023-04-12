import { AlertReceiveChannel } from 'models/alert_receive_channel';

export function prepareForEdit(item: AlertReceiveChannel) {
  return {
    verbal_name: item.verbal_name,
    // description: item.description,
    team: item.team,
  };
}
