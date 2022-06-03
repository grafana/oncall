import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';

export interface Heartbeat {
  id: string;
  last_heartbeat_time_verbal: string;
  alert_receive_channel: AlertReceiveChannel['id'];
  link: string;
  timeout_seconds: number;
  status: boolean;
  instruction: string;
}
