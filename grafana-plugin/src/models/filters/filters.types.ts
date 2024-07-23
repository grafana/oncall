import React from 'react';

import { SelectOption } from 'state/types';

export interface FiltersValues {
  [key: string]: any;
}

export interface FilterExtraInformationValues {
  isClearable?: boolean;
  value?: any;
  portal?: React.RefObject<any>;
  showInputLabel?: boolean;
}

export interface FilterExtraInformation {
  [key: string]: FilterExtraInformationValues;
}

export interface FilterOption {
  name: string;
  type: 'search' | 'options' | 'boolean' | 'daterange' | 'team_select';
  href?: string;
  options?: SelectOption[];
  default?: { value: string };
}
