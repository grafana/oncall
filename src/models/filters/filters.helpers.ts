import { convertRelativeToAbsoluteDate } from 'helpers/datetime';

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

export const convertFiltersToBackendFormat = (filters: FiltersValues = {}, filterOptions: FilterOption[] = []) => {
  const newFilters = { ...filters };
  filterOptions.forEach((filterOption) => {
    if (filterOption.type === 'daterange' && newFilters[filterOption.name]) {
      newFilters[filterOption.name] = convertRelativeToAbsoluteDate(filters[filterOption.name]);
    }
  });
  return newFilters;
};
