import React from 'react';

import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';
import Header from 'navbar/Header/Header';

import Alerts from 'containers/Alerts/Alerts';
import { pages } from 'pages';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';

export const PluginPage = (isTopNavbar() ? RealPlugin : PluginPageFallback) as React.ComponentType<PluginPageProps>;

function RealPlugin(props: PluginPageProps): React.ReactNode {
  const { page } = props;
  const store = useStore();

  return (
    <RealPluginPage {...props}>
      {/* Render alerts at the top */}
      <Alerts />
      <Header page={page} backendLicense={store.backendLicense} />
      {pages[page]?.text && <h3 className="page-title">{pages[page].text}</h3>}
      {props.children}
    </RealPluginPage>
  );
}

export function PluginPageFallback(props: PluginPageProps): React.ReactNode {
  return props.children;
}
