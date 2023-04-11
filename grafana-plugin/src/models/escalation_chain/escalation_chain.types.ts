import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
export interface EscalationChain {
  id: string;
  pk: string; //? because GET related_escalation_chains returns {name,pk}[]
  is_default: boolean;
  name: string;
  number_of_integrations: number;
  number_of_routes: number;
  team: GrafanaTeam['id'];
}

export interface EscalationChainDetails {
  id: string;
  display_name: string;
  channel_filters: Array<{
    id: string;
    display_name: string;
  }>;
  team: string;
}
