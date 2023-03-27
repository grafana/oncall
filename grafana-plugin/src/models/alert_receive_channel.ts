import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Heartbeat } from 'models/heartbeat/heartbeat.types';

import { UserDTO as User } from './user';

export enum MaintenanceMode {
  Debug,
  Maintenance,
}

export interface AlertReceiveChannel {
  id: string;
  integration: number;
  smile_code: string;
  verbal_name: string;
  author: User['pk'];
  team: GrafanaTeam['id'];
  created_at: string;
  integration_url: string;
  allow_source_based_resolving: boolean;
  is_able_to_autoresolve: boolean;
  default_channel_filter: number;
  instructions: string;
  demo_alert_enabled: boolean;
  maintenance_mode?: MaintenanceMode;
  heartbeat: Heartbeat | null;
  is_available_for_integration_heartbeat: boolean;
}

export interface AlertReceiveChannelChoice {
  display_name: string;
  value: number;
}

export const MaintenanceIntegration = 24;
