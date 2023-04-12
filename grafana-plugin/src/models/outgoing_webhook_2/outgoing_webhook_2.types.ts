import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

export interface OutgoingWebhook2 {
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
  last_response_log?: OutgoingWebhook2Response;
  is_webhook_enabled: boolean;
}

export interface OutgoingWebhook2Response {
  timestamp: string;
  url: string;
  request_trigger: string;
  request_headers: string;
  request_data: string;
  status_code: string;
  content: string;
}
