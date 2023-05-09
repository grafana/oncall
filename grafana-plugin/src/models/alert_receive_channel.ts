import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Heartbeat } from 'models/heartbeat/heartbeat.types';

import { UserDTO as User } from './user';

export enum MaintenanceMode {
  Debug,
  Maintenance,
}

export interface AlertReceiveChannel {
  id: string;
  integration: string;
  smile_code: string;
  verbal_name: string;
  description: string;
  description_short: string;
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
  maintenance_till?: number;
  heartbeat: Heartbeat | null;
  is_available_for_integration_heartbeat: boolean;
  routes_count: number;
}

export interface AlertReceiveChannelChoice {
  display_name: string;
  value: number;
}
