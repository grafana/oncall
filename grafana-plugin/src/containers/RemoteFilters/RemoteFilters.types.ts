import { SelectOption } from 'state/types';

export interface RemoteFiltersType {}

export interface FilterOption {
  name: string;
  display_name?: string;
  type: 'search' | 'options' | 'boolean' | 'daterange' | 'team_select' | 'labels' | 'alert_group_labels';
  href?: string;
  options?: SelectOption[];
  default?: { value: string };
  global?: boolean;
  description?: string;
}
