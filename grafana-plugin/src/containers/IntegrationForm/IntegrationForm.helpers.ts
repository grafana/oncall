import { AlertReceiveChannel } from 'models/alert_receive_channel';

export function prepareForEdit(item: AlertReceiveChannel) {
  return {
    verbal_name: item.verbal_name,
    team: item.team,
  };
}
