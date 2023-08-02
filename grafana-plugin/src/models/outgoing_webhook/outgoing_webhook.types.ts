import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

export interface OutgoingWebhook {
  authorization_header: string;
  data: string;
  forward_all: boolean;
  http_method: string;
  id: string;
  name: string;
  password: string;
  team: GrafanaTeam['id'];
  trigger_type: number;
  trigger_type_name: string;
  url: string;
  username: null;
  headers: string;
  trigger_template: string;
  last_response_log?: OutgoingWebhookResponse;
  is_webhook_enabled: boolean;
  is_legacy: boolean;
}

export interface OutgoingWebhookResponse {
  timestamp: string;
  url: string;
  request_trigger: string;
  request_headers: string;
  request_data: string;
  status_code: string;
  content: string;
  event_data: string;
}
