import React from 'react';

import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';
import Header from 'navbar/Header/Header';

import { pages } from 'pages';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';

export const PluginPage = (
  isTopNavbar() ? RealPlugin : PluginPageFallback
) as React.ComponentType<ExtendedPluginPageProps>;

interface ExtendedPluginPageProps extends PluginPageProps {
  renderAlertsFn?: () => React.ReactNode;
  page: string;
}

function RealPlugin(props: ExtendedPluginPageProps): React.ReactNode {
  const { page } = props;
  const store = useStore();

  return (
    <RealPluginPage {...props}>
      {/* Render alerts at the top */}
      {props.renderAlertsFn && props.renderAlertsFn()}
      <Header page={page} backendLicense={store.backendLicense} />
      {pages[page]?.text && <h3 className="page-title">{pages[page].text}</h3>}
      {props.children}
    </RealPluginPage>
  );
}

function PluginPageFallback(props: ExtendedPluginPageProps): React.ReactNode {
  return props.children;
}
