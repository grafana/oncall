import { convertRelativeToAbsoluteDate } from 'utils/datetime';

import { FilterOption } from './RemoteFilters.types';

const normalize = (value: any) => {
  if (!isNaN(Number(value))) {
    return Number(value);
  }

  return value;
};

export function parseFilters(query: { [key: string]: any }, filterOptions: FilterOption[]) {
  const filters = filterOptions.filter((filterOption: FilterOption) => filterOption.name in query);

  const values = filters.reduce((memo: any, filterOption: FilterOption) => {
    const rawValue = query[filterOption.name];
    let value: any = rawValue;
    if (filterOption.type === 'options' || filterOption.type === 'team_select') {
      if (!Array.isArray(rawValue)) {
        value = [rawValue];
      }
      value = value.map(normalize);
    } else if (filterOption.type === 'daterange') {
      value = convertRelativeToAbsoluteDate(value);
    } else if (rawValue === 'true') {
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
