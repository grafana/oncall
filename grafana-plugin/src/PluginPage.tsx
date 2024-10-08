import React from 'react';

import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';
import { DEFAULT_PAGE } from 'helpers/consts';
import { Header } from 'navbar/Header/Header';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { pages } from 'pages/pages';

interface AppPluginPageProps extends PluginPageProps {
  page?: string;
}

export const PluginPage = RealPlugin as React.ComponentType<AppPluginPageProps>;

function RealPlugin(props: AppPluginPageProps): React.ReactNode {
  const { page } = props;
  const isDefaultPage = page === DEFAULT_PAGE;

  return (
    <RealPluginPage {...props}>
      <RenderConditionally shouldRender={isDefaultPage}>
        <Header />
      </RenderConditionally>

      {pages[page]?.text && !pages[page]?.hideTitle && (
        <h3 className="page-title" data-testid="page-title">
          {pages[page].text}
        </h3>
      )}
      {props.children}
    </RealPluginPage>
  );
}
