import React, { useEffect, useMemo } from 'react';

import { DEFAULT_PAGE, PLUGIN_ROOT } from 'helpers/consts';
import { getPathFromQueryParams } from 'helpers/url';
import qs from 'query-string';
import { useNavigate } from 'react-router-dom-v5-compat';

export const NoMatch = () => {
  const navigate = useNavigate();

  const query = useMemo(() => qs.parse(window.location.search), [window.location.search]);

  useEffect(() => {
    if (query.page) {
      const path = getPathFromQueryParams(query);
      navigate(path);
    } else {
      navigate(`${PLUGIN_ROOT}/${DEFAULT_PAGE}`);
    }
  }, [query]);

  return <div>Not Found</div>;
};
