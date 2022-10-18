import { AppRootProps } from '@grafana/data';
import { config } from '@grafana/runtime';

import React, { useMemo } from 'react';
import { Route, Switch } from 'react-router-dom';

import { useNavModel } from 'utils/hooks';

import { pages } from 'pages';

export function App(props: AppRootProps) {
  if (!config.featureToggles.topnav) {
    useNavModel(props as any);
  }

  return (
    <Switch>
      {pages.map((page) => (
        <Route exact path={page.path} component={page.component} />
      ))}
    </Switch>
  );
}
