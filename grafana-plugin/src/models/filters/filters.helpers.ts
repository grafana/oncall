import { convertRelativeToAbsoluteDate } from 'utils/datetime';

import { FilterOption, FiltersValues } from './filters.types';

export const getApiPathByPage = (page: string) => {
  return (
    {
      outgoing_webhooks: 'custom_buttons',
      incidents: 'alertgroups',
      integrations: 'alert_receive_channels',
    }[page] || page
  );
};

export const normalizeFilters = (filters: FiltersValues, filterOptions: FilterOption[]) => {
  const normalizeFilters = { ...filters };
  filterOptions.forEach((filterOption) => {
    if (filterOption.type === 'daterange' && normalizeFilters[filterOption.name]) {
      normalizeFilters[filterOption.name] = convertRelativeToAbsoluteDate(filters[filterOption.name]);
    }
  });
  return normalizeFilters;
};
