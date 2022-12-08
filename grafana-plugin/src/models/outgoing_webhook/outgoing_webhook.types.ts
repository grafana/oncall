export interface OutgoingWebhook {
  authorization_header: string;
  data: string;
  forward_all: boolean;
  http_method: string;
  id: string;
  last_run: string;
  name: string;
  password: string;
  team: null;
  trigger_type: number;
  trigger_type_name: string;
  url: string;
  username: null;
  headers: string;
  trigger_template: string;
  last_status_log?: OutgoingWebhookLog;
}

export interface OutgoingWebhookLog {
  last_run_at: string;
  input_data: string;
  url: string;
  trigger: string;
  headers: string;
  data: string;
  response_status: string;
  response: string;
}
