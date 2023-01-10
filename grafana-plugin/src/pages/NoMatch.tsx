import React, { useEffect, useMemo } from 'react';

import qs from 'query-string';
import { useHistory } from 'react-router-dom';

import { DEFAULT_PAGE, PLUGIN_ROOT } from 'utils/consts';
import { getPathFromQueryParams } from 'utils/url';

const NoMatch = () => {
  const history = useHistory();

  const query = useMemo(() => qs.parse(window.location.search), [window.location.search]);

  useEffect(() => {
    if (query.page) {
      const path = getPathFromQueryParams(query);
      history.push(path);
    } else {
      history.push(`${PLUGIN_ROOT}/${DEFAULT_PAGE}`);
    }
  }, [query]);

  return <div>Not Found</div>;
};

export default NoMatch;
