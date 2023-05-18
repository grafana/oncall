import { AlertReceiveChannel } from './alert_receive_channel/alert_receive_channel.types';

export interface ActionDTO {
  id: string;
  name: string;
  webhook: string;
  user: string;
  password: string;
  alert_receive_channel: AlertReceiveChannel['id'];
  data: string;
  authorization_header: string;
}
