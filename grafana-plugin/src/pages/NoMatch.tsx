import React, { useEffect, useMemo } from 'react';

import qs from 'query-string';
import { useNavigate } from 'react-router-dom';

import { DEFAULT_PAGE, PLUGIN_ROOT } from 'utils/consts';
import { getPathFromQueryParams } from 'utils/url';

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
