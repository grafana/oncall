import React, { useEffect, useMemo, useState } from 'react';

import { initializeFaro, getWebInstrumentations, ReactIntegration, ReactRouterVersion } from '@grafana/faro-react';
import { TracingInstrumentation } from '@grafana/faro-web-tracing';
import { locationService } from '@grafana/runtime';
import classnames from 'classnames';
import dayjs from 'dayjs';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import isoWeek from 'dayjs/plugin/isoWeek';
import localeData from 'dayjs/plugin/localeData';
import timezone from 'dayjs/plugin/timezone';
import { Route, useHistory } from 'react-router';

import utc from 'dayjs/plugin/utc';
import weekday from 'dayjs/plugin/weekday';
import { observer, Provider } from 'mobx-react';
import Header from 'navbar/Header/Header';
import LegacyNavTabsBar from 'navbar/LegacyNavTabsBar';
import { AppRootProps } from 'types';

import Unauthorized from 'components/Unauthorized';
import DefaultPageLayout from 'containers/DefaultPageLayout/DefaultPageLayout';
import 'interceptors';
import { pages } from 'pages';
import { routes } from 'pages/routes';
import { rootStore } from 'state';
import { useStore } from 'state/useStore';
import { isUserActionAllowed } from 'utils/authorization';
import { useQueryParams, useQueryPath } from 'utils/hooks';

import { FaroErrorBoundary } from '@grafana/faro-react';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(weekday);
dayjs.extend(localeData);
dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);
dayjs.extend(isoWeek);

import 'style/vars.css';
import 'style/global.css';
import 'style/utils.css';

import { getQueryParams, isTopNavbar } from './GrafanaPluginRootPage.helpers';
import PluginSetup from './PluginSetup';

import { RootBaseStore } from 'state/rootBaseStore';

export const GrafanaPluginRootPage = (props: AppRootProps) => (
  <Provider store={rootStore}>
    <PluginSetup InitializedComponent={Root} {...props} />
  </Provider>
);

export const Root = observer((props: AppRootProps) => {
  const [didFinishLoading, setDidFinishLoading] = useState(false);
  const queryParams = useQueryParams();
  const page = queryParams.get('page');
  const path = useQueryPath();

  // Required to support grafana instances that use a custom `root_url`.
  const pathWithoutLeadingSlash = path.replace(/^\//, '');

  const store = useStore();
  const history = useHistory();

  useEffect(() => {
    updateBasicData();
  }, []);

  useEffect(() => {
    let link = document.createElement('link');
    link.type = 'text/css';
    link.rel = 'stylesheet';
    link.href = '/public/plugins/grafana-oncall-app/img/grafanaGlobalStyles.css';

    document.head.appendChild(link);

    initFaro(store, history);

    return () => {
      document.head.removeChild(link);
    };
  }, []);

  const updateBasicData = async () => {
    await store.updateBasicData();
    setDidFinishLoading(true);
  };

  const Page = useMemo(() => getPageMatchingComponent(page), [page]);

  if (!didFinishLoading) {
    return null;
  }

  const { action: pagePermissionAction } = pages[page];
  const userHasAccess = pagePermissionAction ? isUserActionAllowed(pagePermissionAction) : true;

  return (
    <FaroErrorBoundary>
      <DefaultPageLayout {...props}>
        {!isTopNavbar() && (
          <>
            <Header page={page} backendLicense={store.backendLicense} />
            <nav className="page-container">
              <LegacyNavTabsBar currentPage={page} />
            </nav>
          </>
        )}

        <div
          className={classnames(
            { 'page-container': !isTopNavbar() },
            { 'page-body': !isTopNavbar() },
            'u-position-relative'
          )}
        >
          {userHasAccess ? (
            <Page {...props} query={...getQueryParams()} path={pathWithoutLeadingSlash} store={store} />
          ) : (
            <Unauthorized requiredUserAction={pagePermissionAction} />
          )}
        </div>
      </DefaultPageLayout>
    </FaroErrorBoundary>
  );
});

function initFaro(store: RootBaseStore, history: any) {
  const faro = initializeFaro({
    url: `http://localhost:${''}/collect`,
    apiKey: '',
    instrumentations: [
      ...getWebInstrumentations({
        captureConsole: true,
      }),
      new TracingInstrumentation(),
      new ReactIntegration({
        router: {
          version: ReactRouterVersion.V5,
          dependencies: {
            history,
            Route,
          },
        },
      }),
    ],
    session: (window as any).__PRELOADED_STATE__?.faro?.session,
    app: {
      name: '',
      version: '',
      environment: '',
    },
  });

  faro.api.pushLog(['Faro was initialized for Grafana On Call']);

  store.faro = faro;
}

function getPageMatchingComponent(pageId: string): (props?: any) => JSX.Element {
  let matchingPage = routes[pageId];
  if (!matchingPage) {
    const defaultPageId = pages['incidents'].id;
    matchingPage = routes[defaultPageId];
    locationService.replace(pages[defaultPageId].path);
  }

  return matchingPage.component;
}
