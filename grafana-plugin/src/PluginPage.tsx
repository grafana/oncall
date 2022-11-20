import React from 'react';

import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';
import Header from 'navbar/Header/Header';

import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';
import { useQueryParams } from 'utils/hooks';

export const PluginPage = (isTopNavbar() ? RealPlugin : PluginPageFallback) as React.ComponentType<PluginPageProps>;

function RealPlugin(props: PluginPageProps): React.ReactNode {
  const store = useStore();

  const queryParams = useQueryParams();
  const page = queryParams.get('page');

  return (
    <RealPluginPage {...props}>
      <Header page={page} backendLicense={store.backendLicense} />
      {props.children}
    </RealPluginPage>
  );
}

function PluginPageFallback(props: PluginPageProps): React.ReactNode {
  return props.children;
}
