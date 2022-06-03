import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { SelectOption } from 'state/types';

export interface IncidentsFiltersType {}

export interface FilterOption {
  name: string;
  type: 'search' | 'options' | 'boolean' | 'daterange';
  href?: string;
  options?: SelectOption[];
  default?: { value: string };
}
