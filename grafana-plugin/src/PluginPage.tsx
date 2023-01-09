import React from 'react';

import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';
import Header from 'navbar/Header/Header';

import { pages } from 'pages';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';
import { DEFAULT_PAGE } from 'utils/consts';
import { useQueryParams } from 'utils/hooks';

export const PluginPage = (
  isTopNavbar() ? RealPlugin : PluginPageFallback
) as React.ComponentType<ExtendedPluginPageProps>;

interface ExtendedPluginPageProps extends PluginPageProps {
  renderAlertsFn?: () => React.ReactNode;
}

function RealPlugin(props: ExtendedPluginPageProps): React.ReactNode {
  const store = useStore();

  const queryParams = useQueryParams();
  const page = queryParams.get('page') || DEFAULT_PAGE;

  return (
    <RealPluginPage {...props}>
      {/* Render alerts at the top */}
      {props.renderAlertsFn && props.renderAlertsFn()}
      <Header page={page} backendLicense={store.backendLicense} />
      {pages[page].text && <h3 className="page-title">{pages[page].text}</h3>}
      {props.children}
    </RealPluginPage>
  );
}

function PluginPageFallback(props: ExtendedPluginPageProps): React.ReactNode {
  return props.children;
}
