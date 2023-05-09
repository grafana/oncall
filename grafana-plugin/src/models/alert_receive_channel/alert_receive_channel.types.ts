import { IRMPlanStatus } from 'models/alertgroup/alertgroup.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Heartbeat } from 'models/heartbeat/heartbeat.types';
import { UserDTO as User } from 'models/user';

export enum MaintenanceMode {
  Debug = 0,
  Maintenance = 1,
}

export interface AlertReceiveChannel {
  id: string;
  integration: any;
  smile_code: string;
  verbal_name: string;
  description: string;
  description_short: string;
  author: User['pk'];
  team: GrafanaTeam['id'];
  created_at: string;
  status: IRMPlanStatus;
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
  allow_delete: boolean;
  deleted?: boolean;
}

export interface AlertReceiveChannelOption {
  display_name: string;
  value: number;
  featured: boolean;
  short_description: string;
}

export interface AlertReceiveChannelCounters {
  alerts_count: number;
  alert_groups_count: number;
}
