import React from 'react';

import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';
import Header from 'navbar/Header/Header';

import { pages } from 'pages';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';
import { useQueryParams } from 'utils/hooks';

export const PluginPage = (isTopNavbar() ? RealPlugin : PluginPageFallback) as React.ComponentType<PluginPageProps>;

function RealPlugin(props: PluginPageProps): React.ReactNode {
  const store = useStore();

  const queryParams = useQueryParams();
  const page = queryParams.get('page') || 'incidents';

  return (
    <RealPluginPage {...props}>
      <Header page={page} backendLicense={store.backendLicense} />
      <h3 className="page-title">{pages[page].text}</h3>
      {props.children}
    </RealPluginPage>
  );
}

function PluginPageFallback(props: PluginPageProps): React.ReactNode {
  return props.children;
}
