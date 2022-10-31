import { convertRelativeToAbsoluteDate } from 'utils/datetime';

import { FilterOption } from './IncidentFilters.types';

export function parseFilters(query: { [key: string]: any }, filterOptions: FilterOption[]) {
  const filters = filterOptions.filter((filterOption: FilterOption) => filterOption.name in query);

  const values = filters.reduce((memo: any, filterOption: FilterOption) => {
    const rawValue = query[filterOption.name];
    let value: any = rawValue;
    if (filterOption.type === 'options') {
      if (!Array.isArray(rawValue)) {
        value = [rawValue];
      }
      value = value.map((item: string) => (!isNaN(Number(item)) ? Number(item) : item));
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
