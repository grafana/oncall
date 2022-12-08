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
  url: string;
  username: null;
}
