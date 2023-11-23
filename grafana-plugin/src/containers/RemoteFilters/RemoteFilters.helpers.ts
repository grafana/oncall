import { convertRelativeToAbsoluteDate } from 'utils/datetime';

import { FilterOption } from './RemoteFilters.types';

const normalize = (value: any) => {
  if (!isNaN(Number(value))) {
    return Number(value);
  }

  return value;
};

export function parseFilters(
  data: { [key: string]: any },
  filterOptions: FilterOption[],
  query: { [key: string]: any }
) {
  const dataWithPredefinedTeams = { ...data, team: data.team || [] };
  const filters = filterOptions.filter((filterOption: FilterOption) => filterOption.name in dataWithPredefinedTeams);

  const values = filters.reduce((memo: any, filterOption: FilterOption) => {
    const rawValue = query[filterOption.name] || dataWithPredefinedTeams[filterOption.name]; // query takes priority over local storage

    let value: any = rawValue;

    if (
      filterOption.type === 'options' ||
      filterOption.type === 'team_select' ||
      filterOption.type === 'labels' ||
      filterOption.type === 'alert_group_labels'
    ) {
      if (!Array.isArray(rawValue)) {
        value = [rawValue];
      }
      value = value.map(normalize);
    } else if (filterOption.type === 'daterange') {
      value = convertRelativeToAbsoluteDate(value);
    } else if ((filterOption.type === 'boolean' && rawValue === '') || rawValue === 'true') {
      value = true;
    } else if (rawValue === 'false') {
      value = false;
    }

    return {
      ...memo,
      [filterOption.name]: value,
    };
  }, {});

  return { filters, values };
}
