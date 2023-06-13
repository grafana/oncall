import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

export interface OutgoingWebhook {
  authorization_header: string;
  data: string;
  forward_whole_payload: boolean;
  id: string;
  name: string;
  password: string;
  team: GrafanaTeam['id'];
  user: null;
  webhook: string;
}
