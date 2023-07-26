import qs, { ParsedQuery } from 'query-string';

import { PLUGIN_ROOT } from './consts';

export function getPathFromQueryParams(query: ParsedQuery<string>) {
  const normalizedQuery = { ...query };

  let path = PLUGIN_ROOT;
  if (normalizedQuery.page) {
    path += `/${normalizedQuery.page}`;

    if (normalizedQuery.id) {
      if (normalizedQuery.page === 'incident' || normalizedQuery.page === 'schedule') {
        path += 's';
      }

      path += `/${normalizedQuery.id}`;
      delete normalizedQuery['id'];
    }

    delete normalizedQuery['page'];
  }

  if (Object.keys(normalizedQuery).length) {
    const query = qs.stringify(normalizedQuery);
    path += `?` + query;
  }

  return path;
}
