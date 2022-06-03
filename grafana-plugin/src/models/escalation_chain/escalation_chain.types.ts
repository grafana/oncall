export interface EscalationChain {
  id: string;
  is_default: boolean;
  name: string;
  number_of_integrations: number;
  number_of_routes: number;
}

export interface EscalationChainDetails {
  id: string;
  display_name: string;
  channel_filters: Array<{
    id: string;
    display_name: string;
  }>;
}
