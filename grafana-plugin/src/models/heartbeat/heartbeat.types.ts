import { ApiSchemas } from 'network/oncall-api/api.types';

export interface Heartbeat {
  id: string;
  last_heartbeat_time_verbal: string;
  alert_receive_channel: ApiSchemas['AlertReceiveChannel']['id'];
  link: string;
  timeout_seconds: number;
  status: boolean;
  instruction: string;
}
