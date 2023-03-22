import { SelectOption } from 'state/types';

export interface FiltersValues {
  [key: string]: any;
}

export interface FilterOption {
  name: string;
  type: 'search' | 'options' | 'boolean' | 'daterange' | 'team_select';
  href?: string;
  options?: SelectOption[];
  default?: { value: string };
}
