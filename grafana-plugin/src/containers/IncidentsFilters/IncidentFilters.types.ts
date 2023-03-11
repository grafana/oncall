import { SelectOption } from 'state/types';

export interface IncidentsFiltersType {}

export interface FilterOption {
  name: string;
  type: 'search' | 'options' | 'boolean' | 'daterange' | 'team_select';
  href?: string;
  options?: SelectOption[];
  default?: { value: string };
}
