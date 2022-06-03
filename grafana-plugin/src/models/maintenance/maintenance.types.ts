import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';

export enum MaintenanceType {
  alert_receive_channel = 'alert_receive_channel',
  organization = 'organization',
}

export enum MaintenanceMode {
  Debug,
  Maintenance,
}

export interface Maintenance {
  alert_receive_channel_id: AlertReceiveChannel['id'];
  type: MaintenanceType;
  maintenance_mode: MaintenanceMode;
  maintenance_till_timestamp: number;
  started_at_timestamp: number;
}
