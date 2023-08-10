import { IRMPlanStatus } from 'models/alertgroup/alertgroup.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Heartbeat } from 'models/heartbeat/heartbeat.types';
import { User } from 'models/user/user.types';

export enum MaintenanceMode {
  Debug = 0,
  Maintenance = 1,
}

export interface AlertReceiveChannelOption {
  display_name: string;
  value: string;
  featured: boolean;
  short_description: string;
  featured_tag_name: string;
}

export interface AlertReceiveChannelCounters {
  alerts_count: number;
  alert_groups_count: number;
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
  status: IRMPlanStatus;
  integration_url: string;
  inbound_email: string;
  allow_source_based_resolving: boolean;
  is_able_to_autoresolve: boolean;
  is_based_on_alertmanager: boolean;
  default_channel_filter: number;
  instructions: string;
  demo_alert_enabled: boolean;
  demo_alert_payload: any;
  maintenance_mode?: MaintenanceMode;
  maintenance_till?: number;
  heartbeat: Heartbeat | null;
  is_available_for_integration_heartbeat: boolean;
  routes_count: number;
  connected_escalations_chains_count: number;
  allow_delete: boolean;
  deleted?: boolean;
}

export interface AlertReceiveChannelChoice {
  display_name: string;
  value: number;
}

export interface ContactPoint {
  dataSourceName: string;
  dataSourceId: string;
  contactPoint: string;
  notificationConnected: boolean;
}
